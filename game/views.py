from __future__ import annotations

from io import StringIO

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .constants import FINAL_STAGE, STAGE_COUNT, STAGE_DETAILS, STAGE_GROUP_SIZES
from .models import Player, PodiumSubmission, Run, StageCode
from .services import (
    archive_current_run,
    compute_stage_sum,
    create_player,
    create_test_users,
    pause_current_run,
    process_podium_submission,
    reset_with_archive,
    resolve_pending_submission,
    resume_current_run,
    start_run,
)


def home(request):
    return redirect("join")


def join_view(request):
    run = Run.current()

    if request.method == "POST":
        username = request.POST.get("username", "")
        if not run:
            messages.error(request, "No current run. Ask the teacher to start a run.")
        else:
            try:
                player = create_player(run, username)
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

    stage_codes = {
        stage_code.stage: stage_code.code
        for stage_code in StageCode.objects.filter(player=player).order_by("stage")
    }

    if player.current_stage > FINAL_STAGE:
        current_stage = FINAL_STAGE
        stage_info = None
    else:
        current_stage = player.current_stage
        stage_info = STAGE_DETAILS[current_stage]

    return render(
        request,
        "game/play.html",
        {
            "player": player,
            "stage_info": stage_info,
            "current_stage": current_stage,
            "stage_codes": stage_codes,
            "final_stage": FINAL_STAGE,
            "stage_count": STAGE_COUNT,
            "stage_group_sizes": STAGE_GROUP_SIZES,
            "stage_rules": [(stage, STAGE_GROUP_SIZES[stage]) for stage in range(1, STAGE_COUNT + 1)],
        },
    )


def dataset_download_view(request, user_id: int, stage: int):
    player = get_object_or_404(Player, id=user_id)
    if stage < 1 or stage > STAGE_COUNT:
        raise Http404("Invalid stage")

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
            submitted_by = request.POST.get("submitted_by", "").strip()
            if not raw_code.isdigit():
                messages.error(request, "Code must be numeric.")
            else:
                submission, matches = process_podium_submission(run, int(raw_code), submitted_by=submitted_by)
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
    if run:
        run_players = list(run.players.order_by("current_stage", "username", "id"))
    if pending_submission:
        candidates = list(pending_submission.candidates.order_by("id"))
        candidate_stage_options = sorted({candidate.stage for candidate in candidates})
    candidate_stage_rows = [(stage, STAGE_GROUP_SIZES[stage]) for stage in candidate_stage_options]

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
            "stage_group_sizes": STAGE_GROUP_SIZES,
        },
    )


def _teacher_authenticated(request) -> bool:
    return bool(request.session.get("teacher_authenticated", False))


def _render_teacher(request, run, computed_sum=None, selected_stage=None, selected_user_ids=None):
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
            "computed_sum": computed_sum,
            "selected_stage": selected_stage,
            "selected_user_ids": set(selected_user_ids or []),
            "stage_group_sizes": STAGE_GROUP_SIZES,
            "stage_count": STAGE_COUNT,
            "stage_numbers": range(1, STAGE_COUNT + 1),
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
    computed_sum = None
    selected_stage = None
    selected_user_ids: list[int] = []

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
            elif action == "compute_sum":
                if not run:
                    messages.error(request, "No current run.")
                else:
                    selected_stage = int(request.POST.get("stage", "1"))
                    selected_user_ids = [int(item) for item in request.POST.getlist("selected_user_ids")]
                    computed_sum = compute_stage_sum(run, selected_stage, selected_user_ids)
                    messages.info(request, f"Stage {selected_stage} sum computed.")
            elif action == "logout_teacher":
                request.session["teacher_authenticated"] = False
                return redirect("teacher")
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Teacher action failed: {exc}")

    run = Run.current()
    return _render_teacher(
        request,
        run=run,
        computed_sum=computed_sum,
        selected_stage=selected_stage,
        selected_user_ids=selected_user_ids,
    )
