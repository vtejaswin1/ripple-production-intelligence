from datetime import datetime, time

from .production_manifest import ProductionManifest


def _next_id(client, table_name: str, id_column: str) -> int:
    row = client.query(
        f"""
        SELECT max({id_column})
        FROM ripple.{table_name}
        """
    ).first_row

    current_max = row[0]

    return (
        1
        if current_max is None
        else int(current_max) + 1
    )


def import_production_manifest(
    client,
    production_id: int,
    manifest: ProductionManifest,
):
    # ---------------------------------------------------------
    # Verify production exists
    # ---------------------------------------------------------
    production_row = client.query(
        """
        SELECT
            start_date,
            end_date
        FROM ripple.productions
        WHERE production_id = %(production_id)s
        LIMIT 1
        """,
        parameters={
            "production_id": production_id,
        },
    ).first_row

    if production_row is None:
        raise ValueError(
            f"Production {production_id} was not found."
        )

    production_start_date = production_row[0]
    production_end_date = production_row[1]

    default_available_from = datetime.combine(
        production_start_date,
        time.min,
    )

    default_available_to = datetime.combine(
        production_end_date,
        time.max.replace(microsecond=0),
    )

    # ---------------------------------------------------------
    # ID counters
    # ---------------------------------------------------------
    next_actor_id = _next_id(
        client,
        "actors",
        "actor_id",
    )

    next_location_id = _next_id(
        client,
        "locations",
        "location_id",
    )

    next_scene_id = _next_id(
        client,
        "scenes",
        "scene_id",
    )

    next_dependency_id = _next_id(
        client,
        "production_dependencies",
        "dependency_id",
    )

    # ---------------------------------------------------------
    # Lookup maps
    # ---------------------------------------------------------
    actor_by_character = {}
    location_by_name = {}

    # ---------------------------------------------------------
    # 1. Actors
    # ---------------------------------------------------------
    actor_rows = []
    actor_availability_rows = []

    for actor in manifest.actors:
        actor_id = next_actor_id
        next_actor_id += 1

        character_key = (
            actor.character_name
            .strip()
            .lower()
        )

        actor_by_character[
            character_key
        ] = actor_id

        actor_rows.append(
            [
                actor_id,
                production_id,
                actor.actor_name.strip(),
                actor.character_name.strip(),
            ]
        )

        for window in actor.availability:
            actor_availability_rows.append(
                [
                    actor_id,
                    window.available_date,
                    window.available_from,
                    window.available_to,
                ]
            )

    if actor_rows:
        client.insert(
            "ripple.actors",
            actor_rows,
            column_names=[
                "actor_id",
                "production_id",
                "actor_name",
                "character_name",
            ],
        )

    if actor_availability_rows:
        client.insert(
            "ripple.actor_availability",
            actor_availability_rows,
            column_names=[
                "actor_id",
                "available_date",
                "available_from",
                "available_to",
            ],
        )

    # ---------------------------------------------------------
    # 2. Locations
    # ---------------------------------------------------------
    location_rows = []
    location_availability_rows = []
    location_constraint_rows = []

    for location in manifest.locations:
        location_id = next_location_id
        next_location_id += 1

        location_key = (
            location.location_name
            .strip()
            .lower()
        )

        location_by_name[
            location_key
        ] = {
            "location_id": location_id,
            "location_type":
                location.location_type.strip().upper(),
        }

        if location.availability:
            overall_available_from = min(
                window.available_from
                for window in location.availability
            )

            overall_available_to = max(
                window.available_to
                for window in location.availability
            )
        else:
            overall_available_from = (
                default_available_from
            )

            overall_available_to = (
                default_available_to
            )

        location_rows.append(
            [
                location_id,
                production_id,
                location.location_name.strip(),
                location.location_type.strip().upper(),
                location.city.strip(),
                overall_available_from,
                overall_available_to,
                location.supports_day_shoot,
                location.supports_night_shoot,
                location.base_cost_per_hour,
            ]
        )

        for window in location.availability:
            location_availability_rows.append(
                [
                    location_id,
                    window.available_date,
                    window.available_from,
                    window.available_to,
                    "AVAILABLE",
                ]
            )

        for constraint in location.constraints:
            location_constraint_rows.append(
                [
                    location_id,
                    constraint.constraint_type,
                    constraint.constraint_description,
                    constraint.effective_date,
                ]
            )

    if location_rows:
        client.insert(
            "ripple.locations",
            location_rows,
            column_names=[
                "location_id",
                "production_id",
                "location_name",
                "location_type",
                "city",
                "available_from",
                "available_to",
                "supports_day_shoot",
                "supports_night_shoot",
                "base_cost_per_hour",
            ],
        )

    if location_availability_rows:
        client.insert(
            "ripple.location_availability",
            location_availability_rows,
            column_names=[
                "location_id",
                "available_date",
                "available_from",
                "available_to",
                "availability_status",
            ],
        )

    if location_constraint_rows:
        client.insert(
            "ripple.location_constraints",
            location_constraint_rows,
            column_names=[
                "location_id",
                "constraint_type",
                "constraint_description",
                "effective_date",
            ],
        )

    # ---------------------------------------------------------
    # 3. Scenes + scene cast + location dependencies
    # ---------------------------------------------------------
    scene_rows = []
    scene_cast_rows = []
    dependency_rows = []

    for scene in manifest.scenes:
        scene_id = next_scene_id
        next_scene_id += 1

        location_key = (
            scene.location_name
            .strip()
            .lower()
        )

        location_info = location_by_name.get(
            location_key
        )

        if location_info is None:
            raise ValueError(
                f"Scene {scene.scene_number} references "
                f"unknown location "
                f"'{scene.location_name}'."
            )

        location_id = (
            location_info["location_id"]
        )

        location_type = (
            location_info["location_type"]
        )

        scene_rows.append(
            [
                scene_id,
                production_id,
                str(scene.scene_number),
                scene.title.strip(),
                location_type,
                scene.time_of_day.strip().upper(),
                scene.scheduled_date,
                scene.scheduled_start_time,
                scene.estimated_duration_minutes,
                scene.estimated_cost,
            ]
        )

        for character in scene.characters:
            actor_id = actor_by_character.get(
                character.strip().lower()
            )

            if actor_id is None:
                raise ValueError(
                    f"Scene {scene.scene_number} references "
                    f"unregistered character "
                    f"'{character}'."
                )

            scene_cast_rows.append(
                [
                    scene_id,
                    actor_id,
                    "CAST",
                ]
            )

        dependency_rows.append(
            [
                next_dependency_id,
                production_id,
                "SCENE",
                scene_id,
                "LOCATION",
                location_id,
                "LOCATION",
                "HARD",
                (
                    f"Scene {scene.scene_number} is "
                    f"scheduled at "
                    f"{scene.location_name}."
                ),
            ]
        )

        next_dependency_id += 1

    if scene_rows:
        client.insert(
            "ripple.scenes",
            scene_rows,
            column_names=[
                "scene_id",
                "production_id",
                "scene_number",
                "title",
                "location_type",
                "time_of_day",
                "scheduled_date",
                "scheduled_start_time",
                "estimated_duration_minutes",
                "estimated_cost",
            ],
        )

    if scene_cast_rows:
        client.insert(
            "ripple.scene_cast",
            scene_cast_rows,
            column_names=[
                "scene_id",
                "actor_id",
                "role_type",
            ],
        )

    if dependency_rows:
        client.insert(
            "ripple.production_dependencies",
            dependency_rows,
            column_names=[
                "dependency_id",
                "production_id",
                "source_entity_type",
                "source_entity_id",
                "target_entity_type",
                "target_entity_id",
                "dependency_type",
                "dependency_strength",
                "notes",
            ],
        )

    # ---------------------------------------------------------
    # Result
    # ---------------------------------------------------------
    return {
        "production_id": production_id,
        "actors_imported": len(actor_rows),
        "actor_availability_windows":
            len(actor_availability_rows),
        "locations_imported":
            len(location_rows),
        "location_availability_windows":
            len(location_availability_rows),
        "location_constraints_imported":
            len(location_constraint_rows),
        "scenes_imported":
            len(scene_rows),
        "scene_cast_links":
            len(scene_cast_rows),
        "location_dependencies":
            len(dependency_rows),
    }