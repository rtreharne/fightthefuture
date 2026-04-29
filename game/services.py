from __future__ import annotations

import itertools
import random
from collections import defaultdict
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from .constants import COMPLETED_STAGE, FINAL_STAGE, STAGE_COUNT, STAGE_GROUP_SIZES
from .models import Player, PodiumSubmission, Run, StageCode, SubmissionCandidate

MAX_MATCHES = 300


@dataclass(frozen=True)
class MatchGroup:
    stage: int
    required_size: int
    player_ids: tuple[int, ...]
    player_usernames: tuple[str, ...]


def normalize_username(username: str) -> str:
    return username.strip()


def required_group_size(run: Run, stage: int) -> int:
    if run.collaboration_size_cap:
        return int(run.collaboration_size_cap)
    return STAGE_GROUP_SIZES[stage]


def create_new_current_run() -> Run:
    with transaction.atomic():
        Run.objects.filter(is_current=True).update(is_current=False)
        return Run.objects.create(status=Run.Status.ACTIVE, is_current=True)


def start_run() -> Run:
    with transaction.atomic():
        current = Run.current()
        if current is None:
            return Run.objects.create(status=Run.Status.ACTIVE, is_current=True)
        if current.status == Run.Status.PAUSED:
            current.status = Run.Status.ACTIVE
            current.save(update_fields=["status"])
        return current


def pause_current_run() -> Run | None:
    current = Run.current()
    if current and current.status == Run.Status.ACTIVE:
        current.status = Run.Status.PAUSED
        current.save(update_fields=["status"])
    return current


def resume_current_run() -> Run | None:
    current = Run.current()
    if current and current.status == Run.Status.PAUSED:
        current.status = Run.Status.ACTIVE
        current.save(update_fields=["status"])
    return current


def archive_current_run() -> Run | None:
    with transaction.atomic():
        current = Run.current()
        if not current:
            return None
        current.status = Run.Status.ARCHIVED
        current.is_current = False
        current.archived_at = timezone.now()
        current.save(update_fields=["status", "is_current", "archived_at"])
        return current


def reset_with_archive() -> Run:
    with transaction.atomic():
        archive_current_run()
        return Run.objects.create(status=Run.Status.ACTIVE, is_current=True)


def _generate_unique_code(run: Run, stage: int) -> int:
    for _ in range(5000):
        code = random.randint(100000, 999999)
        if not StageCode.objects.filter(run=run, stage=stage, code=code).exists():
            return code
    raise RuntimeError("Unable to generate unique stage code")


def _assign_stage_codes(player: Player) -> None:
    for stage in range(1, STAGE_COUNT + 1):
        for _ in range(25):
            code = _generate_unique_code(player.run, stage)
            try:
                StageCode.objects.create(
                    run=player.run,
                    player=player,
                    stage=stage,
                    code=code,
                )
                break
            except IntegrityError:
                continue
        else:
            raise RuntimeError("Failed to assign stage code after retries")


def create_player(run: Run, username: str, is_test_user: bool = False) -> Player:
    cleaned = normalize_username(username)
    if not cleaned:
        raise ValueError("Username is required")
    if run.status == Run.Status.ARCHIVED:
        raise ValueError("Cannot join archived run")

    with transaction.atomic():
        player = Player.objects.create(run=run, username=cleaned, is_test_user=is_test_user)
        _assign_stage_codes(player)
        return player


def create_test_users(run: Run, n_users: int) -> list[Player]:
    if n_users < 1:
        raise ValueError("n_users must be at least 1")

    created: list[Player] = []
    used = set(Player.objects.filter(run=run).values_list("username_key", flat=True))
    index = 1
    while len(created) < n_users:
        candidate = f"test{index:03d}"
        index += 1
        key = candidate.lower()
        if key in used:
            continue
        created.append(create_player(run, candidate, is_test_user=True))
        used.add(key)
    return created


def _stage_entries(run: Run, stage: int) -> list[tuple[Player, int]]:
    codes = (
        StageCode.objects.select_related("player")
        .filter(run=run, stage=stage, player__current_stage=stage)
        .order_by("player_id")
    )
    return [(stage_code.player, stage_code.code) for stage_code in codes]


def _size_one_matches(codes: list[int], target: int) -> list[tuple[int, ...]]:
    return [(idx,) for idx, value in enumerate(codes) if value == target]


def _size_two_matches(codes: list[int], target: int, limit: int) -> list[tuple[int, ...]]:
    results: list[tuple[int, ...]] = []
    for i in range(len(codes)):
        for j in range(i + 1, len(codes)):
            if codes[i] + codes[j] == target:
                results.append((i, j))
                if len(results) >= limit:
                    return results
    return results


