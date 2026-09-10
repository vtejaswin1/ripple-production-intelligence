import json
import os
from datetime import date, datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from ripple_agent.firebase_auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel

from .production_manifest import ProductionManifest
from .production_manifest_importer import import_production_manifest

from .clickhouse_repository import (
    get_client,
    get_scene_42_context,
    get_scene_42_recovery_candidates,
    replace_scene_impacts,
    replace_scene_recovery_plan,
)
from .conflict_engine import detect_impacts
from .recovery_engine import choose_recovery_plan
from .revision_engine import compare_latest_revisions


app = FastAPI(
    title="RIPPLE API",
    description="Production Change Intelligence backend",
    version="0.2.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


gemini_client = genai.Client(
    vertexai=True,
    project=os.getenv(
        "GOOGLE_CLOUD_PROJECT",
        "ripple-production-intelligence",
    ),
    location=os.getenv(
        "GOOGLE_CLOUD_LOCATION",
        "global",
    ),
)


# ============================================================
# Request models
# ============================================================

class FollowUpRequest(BaseModel):
    question: str


class NewProductionRequest(BaseModel):
    production_name: str
    start_date: date
    end_date: date

@app.post("/api/productions/{production_id}/manifest")
def upload_production_manifest(
    production_id: int,
    manifest: ProductionManifest,
    current_user=Depends(get_current_user),
):
    client = get_client()

    production_row = client.query(
        """
        SELECT
            production_name,
            owner_uid
        FROM ripple.productions
        WHERE production_id = %(production_id)s
        LIMIT 1
        """,
        parameters={
            "production_id": production_id,
        },
    ).first_row

    if production_row is None:
        raise HTTPException(
            status_code=404,
            detail="Production not found.",
        )

    if production_row[1] != current_user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this production.",
        )

    try:
        result = import_production_manifest(
            client,
            production_id,
            manifest,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "status": "success",
        "production_id": production_id,
        "production_name": production_row[0],
        "import": result,
    }

# ============================================================
# Health check
# ============================================================

@app.get("/")
def root():
    return {
        "name": "RIPPLE",
        "status": "running",
    }


# ============================================================
# Existing Scene 42 demo analysis
#
# Keep this for the hackathon demo.
# The new generic upload/revision pipeline exists separately.
# ============================================================

@app.get("/api/scenes/42/analyze")
def analyze_scene_42():
    context = get_scene_42_context()

    impacts = detect_impacts(context)

    replace_scene_impacts(
        production_id=1,
        version_id=2,
        scene_id=42,
        impacts=impacts,
    )

    candidates = get_scene_42_recovery_candidates()

    plan = choose_recovery_plan(
        candidates=candidates,
        scene_duration_minutes=120,
        original_start=datetime.fromisoformat(
            context["revised_start_time"]
        ),
    )

    replace_scene_recovery_plan(
        production_id=1,
        version_id=2,
        scene_id=42,
        analysis_id=2004201,
        plan=plan,
    )

    return {
        "scene": {
            "scene_id": context["scene_id"],
            "title": context["scene_title"],
        },
        "revision": {
            "location_type": context[
                "revised_location_type"
            ],
            "time_of_day": context[
                "revised_time_of_day"
            ],
            "start_time": context[
                "revised_start_time"
            ],
        },
        "impacts": [
            {
                "type": impact.impact_type,
                "severity": impact.severity,
                "description": impact.description,
                "evidence": impact.evidence,
            }
            for impact in impacts
        ],
        "recovery": (
            None
            if plan is None
            else {
                "location_id": plan.location_id,
                "location_name": plan.location_name,
                "start_time": plan.start_time.isoformat(),
                "end_time": plan.end_time.isoformat(),
                "delay_minutes": plan.delay_minutes,
                "estimated_cost_change":
                    plan.estimated_cost_change,
                "disruption_score":
                    plan.disruption_score,
                "risk_level": plan.risk_level,
            }
        ),
    }


# ============================================================
# Existing fast Gemini follow-up for Scene 42
# ============================================================

