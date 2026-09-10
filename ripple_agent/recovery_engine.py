from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class RecoveryPlan:
    location_id: int
    location_name: str
    start_time: datetime
    end_time: datetime
    delay_minutes: int
    estimated_cost_change: float
    disruption_score: float
    risk_level: str


def build_recovery_plan(
    *,
    location_id: int,
    location_name: str,
    feasible_start: datetime,
    feasible_end: datetime,
    scene_duration_minutes: int,
    original_start: datetime,
    estimated_cost_change: float = 0.0,
) -> RecoveryPlan | None:

    available_minutes = int(
        (feasible_end - feasible_start).total_seconds() / 60
    )

    if available_minutes < scene_duration_minutes:
        return None

    scene_end = feasible_start + (
        feasible_end - feasible_start
    ) * 0

    from datetime import timedelta

    scene_end = feasible_start + timedelta(
        minutes=scene_duration_minutes
    )

    delay_minutes = int(
        (feasible_start - original_start).total_seconds() / 60
    )

    disruption_score = 3.0

    return RecoveryPlan(
        location_id=location_id,
        location_name=location_name,
        start_time=feasible_start,
        end_time=scene_end,
        delay_minutes=delay_minutes,
        estimated_cost_change=estimated_cost_change,
        disruption_score=disruption_score,
        risk_level="LOW",
    )

def choose_recovery_plan(
    candidates: list[dict],
    scene_duration_minutes: int,
    original_start: datetime,
) -> RecoveryPlan | None:

    valid_candidates = [
        candidate
        for candidate in candidates
        if candidate["feasible_minutes"] >= scene_duration_minutes
    ]

    if not valid_candidates:
        return None

    best = min(
        valid_candidates,
        key=lambda candidate: candidate["feasible_start"],
    )

    return build_recovery_plan(
        location_id=best["location_id"],
        location_name=best["location_name"],
        feasible_start=best["feasible_start"],
        feasible_end=best["feasible_end"],
        scene_duration_minutes=scene_duration_minutes,
        original_start=original_start,
    )

def replace_scene_recovery_plan(
    *,
    production_id: int,
    version_id: int,
    scene_id: int,
    analysis_id: int,
    plan,
) -> None:
    client = get_client()

    client.command(
        f"""
        ALTER TABLE ripple.recovery_plan_actions
        DELETE WHERE plan_id IN (
            SELECT plan_id
            FROM ripple.recovery_plans
            WHERE production_id = {production_id}
              AND version_id = {version_id}
              AND scene_id = {scene_id}
        )
        SETTINGS mutations_sync = 1
        """
    )

    client.command(
        f"""
        ALTER TABLE ripple.recovery_plans
        DELETE WHERE production_id = {production_id}
          AND version_id = {version_id}
          AND scene_id = {scene_id}
        SETTINGS mutations_sync = 1
        """
    )

    if plan is None:
        return

    created_at = datetime.now()

    plan_id = (
        version_id * 1_000_000
        + scene_id * 100
        + 50
    )

    plan_name = (
        f"Move Scene {scene_id} to "
        f"{plan.start_time.strftime('%b %d Night')}"
    )

    recommendation_summary = (
        f"Move Scene {scene_id} to {plan.location_name} on "
        f"{plan.start_time.strftime('%Y-%m-%d')} from "
        f"{plan.start_time.strftime('%I:%M %p')} to "
        f"{plan.end_time.strftime('%I:%M %p')}."
    )

    client.insert(
        "ripple.recovery_plans",
        [[
            plan_id,
            analysis_id,
            production_id,
            version_id,
            scene_id,
            plan_name,
            1,
            plan.estimated_cost_change,
            plan.delay_minutes,
            plan.disruption_score,
            plan.risk_level,
            recommendation_summary,
            created_at,
        ]],
        column_names=[
            "plan_id",
            "analysis_id",
            "production_id",
            "version_id",
            "scene_id",
            "plan_name",
            "plan_rank",
            "estimated_cost_change",
            "estimated_delay_minutes",
            "disruption_score",
            "risk_level",
            "recommendation_summary",
            "created_at",
        ],
        settings={"insert_deduplicate": 0},
    )


def replace_scene_recovery_plan(
    *,
    production_id: int,
    version_id: int,
    scene_id: int,
    analysis_id: int,
    plan,
) -> None:
    client = get_client()

    client.command(
        f"""
        ALTER TABLE ripple.recovery_plan_actions
        DELETE WHERE plan_id IN (
            SELECT plan_id
            FROM ripple.recovery_plans
            WHERE production_id = {production_id}
              AND version_id = {version_id}
              AND scene_id = {scene_id}
        )
        SETTINGS mutations_sync = 1
        """
    )

    client.command(
        f"""
        ALTER TABLE ripple.recovery_plans
        DELETE WHERE production_id = {production_id}
          AND version_id = {version_id}
          AND scene_id = {scene_id}
        SETTINGS mutations_sync = 1
        """
    )

    if plan is None:
        return

    created_at = datetime.now()

    plan_id = (
        version_id * 1_000_000
        + scene_id * 100
        + 50
    )

    plan_name = (
        f"Move Scene {scene_id} to "
        f"{plan.start_time.strftime('%b %d Night')}"
    )

    recommendation_summary = (
        f"Move Scene {scene_id} to {plan.location_name} on "
        f"{plan.start_time.strftime('%Y-%m-%d')} from "
        f"{plan.start_time.strftime('%I:%M %p')} to "
        f"{plan.end_time.strftime('%I:%M %p')}."
    )

    client.insert(
        "ripple.recovery_plans",
        [[
            plan_id,
            analysis_id,
            production_id,
            version_id,
            scene_id,
            plan_name,
            1,
            plan.estimated_cost_change,
            plan.delay_minutes,
            plan.disruption_score,
            plan.risk_level,
            recommendation_summary,
            created_at,
        ]],
        column_names=[
            "plan_id",
            "analysis_id",
            "production_id",
            "version_id",
            "scene_id",
            "plan_name",
            "plan_rank",
            "estimated_cost_change",
            "estimated_delay_minutes",
            "disruption_score",
            "risk_level",
            "recommendation_summary",
            "created_at",
        ],
        settings={"insert_deduplicate": 0},
    )