from __future__ import annotations

import binascii
from collections import defaultdict
from datetime import timedelta
from io import BytesIO, StringIO
import math
import random
import re
import struct
import zipfile
import zlib

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .constants import FINAL_STAGE, STAGE_COUNT, STAGE_GROUP_SIZES
from .models import Player, PlayerFeedback, PodiumSubmission, Run, StageCode
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

FEEDBACK_LIKERT_SECTIONS = [
    (
        "Section 1: Overall experience",
        [
            ("session_engaging", "I found the session engaging."),
            ("scenario_meaningful", "The scenario helped make the coding tasks feel more meaningful."),
            ("challenge_appropriate", "The level of challenge was appropriate for me."),
            ("different_workshop_positive", "The session felt different from a normal coding workshop in a positive way."),
        ],
    ),
    (
        "Section 2: Collaboration and support",
        [
            ("worked_effectively_with_others", "I worked effectively with other students during the session."),
            ("instructions_clear", "The instructions were clear enough for me to get started."),
        ],
    ),
    (
        "Section 3: Overall impact",
        [
            ("recommend_to_student", "I would recommend this session to another student."),
            ("attend_again", "I would be interested in attending another session using this format."),
        ],
    ),
]

FEEDBACK_OPEN_QUESTIONS = [
    ("best_part", "What was the best part of the session?"),
    ("improve_future", "What one thing would improve the session for future students?"),
]


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
    completion_feedback = None
    completion_feedback_submitted = False
    completion_flow_eligible = False

    if player.is_complete:
        final_submissions = player.run.submissions.filter(
            status=PodiumSubmission.Status.ACCEPTED,
            stage=FINAL_STAGE,
        ).order_by("-resolved_at", "-submitted_at")
        completion_flow_eligible = any(
            player.username in (submission.progressed_usernames or [])
            for submission in final_submissions
        )
        if completion_flow_eligible:
            completion_feedback = PlayerFeedback.objects.filter(player=player).first()
            completion_feedback_submitted = completion_feedback is not None

    if player.current_stage > FINAL_STAGE:
        current_stage = FINAL_STAGE
        stage_info = None
        expected = None
        required_collaborators = 0
        waiting_for_collaborators = False
    else:
        current_stage = player.current_stage
        expected = StageCode.objects.filter(player=player, stage=current_stage).values_list("code", flat=True).first()
        stage_info = get_stage_content(current_stage, player.orientation_language)
        available_count = Player.objects.filter(
            run=current_run,
            current_stage=current_stage,
            is_suspended=False,
        ).count()
        current_group_size = required_group_size(current_run, current_stage, available_count=available_count)
        required_collaborators = max(0, current_group_size - 1)
        waiting_for_collaborators = current_group_size > 1 and available_count <= 1

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
                "waiting_for_collaborators": waiting_for_collaborators,
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
        available_count = Player.objects.filter(
            run=current_run,
            current_stage=current_stage,
            is_suspended=False,
        ).count()
        group_size = required_group_size(current_run, current_stage, available_count=available_count)
        if group_size > 1 and available_count <= 1:
            return (
                "Correct. Your personal code is verified. Wait until more players reach this stage, "
                "then combine your codes and enter the sum into AUGUR PODIUM."
            )
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

    if request.method == "POST" and request.POST.get("action") == "submit_feedback":
        if not completion_flow_eligible:
            messages.error(request, "Feedback is only available after final stage completion.")
            return redirect("play", user_id=player.id)

        likert_items = [item for _, items in FEEDBACK_LIKERT_SECTIONS for item in items]
        likert_answers: dict[str, int] = {}
        for field_name, _label in likert_items:
            raw = request.POST.get(field_name, "").strip()
            if not raw.isdigit():
                messages.error(request, "Please select a 1-5 rating for every question.")
                return redirect("play", user_id=player.id)
            value = int(raw)
            if value < 1 or value > 5:
                messages.error(request, "Ratings must be between 1 and 5.")
                return redirect("play", user_id=player.id)
            likert_answers[field_name] = value

        open_answers: dict[str, str] = {}
        for field_name, _label in FEEDBACK_OPEN_QUESTIONS:
            open_answers[field_name] = request.POST.get(field_name, "").strip()[:3000]

        legacy_comments = (
            "\n".join(
                [
                    f"{label} {open_answers.get(field_name, '')}"
                    for field_name, label in FEEDBACK_OPEN_QUESTIONS
                ]
            )
        )[:3000]
        PlayerFeedback.objects.update_or_create(
            player=player,
            defaults={
                "run": player.run,
                "clarity_rating": likert_answers["instructions_clear"],
                "engagement_rating": likert_answers["session_engaging"],
                "collaboration_rating": likert_answers["worked_effectively_with_others"],
                "confidence_rating": likert_answers["recommend_to_student"],
                "pacing_rating": likert_answers["challenge_appropriate"],
                "comments": legacy_comments,
                "likert_responses": likert_answers,
                "open_responses": open_answers,
            },
        )
        messages.success(request, "Thanks for your feedback.")
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
            "waiting_for_collaborators": waiting_for_collaborators,
            "completion_flow_eligible": completion_flow_eligible,
            "completion_feedback_submitted": completion_feedback_submitted,
            "show_completion_modal": completion_flow_eligible and not completion_feedback_submitted,
            "completion_feedback": completion_feedback,
            "feedback_likert_sections": FEEDBACK_LIKERT_SECTIONS,
            "feedback_open_questions": FEEDBACK_OPEN_QUESTIONS,
        },
    )