@app.post("/api/scenes/42/ask")
def ask_scene_42(request: FollowUpRequest):
    client = get_client()

    query = """
    SELECT
        production_name,
        scene_id,
        scene_title,
        version_number,
        version_name,
        changes,
        impacts,
        plan_id,
        plan_name,
        plan_rank,
        plan_cost_change,
        plan_delay_minutes,
        disruption_score,
        risk_level,
        recommendation_summary,
        actions
    FROM ripple.scene_intelligence_v
    WHERE scene_id = 42
    """

    row = client.query(query).first_row

    if row is None:
        return {
            "question": request.question,
            "answer": (
                "No production intelligence was found "
                "for Scene 42."
            ),
        }

    scene_context = {
        "production_name": row[0],
        "scene_id": row[1],
        "scene_title": row[2],
        "version_number": row[3],
        "version_name": row[4],
        "changes": str(row[5]),
        "impacts": str(row[6]),
        "plan_id": row[7],
        "plan_name": row[8],
        "plan_rank": row[9],
        "plan_cost_change": str(row[10]),
        "plan_delay_minutes": row[11],
        "disruption_score": row[12],
        "risk_level": row[13],
        "recommendation_summary": row[14],
        "actions": str(row[15]),
    }

    prompt = f"""
You are RIPPLE, a film production change intelligence assistant.

Answer the user's follow-up question using ONLY the verified
production data supplied below.

Do not invent production facts.
Do not invent alternative schedules or recovery plans.

If the supplied evidence does not answer the question,
say that clearly.

Keep the answer concise and production-oriented.
Use clean Markdown when helpful.

VERIFIED SCENE 42 DATA:

{scene_context}

USER QUESTION:

{request.question}
"""

    response = gemini_client.models.generate_content(
        model="gemini-3.7-flash",
        contents=prompt,
    )

    answer = (
        response.text
        or "No response was generated."
    )

    return {
        "question": request.question,
        "answer": answer,
    }


# ============================================================
# Create a new production
#
# Starting fresh means creating a new production.
# It DOES NOT delete old productions or revisions.
# ============================================================

@app.post("/api/productions")
def create_production(
    request: NewProductionRequest,
    current_user=Depends(get_current_user),
):
    client = get_client()

    production_name = request.production_name.strip()

    if not production_name:
        return {
            "status": "error",
            "message": "Production name is required.",
        }

    if request.end_date < request.start_date:
        return {
            "status": "error",
            "message": (
                "End date cannot be before start date."
            ),
        }

    result = client.query(
        """
        SELECT max(production_id)
        FROM ripple.productions
        """
    ).first_row

    current_max = result[0]

    production_id = (
        1
        if current_max is None
        else int(current_max) + 1
    )


    client.insert(
        "ripple.productions",
        [
            [
                production_id,
                production_name,
                "ACTIVE",
                request.start_date,
                request.end_date,
                current_user["uid"],
            ]
        ],
        column_names=[
            "production_id",
            "production_name",
            "status",
            "start_date",
            "end_date",
            "owner_uid",
        ],
    )

    return {
        "status": "success",
        "production": {
            "production_id": production_id,
            "production_name": production_name,
            "status": "ACTIVE",
            "start_date": str(
                request.start_date
            ),
            "end_date": str(
                request.end_date
            ),
        },
    }


# ============================================================
# Upload screenplay revision
#
# production_id comes from the selected/current production.
# Every production gets its own:
#
# Revision 1
# Revision 2
# Revision 3
#
# No previous revision is deleted.
# ============================================================

