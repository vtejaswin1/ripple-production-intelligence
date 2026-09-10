from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class DynamicConflict:
    conflict_type: str
    severity: str
    message: str
    evidence: str


def evaluate_scene_changes(
    client,
    production_id: int,
    scene_number: int,
    changes: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
):
    conflicts: list[DynamicConflict] = []

    changed_fields = {
        change["field"]: change
        for change in changes
    }

    # ---------------------------------------------------------
    # 1. Location type compatibility
    #
    # The location dependency supplied here has already been
    # resolved for the requested production.
    # ---------------------------------------------------------
    if "location_type" in changed_fields:
        new_location_type = (
            changed_fields["location_type"]["after"]
        )

        location_dependencies = [
            dependency
            for dependency in dependencies
            if dependency["dependency_type"] == "LOCATION"
        ]

        for dependency in location_dependencies:
            location_id = dependency["dependency_id"]

            location_rows = client.query(
                """
                SELECT
                    location_name,
                    location_type
                FROM ripple.locations
                WHERE location_id = %(location_id)s
                LIMIT 1
                """,
                parameters={
                    "location_id": location_id,
                },
            ).result_rows

            if location_rows:
                (
                    location_name,
                    actual_location_type,
                ) = location_rows[0]

                if (
                    actual_location_type
                    != new_location_type
                ):
                    conflicts.append(
                        DynamicConflict(
                            conflict_type="LOCATION_TYPE",
                            severity="HIGH",
                            message=(
                                f"Scene {scene_number} now requires "
                                f"{new_location_type}, but "
                                f"{location_name} is "
                                f"{actual_location_type}."
                            ),
                            evidence=(
                                f"Production {production_id}, "
                                f"Scene {scene_number}: the script "
                                f"revision changed location type to "
                                f"{new_location_type}. The registered "
                                f"location {location_name} is "
                                f"{actual_location_type}."
                            ),
                        )
                    )

    # ---------------------------------------------------------
    # 2. Day / night compatibility
    # ---------------------------------------------------------
    if "time_of_day" in changed_fields:
        new_time_of_day = (
            changed_fields["time_of_day"]["after"]
        )

        location_dependencies = [
            dependency
            for dependency in dependencies
            if dependency["dependency_type"] == "LOCATION"
        ]

        for dependency in location_dependencies:
            location_id = dependency["dependency_id"]

            location_rows = client.query(
                """
                SELECT
                    location_name,
                    supports_day_shoot,
                    supports_night_shoot
                FROM ripple.locations
                WHERE location_id = %(location_id)s
                LIMIT 1
                """,
                parameters={
                    "location_id": location_id,
                },
            ).result_rows

            if location_rows:
                (
                    location_name,
                    supports_day_shoot,
                    supports_night_shoot,
                ) = location_rows[0]

                if (
                    new_time_of_day == "DAY"
                    and not supports_day_shoot
                ):
                    conflicts.append(
                        DynamicConflict(
                            conflict_type="DAY_SHOOT",
                            severity="HIGH",
                            message=(
                                f"{location_name} does not support "
                                f"day shooting for Scene "
                                f"{scene_number}."
                            ),
                            evidence=(
                                f"Production {production_id}, "
                                f"Scene {scene_number} changed to DAY, "
                                f"but its registered location does "
                                f"not support day shoots."
                            ),
                        )
                    )

                if (
                    new_time_of_day == "NIGHT"
                    and not supports_night_shoot
                ):
                    conflicts.append(
                        DynamicConflict(
                            conflict_type="NIGHT_SHOOT",
                            severity="HIGH",
                            message=(
                                f"{location_name} does not support "
                                f"night shooting for Scene "
                                f"{scene_number}."
                            ),
                            evidence=(
                                f"Production {production_id}, "
                                f"Scene {scene_number} changed to "
                                f"NIGHT, but its registered location "
                                f"does not support night shoots."
                            ),
                        )
                    )

    # ---------------------------------------------------------
    # 3. Cast changes
    #
    # IMPORTANT:
    # Do not search ripple.actors globally.
    #
    # A matching actor must already participate in at least one
    # registered scene belonging to THIS production.
    # ---------------------------------------------------------
    if "characters" in changed_fields:
        before_characters = set(
            changed_fields["characters"]["before"]
            or []
        )

        after_characters = set(
            changed_fields["characters"]["after"]
            or []
        )

        added_characters = sorted(
            after_characters - before_characters
        )

        for character in added_characters:
            actor_rows = client.query(
                """
                SELECT DISTINCT
                    a.actor_id,
                    a.actor_name,
                    a.character_name,
                FROM ripple.actors a
                INNER JOIN ripple.scene_cast sc
                    ON a.actor_id = sc.actor_id
                INNER JOIN ripple.scenes s
                    ON sc.scene_id = s.scene_id
                WHERE s.production_id = %(production_id)s
                  AND lower(a.character_name) =
                      lower(%(character)s)
                LIMIT 1
                """,
                parameters={
                    "production_id": production_id,
                    "character": character,
                },
            ).result_rows

            if not actor_rows:
                conflicts.append(
                    DynamicConflict(
                        conflict_type="CAST_DEPENDENCY",
                        severity="MEDIUM",
                        message=(
                            f"{character} was added to Scene "
                            f"{scene_number}, but no registered "
                            f"actor for this production was found."
                        ),
                        evidence=(
                            f"Production {production_id}, "
                            f"Scene {scene_number}: the revised "
                            f"screenplay added {character}, but "
                            f"that character is not currently "
                            f"linked to the production's "
                            f"registered cast data."
                        ),
                    )
                )

    return {
        "production_id": production_id,
        "scene_number": scene_number,
        "conflict_count": len(conflicts),
        "status": (
            "CONFLICTS"
            if conflicts
            else "NO_CONFLICTS"
        ),
        "conflicts": [
            asdict(conflict)
            for conflict in conflicts
        ],
    }