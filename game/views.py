from __future__ import annotations

from datetime import timedelta
from io import StringIO
import random
import re

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .constants import FINAL_STAGE, STAGE_COUNT, STAGE_GROUP_SIZES
from .models import Player, PodiumSubmission, Run, StageCode
from .stage_content import get_stage_content, stage_has_dataset
from .services import (
    archive_current_run,
    create_player,
    create_test_users,
    pause_current_run,
    process_podium_submission,
    required_group_size,
    reset_with_archive,
    resolve_pending_submission,
    resume_current_run,
    start_run,
)

ORIENTATION_MAX_STEP = 5
JOIN_USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _sync_orientation_step(player: Player) -> None:
    if player.orientation_completed:
        player.orientation_step = ORIENTATION_MAX_STEP
        return
    if not player.orientation_device_type:
        player.orientation_step = 1
        return
    if player.orientation_device_type == Player.OrientationDeviceType.OWN and not player.orientation_os:
        player.orientation_step = 2
        return
    if not player.orientation_language:
        player.orientation_step = 3
        return
    if player.orientation_step < 4:
        player.orientation_step = 4


def _update_orientation(player: Player, event: str, value: str) -> None:
    if event == "toggle_collapsed":
        player.orientation_collapsed = not player.orientation_collapsed
        return

    if event == "choose_device":
        if value not in {Player.OrientationDeviceType.OWN, Player.OrientationDeviceType.UOL}:
            return
        player.orientation_device_type = value
        player.orientation_os = None
        player.orientation_language = None
        player.orientation_completed = False
        player.orientation_collapsed = False
        player.orientation_step = 2 if value == Player.OrientationDeviceType.OWN else 3
        return

    if event == "choose_os":
        if player.orientation_device_type != Player.OrientationDeviceType.OWN:
            return
        allowed = {
            Player.OrientationOS.WINDOWS,
            Player.OrientationOS.MAC,
            Player.OrientationOS.CHROMEBOOK,
            Player.OrientationOS.LINUX,
        }
        if value not in allowed:
            return
        player.orientation_os = value
        if player.orientation_step < 3:
            player.orientation_step = 3
        return

    if event == "choose_language":
        if not player.orientation_device_type:
            return
        if player.orientation_device_type == Player.OrientationDeviceType.OWN and not player.orientation_os:
            return
        allowed = {
            Player.OrientationLanguage.R,
            Player.OrientationLanguage.PYTHON,
            Player.OrientationLanguage.JAVASCRIPT,
        }
        if value not in allowed:
            return
        player.orientation_language = value
        if player.orientation_step < 4:
            player.orientation_step = 4
        return

    if event == "next_step":
        _sync_orientation_step(player)
        if player.orientation_step < ORIENTATION_MAX_STEP:
            player.orientation_step += 1
        return

    if event == "complete":
        _sync_orientation_step(player)
        if player.orientation_device_type and player.orientation_language:
            if player.orientation_device_type == Player.OrientationDeviceType.UOL or player.orientation_os:
                player.orientation_completed = True
                player.orientation_step = ORIENTATION_MAX_STEP
                player.orientation_collapsed = True
        return

    if event == "reopen":
        player.orientation_collapsed = False
        return


def home(request):
    return redirect("join")


def join_view(request):
    run = Run.current()

    if request.method == "POST":
        username = request.POST.get("username", "")
        if not run:
            messages.error(request, "No current run. Ask the teacher to start a run.")
        else:
            username_clean = username.strip()
            existing_player = Player.objects.filter(run=run, username_key=username_clean.lower()).first()
            if existing_player:
                return redirect("play", user_id=existing_player.id)
            if any(char.isspace() for char in username_clean):
                messages.error(request, "User name cannot contain spaces.")
            elif not JOIN_USERNAME_RE.fullmatch(username_clean):
                messages.error(request, "Use only letters, numbers, dot, underscore, or hyphen.")
            elif not any(char.isdigit() for char in username_clean):
                messages.error(request, 'Use a more unique user name. Example: "dave23".')
            else:
                try:
                    player = create_player(run, username_clean)
                except Exception as exc:  # noqa: BLE001
                    messages.error(request, f"Could not join: {exc}")
                else:
                    return redirect("play", user_id=player.id)

    return render(
        request,
        "game/join.html",
        {
            "run": run,
        },
    )


