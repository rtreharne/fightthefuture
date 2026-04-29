from django.conf import settings
from django.test import TestCase

from game.models import Player, Run, StageCode
from game.services import create_player, pause_current_run, start_run


class JoinFlowTests(TestCase):
    def test_join_and_case_insensitive_uniqueness(self):
        Run.objects.create(name="run_join", status=Run.Status.ACTIVE, is_current=True)

        response = self.client.post("/join", {"username": "Treharne"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/play/"))

        response2 = self.client.post("/join", {"username": "treharne"}, follow=True)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(Player.objects.count(), 1)


class PodiumProgressionTests(TestCase):
    def setUp(self):
        self.run = Run.objects.create(name="run_podium", status=Run.Status.ACTIVE, is_current=True)

    def test_stage1_and_stage2_progression(self):
        p1 = create_player(self.run, "p1")
        p2 = create_player(self.run, "p2")

        p1_s1 = StageCode.objects.get(player=p1, stage=1).code
        p2_s1 = StageCode.objects.get(player=p2, stage=1).code

        self.client.post("/podium", {"action": "submit", "code": str(p1_s1)})
        self.client.post("/podium", {"action": "submit", "code": str(p2_s1)})

        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertEqual(p1.current_stage, 2)
        self.assertEqual(p2.current_stage, 2)

        stage2_sum = StageCode.objects.get(player=p1, stage=2).code + StageCode.objects.get(player=p2, stage=2).code
        self.client.post("/podium", {"action": "submit", "code": str(stage2_sum)})

        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertEqual(p1.current_stage, 3)
        self.assertEqual(p2.current_stage, 3)

    def test_pause_blocks_podium_but_play_is_readable(self):
        player = create_player(self.run, "solo")
        solo_code = StageCode.objects.get(player=player, stage=1).code

        pause_current_run()
        blocked = self.client.post("/podium", {"action": "submit", "code": str(solo_code)}, follow=True)

        player.refresh_from_db()
        self.assertEqual(player.current_stage, 1)
        self.assertEqual(blocked.status_code, 200)

        play = self.client.get(f"/play/{player.id}")
        self.assertEqual(play.status_code, 200)


class TeacherDashboardTests(TestCase):
    def _teacher_login(self):
        return self.client.post(
            "/teacher",
            {"action": "teacher_login", "passcode": settings.TEACHER_PASSCODE},
            follow=True,
        )

    def test_archive_and_reset_creates_clean_current_run(self):
        run = start_run()
        create_player(run, "one")

        self._teacher_login()
        self.client.post("/teacher", {"action": "reset_run"}, follow=True)

        current = Run.current()
        self.assertIsNotNone(current)
        self.assertNotEqual(current.id, run.id)
        self.assertEqual(current.players.count(), 0)

        run.refresh_from_db()
        self.assertEqual(run.status, Run.Status.ARCHIVED)
        self.assertFalse(run.is_current)

    def test_running_sum_matches_selected_users(self):
        run = Run.objects.create(name="run_sum", status=Run.Status.ACTIVE, is_current=True)
        p1 = create_player(run, "sum1")
        p2 = create_player(run, "sum2")

        expected = StageCode.objects.get(player=p1, stage=1).code + StageCode.objects.get(player=p2, stage=1).code

        self._teacher_login()
        response = self.client.post(
            "/teacher",
            {
                "action": "compute_sum",
                "stage": "1",
                "selected_user_ids": [str(p1.id), str(p2.id)],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(expected))
