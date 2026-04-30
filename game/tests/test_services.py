from django.test import TestCase

from game.constants import STAGE_COUNT
from game.models import Player, PodiumSubmission, Run, StageCode
from game.services import create_player, find_matching_groups, process_podium_submission, resolve_pending_submission


class CodeGenerationTests(TestCase):
    def test_create_player_assigns_unique_six_digit_codes(self):
        run = Run.objects.create(name="run_unit_1", status=Run.Status.ACTIVE, is_current=True)

        player1 = create_player(run, "Alice")
        player2 = create_player(run, "Bob")

        p1_codes = list(StageCode.objects.filter(player=player1).order_by("stage"))
        p2_codes = list(StageCode.objects.filter(player=player2).order_by("stage"))

        self.assertEqual(len(p1_codes), STAGE_COUNT)
        self.assertEqual(len(p2_codes), STAGE_COUNT)

        for stage_code in p1_codes + p2_codes:
            self.assertGreaterEqual(stage_code.code, 100000)
            self.assertLessEqual(stage_code.code, 999999)

        for stage in range(1, STAGE_COUNT + 1):
            stage_values = list(StageCode.objects.filter(run=run, stage=stage).values_list("code", flat=True))
            self.assertEqual(len(stage_values), len(set(stage_values)))


class MatchingEngineTests(TestCase):
    def setUp(self):
        self.run = Run.objects.create(name="run_match", status=Run.Status.ACTIVE, is_current=True)

    def _create_player_with_stage_code(self, username: str, stage: int, code: int) -> Player:
        player = Player.objects.create(run=self.run, username=username)
        player.current_stage = stage
        player.save(update_fields=["current_stage"])
        StageCode.objects.create(run=self.run, player=player, stage=stage, code=code)
        for s in range(1, STAGE_COUNT + 1):
            if s == stage:
                continue
            StageCode.objects.create(run=self.run, player=player, stage=s, code=100000 + (player.id * 10) + s)
        return player

    def test_group_size_one_stage_one_match(self):
        solo = self._create_player_with_stage_code("solo", 1, 456789)
        self._create_player_with_stage_code("other", 1, 123456)

        matches = find_matching_groups(self.run, 456789)
        stage1 = [m for m in matches if m.stage == 1]

        self.assertEqual(len(stage1), 1)
        self.assertEqual(list(stage1[0].player_ids), [solo.id])

    def test_group_size_two_stage_two_match(self):
        a = self._create_player_with_stage_code("a", 2, 100000)
        b = self._create_player_with_stage_code("b", 2, 220000)
        self._create_player_with_stage_code("c", 2, 190000)

        matches = find_matching_groups(self.run, 320000)
        stage2 = [m for m in matches if m.stage == 2]

        self.assertEqual(len(stage2), 1)
        self.assertEqual(set(stage2[0].player_ids), {a.id, b.id})

    def test_group_size_four_stage_three_match(self):
        players = [
            self._create_player_with_stage_code("s3_a", 3, 100000),
            self._create_player_with_stage_code("s3_b", 3, 110000),
            self._create_player_with_stage_code("s3_c", 3, 120000),
            self._create_player_with_stage_code("s3_d", 3, 130000),
        ]

        matches = find_matching_groups(self.run, 460000)
        stage3 = [m for m in matches if m.stage == 3]

        self.assertEqual(len(stage3), 1)
        self.assertEqual(set(stage3[0].player_ids), {p.id for p in players})

    def test_group_size_eight_stage_four_match(self):
        players = [
            self._create_player_with_stage_code(f"s4_{idx}", 4, 100000 + idx * 1000)
            for idx in range(8)
        ]
        target = sum(100000 + idx * 1000 for idx in range(8))

        matches = find_matching_groups(self.run, target)
        stage4 = [m for m in matches if m.stage == 4]

        self.assertEqual(len(stage4), 1)
        self.assertEqual(set(stage4[0].player_ids), {p.id for p in players})

    def test_collaboration_cap_overrides_default_stage_sizes(self):
        self.run.collaboration_size_cap = 2
        self.run.save(update_fields=["collaboration_size_cap"])
        a = self._create_player_with_stage_code("cap_a", 1, 111111)
        b = self._create_player_with_stage_code("cap_b", 1, 222222)

        matches = find_matching_groups(self.run, 333333)
        stage1 = [m for m in matches if m.stage == 1]

        self.assertEqual(len(stage1), 1)
        self.assertEqual(stage1[0].required_size, 2)
        self.assertEqual(set(stage1[0].player_ids), {a.id, b.id})

    def test_collaboration_stage_requires_wait_when_only_one_player_available(self):
        self._create_player_with_stage_code("solo_s2", 2, 234567)

        matches = find_matching_groups(self.run, 234567)
        stage2 = [m for m in matches if m.stage == 2]

        self.assertEqual(stage2, [])

    def test_stranded_player_can_progress_solo_when_all_others_are_ahead(self):
        solo = self._create_player_with_stage_code("solo_s2", 2, 345678)
        ahead = self._create_player_with_stage_code("ahead_s3", 3, 222222)
        ahead.current_stage = 3
        ahead.save(update_fields=["current_stage"])

        matches = find_matching_groups(self.run, 345678)
        stage2 = [m for m in matches if m.stage == 2]

        self.assertEqual(len(stage2), 1)
        self.assertEqual(stage2[0].required_size, 1)
        self.assertEqual(set(stage2[0].player_ids), {solo.id})

    def test_suspended_players_are_excluded_from_matching(self):
        a = self._create_player_with_stage_code("s2_a", 2, 140000)
        b = self._create_player_with_stage_code("s2_b", 2, 180000)
        b.is_suspended = True
        b.save(update_fields=["is_suspended"])

        matches = find_matching_groups(self.run, 320000)
        stage2 = [m for m in matches if m.stage == 2]

        self.assertEqual(stage2, [])
        a.refresh_from_db()
        self.assertFalse(a.is_suspended)


class AmbiguityResolutionTests(TestCase):
    def setUp(self):
        self.run = Run.objects.create(name="run_amb", status=Run.Status.ACTIVE, is_current=True)

    def _mk(self, username: str, stage: int, code: int) -> Player:
        player = Player.objects.create(run=self.run, username=username)
        player.current_stage = stage
        player.save(update_fields=["current_stage"])
        StageCode.objects.create(run=self.run, player=player, stage=stage, code=code)
        for s in range(1, STAGE_COUNT + 1):
            if s == stage:
                continue
            StageCode.objects.create(run=self.run, player=player, stage=s, code=200000 + (player.id * 10) + s)
        return player

    def test_pending_submission_and_manual_resolution(self):
        a = self._mk("a", 2, 100000)
        b = self._mk("b", 2, 210000)
        c = self._mk("c", 2, 130000)
        d = self._mk("d", 2, 180000)

        submission, matches = process_podium_submission(self.run, 310000, submitted_by="tester")

        self.assertEqual(submission.status, PodiumSubmission.Status.PENDING)
        self.assertEqual(len(matches), 2)
        self.assertEqual(submission.candidates.count(), 2)

        resolved = resolve_pending_submission(submission, 2, [a.id, b.id])
        self.assertEqual(resolved.status, PodiumSubmission.Status.ACCEPTED)
        self.assertTrue(resolved.resolved_manually)

        a.refresh_from_db()
        b.refresh_from_db()
        c.refresh_from_db()
        d.refresh_from_db()
        self.assertEqual(a.current_stage, 3)
        self.assertEqual(b.current_stage, 3)
        self.assertEqual(c.current_stage, 2)
        self.assertEqual(d.current_stage, 2)