def play_view(request, user_id: int):
    player = get_object_or_404(Player.objects.select_related("run"), id=user_id)
    current_run = Run.current()
    if not current_run or player.run_id != current_run.id:
        return redirect("join")

    now = timezone.now()
    _sync_orientation_step(player)

    if player.current_stage > FINAL_STAGE:
        current_stage = FINAL_STAGE
        stage_info = None
        expected = None
        required_collaborators = 0
    else:
        current_stage = player.current_stage
        expected = StageCode.objects.filter(player=player, stage=current_stage).values_list("code", flat=True).first()
        stage_info = get_stage_content(current_stage, player.orientation_language)
        required_collaborators = max(0, required_group_size(current_run, current_stage) - 1)

    if request.method == "POST" and request.POST.get("action") == "accept_challenge":
        if not player.intro_accepted:
            player.intro_accepted = True
            player.save(update_fields=["intro_accepted"])
        return redirect("play", user_id=player.id)

    if not player.intro_accepted:
        return render(
            request,
            "game/play.html",
            {
                "player": player,
                "stage_info": stage_info,
                "current_stage": current_stage,
                "checker_is_verified": False,
                "checker_solution_code": None,
                "checker_lock_seconds": 0,
                "orientation_is_open": False,
                "orientation_pause_polling": True,
                "orientation_can_choose_language": False,
                "final_stage": FINAL_STAGE,
                "stage_count": STAGE_COUNT,
                "stage_group_sizes": STAGE_GROUP_SIZES,
                "required_collaborators": required_collaborators,
            },
        )

    # Stage progression resets checker lockout state.
    if player.checker_stage and player.checker_stage != current_stage:
        player.checker_fail_count = 0
        player.checker_locked_until = None
        player.checker_stage = current_stage
        player.save(update_fields=["checker_fail_count", "checker_locked_until", "checker_stage"])

    if player.is_complete:
        expected = None
    checker_is_verified = (player.checker_verified_stage == current_stage)
    is_async_checker = (
        request.method == "POST"
        and request.POST.get("action") == "check_solution"
        and (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.POST.get("response_format") == "json"
        )
    )

    def checker_success_message() -> str:
        group_size = required_group_size(current_run, current_stage)
        collaborators = max(0, group_size - 1)
        if collaborators == 0:
            return "Correct. Enter your code into AUGUR PODIUM."
        suffix = "" if collaborators == 1 else "s"
        return (
            f"Correct. Combine your code with {collaborators} collaborator{suffix} "
            "and enter the sum into AUGUR PODIUM."
        )

    def checker_response(level: str, message_text: str, **payload):
        if is_async_checker:
            body = {"ok": level == "success", "level": level, "message": message_text}
            body.update(payload)
            return JsonResponse(body)
        if level == "success":
            messages.success(request, message_text)
        elif level == "info":
            messages.info(request, message_text)
        else:
            messages.error(request, message_text)
        return redirect("play", user_id=player.id)

    if request.method == "POST" and request.POST.get("action") == "orientation_update":
        event = request.POST.get("orientation_event", "").strip()
        value = request.POST.get("orientation_value", "").strip().lower()
        _update_orientation(player, event, value)
        _sync_orientation_step(player)
        player.save(
            update_fields=[
                "orientation_completed",
                "orientation_collapsed",
                "orientation_step",
                "orientation_device_type",
                "orientation_os",
                "orientation_language",
            ]
        )
        return redirect("play", user_id=player.id)

    if request.method == "POST" and request.POST.get("action") == "check_solution":
        if player.is_suspended:
            return checker_response(
                "error",
                "Your account is suspended. Ask the facilitator to reactivate you.",
                checker_verified=False,
            )

        if player.is_complete:
            return checker_response("info", "You already completed all stages.", checker_verified=False)

        if player.checker_stage != current_stage:
            player.checker_stage = current_stage
            player.checker_fail_count = 0
            player.checker_locked_until = None
            player.save(update_fields=["checker_stage", "checker_fail_count", "checker_locked_until"])

        if checker_is_verified:
            return checker_response(
                "info",
                checker_success_message(),
                checker_verified=True,
                checker_solution_code=expected,
            )

        if player.checker_locked_until and player.checker_locked_until > now:
            remaining = max(1, int((player.checker_locked_until - now).total_seconds()))
            return checker_response(
                "error",
                f"Checker locked. Try again in {remaining} seconds.",
                checker_verified=False,
                checker_lock_seconds=remaining,
            )

        submitted_raw = request.POST.get("personal_code", "").strip()
        if not submitted_raw.isdigit():
            return checker_response("error", "Enter a numeric code.", checker_verified=False)

        if expected is None:
            return checker_response("error", "No code found for your current stage.", checker_verified=False)

        submitted = int(submitted_raw)
        if submitted == expected:
            player.checker_fail_count = 0
            player.checker_locked_until = None
            player.checker_stage = current_stage
            player.checker_verified_stage = current_stage
            player.save(update_fields=["checker_fail_count", "checker_locked_until", "checker_stage", "checker_verified_stage"])
            return checker_response(
                "success",
                checker_success_message(),
                checker_verified=True,
                checker_solution_code=expected,
                checker_lock_seconds=0,
            )

        player.checker_fail_count += 1
        if player.checker_fail_count == 1:
            lock_seconds = 30
        elif player.checker_fail_count == 2:
            lock_seconds = 60
        else:
            lock_seconds = 120
        player.checker_locked_until = now + timedelta(seconds=lock_seconds)
        player.checker_stage = current_stage
        player.save(update_fields=["checker_fail_count", "checker_locked_until", "checker_stage"])

        direction = "too low" if submitted < expected else "too high"
        return checker_response(
            "error",
            f"Incorrect: {direction}. Wait {lock_seconds} seconds.",
            checker_verified=False,
            checker_lock_seconds=lock_seconds,
        )

    checker_lock_seconds = 0
    if (not checker_is_verified) and player.checker_locked_until and player.checker_locked_until > now:
        checker_lock_seconds = max(1, int((player.checker_locked_until - now).total_seconds()))
    orientation_is_open = not player.orientation_collapsed
    orientation_pause_polling = orientation_is_open and not player.orientation_completed
    orientation_can_choose_language = bool(player.orientation_device_type) and (
        player.orientation_device_type != Player.OrientationDeviceType.OWN or bool(player.orientation_os)
    )

    return render(
        request,
        "game/play.html",
        {
            "player": player,
            "stage_info": stage_info,
            "current_stage": current_stage,
            "checker_is_verified": checker_is_verified,
            "checker_solution_code": expected if checker_is_verified else None,
            "checker_lock_seconds": checker_lock_seconds,
            "orientation_is_open": orientation_is_open,
            "orientation_pause_polling": orientation_pause_polling,
            "orientation_can_choose_language": orientation_can_choose_language,
            "final_stage": FINAL_STAGE,
            "stage_count": STAGE_COUNT,
            "stage_group_sizes": STAGE_GROUP_SIZES,
            "required_collaborators": required_collaborators,
        },
    )


