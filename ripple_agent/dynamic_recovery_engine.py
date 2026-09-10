from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class RecoveryOption:
    location_id: int
    location_name: str
    start_time: str
    end_time: str
    duration_minutes: int
    delay_minutes: int
    estimated_location_cost: float
    risk_level: str
    reason: str


def _parse_scene_requirements(changes):
    required_location_type = None
    required_time_of_day = None
    required_characters = []

    for change in changes:
        field = change["field"]

        if field == "location_type":
            required_location_type = change["after"]

        elif field == "time_of_day":
            required_time_of_day = change["after"]

        elif field == "characters":
            required_characters = change["after"] or []

    return (
        required_location_type,
        required_time_of_day,
        required_characters,
    )


def find_recovery_options(
    client,
    production_id: int,
    scene_number: int,
    changes: list[dict],
    max_options: int = 3,
):
    # ---------------------------------------------------------
    # 1. Get scene schedule/duration
    # ---------------------------------------------------------
    scene_row = client.query(
        """
        SELECT
            scheduled_start_time,
            estimated_duration_minutes
        FROM ripple.scenes
        WHERE production_id = %(production_id)s
          AND toUInt32(scene_number) = %(scene_number)s
        LIMIT 1
        """,
        parameters={
            "production_id": production_id,
            "scene_number": scene_number,
        },
    ).first_row

    if scene_row is None:
        return []

    original_start = scene_row[0]
    duration_minutes = int(scene_row[1])

    (
        required_location_type,
        required_time_of_day,
        required_characters,
    ) = _parse_scene_requirements(changes)

    # ---------------------------------------------------------
    # 2. If a field did not change, use current scene value
    # ---------------------------------------------------------
    current_scene = client.query(
        """
        SELECT
            location_type,
            time_of_day
        FROM ripple.scenes
        WHERE production_id = %(production_id)s
          AND toUInt32(scene_number) = %(scene_number)s
        LIMIT 1
        """,
        parameters={
            "production_id": production_id,
            "scene_number": scene_number,
        },
    ).first_row

    if current_scene:
        if required_location_type is None:
            required_location_type = current_scene[0]

        if required_time_of_day is None:
            required_time_of_day = current_scene[1]

    # ---------------------------------------------------------
    # 3. Resolve required actors from screenplay characters
    # ---------------------------------------------------------
    actor_ids = []

    for character in required_characters:
        actor_row = client.query(
            """
            SELECT actor_id
            FROM ripple.actors
            WHERE production_id = %(production_id)s
              AND lower(character_name) = lower(%(character)s)
            LIMIT 1
            """,
            parameters={
                "production_id": production_id,
                "character": character,
            },
        ).first_row

        if actor_row is None:
            # Cannot build a safe plan if required cast is unregistered.
            return []

        actor_ids.append(int(actor_row[0]))

    # ---------------------------------------------------------
    # 4. Find compatible locations
    # ---------------------------------------------------------
    location_query = """
    SELECT
        location_id,
        location_name,
        base_cost_per_hour
    FROM ripple.locations
    WHERE production_id = %(production_id)s
      AND location_type = %(location_type)s
    """

    location_rows = client.query(
        location_query,
        parameters={
            "production_id": production_id,
            "location_type": required_location_type,
        },
    ).result_rows

    options = []

    # ---------------------------------------------------------
    # 5. Test each location's availability + cast overlap
    # ---------------------------------------------------------
    for (
        location_id,
        location_name,
        base_cost_per_hour,
    ) in location_rows:

        # Day/night capability
        capability_row = client.query(
            """
            SELECT
                supports_day_shoot,
                supports_night_shoot
            FROM ripple.locations
            WHERE location_id = %(location_id)s
              AND production_id = %(production_id)s
            LIMIT 1
            """,
            parameters={
                "location_id": location_id,
                "production_id": production_id,
            },
        ).first_row

        if capability_row is None:
            continue

        supports_day, supports_night = capability_row

        if (
            required_time_of_day == "DAY"
            and not supports_day
        ):
            continue

        if (
            required_time_of_day == "NIGHT"
            and not supports_night
        ):
            continue

        # Get available windows for location
        availability_rows = client.query(
            """
            SELECT
                available_from,
                available_to
            FROM ripple.location_availability
            WHERE location_id = %(location_id)s
              AND availability_status = 'AVAILABLE'
            ORDER BY available_from
            """,
            parameters={
                "location_id": location_id,
            },
        ).result_rows

        for location_start, location_end in availability_rows:

            overlap_start = location_start
            overlap_end = location_end

            # Restrict by every required actor
            all_actors_available = True

            for actor_id in actor_ids:
                actor_window = client.query(
                    """
                    SELECT
                        available_from,
                        available_to
                    FROM ripple.actor_availability
                    WHERE actor_id = %(actor_id)s
                      AND available_from <= %(location_end)s
                      AND available_to >= %(location_start)s
                    ORDER BY available_from
                    LIMIT 1
                    """,
                    parameters={
                        "actor_id": actor_id,
                        "location_start": location_start,
                        "location_end": location_end,
                    },
                ).first_row

                if actor_window is None:
                    all_actors_available = False
                    break

                actor_start, actor_end = actor_window

                overlap_start = max(
                    overlap_start,
                    actor_start,
                )

                overlap_end = min(
                    overlap_end,
                    actor_end,
                )

            if not all_actors_available:
                continue

            available_minutes = int(
                (
                    overlap_end - overlap_start
                ).total_seconds()
                / 60
            )

            if available_minutes < duration_minutes:
                continue

            proposed_start = overlap_start
            proposed_end = proposed_start + timedelta(
                minutes=duration_minutes
            )

            delay_minutes = int(
                (
                    proposed_start - original_start
                ).total_seconds()
                / 60
            )

            estimated_location_cost = round(
                float(base_cost_per_hour)
                * (duration_minutes / 60),
                2,
            )

            risk_level = (
                "LOW"
                if delay_minutes <= 1440
                else "MEDIUM"
                if delay_minutes <= 2880
                else "HIGH"
            )

            options.append(
                RecoveryOption(
                    location_id=int(location_id),
                    location_name=location_name,
                    start_time=proposed_start.isoformat(
                        sep=" "
                    ),
                    end_time=proposed_end.isoformat(
                        sep=" "
                    ),
                    duration_minutes=duration_minutes,
                    delay_minutes=delay_minutes,
                    estimated_location_cost=estimated_location_cost,
                    risk_level=risk_level,
                    reason=(
                        f"{location_name} matches "
                        f"{required_location_type} / "
                        f"{required_time_of_day}, "
                        f"and the registered cast has "
                        f"a {duration_minutes}-minute "
                        f"overlapping availability window."
                    ),
                )
            )

    # ---------------------------------------------------------
    # 6. Rank options
    #
    # Lowest positive delay first, then lowest cost.
    # ---------------------------------------------------------
    options.sort(
        key=lambda option: (
            max(option.delay_minutes, 0),
            option.estimated_location_cost,
        )
    )

    return [
        asdict(option)
        for option in options[:max_options]
    ]