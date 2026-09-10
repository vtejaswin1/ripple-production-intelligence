from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Impact:
    impact_type: str
    severity: str
    description: str
    evidence: str
    impacted_entity_type: str
    impacted_entity_id: int
    estimated_cost_change: float = 0.0
    estimated_delay_minutes: int = 0


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def detect_actor_availability_conflict(
    actor_id: int,
    actor_name: str,
    revised_start_time: str,
    available_to: str,
) -> Impact | None:
    revised_start = parse_dt(revised_start_time)
    actor_available_to = parse_dt(available_to)

    if revised_start > actor_available_to:
        return Impact(
            impact_type="ACTOR_AVAILABILITY",
            severity="HIGH",
            description=(
                f"{actor_name} is unavailable at the revised scene start time."
            ),
            evidence=(
                f"{actor_name} is available until {actor_available_to.isoformat(sep=' ')}; "
                f"the revised scene starts at {revised_start.isoformat(sep=' ')}."
            ),
            impacted_entity_type="ACTOR",
            impacted_entity_id=actor_id,
        )

    return None


def detect_location_type_conflict(
    location_id: int,
    location_name: str,
    current_location_type: str,
    revised_location_type: str,
) -> Impact | None:
    if current_location_type.upper() != revised_location_type.upper():
        return Impact(
            impact_type="LOCATION_TYPE",
            severity="HIGH",
            description=(
                f"The revised scene requires a {revised_location_type} location, "
                f"but {location_name} is {current_location_type}."
            ),
            evidence=(
                f"Assigned location {location_name} has location_type="
                f"{current_location_type}; revised requirement="
                f"{revised_location_type}."
            ),
            impacted_entity_type="LOCATION",
            impacted_entity_id=location_id,
        )

    return None


def detect_night_shoot_conflict(
    location_id: int,
    location_name: str,
    revised_time_of_day: str,
    supports_night_shoot: bool,
) -> Impact | None:
    if revised_time_of_day.upper() == "NIGHT" and not supports_night_shoot:
        return Impact(
            impact_type="NIGHT_SHOOT",
            severity="HIGH",
            description=(
                f"The revised scene is a night shoot, but {location_name} "
                f"does not support night shooting."
            ),
            evidence=(
                f"Revised time_of_day=NIGHT; "
                f"{location_name} supports_night_shoot={supports_night_shoot}."
            ),
            impacted_entity_type="LOCATION",
            impacted_entity_id=location_id,
        )

    return None


def detect_impacts(context: dict[str, Any]) -> list[Impact]:
    impacts: list[Impact] = []

    actor_impact = detect_actor_availability_conflict(
        actor_id=context["actor_id"],
        actor_name=context["actor_name"],
        revised_start_time=context["revised_start_time"],
        available_to=context["actor_available_to"],
    )
    if actor_impact:
        impacts.append(actor_impact)

    location_type_impact = detect_location_type_conflict(
        location_id=context["location_id"],
        location_name=context["location_name"],
        current_location_type=context["current_location_type"],
        revised_location_type=context["revised_location_type"],
    )
    if location_type_impact:
        impacts.append(location_type_impact)

    night_impact = detect_night_shoot_conflict(
        location_id=context["location_id"],
        location_name=context["location_name"],
        revised_time_of_day=context["revised_time_of_day"],
        supports_night_shoot=context["supports_night_shoot"],
    )
    if night_impact:
        impacts.append(night_impact)

    return impacts