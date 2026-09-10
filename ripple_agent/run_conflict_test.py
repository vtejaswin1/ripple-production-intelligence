from clickhouse_repository import (
    get_scene_42_context,
    replace_scene_impacts,
)
from conflict_engine import detect_impacts


def main():
    context = get_scene_42_context()

    print("\nSCENE CONTEXT")
    print("-" * 50)

    for key, value in context.items():
        print(f"{key}: {value}")

    impacts = detect_impacts(context)
    replace_scene_impacts(
        production_id=1,
        version_id=2,
        scene_id=context["scene_id"],
        impacts=impacts,
    )

    print("\nSaved impacts to ripple.impact_analysis")

    print("\nDETECTED IMPACTS")
    print("-" * 50)

    if not impacts:
        print("No conflicts detected.")
        return

    for index, impact in enumerate(impacts, start=1):
        print(f"\nImpact {index}")
        print(f"Type: {impact.impact_type}")
        print(f"Severity: {impact.severity}")
        print(f"Description: {impact.description}")
        print(f"Evidence: {impact.evidence}")
        print(
            f"Entity: {impact.impacted_entity_type} "
            f"{impact.impacted_entity_id}"
        )


if __name__ == "__main__":
    main()