def dataset_download_view(request, user_id: int, stage: int):
    player = get_object_or_404(Player, id=user_id)
    if stage < 1 or stage > STAGE_COUNT:
        raise Http404("Invalid stage")
    if not stage_has_dataset(stage):
        raise Http404("No dataset is configured for this stage")
    if stage == 1:
        stage_code = (
            StageCode.objects.filter(player=player, stage=1).values_list("code", flat=True).first()
        )
        if stage_code is None:
            raise Http404("Stage 1 code not found")

        digits = [int(ch) for ch in f"{int(stage_code):06d}"]
        rng = random.Random(f"stage1:{player.id}:{stage_code}:{player.username_key}")
        rows: list[dict[str, int]] = []

        for pos, digit in enumerate(digits, start=1):
            key = rng.randint(11, 97)
            encoded = (digit + key + (pos * 3)) % 10
            rows.append({"keep": 1, "pos": pos, "key": key, "encoded": encoded})

        for _ in range(8):
            rows.append(
                {
                    "keep": 0,
                    "pos": rng.randint(1, 9),
                    "key": rng.randint(11, 97),
                    "encoded": rng.randint(0, 9),
                }
            )

        rng.shuffle(rows)
        handle = StringIO()
        handle.write("record_id,keep,pos,key,encoded\n")
        for idx, row in enumerate(rows, start=1):
            handle.write(f"{idx},{row['keep']},{row['pos']},{row['key']},{row['encoded']}\n")

        response = HttpResponse(handle.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="stage_{stage}_dataset_{player.username}.csv"'
        return response

    rng_base = (player.id * 97) + (stage * 13)
    handle = StringIO()
    handle.write("record_id,value\n")
    for idx in range(1, 11):
        value = (rng_base + idx * 17) % 10000
        handle.write(f"{idx},{value}\n")

    response = HttpResponse(handle.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="stage_{stage}_dataset_{player.username}.csv"'
    return response


def _get_pending_submission(run: Run, submission_id: str | None) -> PodiumSubmission | None:
    if not submission_id:
        return None
    try:
        parsed = int(submission_id)
    except ValueError:
        return None
    return PodiumSubmission.objects.filter(
        id=parsed,
        run=run,
        status=PodiumSubmission.Status.PENDING,
    ).first()


def podium_view(request):
    run = Run.current()
    latest_submission = None
    matches = []

    pending_submission = None
    if run:
        pending_submission = _get_pending_submission(run, request.GET.get("submission"))

    if request.method == "POST":
        action = request.POST.get("action", "submit")
        if not run:
            messages.error(request, "No current run is available.")
        elif action == "submit":
            raw_code = request.POST.get("code", "").strip()
            if not raw_code.isdigit():
                messages.error(request, "Code must be numeric.")
            else:
                submission, matches = process_podium_submission(run, int(raw_code), submitted_by="")
                latest_submission = submission
                if submission.status == PodiumSubmission.Status.PENDING:
                    return redirect(f"{reverse('podium')}?submission={submission.id}")
                if submission.status == PodiumSubmission.Status.ACCEPTED:
                    messages.success(request, submission.message)
                else:
                    messages.error(request, submission.message)
        elif action == "resolve":
            if run.status == Run.Status.PAUSED:
                messages.error(request, "Run is paused. Podium is temporarily disabled.")
            else:
                submission_id = request.POST.get("submission_id", "")
                stage_raw = request.POST.get("stage", "")
                member_ids = request.POST.getlist("member_ids")
                pending_submission = _get_pending_submission(run, submission_id)
                if not pending_submission:
                    messages.error(request, "Pending submission was not found.")
                else:
                    try:
                        stage = int(stage_raw)
                        selected_ids = [int(item) for item in member_ids]
                        resolved = resolve_pending_submission(pending_submission, stage, selected_ids)
                        latest_submission = resolved
                        pending_submission = None
                        messages.success(request, resolved.message)
                    except Exception as exc:  # noqa: BLE001
                        messages.error(request, f"Could not resolve submission: {exc}")

    candidate_stage_options: list[int] = []
    candidates = []
    run_players = []
    submission_log = []
    if run:
        run_players = list(run.players.order_by("current_stage", "username", "id"))
        submissions = list(run.submissions.order_by("-submitted_at"))
        for submission in submissions:
            if submission.status == PodiumSubmission.Status.ACCEPTED:
                status_label = "Resolved"
            elif submission.status == PodiumSubmission.Status.INVALID:
                status_label = "Rejected"
            else:
                status_label = "Pending"

            stage_completed = f"Stage {submission.stage}" if submission.stage else "-"
            progressed = ", ".join(submission.progressed_usernames) if submission.progressed_usernames else "-"
            submission_log.append(
                {
                    "id": submission.id,
                    "timestamp": submission.submitted_at,
                    "code": submission.submitted_sum,
                    "status_label": status_label,
                    "stage_completed": stage_completed,
                    "progressed_usernames": progressed,
                }
            )
    if pending_submission:
        candidates = list(pending_submission.candidates.order_by("id"))
        candidate_stage_options = sorted({candidate.stage for candidate in candidates})
    candidate_stage_rows = [(stage, required_group_size(run, stage)) for stage in candidate_stage_options] if run else []

    return render(
        request,
        "game/podium.html",
        {
            "run": run,
            "latest_submission": latest_submission,
            "matches": matches,
            "pending_submission": pending_submission,
            "candidates": candidates,
            "candidate_stage_rows": candidate_stage_rows,
            "run_players": run_players,
            "submission_log": submission_log,
            "stage_group_sizes": STAGE_GROUP_SIZES,
        },
    )


def _teacher_authenticated(request) -> bool:
    return bool(request.session.get("teacher_authenticated", False))


def _render_teacher(request, run):
    players = []
    stage_codes = {}
    if run:
        players = list(run.players.order_by("id"))
        for stage_code in StageCode.objects.filter(run=run).order_by("player_id", "stage"):
            stage_codes.setdefault(stage_code.player_id, {})[stage_code.stage] = stage_code.code

    return render(
        request,
        "game/teacher.html",
        {
            "authed": _teacher_authenticated(request),
            "run": run,
            "players": players,
            "stage_codes": stage_codes,
            "stage_group_sizes": STAGE_GROUP_SIZES,
            "stage_count": STAGE_COUNT,
            "stage_numbers": range(1, STAGE_COUNT + 1),
            "collaboration_size_cap": run.collaboration_size_cap if run else None,
        },
    )


def teacher_view(request):
    if request.method == "POST" and request.POST.get("action") == "teacher_login":
        passcode = request.POST.get("passcode", "")
        if passcode == settings.TEACHER_PASSCODE:
            request.session["teacher_authenticated"] = True
            messages.success(request, "Teacher access granted.")
            return redirect("teacher")
        messages.error(request, "Invalid teacher passcode.")

    if not _teacher_authenticated(request):
        return _render_teacher(request, run=Run.current())

    run = Run.current()

    if request.method == "POST":
        action = request.POST.get("action", "")

        try:
            if action == "start_run":
                run = start_run()
                messages.success(request, "Run started.")
            elif action == "pause_run":
                run = pause_current_run()
                messages.success(request, "Run paused.")
            elif action == "resume_run":
                run = resume_current_run()
                messages.success(request, "Run resumed.")
            elif action == "archive_run":
                if run:
                    archive_current_run()
                    run = None
                    messages.success(request, "Run archived.")
                else:
                    messages.error(request, "No current run to archive.")
            elif action == "reset_run":
                run = reset_with_archive()
                messages.success(request, "Run archived and reset to a fresh run.")
            elif action == "create_test_users":
                if not run:
                    messages.error(request, "No current run. Start one first.")
                else:
                    n_users = int(request.POST.get("n_users", "0"))
                    if n_users < 1:
                        messages.error(request, "n must be at least 1.")
                    else:
                        created = create_test_users(run, n_users)
                        messages.success(request, f"Created {len(created)} test users.")
            elif action == "set_collaboration_cap":
                if not run:
                    messages.error(request, "No current run.")
                else:
                    cap_value = int(request.POST.get("collaboration_size_cap", "0"))
                    if cap_value < 1 or cap_value > 8:
                        messages.error(request, "Collaboration cap must be between 1 and 8.")
                    else:
                        run.collaboration_size_cap = cap_value
                        run.save(update_fields=["collaboration_size_cap"])
                        messages.success(request, f"Collaboration size override set to {cap_value}.")
            elif action == "clear_collaboration_cap":
                if not run:
                    messages.error(request, "No current run.")
                else:
                    run.collaboration_size_cap = None
                    run.save(update_fields=["collaboration_size_cap"])
                    messages.success(request, "Collaboration size override cleared.")
            elif action == "suspend_user":
                if not run:
                    messages.error(request, "No current run.")
                else:
                    username = request.POST.get("username", "").strip()
                    if not username:
                        messages.error(request, "Enter a username.")
                    else:
                        player = Player.objects.filter(run=run, username_key=username.lower()).first()
                        if not player:
                            messages.error(request, f'User "{username}" was not found in the current run.')
                        elif player.is_suspended:
                            messages.info(request, f'{player.username} is already suspended.')
                        else:
                            player.is_suspended = True
                            player.save(update_fields=["is_suspended"])
                            messages.success(request, f"{player.username} has been suspended.")
            elif action == "reactivate_user":
                if not run:
                    messages.error(request, "No current run.")
                else:
                    username = request.POST.get("username", "").strip()
                    if not username:
                        messages.error(request, "Enter a username.")
                    else:
                        player = Player.objects.filter(run=run, username_key=username.lower()).first()
                        if not player:
                            messages.error(request, f'User "{username}" was not found in the current run.')
                        elif not player.is_suspended:
                            messages.info(request, f"{player.username} is already active.")
                        else:
                            player.is_suspended = False
                            player.save(update_fields=["is_suspended"])
                            messages.success(request, f"{player.username} has been reactivated.")
            elif action == "logout_teacher":
                request.session["teacher_authenticated"] = False
                return redirect("teacher")
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Teacher action failed: {exc}")

        # Post/Redirect/Get: avoid form re-submission prompts during auto-polling refreshes.
        return redirect("teacher")

    run = Run.current()
    return _render_teacher(request, run=run)