@app.post("/api/scripts/upload")
async def upload_script(
    production_id: int,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    client = get_client()

    # --------------------------------------------------------
    # Confirm production exists BEFORE calling Gemini
    # --------------------------------------------------------

    production_row = client.query(
    """
    SELECT
        production_name,
        owner_uid
    FROM ripple.productions
    WHERE production_id = %(production_id)s
    LIMIT 1
    """,
    parameters={
        "production_id": production_id,
    },
).first_row

    if production_row is None:
        return {
            "status": "error",
            "message": (
                f"Production {production_id} "
                "was not found."
            ),
        }
    if production_row[1] != current_user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this production.",
    )

    production_name = production_row[0]

    # --------------------------------------------------------
    # Read uploaded file
    # --------------------------------------------------------

    content = await file.read()

    try:
        script_text = content.decode("utf-8")
    except UnicodeDecodeError:
        return {
            "status": "error",
            "message": (
                "For the first version, upload a "
                "plain text .txt screenplay file."
            ),
        }

    if not script_text.strip():
        return {
            "status": "error",
            "message": "The uploaded script is empty.",
        }

    # --------------------------------------------------------
    # Extract structured scenes with Gemini
    # --------------------------------------------------------

    prompt = f"""
You are RIPPLE's screenplay extraction engine.

Extract the screenplay into structured scene data.

Return ONLY valid JSON.

For each scene return:

- scene_number
- heading
- location_name
- location_type: INTERIOR or EXTERIOR
- time_of_day: DAY, NIGHT, EVENING, MORNING, or UNKNOWN
- characters: list of character names

Do not invent scenes.
Do not invent characters.
Preserve the screenplay's actual scene numbers.

SCREENPLAY:

{script_text}
"""

    response = gemini_client.models.generate_content(
        model="gemini-3.7-flash",
        contents=prompt,
        config={
            "response_mime_type":
                "application/json",
        },
    )

    if not response.text:
        return {
            "status": "error",
            "message": (
                "Gemini returned no screenplay data."
            ),
        }

    try:
        extracted = json.loads(response.text)
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": (
                "Gemini returned invalid JSON while "
                "extracting the screenplay."
            ),
        }

    # Gemini may return either:
    # {"scenes": [...]} OR directly [...]
    if isinstance(extracted, dict):
        scenes = extracted.get("scenes", [])
    else:
        scenes = extracted

    if not scenes:
        return {
            "status": "error",
            "message": (
                "Gemini did not extract any scenes "
                "from the screenplay."
            ),
        }

    # --------------------------------------------------------
    # Determine next revision FOR THIS production only
    # --------------------------------------------------------

    version_query = """
    SELECT
        max(version_id)
    FROM ripple.uploaded_script_scenes
    WHERE production_id = %(production_id)s
    """

    current_max_version = client.query(
        version_query,
        parameters={
            "production_id": production_id,
        },
    ).first_row[0]

    if current_max_version is None:
        version_id = 1
    else:
        version_id = (
            int(current_max_version) + 1
        )

    version_name = f"Revision {version_id}"

    # --------------------------------------------------------
    # Build ClickHouse rows
    # --------------------------------------------------------

    rows = []

    for scene in scenes:
        scene_number = scene.get(
            "scene_number"
        )

        if scene_number is None:
            continue

        rows.append(
            [
                production_id,
                production_name,
                version_id,
                version_name,
                file.filename or "uploaded_script.txt",
                int(scene_number),
                scene.get("heading", ""),
                scene.get("location_name", ""),
                scene.get(
                    "location_type",
                    "UNKNOWN",
                ),
                scene.get(
                    "time_of_day",
                    "UNKNOWN",
                ),
                scene.get(
                    "characters",
                    [],
                ),
            ]
        )

    if not rows:
        return {
            "status": "error",
            "message": (
                "No valid scene rows could be created "
                "from this screenplay."
            ),
        }

    # --------------------------------------------------------
    # Insert revision
    #
    # Old revisions remain in ClickHouse.
    # --------------------------------------------------------

    client.insert(
        "ripple.uploaded_script_scenes",
        rows,
        column_names=[
            "production_id",
            "production_name",
            "version_id",
            "version_name",
            "filename",
            "scene_number",
            "heading",
            "location_name",
            "location_type",
            "time_of_day",
            "characters",
        ],
    )

    return {
        "status": "success",
        "production_id": production_id,
        "production_name": production_name,
        "filename": file.filename,
        "version_id": version_id,
        "version_name": version_name,
        "scene_count": len(rows),
        "scenes": scenes,
    }


# ============================================================
# Analyze latest two revisions for selected production
#
# Behavior:
#
# no uploads  -> NO_UPLOAD
# 1 revision  -> BASELINE
# same script -> NO_CHANGES
# differences -> CHANGES + dependencies + conflicts
# ============================================================

