from __future__ import annotations

import os
from typing import Any

import clickhouse_connect
from dotenv import load_dotenv
from datetime import datetime


load_dotenv(
    os.path.join(os.path.dirname(__file__), ".env")
)


def get_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
        username=os.getenv("CLICKHOUSE_USER"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        secure=True,
        database=os.getenv("CLICKHOUSE_DATABASE", "ripple"),
        connect_timeout=30,
    )


def get_scene_42_context() -> dict[str, Any]:
    client = get_client()

    query = """
    SELECT
        s.scene_id,
        s.title,
        l.location_id,
        l.location_name,
        l.location_type AS current_location_type,
        l.supports_night_shoot,

        a.actor_id,
        a.actor_name,

        aa.available_to AS actor_available_to,

        maxIf(
            sc.new_value,
            sc.field_name = 'location_type'
        ) AS revised_location_type,

        maxIf(
            sc.new_value,
            sc.field_name = 'time_of_day'
        ) AS revised_time_of_day,

        maxIf(
            sc.new_value,
            sc.field_name = 'scheduled_start_time'
        ) AS revised_start_time

    FROM ripple.scenes s

    JOIN ripple.locations l
        ON s.location_id = l.location_id

    JOIN ripple.scene_cast cast
        ON s.scene_id = cast.scene_id

    JOIN ripple.actors a
        ON cast.actor_id = a.actor_id

    JOIN ripple.actor_availability aa
        ON a.actor_id = aa.actor_id

    JOIN ripple.script_changes sc
        ON s.scene_id = sc.scene_id

    WHERE s.scene_id = 42
      AND a.actor_name = 'Maya Chen'
      AND aa.available_date = '2026-08-25'
      AND sc.version_id = 2

    GROUP BY
        s.scene_id,
        s.title,
        l.location_id,
        l.location_name,
        l.location_type,
        l.supports_night_shoot,
        a.actor_id,
        a.actor_name,
        aa.available_to
    """

    row = client.query(query).first_row

    if row is None:
        raise RuntimeError("No Scene 42 context found in ClickHouse.")

    return {
        "scene_id": row[0],
        "scene_title": row[1],
        "location_id": row[2],
        "location_name": row[3],
        "current_location_type": row[4],
        "supports_night_shoot": bool(row[5]),
        "actor_id": row[6],
        "actor_name": row[7],
        "actor_available_to": str(row[8]),
        "revised_location_type": row[9],
        "revised_time_of_day": row[10],
        "revised_start_time": row[11],
    }

def replace_scene_impacts(
    production_id: int,
    version_id: int,
    scene_id: int,
    impacts,
) -> None:
    client = get_client()

    # Make reruns safe: remove the previous analysis for this scene/version first.
    client.command(
        f"""
        ALTER TABLE ripple.impact_analysis
        DELETE WHERE production_id = {production_id}
          AND version_id = {version_id}
          AND scene_id = {scene_id}
        SETTINGS mutations_sync = 1
        """
    )

    if not impacts:
        return
    created_at = datetime.now()

    rows = []

    for index, impact in enumerate(impacts, start=1):
        analysis_id = (
            version_id * 1_000_000
            + scene_id * 100
            + index
        )

        rows.append(
            [
                analysis_id,
                production_id,
                version_id,
                scene_id,
                impact.impact_type,
                impact.impacted_entity_type,
                impact.impacted_entity_id,
                impact.severity,
                impact.description,
                impact.estimated_cost_change,
                impact.estimated_delay_minutes,
                impact.evidence,
                created_at,
            ]
        )

    client.insert(
        "ripple.impact_analysis",
        rows,
        column_names=[
            "analysis_id",
            "production_id",
            "version_id",
            "scene_id",
            "impact_type",
            "impacted_entity_type",
            "impacted_entity_id",
            "severity",
            "impact_description",
            "estimated_cost_change",
            "estimated_delay_minutes",
            "evidence",
            "created_at",
        ],
        settings={"insert_deduplicate": 0},
    )

def get_scene_42_recovery_candidates() -> list[dict[str, Any]]:
    client = get_client()

    query = """
    SELECT
        l.location_id,
        l.location_name,

        greatest(
            aa.available_from,
            la.available_from,
            sw.window_start
        ) AS feasible_start,

        least(
            aa.available_to,
            la.available_to,
            sw.window_end
        ) AS feasible_end,

        dateDiff(
            'minute',
            greatest(
                aa.available_from,
                la.available_from,
                sw.window_start
            ),
            least(
                aa.available_to,
                la.available_to,
                sw.window_end
            )
        ) AS feasible_minutes

    FROM ripple.locations l

    JOIN ripple.location_availability la
        ON l.location_id = la.location_id

    JOIN ripple.actor_availability aa
        ON aa.actor_id = 1
       AND aa.available_date = la.available_date

    JOIN ripple.shooting_windows sw
        ON sw.production_id = 1
       AND sw.shoot_date = la.available_date
       AND sw.window_type = 'NIGHT'

    WHERE l.production_id = 1
      AND l.location_type = 'EXTERIOR'
      AND l.supports_night_shoot = true
      AND la.availability_status = 'AVAILABLE'
      AND aa.availability_status = 'AVAILABLE'

    ORDER BY feasible_start
    """

    result = client.query(query)

    candidates = []

    for row in result.result_rows:
        candidates.append(
            {
                "location_id": row[0],
                "location_name": row[1],
                "feasible_start": row[2],
                "feasible_end": row[3],
                "feasible_minutes": row[4],
            }
        )

    return candidates

def replace_scene_recovery_plan(
    *,
    production_id: int,
    version_id: int,
    scene_id: int,
    analysis_id: int,
    plan,
) -> None:
    client = get_client()

    # Remove previous recovery actions for this scene/version.
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

    # Remove previous recovery plan for this scene/version.
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

    # Save recovery plan.
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

    # Save concrete recovery actions.
    actions = [
        [
            1,
            plan_id,
            1,
            "RESCHEDULE",
            "SCENE",
            scene_id,
            (
                f"Reschedule Scene {scene_id} to "
                f"{plan.start_time.strftime('%Y-%m-%d %I:%M %p')}."
            ),
            0.0,
            plan.delay_minutes,
        ],
        [
            2,
            plan_id,
            2,
            "CHANGE_LOCATION",
            "LOCATION",
            plan.location_id,
            (
                f"Move Scene {scene_id} to {plan.location_name}."
            ),
            plan.estimated_cost_change,
            0,
        ],
    ]

    client.insert(
        "ripple.recovery_plan_actions",
        actions,
        column_names=[
            "action_id",
            "plan_id",
            "action_order",
            "action_type",
            "entity_type",
            "entity_id",
            "action_description",
            "estimated_cost_change",
            "estimated_delay_minutes",
        ],
        settings={"insert_deduplicate": 0},
    )