from django.contrib import admin

from .models import Player, PodiumSubmission, Run, StageCode, SubmissionCandidate


@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "is_current", "created_at", "archived_at")
    list_filter = ("status", "is_current")


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "run",
        "current_stage",
        "orientation_completed",
        "orientation_step",
        "orientation_device_type",
        "orientation_language",
        "is_test_user",
        "is_suspended",
        "joined_at",
    )
    list_filter = ("run", "current_stage", "is_test_user", "is_suspended")
    search_fields = ("username", "username_key")


@admin.register(StageCode)
class StageCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "run", "player", "stage", "code")
    list_filter = ("run", "stage")


@admin.register(PodiumSubmission)
class PodiumSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "run",
        "submitted_sum",
        "status",
        "stage",
        "required_size",
        "resolved_manually",
        "submitted_at",
    )
    list_filter = ("run", "status", "resolved_manually", "stage")


@admin.register(SubmissionCandidate)
class SubmissionCandidateAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "stage", "player_ids", "created_at")
    list_filter = ("stage",)
