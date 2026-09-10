from dataclasses import dataclass
from typing import List


@dataclass
class SceneDependency:
    dependency_type: str
    dependency_name: str
    dependency_id: int | None
    status: str
    evidence: str


def resolve_scene_dependencies(
    client,
    production_id: int,
    scene_number: int,
) -> List[SceneDependency]:

    dependencies: List[SceneDependency] = []

    # ---------------------------------------------------------
    # 1. Actor dependencies
    #
    # Only resolve cast from the requested production.
    # This prevents another production with the same
    # scene number from leaking into the analysis.
    # ---------------------------------------------------------
    cast_query = """
    SELECT DISTINCT
        a.actor_id,
        a.actor_name
    FROM ripple.scene_cast sc
    INNER JOIN ripple.actors a
        ON sc.actor_id = a.actor_id
    INNER JOIN ripple.scenes s
        ON sc.scene_id = s.scene_id
    WHERE s.production_id = %(production_id)s
      AND toUInt32(s.scene_number) = %(scene_number)s
    """

    cast_rows = client.query(
        cast_query,
        parameters={
            "production_id": production_id,
            "scene_number": scene_number,
        },
    ).result_rows

    for actor_id, actor_name in cast_rows:
        dependencies.append(
            SceneDependency(
                dependency_type="ACTOR",
                dependency_name=actor_name,
                dependency_id=int(actor_id),
                status="FOUND",
                evidence=(
                    f"{actor_name} is assigned to "
                    f"Scene {scene_number} in "
                    f"Production {production_id}."
                ),
            )
        )

    # ---------------------------------------------------------
    # 2. Current location dependency
#
# Scene -> Location relationships are stored through
# ripple.production_dependencies because ripple.scenes
# does not contain location_id.
# ---------------------------------------------------------
    location_query = """
SELECT DISTINCT
    l.location_id,
    l.location_name,
    pd.dependency_strength,
    pd.notes
FROM ripple.production_dependencies pd
INNER JOIN ripple.scenes s
    ON pd.source_entity_id = s.scene_id
INNER JOIN ripple.locations l
    ON pd.target_entity_id = l.location_id
WHERE pd.production_id = %(production_id)s
  AND pd.source_entity_type = 'SCENE'
  AND pd.target_entity_type = 'LOCATION'
  AND s.production_id = %(production_id)s
  AND toUInt32(s.scene_number) = %(scene_number)s
"""

    location_rows = client.query(
        location_query,
        parameters={
            "production_id": production_id,
            "scene_number": scene_number,
        },
    ).result_rows

    for (
    location_id,
    location_name,
    dependency_strength,
    notes,
) in location_rows:
        dependencies.append(
            SceneDependency(
                dependency_type="LOCATION",
                dependency_name=location_name,
                dependency_id=int(location_id),
                status=dependency_strength or "FOUND",
                evidence=(
            notes
            if notes
            else (
                f"{location_name} is the registered location "
                f"dependency for Scene {scene_number} in "
                f"Production {production_id}."
            )
        ),
            )
        )

    # ---------------------------------------------------------
    # 3. Explicit production dependencies
    #
    # IMPORTANT:
    # The old implementation was hardcoded to production_id = 1.
    # This now uses the requested production_id everywhere.
    # ---------------------------------------------------------
    dependency_query = """
    SELECT
        dependency_type,
        target_entity_type,
        target_entity_id,
        dependency_strength,
        notes
    FROM ripple.production_dependencies
    WHERE production_id = %(production_id)s
      AND source_entity_type = 'SCENE'
      AND target_entity_type != 'LOCATION'
      AND source_entity_id = (
          SELECT scene_id
          FROM ripple.scenes
          WHERE production_id = %(production_id)s
            AND toUInt32(scene_number) = %(scene_number)s
          LIMIT 1
      )
    """

    dependency_rows = client.query(
        dependency_query,
        parameters={
            "production_id": production_id,
            "scene_number": scene_number,
        },
    ).result_rows

    for (
        dependency_type,
        target_entity_type,
        target_entity_id,
        dependency_strength,
        notes,
    ) in dependency_rows:

        dependency_name = (
            f"{target_entity_type} #{target_entity_id}"
        )

        evidence = (
            notes
            if notes
            else (
                f"Scene {scene_number} in "
                f"Production {production_id} has a "
                f"{dependency_type} dependency on "
                f"{target_entity_type} "
                f"#{target_entity_id}."
            )
        )

        dependencies.append(
            SceneDependency(
                dependency_type=dependency_type,
                dependency_name=dependency_name,
                dependency_id=int(target_entity_id),
                status=dependency_strength,
                evidence=evidence,
            )
        )

    return dependencies