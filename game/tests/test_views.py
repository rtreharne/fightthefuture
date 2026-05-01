from collections import defaultdict
from datetime import timedelta
import csv
from io import BytesIO, StringIO
import re
import zipfile

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from game.constants import FINAL_STAGE
from game.models import Player, PlayerFeedback, Run, StageCode
from game.services import create_player, pause_current_run, start_run


class JoinFlowTests(TestCase):
    def test_join_existing_username_redirects_to_existing_play_endpoint(self):
        Run.objects.create(name="run_join", status=Run.Status.ACTIVE, is_current=True)

        response = self.client.post("/join", {"username": "Treharne7"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/play/"))
        player = Player.objects.get()

        response2 = self.client.post("/join", {"username": "treharne7"})
        self.assertEqual(response2.status_code, 302)
        self.assertEqual(response2["Location"], f"/play/{player.id}")
        self.assertEqual(Player.objects.count(), 1)

    def test_join_rejects_spaces_and_non_unique_style_names(self):
        Run.objects.create(name="run_join_rules", status=Run.Status.ACTIVE, is_current=True)

        response_spaces = self.client.post("/join", {"username": "dave 23"}, follow=True)
        self.assertEqual(response_spaces.status_code, 200)
        self.assertContains(response_spaces, "User name cannot contain spaces.")
        self.assertEqual(Player.objects.count(), 0)

        response_simple = self.client.post("/join", {"username": "Dave"}, follow=True)
        self.assertEqual(response_simple.status_code, 200)
        self.assertContains(response_simple, "Use a more unique user name.")
        self.assertEqual(Player.objects.count(), 0)

    def test_play_redirects_to_join_when_player_not_in_current_run(self):
        old_run = Run.objects.create(name="run_old", status=Run.Status.ACTIVE, is_current=True)
        player = create_player(old_run, "legacy")

        old_run.is_current = False
        old_run.save(update_fields=["is_current"])
        Run.objects.create(name="run_new", status=Run.Status.ACTIVE, is_current=True)

        response = self.client.get(f"/play/{player.id}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/join")


class PodiumProgressionTests(TestCase):
    def setUp(self):
        self.run = Run.objects.create(name="run_podium", status=Run.Status.ACTIVE, is_current=True)

    def test_stage1_and_stage2_progression(self):
        p1 = create_player(self.run, "p1")
        p2 = create_player(self.run, "p2")

        p1_s1 = StageCode.objects.get(player=p1, stage=1).code
        p2_s1 = StageCode.objects.get(player=p2, stage=1).code

        stage1_response = self.client.post("/podium", {"action": "submit", "code": str(p1_s1)}, follow=True)
        self.assertContains(stage1_response, "p1 has successfully completed stage 1 and progressed.")
        self.client.post("/podium", {"action": "submit", "code": str(p2_s1)})

        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertEqual(p1.current_stage, 2)
        self.assertEqual(p2.current_stage, 2)

        stage2_sum = StageCode.objects.get(player=p1, stage=2).code + StageCode.objects.get(player=p2, stage=2).code
        stage2_response = self.client.post("/podium", {"action": "submit", "code": str(stage2_sum)}, follow=True)
        self.assertContains(stage2_response, "p1 and p2 have worked together to complete stage 2 and progressed.")

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

    def test_final_stage_submission_shows_celebration_and_feedback_flow(self):
        self.run.collaboration_size_cap = 2
        self.run.save(update_fields=["collaboration_size_cap"])
        p1 = create_player(self.run, "p1")
        p2 = create_player(self.run, "p2")

        Player.objects.filter(id__in=[p1.id, p2.id]).update(
            current_stage=FINAL_STAGE,
            intro_accepted=True,
            orientation_completed=True,
            orientation_collapsed=True,
        )
        stage_sum = StageCode.objects.get(player=p1, stage=FINAL_STAGE).code + StageCode.objects.get(player=p2, stage=FINAL_STAGE).code

        podium_response = self.client.post("/podium", {"action": "submit", "code": str(stage_sum)}, follow=True)
        self.assertContains(podium_response, "Congratulations! You have captured and disabled AUGUR. The city is safe!")

        p1.refresh_from_db()
        self.assertTrue(p1.is_complete)

        play_response = self.client.get(f"/play/{p1.id}")
        self.assertContains(play_response, "AUGUR DISABLED")
        self.assertContains(play_response, "Submit Feedback")

        feedback_post = self.client.post(
            f"/play/{p1.id}",
            {
                "action": "submit_feedback",
                "session_engaging": "5",
                "scenario_meaningful": "4",
                "challenge_appropriate": "4",
                "different_workshop_positive": "5",
                "worked_effectively_with_others": "5",
                "instructions_clear": "5",
                "recommend_to_student": "5",
                "attend_again": "5",
                "best_part": "Great scenario.",
                "improve_future": "More time for debrief.",
            },
            follow=True,
        )
        self.assertContains(feedback_post, "Thanks for your feedback.")
        self.assertTrue(PlayerFeedback.objects.filter(player=p1).exists())


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

    def test_teacher_can_suspend_and_reactivate_user_by_username(self):
        run = Run.objects.create(name="run_suspend", status=Run.Status.ACTIVE, is_current=True)
        player = create_player(run, "DeltaUser")
        self._teacher_login()

        suspend = self.client.post(
            "/teacher",
            {"action": "suspend_user", "username": "deltauser"},
            follow=True,
        )
        self.assertEqual(suspend.status_code, 200)
        self.assertContains(suspend, "has been suspended")
        player.refresh_from_db()
        self.assertTrue(player.is_suspended)

        reactivate = self.client.post(
            "/teacher",
            {"action": "reactivate_user", "username": "DELTAUSER"},
            follow=True,
        )
        self.assertEqual(reactivate.status_code, 200)
        self.assertContains(reactivate, "has been reactivated")
        player.refresh_from_db()
        self.assertFalse(player.is_suspended)


class OrientationWalkthroughTests(TestCase):
    def setUp(self):
        self.run = Run.objects.create(name="run_orient", status=Run.Status.ACTIVE, is_current=True)
        self.player = create_player(self.run, "orient")

    def test_first_visit_shows_introduction_gate(self):
        response = self.client.get(f"/play/{self.player.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Introduction")
        self.assertContains(response, "The year is 2030.")
        self.assertContains(response, "Accept Challenge")
        self.assertNotContains(response, "ORIENTATION")
        self.assertNotContains(response, "Step 1.")
        self.assertNotContains(response, "Current stage:")
        self.assertContains(response, "var pausePolling = true;")

    def test_accept_challenge_opens_orientation(self):
        response = self.client.post(
            f"/play/{self.player.id}",
            {"action": "accept_challenge"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.player.refresh_from_db()
        self.assertTrue(self.player.intro_accepted)
        self.assertContains(response, "ORIENTATION")
        self.assertContains(response, "Step 1.")

    def test_own_device_requires_os_before_language(self):
        self.player.intro_accepted = True
        self.player.save(update_fields=["intro_accepted"])
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
        self.player.intro_accepted = True
        self.player.save(update_fields=["intro_accepted"])
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

    def test_review_orientation_reopens_expanded_orientation_panel(self):
        self.player.intro_accepted = True
        self.player.orientation_completed = True
        self.player.orientation_collapsed = True
        self.player.orientation_step = 5
        self.player.orientation_device_type = Player.OrientationDeviceType.UOL
        self.player.orientation_language = Player.OrientationLanguage.PYTHON
        self.player.save(
            update_fields=[
                "intro_accepted",
                "orientation_completed",
                "orientation_collapsed",
                "orientation_step",
                "orientation_device_type",
                "orientation_language",
            ]
        )

        response = self.client.post(
            f"/play/{self.player.id}",
            {"action": "orientation_update", "orientation_event": "reopen"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.player.refresh_from_db()
        self.assertFalse(self.player.orientation_collapsed)
        self.assertContains(response, "ORIENTATION")
        self.assertContains(response, "Step 1.")
        self.assertNotContains(response, "Orientation complete.")


class PersonalCheckerTests(TestCase):
    def setUp(self):
        self.run = Run.objects.create(name="run_checker", status=Run.Status.ACTIVE, is_current=True)
        self.player = create_player(self.run, "checker")
        self.player.intro_accepted = True
        self.player.orientation_completed = True
        self.player.orientation_collapsed = True
        self.player.orientation_step = 5
        self.player.save(update_fields=["intro_accepted", "orientation_completed", "orientation_collapsed", "orientation_step"])
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
        self.assertContains(response, "Correct. Enter your code into AUGUR PODIUM.")
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

    def test_async_checker_success_stage1_returns_json_without_refresh(self):
        response = self.client.post(
            f"/play/{self.player.id}",
            {
                "action": "check_solution",
                "personal_code": str(self.current_code),
                "response_format": "json",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["level"], "success")
        self.assertEqual(payload["message"], "Correct. Enter your code into AUGUR PODIUM.")
        self.assertTrue(payload["checker_verified"])
        self.assertEqual(payload["checker_solution_code"], self.current_code)

    def test_async_checker_success_stage2_includes_collaborator_count_message(self):
        self.player.current_stage = 2
        self.player.checker_stage = None
        self.player.checker_verified_stage = None
        self.player.save(update_fields=["current_stage", "checker_stage", "checker_verified_stage"])
        partner = create_player(self.run, "checker_partner")
        partner.current_stage = 2
        partner.save(update_fields=["current_stage"])
        stage2_code = StageCode.objects.get(player=self.player, stage=2).code

        response = self.client.post(
            f"/play/{self.player.id}",
            {
                "action": "check_solution",
                "personal_code": str(stage2_code),
                "response_format": "json",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["level"], "success")
        self.assertEqual(
            payload["message"],
            "Correct. Combine your code with 1 collaborator and enter the sum into AUGUR PODIUM.",
        )
        self.assertTrue(payload["checker_verified"])
        self.assertEqual(payload["checker_solution_code"], stage2_code)

        persisted = self.client.get(f"/play/{self.player.id}")
        self.assertEqual(persisted.status_code, 200)
        self.assertContains(
            persisted,
            "Correct. Combine your code with 1 collaborator and enter the sum into AUGUR PODIUM.",
        )

    def test_async_checker_success_stage2_waits_when_no_other_players(self):
        self.player.current_stage = 2
        self.player.checker_stage = None
        self.player.checker_verified_stage = None
        self.player.save(update_fields=["current_stage", "checker_stage", "checker_verified_stage"])
        stage2_code = StageCode.objects.get(player=self.player, stage=2).code

        response = self.client.post(
            f"/play/{self.player.id}",
            {
                "action": "check_solution",
                "personal_code": str(stage2_code),
                "response_format": "json",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["message"],
            "Correct. Your personal code is verified. Wait until more players reach this stage, then combine your codes and enter the sum into AUGUR PODIUM.",
        )

    def test_async_checker_success_stage2_allows_stranded_player_to_submit(self):
        self.player.current_stage = 2
        self.player.checker_stage = None
        self.player.checker_verified_stage = None
        self.player.save(update_fields=["current_stage", "checker_stage", "checker_verified_stage"])
        ahead = create_player(self.run, "already_ahead")
        ahead.current_stage = 3
        ahead.save(update_fields=["current_stage"])
        stage2_code = StageCode.objects.get(player=self.player, stage=2).code

        response = self.client.post(
            f"/play/{self.player.id}",
            {
                "action": "check_solution",
                "personal_code": str(stage2_code),
                "response_format": "json",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["message"], "Correct. Enter your code into AUGUR PODIUM.")

    def test_verified_view_message_is_dynamic_when_collaboration_cap_is_one(self):
        self.player.current_stage = 2
        self.player.checker_stage = None
        self.player.checker_verified_stage = None
        self.player.save(update_fields=["current_stage", "checker_stage", "checker_verified_stage"])
        self.run.collaboration_size_cap = 1
        self.run.save(update_fields=["collaboration_size_cap"])
        stage2_code = StageCode.objects.get(player=self.player, stage=2).code

        response = self.client.post(
            f"/play/{self.player.id}",
            {
                "action": "check_solution",
                "personal_code": str(stage2_code),
                "response_format": "json",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["message"], "Correct. Enter your code into AUGUR PODIUM.")

        persisted = self.client.get(f"/play/{self.player.id}")
        self.assertEqual(persisted.status_code, 200)
        self.assertContains(persisted, "Correct. Enter your code into AUGUR PODIUM.")
        self.assertNotContains(persisted, "Combine your code with 0 collaborators")

    def test_async_checker_wrong_answer_returns_direction_hint(self):
        response = self.client.post(
            f"/play/{self.player.id}",
            {
                "action": "check_solution",
                "personal_code": str(self.current_code + 1),
                "response_format": "json",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["level"], "error")
        self.assertIn("too high", payload["message"])

    def test_checker_rejects_suspended_player(self):
        self.player.is_suspended = True
        self.player.save(update_fields=["is_suspended"])

        response = self.client.post(
            f"/play/{self.player.id}",
            {
                "action": "check_solution",
                "personal_code": str(self.current_code),
                "response_format": "json",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["ok"])
        self.assertIn("suspended", payload["message"].lower())


class StageContentTests(TestCase):
    def setUp(self):
        self.run = Run.objects.create(name="run_stage_content", status=Run.Status.ACTIVE, is_current=True)
        self.player = create_player(self.run, "builder")
        self.player.intro_accepted = True
        self.player.orientation_completed = True
        self.player.orientation_collapsed = True
        self.player.orientation_step = 5
        self.player.save(update_fields=["intro_accepted", "orientation_completed", "orientation_collapsed", "orientation_step"])

    def test_stage1_uses_language_specific_yaml_content(self):
        self.player.orientation_language = Player.OrientationLanguage.PYTHON
        self.player.save(update_fields=["orientation_language"])

        python_response = self.client.get(f"/play/{self.player.id}")
        self.assertEqual(python_response.status_code, 200)
        self.assertContains(python_response, "Stage 1: Signal Capture")
        self.assertContains(python_response, "Download the Stage 1 dataset")
        self.assertContains(python_response, "Download Stage 1 dataset")
        self.assertContains(python_response, "stage1_signal.py")
        self.assertContains(python_response, "python stage1_signal.py stage1_dataset.csv")
        self.assertContains(python_response, "signals = sorted")
        self.assertNotContains(python_response, "TARGET_CODE")

        self.player.orientation_language = Player.OrientationLanguage.R
        self.player.save(update_fields=["orientation_language"])
        r_response = self.client.get(f"/play/{self.player.id}")
        self.assertContains(r_response, "stage1_signal.R")
        self.assertContains(r_response, "Rscript stage1_signal.R stage1_dataset.csv")
        self.assertContains(r_response, "decode_digit")
        self.assertNotContains(r_response, "target_code")

    def test_stage1_dataset_encodes_player_stage_code(self):
        stage1_code = StageCode.objects.get(player=self.player, stage=1).code
        response = self.client.get(f"/play/{self.player.id}/dataset/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="stage1_dataset.csv"',
        )

        lines = response.content.decode().strip().splitlines()
        header = lines[0].split(",")
        rows = []
        for line in lines[1:]:
            values = line.split(",")
            rows.append(dict(zip(header, values)))

        signals = [row for row in rows if int(row["keep"]) == 1]
        self.assertEqual(len(signals), 6)
        signals.sort(key=lambda row: int(row["pos"]))
        decoded_digits = [
            str((int(row["encoded"]) - int(row["key"]) - (int(row["pos"]) * 3)) % 10)
            for row in signals
        ]
        decoded_code = "".join(decoded_digits)
        self.assertEqual(decoded_code, f"{stage1_code:06d}")

    def test_stage2_uses_ghost_audit_content_and_python_run_command(self):
        self.player.current_stage = 2
        self.player.orientation_language = Player.OrientationLanguage.PYTHON
        self.player.save(update_fields=["current_stage", "orientation_language"])
        partner = create_player(self.run, "partner2")
        partner.current_stage = 2
        partner.save(update_fields=["current_stage"])

        response = self.client.get(f"/play/{self.player.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stage 2: Ghost Audit")
        self.assertContains(response, "AUGUR noticed the first breach.")
        self.assertContains(response, "stage2_ghost_audit.py")
        self.assertContains(response, "python stage2_ghost_audit.py stage2_dataset.csv")
        self.assertContains(response, "load = units * multiplier")
        self.assertContains(response, "Work with 1 collaborator")

    def test_stage3_uses_signal_test_content_and_python_run_command(self):
        self.player.current_stage = 3
        self.player.orientation_language = Player.OrientationLanguage.PYTHON
        self.player.save(update_fields=["current_stage", "orientation_language"])

        response = self.client.get(f"/play/{self.player.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stage 3: Signal Test")
        self.assertContains(response, "AUGUR has stopped simply hiding information.")
        self.assertContains(response, "Create a new script file in your preferred programming language")
        self.assertNotContains(response, "stage3_signal_test.py")
        self.assertNotContains(response, "python stage3_signal_test.py stage3_signal_readings.csv")
        self.assertContains(response, "ANOVA and post-hoc tests")

    def test_stage4_uses_forever_alone_drone_content(self):
        self.player.current_stage = 4
        self.player.orientation_language = Player.OrientationLanguage.PYTHON
        self.player.save(update_fields=["current_stage", "orientation_language"])

        response = self.client.get(f"/play/{self.player.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stage 4: Isolate and Capture")
        self.assertContains(response, "There are 20 drones in total.")
        self.assertContains(response, "Download the Stage 4 ZIP dataset")
        self.assertContains(response, "drone_serials.csv")

    def test_collaboration_requirement_respects_teacher_cap(self):
        self.player.current_stage = 2
        self.player.orientation_language = Player.OrientationLanguage.PYTHON
        self.player.save(update_fields=["current_stage", "orientation_language"])
        partner = create_player(self.run, "partner_cap")
        partner.current_stage = 2
        partner.save(update_fields=["current_stage"])

        self.run.collaboration_size_cap = 1
        self.run.save(update_fields=["collaboration_size_cap"])

        response = self.client.get(f"/play/{self.player.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No collaborators required.")
        self.assertNotContains(response, "Work with 1 collaborator")

    def test_stage2_dataset_decodes_to_player_stage2_code(self):
        stage2_code = StageCode.objects.get(player=self.player, stage=2).code
        response = self.client.get(f"/play/{self.player.id}/dataset/2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="stage2_dataset.csv"',
        )

        rows = list(csv.DictReader(StringIO(response.content.decode())))
        self.assertGreaterEqual(len(rows), 80)
        self.assertTrue(rows)
        self.assertEqual(
            set(rows[0].keys()),
            {"record_id", "sector", "status", "authentic", "priority", "units", "multiplier", "bias_key"},
        )

        sectors = {row["sector"] for row in rows}
        self.assertTrue(
            {"power", "traffic", "water", "emergency", "communications", "waste", "transit"}.issubset(sectors)
        )

        bias_values = {row["bias_key"] for row in rows}
        self.assertEqual(len(bias_values), 1)
        bias_key = int(next(iter(bias_values)))

        valid_rows = [
            row for row in rows
            if (
                row["status"] == "ACTIVE"
                and int(row["authentic"]) == 1
                and int(row["priority"]) >= 4
            )
        ]
        self.assertTrue(valid_rows)

        decoded = (sum(int(row["units"]) * int(row["multiplier"]) for row in valid_rows) + bias_key) % 1_000_000
        self.assertEqual(decoded, stage2_code)

        self.assertTrue(any(row["status"] != "ACTIVE" for row in rows))
        self.assertTrue(any(int(row["authentic"]) == 0 for row in rows))
        self.assertTrue(any(int(row["priority"]) < 4 for row in rows))

    def test_stage3_dataset_decodes_to_player_stage3_code(self):
        stage3_code = StageCode.objects.get(player=self.player, stage=3).code
        response = self.client.get(f"/play/{self.player.id}/dataset/3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="stage3_signal_readings.csv"',
        )

        rows = list(csv.DictReader(StringIO(response.content.decode())))
        self.assertTrue(rows)
        self.assertEqual(
            set(rows[0].keys()),
            {"reading_id", "district", "signal_strength", "district_code"},
        )

        counts_by_district: dict[str, int] = defaultdict(int)
        districts = set()
        signal_by_district: dict[str, list[float]] = defaultdict(list)
        district_codes_by_district: dict[str, set[int]] = defaultdict(set)

        for row in rows:
            district = row["district"]
            counts_by_district[district] += 1
            districts.add(district)
            signal_by_district[district].append(float(row["signal_strength"]))
            district_codes_by_district[district].add(int(row["district_code"]))

        self.assertGreaterEqual(len(districts), 20)
        for district in districts:
            self.assertEqual(len(district_codes_by_district[district]), 1)
            self.assertGreaterEqual(counts_by_district[district], 60)

        matching_districts = [
            district
            for district in districts
            if next(iter(district_codes_by_district[district])) == stage3_code
        ]
        self.assertEqual(len(matching_districts), 1)
        abnormal_district = matching_districts[0]

        decoded = next(iter(district_codes_by_district[abnormal_district])) % 1_000_000
        self.assertEqual(decoded, stage3_code)

        means_by_district = {
            district: sum(values) / len(values)
            for district, values in signal_by_district.items()
        }
        highest_mean_district = max(means_by_district, key=means_by_district.get)
        lowest_mean_district = min(means_by_district, key=means_by_district.get)
        self.assertNotIn(abnormal_district, {highest_mean_district, lowest_mean_district})

    def test_stage4_dataset_zip_contains_images_and_serial_mapping(self):
        stage4_code = StageCode.objects.get(player=self.player, stage=4).code
        response = self.client.get(f"/play/{self.player.id}/dataset/4")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="stage4_drone_fleet.zip"',
        )

        archive = zipfile.ZipFile(BytesIO(response.content))
        names = archive.namelist()
        image_names = sorted(name for name in names if name.startswith("images/") and name.endswith(".png"))
        self.assertEqual(len(image_names), 25)
        self.assertIn("drone_serials.csv", names)
        self.assertIn("sanity_check.csv", names)

        mapping_rows = list(csv.DictReader(StringIO(archive.read("drone_serials.csv").decode())))
        self.assertEqual(len(mapping_rows), 20)
        self.assertEqual(
            set(mapping_rows[0].keys()),
            {"drone_id", "serial_number"},
        )
        drone_ids = {int(row["drone_id"]) for row in mapping_rows}
        self.assertEqual(drone_ids, set(range(1, 21)))

        matching = [row for row in mapping_rows if int(row["serial_number"]) == stage4_code]
        self.assertEqual(len(matching), 1)

        sanity_rows = list(csv.DictReader(StringIO(archive.read("sanity_check.csv").decode())))
        self.assertTrue(sanity_rows)
        self.assertEqual(set(sanity_rows[0].keys()), {"image_name", "drone_id", "x", "y"})
        sanity_images = {row["image_name"] for row in sanity_rows}
        self.assertEqual(sanity_images, {"001.png", "002.png"})
        self.assertTrue(all(int(row["drone_id"]) in drone_ids for row in sanity_rows))