def _size_four_matches(codes: list[int], target: int, limit: int) -> list[tuple[int, ...]]:
    pair_sums: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for i in range(len(codes)):
        for j in range(i + 1, len(codes)):
            pair_sums[codes[i] + codes[j]].append((i, j))

    seen: set[tuple[int, ...]] = set()
    results: list[tuple[int, ...]] = []
    for sum_a, pairs_a in pair_sums.items():
        sum_b = target - sum_a
        pairs_b = pair_sums.get(sum_b)
        if not pairs_b or sum_a > sum_b:
            continue
        for a1, a2 in pairs_a:
            for b1, b2 in pairs_b:
                indices = {a1, a2, b1, b2}
                if len(indices) != 4:
                    continue
                combo = tuple(sorted(indices))
                if combo in seen:
                    continue
                seen.add(combo)
                results.append(combo)
                if len(results) >= limit:
                    return results
    return results


def _mask(indices: tuple[int, ...]) -> int:
    bitmask = 0
    for idx in indices:
        bitmask |= 1 << idx
    return bitmask


def _size_eight_matches(codes: list[int], target: int, limit: int) -> list[tuple[int, ...]]:
    quads_by_sum: dict[int, list[tuple[int, tuple[int, ...]]]] = defaultdict(list)
    for quad in itertools.combinations(range(len(codes)), 4):
        quad_tuple = tuple(quad)
        quad_sum = sum(codes[idx] for idx in quad_tuple)
        quads_by_sum[quad_sum].append((_mask(quad_tuple), quad_tuple))

    seen: set[tuple[int, ...]] = set()
    results: list[tuple[int, ...]] = []
    for sum_a, quads_a in quads_by_sum.items():
        sum_b = target - sum_a
        quads_b = quads_by_sum.get(sum_b)
        if not quads_b or sum_a > sum_b:
            continue
        for mask_a, quad_a in quads_a:
            for mask_b, quad_b in quads_b:
                if mask_a & mask_b:
                    continue
                combo = tuple(sorted((*quad_a, *quad_b)))
                if combo in seen:
                    continue
                seen.add(combo)
                results.append(combo)
                if len(results) >= limit:
                    return results
    return results


def _matching_indices(codes: list[int], target: int, group_size: int, limit: int) -> list[tuple[int, ...]]:
    if group_size == 1:
        return _size_one_matches(codes, target)[:limit]
    if group_size == 2:
        return _size_two_matches(codes, target, limit)
    if group_size == 4:
        return _size_four_matches(codes, target, limit)
    if group_size == 8:
        return _size_eight_matches(codes, target, limit)

    results: list[tuple[int, ...]] = []
    for combo in itertools.combinations(range(len(codes)), group_size):
        if sum(codes[idx] for idx in combo) == target:
            results.append(combo)
            if len(results) >= limit:
                return results
    return results


def find_matching_groups(run: Run, submitted_sum: int, limit: int = MAX_MATCHES) -> list[MatchGroup]:
    matches: list[MatchGroup] = []

    for stage in range(1, STAGE_COUNT + 1):
        if len(matches) >= limit:
            break
        group_size = required_group_size(run, stage)

        entries = _stage_entries(run, stage)
        if len(entries) < group_size:
            continue

        players = [entry[0] for entry in entries]
        codes = [entry[1] for entry in entries]
        remaining = max(1, limit - len(matches))
        combos = _matching_indices(codes, submitted_sum, group_size, remaining)
        for combo in combos:
            selected_players = [players[idx] for idx in combo]
            matches.append(
                MatchGroup(
                    stage=stage,
                    required_size=group_size,
                    player_ids=tuple(player.id for player in selected_players),
                    player_usernames=tuple(player.username for player in selected_players),
                )
            )
            if len(matches) >= limit:
                break

    matches.sort(key=lambda m: (m.stage, m.player_usernames))
    return matches


def _validate_stage_group(run: Run, stage: int, player_ids: list[int], submitted_sum: int) -> list[Player]:
    expected_size = required_group_size(run, stage)
    selected_ids = sorted(set(player_ids))
    if len(selected_ids) != expected_size:
        raise ValueError(f"Stage {stage} requires exactly {expected_size} players")

    players = list(
        Player.objects.select_for_update()
        .filter(run=run, id__in=selected_ids)
        .order_by("id")
    )
    if len(players) != expected_size:
        raise ValueError("Selected players are invalid for this run")
    if any(player.current_stage != stage for player in players):
        raise ValueError("All selected players must currently be at the chosen stage")

    total = (
        StageCode.objects.filter(run=run, stage=stage, player_id__in=selected_ids).aggregate(total=Sum("code"))["total"]
        or 0
    )
    if total != submitted_sum:
        raise ValueError("Selected players do not match submitted code sum")

    return players