@app.get("/api/scripts/analyze")
def analyze_latest_script(
    production_id: int,
    current_user=Depends(get_current_user),
):
    client = get_client()

    production_row = client.query(
    """
    SELECT
        production_name,
        owner_uid
    FROM ripple.productions
    WHERE production_id = %(production_id)s
    LIMIT 1
    """,
    parameters={
        "production_id": production_id,
    },
).first_row

    if production_row is None:
        return {
            "status": "error",
            "message": (
                f"Production {production_id} "
                "was not found."
            ),
        }
    if production_row[1] != current_user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this production.",
        )

    result = compare_latest_revisions(
        client,
        production_id=production_id,
    )

    result["production_id"] = production_id
    result["production_name"] = production_row[0]

    return result


@app.get("/api/productions")
def list_productions(
    current_user=Depends(get_current_user),
):
    client = get_client()

    rows = client.query(
        """
        SELECT
            production_id,
            production_name,
            status,
            start_date,
            end_date
        FROM ripple.productions
        WHERE owner_uid = %(owner_uid)s
        ORDER BY production_id DESC
        """,
        parameters={
            "owner_uid": current_user["uid"],
        },
    ).result_rows

    productions = []

    for (
        production_id,
        production_name,
        status,
        start_date,
        end_date,
    ) in rows:
        productions.append(
            {
                "production_id": int(production_id),
                "production_name": production_name,
                "status": status,
                "start_date": str(start_date),
                "end_date": str(end_date),
            }
        )

    return {
        "status": "success",
        "productions": productions,
    }

@app.get("/api/productions/{production_id}/revisions")
def list_production_revisions(
    production_id: int,
    current_user=Depends(get_current_user),
):
    client = get_client()

    production_owner = client.query(
        """
        SELECT owner_uid
        FROM ripple.productions
        WHERE production_id = %(production_id)s
        LIMIT 1
        """,
        parameters={
            "production_id": production_id,
        },
    ).first_row

    if production_owner is None:
        raise HTTPException(
            status_code=404,
            detail="Production not found.",
        )

    if production_owner[0] != current_user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this production.",
        )

    rows = client.query(
        """
        SELECT
            version_id,
            any(version_name) AS version_name,
            any(filename) AS filename,
            count() AS scene_count,
            max(uploaded_at) AS uploaded_at
        FROM ripple.uploaded_script_scenes
        WHERE production_id = %(production_id)s
        GROUP BY version_id
        ORDER BY version_id DESC
        """,
        parameters={
            "production_id": production_id,
        },
    ).result_rows

    revisions = []

    for (
        version_id,
        version_name,
        filename,
        scene_count,
        uploaded_at,
    ) in rows:
        revisions.append(
            {
                "version_id": int(version_id),
                "version_name": version_name,
                "filename": filename,
                "scene_count": int(scene_count),
                "uploaded_at": str(uploaded_at),
            }
        )

    return {
        "status": "success",
        "production_id": production_id,
        "revisions": revisions,
    }

@app.delete(
    "/api/productions/{production_id}/revisions/{version_id}"
)
def delete_production_revision(
    production_id: int,
    version_id: int,
    current_user=Depends(get_current_user),
):
    client = get_client()

    production_owner = client.query(
        """
        SELECT owner_uid
        FROM ripple.productions
        WHERE production_id = %(production_id)s
        LIMIT 1
        """,
        parameters={
            "production_id": production_id,
        },
    ).first_row

    if production_owner is None:
        raise HTTPException(
            status_code=404,
            detail="Production not found.",
        )

    if production_owner[0] != current_user["uid"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this production.",
        )

    existing = client.query(
        """
        SELECT count()
        FROM ripple.uploaded_script_scenes
        WHERE production_id = %(production_id)s
          AND version_id = %(version_id)s
        """,
        parameters={
            "production_id": production_id,
            "version_id": version_id,
        },
    ).result_rows[0][0]

    if existing == 0:
        raise HTTPException(
            status_code=404,
            detail="Revision not found.",
        )

    client.command(
        """
        ALTER TABLE ripple.uploaded_script_scenes
        DELETE WHERE
            production_id = %(production_id)s
            AND version_id = %(version_id)s
        """,
        parameters={
            "production_id": production_id,
            "version_id": version_id,
        },
    )

    return {
        "status": "success",
        "message": "Revision deleted.",
        "production_id": production_id,
        "version_id": version_id,
    }

@app.get("/api/auth/me")
def auth_me(
    current_user=Depends(get_current_user),
):
    return {
        "status": "success",
        "user": current_user,
    }