from datetime import timedelta
import re

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from game.models import Player, Run, StageCode
from game.services import create_player, pause_current_run, start_run


class JoinFlowTests(TestCase):
    def test_join_existing_username_redirects_to_existing_play_endpoint(self):
        Run.objects.create(name="run_join", status=Run.Status.ACTIVE, is_current=True)

        response = self.client.post("/join", {"username": "Treharne"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/play/"))
        player = Player.objects.get()

        response2 = self.client.post("/join", {"username": "treharne"})
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(response2["Location"], f"/play/{player.id}")
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

    def test_podium_shows_timestamped_log_with_status_and_progress(self):
        p1 = create_player(self.run, "p1")
        p1_s1 = StageCode.objects.get(player=p1, stage=1).code

        self.client.post("/podium", {"action": "submit", "code": str(p1_s1)}, follow=True)
        self.client.post("/podium", {"action": "submit", "code": "1"}, follow=True)

        response = self.client.get("/podium")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Submitted by")
        self.assertContains(response, "AUGUR LOG")
        self.assertContains(response, "Resolved")
        self.assertContains(response, "Rejected")
        self.assertContains(response, "Stage 1")
        self.assertContains(response, "p1")
        self.assertNotContains(response, "Submission #")
        self.assertIsNotNone(re.search(r"\[\d{2}:\d{2}:\d{2}\]\s+code=", response.content.decode()))


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

    def test_running_sum_tool_is_click_based_and_stage_stratified(self):
        run = Run.objects.create(name="run_sum", status=Run.Status.ACTIVE, is_current=True)
        p1 = create_player(run, "sum1")
        create_player(run, "sum2")
        stage1_code = StageCode.objects.get(player=p1, stage=1).code

        self._teacher_login()
        response = self.client.get("/teacher")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Running Sums")
        self.assertContains(response, 'id="running-sum-box"')
        self.assertContains(response, 'id="sum-stage-1"')
        self.assertContains(response, f'data-code="{stage1_code}"')
        self.assertNotContains(response, 'name="selected_user_ids"')

    def test_teacher_can_set_and_clear_collaboration_cap(self):
        run = Run.objects.create(name="run_cap", status=Run.Status.ACTIVE, is_current=True)
        self._teacher_login()

        self.client.post(
            "/teacher",
            {"action": "set_collaboration_cap", "collaboration_size_cap": "3"},
            follow=True,
        )
        run.refresh_from_db()
        self.assertEqual(run.collaboration_size_cap, 3)

        self.client.post(
            "/teacher",
            {"action": "clear_collaboration_cap"},
            follow=True,
        )
        run.refresh_from_db()
        self.assertIsNone(run.collaboration_size_cap)


class OrientationWalkthroughTests(TestCase):
    def setUp(self):
        self.run = Run.objects.create(name="run_orient", status=Run.Status.ACTIVE, is_current=True)
        self.player = create_player(self.run, "orient")

    def test_first_visit_starts_orientation_open_at_step_one(self):
        response = self.client.get(f"/play/{self.player.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ORIENTATION")
        self.assertContains(response, "Step 1.")
        self.assertContains(response, "Tablet devices and mobile phones cannot be used")
        self.assertNotContains(response, "Current stage:")
        self.assertContains(response, "var pausePolling = true;")

    def test_own_device_requires_os_before_language(self):
        self.client.post(
            f"/play/{self.player.id}",
            {"action": "orientation_update", "orientation_event": "choose_device", "orientation_value": "own"},
        )
        self.player.refresh_from_db()
        self.assertEqual(self.player.orientation_step, 2)
        self.assertEqual(self.player.orientation_device_type, "own")

        self.client.post(
            f"/play/{self.player.id}",
            {"action": "orientation_update", "orientation_event": "choose_language", "orientation_value": "python"},
        )
        self.player.refresh_from_db()
        self.assertIsNone(self.player.orientation_language)
        self.assertEqual(self.player.orientation_step, 2)

        self.client.post(
            f"/play/{self.player.id}",
            {"action": "orientation_update", "orientation_event": "choose_os", "orientation_value": "windows"},
        )
        self.client.post(
            f"/play/{self.player.id}",
            {"action": "orientation_update", "orientation_event": "choose_language", "orientation_value": "python"},
        )
        self.player.refresh_from_db()
        self.assertEqual(self.player.orientation_os, "windows")
        self.assertEqual(self.player.orientation_language, "python")
        self.assertEqual(self.player.orientation_step, 4)

    def test_uol_flow_can_skip_os_and_complete_collapses(self):
        self.client.post(
            f"/play/{self.player.id}",
            {"action": "orientation_update", "orientation_event": "choose_device", "orientation_value": "uol"},
        )
        self.client.post(
            f"/play/{self.player.id}",
            {"action": "orientation_update", "orientation_event": "choose_language", "orientation_value": "r"},
        )
        self.client.post(
            f"/play/{self.player.id}",
            {"action": "orientation_update", "orientation_event": "next_step"},
        )
        self.client.post(
            f"/play/{self.player.id}",
            {"action": "orientation_update", "orientation_event": "complete"},
        )
        self.player.refresh_from_db()
        self.assertTrue(self.player.orientation_completed)
        self.assertTrue(self.player.orientation_collapsed)
        self.assertEqual(self.player.orientation_step, 5)

        response = self.client.get(f"/play/{self.player.id}")
        self.assertContains(response, "Orientation complete.")
        self.assertContains(response, "Review Orientation")
        self.assertContains(response, "Current stage:")
        self.assertContains(response, "var pausePolling = false;")


class PersonalCheckerTests(TestCase):
    def setUp(self):
        self.run = Run.objects.create(name="run_checker", status=Run.Status.ACTIVE, is_current=True)
        self.player = create_player(self.run, "checker")
        self.player.orientation_completed = True
        self.player.orientation_collapsed = True
        self.player.orientation_step = 5
        self.player.save(update_fields=["orientation_completed", "orientation_collapsed", "orientation_step"])
        self.current_code = StageCode.objects.get(player=self.player, stage=1).code

    def _expire_lock(self):
        self.player.refresh_from_db()
        self.player.checker_locked_until = timezone.now() - timedelta(seconds=1)
        self.player.save(update_fields=["checker_locked_until"])

    def _assert_lock_seconds_between(self, min_seconds: int, max_seconds: int):
        self.player.refresh_from_db()
        self.assertIsNotNone(self.player.checker_locked_until)
        remaining = (self.player.checker_locked_until - timezone.now()).total_seconds()
        self.assertGreaterEqual(remaining, min_seconds)
        self.assertLessEqual(remaining, max_seconds)

    def test_wrong_answers_show_direction_and_lockout_escalates(self):
        response = self.client.post(
            f"/play/{self.player.id}",
            {"action": "check_solution", "personal_code": str(self.current_code - 1)},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect: too low. Wait 30 seconds.")
        self.assertContains(response, 'id="checker-countdown"')
        self.player.refresh_from_db()
        self.assertEqual(self.player.checker_fail_count, 1)
        self._assert_lock_seconds_between(20, 30)

        self._expire_lock()
        response = self.client.post(
            f"/play/{self.player.id}",
            {"action": "check_solution", "personal_code": str(self.current_code + 1)},
            follow=True,
        )
        self.assertContains(response, "Incorrect: too high. Wait 60 seconds.")
        self.player.refresh_from_db()
        self.assertEqual(self.player.checker_fail_count, 2)
        self._assert_lock_seconds_between(50, 60)

        self._expire_lock()
        response = self.client.post(
            f"/play/{self.player.id}",
            {"action": "check_solution", "personal_code": str(self.current_code - 2)},
            follow=True,
        )
        self.assertContains(response, "Incorrect: too low. Wait 120 seconds.")
        self.player.refresh_from_db()
        self.assertEqual(self.player.checker_fail_count, 3)
        self._assert_lock_seconds_between(110, 120)

        self._expire_lock()
        response = self.client.post(
            f"/play/{self.player.id}",
            {"action": "check_solution", "personal_code": str(self.current_code - 3)},
            follow=True,
        )
        self.assertContains(response, "Incorrect: too low. Wait 120 seconds.")
        self.player.refresh_from_db()
        self.assertEqual(self.player.checker_fail_count, 4)
        self._assert_lock_seconds_between(110, 120)

    def test_locked_checker_rejects_attempts_until_timer_expires(self):
        self.client.post(
            f"/play/{self.player.id}",
            {"action": "check_solution", "personal_code": str(self.current_code - 1)},
            follow=True,
        )
        response = self.client.post(
            f"/play/{self.player.id}",
            {"action": "check_solution", "personal_code": str(self.current_code)},
            follow=True,
        )
        self.assertContains(response, "Checker locked. Try again in")
        self.player.refresh_from_db()
        self.assertEqual(self.player.checker_fail_count, 1)

    def test_correct_answer_hides_checker_and_shows_solution_persistently(self):
        response = self.client.post(
            f"/play/{self.player.id}",
            {"action": "check_solution", "personal_code": str(self.current_code)},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Correct. Enter your code into the podium.")
        self.assertContains(response, "Correct solution:")
        self.assertContains(response, str(self.current_code))
        self.assertNotContains(response, 'name="personal_code"')
        self.player.refresh_from_db()
        self.assertEqual(self.player.checker_verified_stage, 1)

        persisted = self.client.get(f"/play/{self.player.id}")
        self.assertEqual(persisted.status_code, 200)
        self.assertContains(persisted, "Correct solution:")
        self.assertContains(persisted, str(self.current_code))
        self.assertNotContains(persisted, 'name="personal_code"')