def advance_players_for_stage(run: Run, stage: int, player_ids: list[int]) -> list[Player]:
    with transaction.atomic():
        players = _validate_stage_group(run, stage, player_ids, submitted_sum=(
            StageCode.objects.filter(run=run, stage=stage, player_id__in=player_ids).aggregate(total=Sum("code"))["total"]
            or 0
        ))
        now = timezone.now()
        for player in players:
            if stage >= FINAL_STAGE:
                player.current_stage = COMPLETED_STAGE
                player.completed_at = now
            else:
                player.current_stage = stage + 1
        Player.objects.bulk_update(players, ["current_stage", "completed_at"])
        return players


def process_podium_submission(run: Run, submitted_sum: int, submitted_by: str = "") -> tuple[PodiumSubmission, list[MatchGroup]]:
    if run.status == Run.Status.PAUSED:
        submission = PodiumSubmission.objects.create(
            run=run,
            submitted_sum=submitted_sum,
            submitted_by=submitted_by,
            status=PodiumSubmission.Status.INVALID,
            message="Run is paused. Podium is temporarily disabled.",
            resolved_at=timezone.now(),
        )
        return submission, []

    matches = find_matching_groups(run, submitted_sum)

    if not matches:
        submission = PodiumSubmission.objects.create(
            run=run,
            submitted_sum=submitted_sum,
            submitted_by=submitted_by,
            status=PodiumSubmission.Status.INVALID,
            message="No valid collaboration matched that code.",
            resolved_at=timezone.now(),
        )
        return submission, []

    if len(matches) == 1:
        match = matches[0]
        with transaction.atomic():
            players = _validate_stage_group(run, match.stage, list(match.player_ids), submitted_sum=submitted_sum)
            now = timezone.now()
            for player in players:
                if match.stage >= FINAL_STAGE:
                    player.current_stage = COMPLETED_STAGE
                    player.completed_at = now
                else:
                    player.current_stage = match.stage + 1
            Player.objects.bulk_update(players, ["current_stage", "completed_at"])

            submission = PodiumSubmission.objects.create(
                run=run,
                submitted_sum=submitted_sum,
                submitted_by=submitted_by,
                status=PodiumSubmission.Status.ACCEPTED,
                stage=match.stage,
                required_size=match.required_size,
                resolved_manually=False,
                progressed_usernames=[player.username for player in players],
                message="Code accepted and progress applied.",
                resolved_at=now,
            )
        return submission, [match]

    with transaction.atomic():
        submission = PodiumSubmission.objects.create(
            run=run,
            submitted_sum=submitted_sum,
            submitted_by=submitted_by,
            status=PodiumSubmission.Status.PENDING,
            message="Multiple collaborations match this code. Select members to resolve.",
        )
        for match in matches:
            SubmissionCandidate.objects.create(
                submission=submission,
                stage=match.stage,
                player_ids=list(match.player_ids),
                player_usernames=list(match.player_usernames),
            )
    return submission, matches


def resolve_pending_submission(submission: PodiumSubmission, stage: int, player_ids: list[int]) -> PodiumSubmission:
    if submission.status != PodiumSubmission.Status.PENDING:
        raise ValueError("Submission is not pending")

    run = submission.run
    if run.status == Run.Status.PAUSED:
        raise ValueError("Run is paused. Podium is temporarily disabled.")

    with transaction.atomic():
        players = _validate_stage_group(run, stage, player_ids, submitted_sum=submission.submitted_sum)
        now = timezone.now()
        for player in players:
            if stage >= FINAL_STAGE:
                player.current_stage = COMPLETED_STAGE
                player.completed_at = now
            else:
                player.current_stage = stage + 1
        Player.objects.bulk_update(players, ["current_stage", "completed_at"])

        submission.status = PodiumSubmission.Status.ACCEPTED
        submission.stage = stage
        submission.required_size = required_group_size(run, stage)
        submission.resolved_manually = True
        submission.progressed_usernames = [player.username for player in players]
        submission.message = "Ambiguous code resolved manually and progress applied."
        submission.resolved_at = now
        submission.save(
            update_fields=[
                "status",
                "stage",
                "required_size",
                "resolved_manually",
                "progressed_usernames",
                "message",
                "resolved_at",
            ]
        )

    return submission


def compute_stage_sum(run: Run, stage: int, player_ids: list[int]) -> int:
    if stage < 1 or stage > STAGE_COUNT:
        raise ValueError("Invalid stage")
    if not player_ids:
        return 0

    total = (
        StageCode.objects.filter(run=run, stage=stage, player_id__in=player_ids).aggregate(total=Sum("code"))["total"]
        or 0
    )
    return int(total)
