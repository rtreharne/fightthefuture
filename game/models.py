from __future__ import annotations

from django.core.validators import EmailValidator
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .constants import FINAL_STAGE, STAGE_COUNT


class EventSettings(models.Model):
    title = models.CharField(max_length=200, default="Fight The Future")
    event_date = models.CharField(max_length=120, blank=True)
    event_time = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=200, blank=True)
    permitted_email_domain = models.CharField(max_length=120, default="liverpool.ac.uk")
    registration_limit = models.PositiveSmallIntegerField(default=100, validators=[MinValueValidator(1), MaxValueValidator(10000)])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "event settings"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        self.title = self.title.strip() or "Fight The Future"
        self.event_date = self.event_date.strip()
        self.event_time = self.event_time.strip()
        self.location = self.location.strip()
        self.permitted_email_domain = self.permitted_email_domain.strip().lower().lstrip("@") or "liverpool.ac.uk"
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> EventSettings:
        settings_obj, _created = cls.objects.get_or_create(pk=1)
        return settings_obj


class EventRegistration(models.Model):
    event_settings = models.ForeignKey(EventSettings, on_delete=models.CASCADE, related_name="registrations")
    full_name = models.CharField(max_length=200)
    email = models.EmailField(max_length=254, validators=[EmailValidator()])
    email_key = models.CharField(max_length=254, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"

    def save(self, *args, **kwargs):
        self.full_name = self.full_name.strip()
        self.email = self.email.strip()
        self.email_key = self.email.strip().lower()
        super().save(*args, **kwargs)


class Run(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_current = models.BooleanField(default=False, db_index=True)
    collaboration_size_cap = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(8)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name or f"Run {self.pk}"

    def save(self, *args, **kwargs):
        if not self.name:
            stamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
            self.name = f"run_{stamp}"
        super().save(*args, **kwargs)

    @classmethod
    def current(cls) -> Run | None:
        return cls.objects.filter(is_current=True).first()


class Player(models.Model):
    class OrientationDeviceType(models.TextChoices):
        OWN = "own", "Own Device"
        UOL = "uol", "University of Liverpool Machine"

    class OrientationOS(models.TextChoices):
        WINDOWS = "windows", "Windows"
        MAC = "mac", "Mac"
        CHROMEBOOK = "chromebook", "Chromebook"
        LINUX = "linux", "Linux"

    class OrientationLanguage(models.TextChoices):
        R = "r", "R"
        PYTHON = "python", "Python"
        JAVASCRIPT = "javascript", "JavaScript"

    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="players")
    username = models.CharField(max_length=80)
    username_key = models.CharField(max_length=80)
    current_stage = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(FINAL_STAGE + 1)],
    )
    is_test_user = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    checker_fail_count = models.PositiveSmallIntegerField(default=0)
    checker_locked_until = models.DateTimeField(null=True, blank=True)
    checker_stage = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(STAGE_COUNT)],
    )
    checker_verified_stage = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(STAGE_COUNT)],
    )
    intro_accepted = models.BooleanField(default=False)
    orientation_completed = models.BooleanField(default=False)
    orientation_collapsed = models.BooleanField(default=False)
    orientation_step = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    orientation_device_type = models.CharField(
        max_length=12,
        choices=OrientationDeviceType.choices,
        null=True,
        blank=True,
    )
    orientation_os = models.CharField(
        max_length=16,
        choices=OrientationOS.choices,
        null=True,
        blank=True,
    )
    orientation_language = models.CharField(
        max_length=16,
        choices=OrientationLanguage.choices,
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["run", "username_key"], name="uniq_player_name_per_run"),
        ]
        ordering = ["joined_at", "id"]

    def __str__(self) -> str:
        return f"{self.username} ({self.run})"

    def save(self, *args, **kwargs):
        self.username = self.username.strip()
        self.username_key = self.username.lower()
        super().save(*args, **kwargs)

    @property
    def is_complete(self) -> bool:
        return self.current_stage > FINAL_STAGE


class StageCode(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="stage_codes")
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="stage_codes")
    stage = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(STAGE_COUNT)]
    )
    code = models.PositiveIntegerField(
        validators=[MinValueValidator(100000), MaxValueValidator(999999)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["player", "stage"], name="uniq_stage_code_per_player_stage"),
            models.UniqueConstraint(fields=["run", "stage", "code"], name="uniq_stage_code_per_run_stage"),
        ]
        ordering = ["player_id", "stage"]

    def __str__(self) -> str:
        return f"{self.player.username} S{self.stage}={self.code}"


class PodiumSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        INVALID = "invalid", "Invalid"

    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="submissions")
    submitted_sum = models.BigIntegerField()
    submitted_by = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    stage = models.PositiveSmallIntegerField(null=True, blank=True)
    required_size = models.PositiveSmallIntegerField(null=True, blank=True)
    resolved_manually = models.BooleanField(default=False)
    progressed_usernames = models.JSONField(default=list)
    message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"Submission {self.id} ({self.status})"


class SubmissionCandidate(models.Model):
    submission = models.ForeignKey(
        PodiumSubmission,
        on_delete=models.CASCADE,
        related_name="candidates",
    )
    stage = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(STAGE_COUNT)]
    )
    player_ids = models.JSONField(default=list)
    player_usernames = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"Candidate {self.id} for submission {self.submission_id}"


class PlayerFeedback(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="player_feedback")
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name="feedback")
    clarity_rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    engagement_rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    collaboration_rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    confidence_rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pacing_rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.TextField(blank=True)
    likert_responses = models.JSONField(default=dict, blank=True)
    open_responses = models.JSONField(default=dict, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"Feedback {self.player.username} ({self.run})"