def dataset_download_view(request, user_id: int, stage: int):
    player = get_object_or_404(Player, id=user_id)
    if stage < 1 or stage > STAGE_COUNT:
        raise Http404("Invalid stage")
    if not stage_has_dataset(stage):
        raise Http404("No dataset is configured for this stage")
    dataset_filename = f"stage{stage}_dataset.csv"
    if stage == 3:
        dataset_filename = "stage3_signal_readings.csv"
    if stage == 4:
        dataset_filename = "stage4_drone_fleet.zip"
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
        response["Content-Disposition"] = f'attachment; filename="{dataset_filename}"'
        return response
    if stage == 2:
        stage_code = (
            StageCode.objects.filter(player=player, stage=2).values_list("code", flat=True).first()
        )
        if stage_code is None:
            raise Http404("Stage 2 code not found")

        target_code = int(stage_code)
        rng = random.Random(f"stage2:{player.id}:{stage_code}:{player.username_key}")
        sectors = ["power", "traffic", "water", "emergency", "communications", "waste", "transit"]
        invalid_statuses = ["INACTIVE", "COMPLETE", "DEFERRED", "QUEUED"]

        rows: list[dict[str, int | str]] = []
        row_modes = ["valid", "bad_status", "fake", "low_priority", "combo"]

        def build_row(mode: str, forced_sector: str | None = None) -> dict[str, int | str]:
            sector = forced_sector or rng.choice(sectors)
            units = rng.randint(6, 180)
            multiplier = rng.randint(4, 140)
            if mode == "valid":
                status = "ACTIVE"
                authentic = 1
                priority = rng.randint(4, 7)
            elif mode == "bad_status":
                status = rng.choice(invalid_statuses)
                authentic = 1
                priority = rng.randint(4, 7)
            elif mode == "fake":
                status = "ACTIVE"
                authentic = 0
                priority = rng.randint(4, 7)
            elif mode == "low_priority":
                status = "ACTIVE"
                authentic = 1
                priority = rng.randint(1, 3)
            else:
                status = rng.choice(invalid_statuses)
                authentic = rng.choice([0, 1])
                priority = rng.randint(1, 3)

            return {
                "record_id": "",
                "sector": sector,
                "status": status,
                "authentic": authentic,
                "priority": priority,
                "units": units,
                "multiplier": multiplier,
                "bias_key": 0,
            }

        # Force coverage of all sectors plus each invalid reason.
        forced_modes = ["valid", "bad_status", "fake", "low_priority", "combo", "valid", "fake"]
        for sector, mode in zip(sectors, forced_modes):
            rows.append(build_row(mode, forced_sector=sector))

        # Generate a realistic mixed ledger where only some rows are valid.
        while len(rows) < 84:
            rows.append(build_row(rng.choice(row_modes)))

        def is_valid(row: dict[str, int | str]) -> bool:
            return (
                row["status"] == "ACTIVE"
                and int(row["authentic"]) == 1
                and int(row["priority"]) >= 4
            )

        base_total = sum(int(row["units"]) * int(row["multiplier"]) for row in rows if is_valid(row))
        modulus = 1_000_000

        candidate_adjustments = list(range(0, 20_001))
        rng.shuffle(candidate_adjustments)
        bias_key = None
        adjustment = None
        for candidate_adjustment in candidate_adjustments:
            candidate_bias = (target_code - base_total - candidate_adjustment) % modulus
            if 1000 <= candidate_bias <= 9999:
                bias_key = candidate_bias
                adjustment = candidate_adjustment
                break
        if bias_key is None or adjustment is None:
            bias_key = rng.randint(1000, 9999)
            adjustment = (target_code - base_total - bias_key) % modulus

        def factor_pair(value: int) -> tuple[int, int] | None:
            pairs: list[tuple[int, int]] = []
            for multiplier_candidate in range(5, 141):
                if value % multiplier_candidate != 0:
                    continue
                units_candidate = value // multiplier_candidate
                if 6 <= units_candidate <= 220:
                    pairs.append((units_candidate, multiplier_candidate))
            if pairs:
                return rng.choice(pairs)
            if value <= 220:
                return (value, 1)
            return None

        def split_adjustment(total_adjustment: int) -> list[tuple[int, int]]:
            if total_adjustment == 0:
                return []

            for _ in range(400):
                max_parts = min(4, max(1, total_adjustment))
                parts_count = rng.randint(1, max_parts)
                if parts_count == 1:
                    pieces = [total_adjustment]
                else:
                    cuts = sorted(rng.sample(range(1, total_adjustment), parts_count - 1))
                    points = [0, *cuts, total_adjustment]
                    pieces = [points[idx + 1] - points[idx] for idx in range(parts_count)]

                factored: list[tuple[int, int]] = []
                ok = True
                for piece in pieces:
                    pair = factor_pair(piece)
                    if pair is None:
                        ok = False
                        break
                    factored.append(pair)
                if ok:
                    return factored

            fallback: list[tuple[int, int]] = []
            remaining = total_adjustment
            while remaining > 0:
                piece = min(remaining, 220)
                fallback.append((piece, 1))
                remaining -= piece
            return fallback

        adjustment_pairs = split_adjustment(adjustment)
        for units, multiplier in adjustment_pairs:
            rows.append(
                {
                    "record_id": "",
                    "sector": rng.choice(sectors),
                    "status": "ACTIVE",
                    "authentic": 1,
                    "priority": rng.randint(4, 7),
                    "units": units,
                    "multiplier": multiplier,
                    "bias_key": bias_key,
                }
            )

        for row in rows:
            row["bias_key"] = bias_key

        rng.shuffle(rows)
        for idx, row in enumerate(rows, start=1):
            row["record_id"] = f"R{idx:04d}"

        verified_total = sum(int(row["units"]) * int(row["multiplier"]) for row in rows if is_valid(row))
        decoded = (verified_total + int(bias_key)) % modulus
        if decoded != target_code:
            raise RuntimeError("Stage 2 dataset verification failed")

        handle = StringIO()
        handle.write("record_id,sector,status,authentic,priority,units,multiplier,bias_key\n")
        for row in rows:
            handle.write(
                f"{row['record_id']},{row['sector']},{row['status']},{row['authentic']},{row['priority']},"
                f"{row['units']},{row['multiplier']},{row['bias_key']}\n"
            )

        response = HttpResponse(handle.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{dataset_filename}"'
        return response
    if stage == 3:
        stage_code = (
            StageCode.objects.filter(player=player, stage=3).values_list("code", flat=True).first()
        )
        if stage_code is None:
            raise Http404("Stage 3 code not found")

        target_code = int(stage_code)
        readings_per_district = 96

        districts = [
            "anfield",
            "aigburth",
            "allerton",
            "birkenhead",
            "bootle",
            "broadgreen",
            "childwall",
            "crosby",
            "everton",
            "fazakerley",
            "garston",
            "huyton",
            "kirkby",
            "kirkdale",
            "knotty_ash",
            "maghull",
            "mossley_hill",
            "old_swan",
            "prescot",
            "sefton_park",
            "speke",
            "toxteth",
            "wavertree",
            "west_derby",
            "woolton",
        ]
        def _welch_t(values_a: list[float], values_b: list[float]) -> tuple[float, float]:
            if len(values_a) < 2 or len(values_b) < 2:
                return 0.0, 1.0
            mean_a = sum(values_a) / len(values_a)
            mean_b = sum(values_b) / len(values_b)
            var_a = sum((value - mean_a) ** 2 for value in values_a) / (len(values_a) - 1)
            var_b = sum((value - mean_b) ** 2 for value in values_b) / (len(values_b) - 1)
            se = math.sqrt((var_a / len(values_a)) + (var_b / len(values_b)))
            if se == 0:
                return 0.0, 1.0
            t_stat = (mean_a - mean_b) / se
            p_approx = math.erfc(abs(t_stat) / math.sqrt(2.0))
            return t_stat, p_approx

        def _rank_districts(values_by_district: dict[str, list[float]]) -> list[tuple[int, float, float, str]]:
            ranking_rows: list[tuple[int, float, float, str]] = []
            for district in sorted(values_by_district):
                pair_stats: list[tuple[float, float]] = []
                for other in values_by_district:
                    if other == district:
                        continue
                    t_stat, p_value = _welch_t(values_by_district[district], values_by_district[other])
                    pair_stats.append((t_stat, p_value))
                if not pair_stats:
                    continue
                significant_count = sum(1 for _, p_value in pair_stats if p_value < 0.05)
                avg_abs_t = sum(abs(t_stat) for t_stat, _ in pair_stats) / len(pair_stats)
                ordered_ps = sorted(p_value for _, p_value in pair_stats)
                mid_idx = len(ordered_ps) // 2
                median_p = (
                    ordered_ps[mid_idx]
                    if len(ordered_ps) % 2 == 1
                    else (ordered_ps[mid_idx - 1] + ordered_ps[mid_idx]) / 2
                )
                ranking_rows.append((significant_count, avg_abs_t, -median_p, district))
            ranking_rows.sort(reverse=True)
            return ranking_rows

        def _assign_codes(
            candidate_rows: list[dict[str, str | int | float]],
            answer_district: str,
            candidate_rng: random.Random,
        ) -> None:
            district_codes: dict[str, int] = {}
            for district in districts:
                if district == answer_district:
                    district_codes[district] = target_code
                    continue
                for _ in range(200):
                    candidate_code = candidate_rng.randint(100000, 999999)
                    if candidate_code != target_code and candidate_code not in district_codes.values():
                        district_codes[district] = candidate_code
                        break
                else:
                    raise RuntimeError("Stage 3 district code generation failed")
            for row in candidate_rows:
                row["district_code"] = district_codes[str(row["district"])]

        rows: list[dict[str, str | int | float]] | None = None
        rng: random.Random | None = None
        for attempt in range(220):
            rng = random.Random(f"stage3:{player.id}:{stage_code}:{player.username_key}:{attempt}")
            abnormal_district = rng.choice(districts)
            candidate_rows: list[dict[str, str | int | float]] = []

            baseline_center = rng.uniform(70.0, 75.0)
            for district in districts:
                mean_offset = rng.uniform(-0.55, 0.55)
                noise_sigma = rng.uniform(0.95, 1.25)

                if district == abnormal_district:
                    # Subtle mean offset + tighter spread: detectable statistically, not obvious visually.
                    mean_offset = rng.choice([-1.0, 1.0]) * rng.uniform(0.28, 0.42)
                    noise_sigma = rng.uniform(0.45, 0.65)

                district_signal_base = baseline_center + mean_offset
                for _ in range(readings_per_district):
                    signal = rng.gauss(district_signal_base, noise_sigma)
                    signal = max(45.0, min(99.9, signal))
                    candidate_rows.append(
                        {
                            "reading_id": "",
                            "district": district,
                            "signal_strength": round(signal, 3),
                            "district_code": 0,
                        }
                    )

            mean_sums: dict[str, float] = defaultdict(float)
            mean_counts: dict[str, int] = defaultdict(int)
            for row in candidate_rows:
                district = str(row["district"])
                mean_sums[district] += float(row["signal_strength"])
                mean_counts[district] += 1
            realized_means = {
                district: mean_sums[district] / mean_counts[district]
                for district in mean_counts
                if mean_counts[district] > 0
            }
            highest_mean_district = max(realized_means, key=realized_means.get)
            lowest_mean_district = min(realized_means, key=realized_means.get)
            if abnormal_district in {highest_mean_district, lowest_mean_district}:
                continue

            values_by_district: dict[str, list[float]] = {}
            for row in candidate_rows:
                district = str(row["district"])
                values_by_district.setdefault(district, []).append(float(row["signal_strength"]))

            ranking_rows = _rank_districts(values_by_district)
            if not ranking_rows:
                continue
            if ranking_rows[0][3] != abnormal_district:
                continue

            _assign_codes(candidate_rows, abnormal_district, rng)
            rows = candidate_rows
            break

        # Fail-safe fallback for rare unlucky seeds: keep subtle data, select best-ranked non-extreme district.
        if rows is None or rng is None:
            for attempt in range(220, 620):
                rng = random.Random(f"stage3:{player.id}:{stage_code}:{player.username_key}:{attempt}")
                candidate_rows = []
                baseline_center = rng.uniform(70.0, 75.0)
                for district in districts:
                    mean_offset = rng.uniform(-0.55, 0.55)
                    noise_sigma = rng.uniform(0.95, 1.25)
                    district_signal_base = baseline_center + mean_offset
                    for _ in range(readings_per_district):
                        signal = rng.gauss(district_signal_base, noise_sigma)
                        signal = max(45.0, min(99.9, signal))
                        candidate_rows.append(
                            {
                                "reading_id": "",
                                "district": district,
                                "signal_strength": round(signal, 3),
                                "district_code": 0,
                            }
                        )

                mean_sums = defaultdict(float)
                mean_counts = defaultdict(int)
                values_by_district = {}
                for row in candidate_rows:
                    district = str(row["district"])
                    value = float(row["signal_strength"])
                    mean_sums[district] += value
                    mean_counts[district] += 1
                    values_by_district.setdefault(district, []).append(value)
                realized_means = {
                    district: mean_sums[district] / mean_counts[district]
                    for district in mean_counts
                    if mean_counts[district] > 0
                }
                highest_mean_district = max(realized_means, key=realized_means.get)
                lowest_mean_district = min(realized_means, key=realized_means.get)

                ranking_rows = _rank_districts(values_by_district)
                if not ranking_rows:
                    continue
                chosen = next(
                    (
                        district
                        for _, _, _, district in ranking_rows
                        if district not in {highest_mean_district, lowest_mean_district}
                    ),
                    ranking_rows[0][3],
                )
                _assign_codes(candidate_rows, chosen, rng)
                rows = candidate_rows
                break

        if rows is None or rng is None:
            raise RuntimeError("Stage 3 subtle dataset generation failed")
        target_districts = {row["district"] for row in rows if int(row["district_code"]) == target_code}
        if len(target_districts) != 1:
            raise RuntimeError("Stage 3 abnormal district code mismatch")

        rng.shuffle(rows)
        for idx, row in enumerate(rows, start=1):
            row["reading_id"] = f"R{idx:04d}"

        handle = StringIO()
        handle.write("reading_id,district,signal_strength,district_code\n")
        for row in rows:
            handle.write(
                f"{row['reading_id']},{row['district']},{row['signal_strength']:.3f},{row['district_code']}\n"
            )

        response = HttpResponse(handle.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{dataset_filename}"'
        return response

    if stage == 4:
        stage_code = (
            StageCode.objects.filter(player=player, stage=4).values_list("code", flat=True).first()
        )
        if stage_code is None:
            raise Http404("Stage 4 code not found")

        rng = random.Random(f"stage4:{player.id}:{stage_code}:{player.username_key}")
        target_code = int(stage_code)
        drone_ids = list(range(1, 21))
        target_drone_id = rng.choice(drone_ids)

        serials: dict[int, int] = {target_drone_id: target_code}
        used_serials = {target_code}
        for drone_id in drone_ids:
            if drone_id == target_drone_id:
                continue
            for _ in range(400):
                candidate = rng.randint(100000, 999999)
                if candidate not in used_serials:
                    serials[drone_id] = candidate
                    used_serials.add(candidate)
                    break
            else:
                raise RuntimeError("Stage 4 serial generation failed")

        width = 360
        height = 360
        margin = 16
        radius = 14
        min_center_sep = (radius * 2) + 3
        min_winner_gap = 3.0
        total_images = 25

        digit_font = {
            "0": ("111", "101", "101", "101", "111"),
            "1": ("010", "110", "010", "010", "111"),
            "2": ("111", "001", "111", "100", "111"),
            "3": ("111", "001", "111", "001", "111"),
            "4": ("101", "101", "111", "001", "001"),
            "5": ("111", "100", "111", "001", "111"),
            "6": ("111", "100", "111", "101", "111"),
            "7": ("111", "001", "001", "001", "001"),
            "8": ("111", "101", "111", "101", "111"),
            "9": ("111", "101", "111", "001", "111"),
        }

        def _clamp(value: int, low: int, high: int) -> int:
            return max(low, min(high, value))

        def _set_px(buf: bytearray, x: int, y: int, color: tuple[int, int, int, int]) -> None:
            if x < 0 or y < 0 or x >= width or y >= height:
                return
            idx = (y * width + x) * 4
            buf[idx] = color[0]
            buf[idx + 1] = color[1]
            buf[idx + 2] = color[2]
            buf[idx + 3] = color[3]

        def _draw_circle(buf: bytearray, cx: int, cy: int, r: int, fill: tuple[int, int, int, int]) -> None:
            r2 = r * r
            for yy in range(cy - r, cy + r + 1):
                for xx in range(cx - r, cx + r + 1):
                    if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r2:
                        _set_px(buf, xx, yy, fill)

        def _draw_text(
            buf: bytearray,
            text: str,
            x: int,
            y: int,
            scale: int = 2,
            color: tuple[int, int, int, int] = (0, 0, 0, 255),
        ) -> None:
            cursor = x
            for char in text:
                pattern = digit_font.get(char)
                if not pattern:
                    cursor += 4 * scale
                    continue
                for row_idx, row_bits in enumerate(pattern):
                    for col_idx, bit in enumerate(row_bits):
                        if bit != "1":
                            continue
                        for sy in range(scale):
                            for sx in range(scale):
                                _set_px(buf, cursor + (col_idx * scale) + sx, y + (row_idx * scale) + sy, color)
                cursor += 4 * scale

        def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
            return (
                struct.pack(">I", len(payload))
                + chunk_type
                + payload
                + struct.pack(">I", binascii.crc32(chunk_type + payload) & 0xFFFFFFFF)
            )

        def _encode_png(buf: bytearray) -> bytes:
            raw = bytearray()
            stride = width * 4
            for y in range(height):
                raw.append(0)  # no filter
                start = y * stride
                raw.extend(buf[start:start + stride])
            compressed = zlib.compress(bytes(raw), level=9)
            signature = b"\x89PNG\r\n\x1a\n"
            ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
            return signature + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", compressed) + _png_chunk(b"IEND", b"")

        archive = BytesIO()
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            csv_handle = StringIO()
            csv_handle.write("drone_id,serial_number\n")
            for drone_id in sorted(drone_ids):
                csv_handle.write(f"{drone_id},{serials[drone_id]:06d}\n")
            zf.writestr("drone_serials.csv", csv_handle.getvalue())

            def _is_valid_position(px: int, py: int, existing: list[tuple[int, int]], min_sep: int) -> bool:
                for ex, ey in existing:
                    if (px - ex) * (px - ex) + (py - ey) * (py - ey) < (min_sep * min_sep):
                        return False
                return True

            def _pick_position(
                existing: list[tuple[int, int]],
                center_x: int,
                center_y: int,
                sigma: float,
                mode: str = "cluster",
            ) -> tuple[int, int]:
                relax_steps = (min_center_sep, min_center_sep - 3, min_center_sep - 6, min_center_sep - 9)

                def _sample_candidate() -> tuple[int, int]:
                    if mode == "ring_far":
                        angle = rng.uniform(0, math.tau)
                        dist = rng.uniform(88.0, 126.0)
                        raw_x = center_x + math.cos(angle) * dist + rng.gauss(0, 6.5)
                        raw_y = center_y + math.sin(angle) * dist + rng.gauss(0, 6.5)
                    elif mode == "scatter":
                        raw_x = rng.uniform(margin, width - margin)
                        raw_y = rng.uniform(margin, height - margin)
                    else:
                        raw_x = rng.gauss(center_x, sigma)
                        raw_y = rng.gauss(center_y, sigma)
                    px = _clamp(int(raw_x), margin, width - margin)
                    py = _clamp(int(raw_y), margin, height - margin)
                    return px, py

                for sep in relax_steps:
                    for _ in range(500):
                        px, py = _sample_candidate()
                        if _is_valid_position(px, py, existing, max(6, sep)):
                            return px, py

                # Final fallback: choose point maximizing minimum distance to existing points.
                best = None
                best_dist2 = -1
                for _ in range(900):
                    px = rng.randint(margin, width - margin)
                    py = rng.randint(margin, height - margin)
                    if not existing:
                        return px, py
                    dist2 = min((px - ex) * (px - ex) + (py - ey) * (py - ey) for ex, ey in existing)
                    if dist2 > best_dist2:
                        best_dist2 = dist2
                        best = (px, py)
                return best if best is not None else (width // 2, height // 2)

            def _pick_farthest_point(existing: list[tuple[int, int]]) -> tuple[int, int]:
                if not existing:
                    return rng.randint(margin, width - margin), rng.randint(margin, height - margin)
                best = (width // 2, height // 2)
                best_dist2 = -1
                for _ in range(1400):
                    px = rng.randint(margin, width - margin)
                    py = rng.randint(margin, height - margin)
                    dist2 = min((px - ex) * (px - ex) + (py - ey) * (py - ey) for ex, ey in existing)
                    if dist2 > best_dist2:
                        best_dist2 = dist2
                        best = (px, py)
                return best

            def _average_distance_scores(frames: list[dict[int, tuple[int, int]]]) -> dict[int, float]:
                total_by_id: dict[int, float] = defaultdict(float)
                seen_by_id: dict[int, int] = defaultdict(int)
                for frame in frames:
                    if len(frame) < 2:
                        continue
                    for drone_id, (px, py) in frame.items():
                        dist_sum = 0.0
                        others = 0
                        for other_id, (ox, oy) in frame.items():
                            if other_id == drone_id:
                                continue
                            dist_sum += math.hypot(px - ox, py - oy)
                            others += 1
                        if others > 0:
                            total_by_id[drone_id] += dist_sum / others
                            seen_by_id[drone_id] += 1
                return {
                    drone_id: (total_by_id[drone_id] / seen_by_id[drone_id])
                    for drone_id in drone_ids
                    if seen_by_id.get(drone_id, 0) > 0
                }

            def _score_winner(scores: dict[int, float], eps: float = 1e-9) -> tuple[int, float]:
                best_id = drone_ids[0]
                best_score = -1.0
                for drone_id in sorted(drone_ids):
                    score = scores.get(drone_id, 0.0)
                    if score > (best_score + eps):
                        best_id = drone_id
                        best_score = score
                    elif abs(score - best_score) <= eps and drone_id < best_id:
                        best_id = drone_id
                        best_score = score
                return best_id, best_score

            def _frame_avg_dist(frame: dict[int, tuple[int, int]], drone_id: int) -> float:
                if drone_id not in frame or len(frame) < 2:
                    return 0.0
                px, py = frame[drone_id]
                dist_sum = 0.0
                count = 0
                for other_id, (ox, oy) in frame.items():
                    if other_id == drone_id:
                        continue
                    dist_sum += math.hypot(px - ox, py - oy)
                    count += 1
                return dist_sum / count if count else 0.0

            def _make_frame(include_target: bool) -> dict[int, tuple[int, int]]:
                drone_count = rng.randint(3, 5)
                if include_target:
                    visible = set(rng.sample(non_target_ids, drone_count - 1))
                    visible.add(target_drone_id)
                else:
                    visible = set(rng.sample(non_target_ids, drone_count))

                center_x = rng.randint(width // 3, (2 * width) // 3)
                center_y = rng.randint(height // 3, (2 * height) // 3)
                positions: dict[int, tuple[int, int]] = {}
                placed_points: list[tuple[int, int]] = []

                if include_target:
                    target_mode = "ring_far" if rng.random() < 0.86 else "cluster"
                    tx, ty = _pick_position(placed_points, center_x, center_y, 66.0, mode=target_mode)
                    positions[target_drone_id] = (tx, ty)
                    placed_points.append((tx, ty))

                for drone_id in sorted(visible):
                    if drone_id == target_drone_id:
                        continue
                    mode = "scatter" if rng.random() < 0.11 else "cluster"
                    sigma = 48.0 if mode == "cluster" else 80.0
                    px, py = _pick_position(placed_points, center_x, center_y, sigma, mode=mode)
                    positions[drone_id] = (px, py)
                    placed_points.append((px, py))

                return positions

            include_target_count = rng.randint(14, 19)
            include_target_images = set(rng.sample(range(1, total_images + 1), include_target_count))
            non_target_ids = [drone_id for drone_id in drone_ids if drone_id != target_drone_id]
            selected_frames = [
                _make_frame(image_idx in include_target_images) for image_idx in range(1, total_images + 1)
            ]

            for _ in range(220):
                scores = _average_distance_scores(selected_frames)
                winner_id, winner_score = _score_winner(scores)
                runner_up = max(
                    (scores.get(drone_id, 0.0) for drone_id in drone_ids if drone_id != winner_id),
                    default=-1.0,
                )
                if winner_id == target_drone_id and winner_score >= (runner_up + min_winner_gap):
                    break

                candidate_indices = [idx for idx, frame in enumerate(selected_frames) if target_drone_id in frame]
                if not candidate_indices:
                    break

                # Prefer the frame where the target is currently least separated.
                chosen_idx = min(
                    candidate_indices,
                    key=lambda idx: _frame_avg_dist(selected_frames[idx], target_drone_id),
                )
                frame = selected_frames[chosen_idx]
                others = [pt for drone_id, pt in frame.items() if drone_id != target_drone_id]
                frame[target_drone_id] = _pick_farthest_point(others)
            else:
                raise RuntimeError("Stage 4 drone fleet generation failed to create a unique average-distance winner")

            final_scores = _average_distance_scores(selected_frames)
            final_winner, final_winner_score = _score_winner(final_scores)
            final_runner_up = max(
                (final_scores.get(drone_id, 0.0) for drone_id in drone_ids if drone_id != final_winner),
                default=-1.0,
            )
            if final_winner != target_drone_id or final_winner_score < (final_runner_up + min_winner_gap):
                raise RuntimeError("Stage 4 drone fleet generation failed to create a unique average-distance winner")

            sanity_handle = StringIO()
            sanity_handle.write("image_name,drone_id,x,y\n")
            for image_idx in (1, 2):
                frame = selected_frames[image_idx - 1]
                image_name = f"{image_idx:03d}.png"
                for drone_id in sorted(frame):
                    px, py = frame[drone_id]
                    sanity_handle.write(f"{image_name},{drone_id},{px},{py}\n")
            zf.writestr("sanity_check.csv", sanity_handle.getvalue())

            for image_idx, positions in enumerate(selected_frames, start=1):
                pixels = bytearray([248, 248, 248, 255] * (width * height))
                for drone_id in sorted(positions):
                    px, py = positions[drone_id]
                    _draw_circle(pixels, px, py, radius, (70, 122, 213, 255))
                    label = str(drone_id)
                    text_w = len(label) * 8
                    text_h = 10
                    label_x = _clamp(px - (text_w // 2), 0, width - text_w)
                    label_y = _clamp(py - (text_h // 2), 0, height - text_h)
                    _draw_text(pixels, label, label_x, label_y, scale=2, color=(0, 0, 0, 255))

                png_bytes = _encode_png(pixels)
                zf.writestr(f"images/{image_idx:03d}.png", png_bytes)

        response = HttpResponse(archive.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{dataset_filename}"'
        return response

    rng_base = (player.id * 97) + (stage * 13)
    handle = StringIO()
    handle.write("record_id,value\n")
    for idx in range(1, 11):
        value = (rng_base + idx * 17) % 10000
        handle.write(f"{idx},{value}\n")

    response = HttpResponse(handle.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{dataset_filename}"'
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
    show_finale_celebration = False
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
                    if submission.stage == FINAL_STAGE:
                        messages.success(request, "Congratulations! You have captured and disabled AUGUR. The city is safe!")
                        show_finale_celebration = True
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
                        if resolved.stage == FINAL_STAGE:
                            messages.success(request, "Congratulations! You have captured and disabled AUGUR. The city is safe!")
                            show_finale_celebration = True
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
            "show_finale_celebration": show_finale_celebration,
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
