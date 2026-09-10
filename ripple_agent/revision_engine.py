from dataclasses import dataclass, asdict
from typing import Any
from .dependency_engine import resolve_scene_dependencies
from .dynamic_conflict_engine import evaluate_scene_changes
from .dynamic_recovery_engine import find_recovery_options

@dataclass
class FieldChange:
    field: str
    before: Any
    after: Any


@dataclass
class SceneChange:
    scene_number: int
    change_type: str
    changes: list[FieldChange]

def _build_changed_scene_result(
    client,
    production_id: int,
    item,
):
    changes = [
        asdict(change)
        for change in item.changes
    ]

    if item.change_type == "REMOVED":
        return {
            "scene_number": item.scene_number,
            "change_type": item.change_type,
            "changes": changes,
            "dependencies": [],
            "recovery_options": [],
            "analysis": {
                "scene_number": item.scene_number,
                "conflict_count": 0,
                "status": "NOT_ANALYZED",
                "conflicts": [],
            },
        }

    dependencies = [
        asdict(dependency)
        for dependency in resolve_scene_dependencies(
            client,
            production_id,
            item.scene_number,
        )
    ]

    analysis = evaluate_scene_changes(
        client,
        production_id,
        item.scene_number,
        changes,
        dependencies,
    )

    recovery_options = find_recovery_options(
        client,
        production_id,
        item.scene_number,
        changes,
    )

    return {
        "scene_number": item.scene_number,
        "change_type": item.change_type,
        "changes": changes,
        "dependencies": dependencies,
        "analysis": analysis,
        "recovery_options": recovery_options,
    }

def compare_latest_revisions(client, production_id: int = 1):
    version_rows = client.query(
        """
        SELECT DISTINCT version_id
        FROM ripple.uploaded_script_scenes
        WHERE production_id = %(production_id)s
        ORDER BY version_id DESC
        LIMIT 2
        """,
        parameters={"production_id": production_id},
    ).result_rows

    if not version_rows:
        return {
            "status": "NO_UPLOAD",
            "message": "No script uploaded yet. Upload a screenplay to begin analysis.",
            "previous_version": None,
            "current_version": None,
            "changed_scenes": [],
        }

    current_version = int(version_rows[0][0])

    if len(version_rows) == 1:
        return {
            "status": "BASELINE",
            "message": (
                "Baseline script created. No previous revision exists to compare, "
                "so no changes were detected."
            ),
            "previous_version": None,
            "current_version": current_version,
            "changed_scenes": [],
        }

    previous_version = int(version_rows[1][0])

    query = """
    SELECT
        version_id,
        scene_number,
        heading,
        location_name,
        location_type,
        time_of_day,
        characters
    FROM ripple.uploaded_script_scenes
    WHERE production_id = %(production_id)s
      AND version_id IN (%(previous_version)s, %(current_version)s)
    ORDER BY version_id, scene_number
    """

    rows = client.query(
        query,
        parameters={
            "production_id": production_id,
            "previous_version": previous_version,
            "current_version": current_version,
        },
    ).result_rows

    previous_scenes = {}
    current_scenes = {}

    for row in rows:
        (
            version_id,
            scene_number,
            heading,
            location_name,
            location_type,
            time_of_day,
            characters,
        ) = row

        scene_data = {
            "heading": heading,
            "location_name": location_name,
            "location_type": location_type,
            "time_of_day": time_of_day,
            "characters": sorted(characters or []),
        }

        if int(version_id) == previous_version:
            previous_scenes[int(scene_number)] = scene_data
        else:
            current_scenes[int(scene_number)] = scene_data

    changed_scenes = []

    all_scene_numbers = sorted(
        set(previous_scenes.keys()) | set(current_scenes.keys())
    )

    for scene_number in all_scene_numbers:
        before = previous_scenes.get(scene_number)
        after = current_scenes.get(scene_number)

        if before is None:
            changed_scenes.append(
                SceneChange(
                    scene_number=scene_number,
                    change_type="ADDED",
                    changes=[],
                )
            )
            continue

        if after is None:
            changed_scenes.append(
                SceneChange(
                    scene_number=scene_number,
                    change_type="REMOVED",
                    changes=[],
                )
            )
            continue

        field_changes = []

        for field in [
            "heading",
            "location_name",
            "location_type",
            "time_of_day",
            "characters",
        ]:
            if before[field] != after[field]:
                field_changes.append(
                    FieldChange(
                        field=field,
                        before=before[field],
                        after=after[field],
                    )
                )

        if field_changes:
            changed_scenes.append(
                SceneChange(
                    scene_number=scene_number,
                    change_type="MODIFIED",
                    changes=field_changes,
                )
            )

    return {
        "status": "CHANGES" if changed_scenes else "NO_CHANGES",
        "message": (
            f"{len(changed_scenes)} changed scene(s) detected."
            if changed_scenes
            else "No changes detected between the latest two revisions."
        ),
        "previous_version": previous_version,
        "current_version": current_version,
        "changed_scenes": [
    _build_changed_scene_result(
        client,
        production_id,
        item,
    )
    for item in changed_scenes
],
    }