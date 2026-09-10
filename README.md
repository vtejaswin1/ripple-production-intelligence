[RIPPLE_README.md](https://github.com/user-attachments/files/32032679/RIPPLE_README.md)
# RIPPLE – Production Change Intelligence

> **Every change in a film production creates a ripple. RIPPLE finds the ripple before it becomes expensive.**

RIPPLE is an AI-powered production change intelligence platform built for the **Google Cloud Agentic Cinema Hackathon – ClickHouse Track**. It connects screenplay revisions with production logistics so a team can see what changed, what downstream resources are affected, what conflicts are created, and what recovery options are feasible.

## What RIPPLE does

A user signs up, creates or selects a production, loads production logistics, uploads a baseline screenplay, then uploads revised screenplay versions. Gemini extracts structured scene information, RIPPLE compares revisions, ClickHouse stores and queries production intelligence, the dependency engine traces affected resources, the conflict engine checks feasibility, and the recovery engine ranks alternatives based on timing, availability, cost, and risk.

RIPPLE is designed to answer one practical question:

> **If the script changes today, what else breaks, and what is the best way to recover before that change becomes expensive?**

## Core features

- Firebase Authentication for sign-up, login, logout, password change, and protected requests.
- User-owned productions so one user's production data is isolated from another's.
- Generic production logistics import from JSON.
- Baseline screenplay upload and revision history.
- Gemini-based screenplay understanding and scene extraction.
- Revision comparison across scene number, location, INT/EXT, time of day, and characters.
- Production dependency tracing.
- Conflict detection using structured production data.
- Ranked recovery options using location type, day/night support, actor availability, location availability, duration, delay, cost, and risk.
- ClickHouse Cloud as the production intelligence layer.
- Official `mcp-clickhouse` integration through Google ADK.

## Architecture

```text
User
  ↓
React + Vite
  ↓
Firebase Authentication
  ↓
FastAPI Backend
  ↓
Google Agent Development Kit (ADK)
  ↓
Gemini
  ↓
Official mcp-clickhouse MCP Server
  ↓
ClickHouse Cloud
  ↓
Changes → Dependencies → Conflicts → Recovery Options
```

## Tech stack

### Google Cloud / AI
- Gemini
- Google Agent Development Kit (`google-adk`)
- Google Cloud Agent Platform
- Google Cloud IAM
- Application Default Credentials

### Data / partner track
- ClickHouse Cloud
- Official `mcp-clickhouse`
- `clickhouse-connect`

### Backend
- Python 3.10
- FastAPI
- Uvicorn
- Pydantic
- `python-dotenv`
- `firebase-admin`

### Frontend
- React
- Vite
- JavaScript
- React Router
- Firebase Web SDK

### Development
- Git
- GitHub
- Windows CMD
- VS Code

## Project structure

```text
ripple-production-intelligence/
│
├── .env
├── .gitignore
├── LICENSE
├── README.md
│
├── ripple_agent/
│   ├── __init__.py
│   ├── agent.py
│   ├── api.py
│   ├── firebase_auth.py
│   ├── revision_engine.py
│   ├── dependency_engine.py
│   ├── dynamic_conflict_engine.py
│   ├── dynamic_recovery_engine.py
│   ├── production_manifest.py
│   └── production_manifest_importer.py
│
└── ripple-web/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── App.css
        ├── firebase.js
        ├── main.jsx
        ├── components/
        │   └── ProtectedRoute.jsx
        └── pages/
            ├── LoginPage.jsx
            ├── SignupPage.jsx
            └── ProfilePage.jsx
```

## Prerequisites

Install:

- Git
- Python 3.10+
- Node.js and npm
- Google Cloud CLI
- Google Cloud account/project
- ClickHouse Cloud service
- Firebase project

Versions used during development included:

```text
Python 3.10.11
Git 2.37.1.windows.1
google-adk 2.7.1
mcp 1.29.0
mcp-clickhouse 0.4.1
```

## Google Cloud setup

The development project used:

```text
Project name: Ripple Production Intelligence
Project ID: ripple-production-intelligence
```

Sign in to Google Cloud CLI:

```bat
gcloud auth login
```

Set the project:

```bat
gcloud config set project ripple-production-intelligence
```

Verify:

```bat
gcloud config get-value project
```

Create Application Default Credentials:

```bat
gcloud auth application-default login
```

Set the ADC quota project:

```bat
gcloud auth application-default set-quota-project ripple-production-intelligence
```

Check the signed-in accounts:

```bat
gcloud auth list
```

List enabled APIs:

```bat
gcloud services list --enabled
```

## ClickHouse Cloud setup

The development ClickHouse configuration used:

```text
Service: ripple-production-intelligence
Cloud: Google Cloud
Region: us-east1
Database: ripple
```

Store ClickHouse credentials only in `.env`.

Example:

```env
CLICKHOUSE_HOST=your-clickhouse-host
CLICKHOUSE_PORT=8443
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your-clickhouse-password
CLICKHOUSE_DATABASE=ripple
```

**Never commit your ClickHouse password.**

## Firebase setup

Firebase Authentication is connected to the Google Cloud project.

Enable:

```text
Firebase Console
→ Authentication
→ Sign-in method
→ Email/Password
→ Enable
```

Frontend Firebase configuration lives in:

```text
ripple-web/src/firebase.js
```

Backend Firebase token verification lives in:

```text
ripple_agent/firebase_auth.py
```

The frontend sends:

```http
Authorization: Bearer <FIREBASE_ID_TOKEN>
```

The backend verifies the token and uses the authenticated Firebase UID for production ownership.

## Clone / open the project

Clone:

```bat
cd /d C:\Users\Sai
git clone https://github.com/vtejaswin1/ripple-production-intelligence.git
cd /d C:\Users\Sai\ripple-production-intelligence
```

If already cloned:

```bat
cd /d C:\Users\Sai\ripple-production-intelligence
```

Check Git status:

```bat
git status
```

## Python environment setup

Create the virtual environment:

```bat
cd /d C:\Users\Sai\ripple-production-intelligence
py -3.10 -m venv .venv
```

If the Python launcher is unavailable:

```bat
python -m venv .venv
```

Activate it:

```bat
.venv\Scripts\activate
```

Upgrade pip:

```bat
python -m pip install --upgrade pip
```

Install the main backend packages:

```bat
pip install fastapi uvicorn pydantic python-dotenv clickhouse-connect firebase-admin google-adk mcp mcp-clickhouse
```

Versions used during development:

```bat
pip install google-adk==2.7.1
pip install mcp==1.29.0
pip install mcp-clickhouse==0.4.1
```

If the repo contains `requirements.txt`, use:

```bat
pip install -r requirements.txt
```

Verify Python:

```bat
.venv\Scripts\python.exe --version
```

## Frontend setup

Move to the frontend:

```bat
cd /d C:\Users\Sai\ripple-production-intelligence\ripple-web
```

Install packages:

```bat
npm install
```

Packages used include Firebase and React Router. If needed individually:

```bat
npm install firebase react-router-dom
```

Build check:

```bat
npm run build
```

Run Vite:

```bat
npm run dev
```

Typical local frontend URL:

```text
http://localhost:5173
```

If port 5173 is occupied, Vite may use 5174. The backend CORS configuration must allow the frontend port being used.

## Environment variables

Create:

```text
C:\Users\Sai\ripple-production-intelligence\.env
```

Example:

```env
GOOGLE_CLOUD_PROJECT=ripple-production-intelligence
GOOGLE_CLOUD_LOCATION=your-google-cloud-location

CLICKHOUSE_HOST=your-clickhouse-host
CLICKHOUSE_PORT=8443
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your-clickhouse-password
CLICKHOUSE_DATABASE=ripple
```

Keep `.env` in `.gitignore`.

Never commit:

- ClickHouse passwords
- Firebase ID tokens
- service-account private keys
- `.env`
- private API credentials

## The three CMD windows we used every day

### CMD 1 — Backend

```bat
cd /d C:\Users\Sai\ripple-production-intelligence
.venv\Scripts\python.exe -m uvicorn ripple_agent.api:app --reload
```

Leave this CMD window running.

### CMD 2 — Frontend

```bat
cd /d C:\Users\Sai\ripple-production-intelligence\ripple-web
npm run dev
```

Leave this CMD window running.

### CMD 3 — Testing / compile / Git

```bat
cd /d C:\Users\Sai\ripple-production-intelligence
```

This third window was used for Python compilation checks, Git, package checks, and one-off tests.

## Useful compile checks

Compile the API:

```bat
cd /d C:\Users\Sai\ripple-production-intelligence
.venv\Scripts\python.exe -m py_compile ripple_agent\api.py
```

Compile production manifest model:

```bat
.venv\Scripts\python.exe -m py_compile ripple_agent\production_manifest.py
```

Compile production manifest importer:

```bat
.venv\Scripts\python.exe -m py_compile ripple_agent\production_manifest_importer.py
```

Compile several files:

```bat
.venv\Scripts\python.exe -m py_compile ripple_agent\production_manifest.py
.venv\Scripts\python.exe -m py_compile ripple_agent\production_manifest_importer.py
.venv\Scripts\python.exe -m py_compile ripple_agent\api.py
```

No output normally means the syntax check passed.

Check installed versions:

```bat
.venv\Scripts\python.exe -m pip show google-adk
.venv\Scripts\python.exe -m pip show mcp
.venv\Scripts\python.exe -m pip show mcp-clickhouse
```

List installed Python packages:

```bat
.venv\Scripts\python.exe -m pip list
```

## FastAPI local URLs

Backend:

```text
http://127.0.0.1:8000
```

Interactive API docs:

```text
http://127.0.0.1:8000/docs
```

## Production manifest import

Files:

```text
ripple_agent/production_manifest.py
ripple_agent/production_manifest_importer.py
```

Authenticated endpoint:

```text
POST /api/productions/{production_id}/manifest
```

The generic manifest can contain actors, actor availability, locations, location availability, constraints, scheduled scenes, cast links, and scene-to-location relationships.

Example:

```json
{
  "actors": [
    {
      "actor_name": "Ethan Cole",
      "character_name": "ALEX",
      "availability": [
        {
          "available_date": "2026-09-10",
          "available_from": "2026-09-10T08:00:00",
          "available_to": "2026-09-10T18:00:00"
        }
      ]
    }
  ],
  "locations": [
    {
      "location_name": "Downtown Rooftop",
      "location_type": "EXTERIOR",
      "city": "Los Angeles",
      "supports_day_shoot": true,
      "supports_night_shoot": true,
      "base_cost_per_hour": 850,
      "availability": [],
      "constraints": []
    }
  ],
  "scenes": [
    {
      "scene_number": 42,
      "title": "Final Confrontation",
      "scheduled_date": "2026-09-10",
      "scheduled_start_time": "2026-09-10T15:00:00",
      "estimated_duration_minutes": 120,
      "estimated_cost": 8000,
      "location_name": "Downtown Rooftop",
      "time_of_day": "NIGHT",
      "characters": ["ALEX"]
    }
  ]
}
```

The importer writes production-specific rows to ClickHouse for:

- actors
- actor availability
- locations
- location availability
- location constraints
- scenes
- scene cast links
- scene-to-location dependencies

## Screenplay upload flow

1. Log in.
2. Create or select a production.
3. Upload the first screenplay as the baseline.
4. Upload a second screenplay as a revision.
5. Click **Analyze RIPPLE**.
6. Review changed scenes.
7. Review dependencies.
8. Review conflicts.
9. Review recovery options.

## Demo screenplay example

Baseline:

```text
SCENE 42
INT. GRAND HOTEL SUITE - DAY

Characters: DANIEL, ALEX, MAYA

Daniel confronts Alex and Maya inside the hotel suite.
```

Revision:

```text
SCENE 42
EXT. SKYLINE ROOFTOP - NIGHT

Characters: DANIEL, ALEX, MAYA, JORDAN

The confrontation is moved to the skyline rooftop at night,
and Jordan joins the scene.
```

RIPPLE should identify changes such as:

```text
Grand Hotel Suite → Skyline Rooftop
INTERIOR → EXTERIOR
DAY → NIGHT
JORDAN added
```

## ClickHouse schema used by RIPPLE

Core tables:

```text
productions
scenes
actors
actor_availability
scene_cast
locations
location_constraints
script_versions
script_changes
scene_requirements
production_dependencies
impact_analysis
recovery_plans
recovery_plan_actions
shooting_windows
location_availability
uploaded_script_scenes
```

### productions

```text
production_id UInt32
production_name String
status String
start_date Date
end_date Date
owner_uid String
```

### scenes

```text
scene_id UInt32
production_id UInt32
scene_number String
title String
location_type String
time_of_day String
scheduled_date Date
scheduled_start_time DateTime
estimated_duration_minutes UInt32
estimated_cost Decimal(12,2)
```

### actors

```text
actor_id UInt32
production_id UInt32
actor_name String
character_name String
```

### actor_availability

```text
actor_id UInt32
available_date Date
available_from DateTime
available_to DateTime
```

### locations

```text
location_id UInt32
production_id UInt32
location_name String
location_type String
city String
available_from DateTime
available_to DateTime
supports_day_shoot Bool
supports_night_shoot Bool
base_cost_per_hour Decimal(12,2)
```

### location_constraints

```text
location_id UInt32
constraint_type String
constraint_description String
effective_date Date
```

### scene_cast

```text
scene_id UInt32
actor_id UInt32
role_type String
```

### location_availability

```text
location_id UInt32
available_date Date
available_from DateTime
available_to DateTime
availability_status String
```

### production_dependencies

```text
dependency_id UInt32
production_id UInt32
source_entity_type String
source_entity_id UInt32
target_entity_type String
target_entity_id UInt32
dependency_type String
dependency_strength String
notes String
```

### uploaded_script_scenes

```text
production_id UInt32
production_name String
version_id UInt32
version_name String
filename String
scene_number UInt32
heading String
location_name String
location_type String
time_of_day String
characters Array(String)
uploaded_at DateTime
```

The development table used:

```sql
ENGINE = MergeTree
ORDER BY (production_id, version_id, scene_number)
```

## Revision engine

File:

```text
ripple_agent/revision_engine.py
```

Main concept:

```python
compare_latest_revisions(client, production_id)
```

Revision states include:

```text
NO_UPLOAD
BASELINE
NO_CHANGES
CHANGES
```

When changes are found, RIPPLE resolves dependencies, evaluates conflicts, and generates recovery options for the changed scene.

## Dependency engine

File:

```text
ripple_agent/dependency_engine.py
```

Main concept:

```python
resolve_scene_dependencies(client, production_id, scene_number)
```

The dependency engine resolves registered cast and scene-to-location relationships for the selected production.

Important implementation detail: the `scenes` table does **not** contain `location_id`. The scene/location relationship is modeled through `production_dependencies` using a `SCENE → LOCATION` relationship.

## Conflict engine

File:

```text
ripple_agent/dynamic_conflict_engine.py
```

Main concept:

```python
evaluate_scene_changes(
    client,
    production_id,
    scene_number,
    changes,
    dependencies
)
```

The engine can flag problems such as:

- location type mismatch
- day/night mismatch
- a location not supporting night shoots
- a new screenplay character not being registered for the production
- revised requirements conflicting with existing production setup

Character resolution uses `actors.character_name`, because screenplay files contain character names rather than actor names.

## Recovery engine

File:

```text
ripple_agent/dynamic_recovery_engine.py
```

Main concept:

```python
find_recovery_options(
    client,
    production_id,
    scene_number,
    changes,
    max_options=3
)
```

The engine:

1. Loads the original scene schedule.
2. Reads revised scene requirements.
3. Resolves required characters.
4. Finds candidate locations for the same production.
5. Checks location type.
6. Checks day/night capability.
7. Reads location availability.
8. Intersects each location window with actor availability.
9. Ensures enough continuous time exists for the scene duration.
10. Proposes a start and end time.
11. Calculates delay from the original schedule.
12. Estimates location cost.
13. Assigns a risk level.
14. Sorts and returns the best options.

Recovery option fields include:

```text
location_id
location_name
start_time
end_time
duration_minutes
delay_minutes
estimated_location_cost
risk_level
reason
```

## MCP + Google ADK

Main file:

```text
ripple_agent/agent.py
```

RIPPLE integrates the official ClickHouse MCP server:

```text
mcp-clickhouse
```

The local MCP workflow was tested through stdio.

Runtime chain:

```text
Gemini
  ↓
Google ADK
  ↓
mcp-clickhouse
  ↓
ClickHouse Cloud
```

This is important for the ClickHouse hackathon track: the MCP server is used in runtime code, not only mentioned in documentation.

## Authentication and production ownership

RIPPLE uses Firebase Authentication and protects production APIs using verified Firebase ID tokens.

Protected operations include:

- create production
- list productions
- view revision history
- upload screenplay revisions
- delete revisions
- analyze a production
- import a production manifest

Each production contains:

```text
owner_uid
```

The backend compares that value with the authenticated Firebase UID before allowing production-specific actions.

## Development validation we used

### Backend syntax check

```bat
.venv\Scripts\python.exe -m py_compile ripple_agent\api.py
```

### Manifest model syntax check

```bat
.venv\Scripts\python.exe -m py_compile ripple_agent\production_manifest.py
```

### Manifest importer syntax check

```bat
.venv\Scripts\python.exe -m py_compile ripple_agent\production_manifest_importer.py
```

### Frontend production build check

```bat
cd /d C:\Users\Sai\ripple-production-intelligence\ripple-web
npm run build
```

### Git status

```bat
cd /d C:\Users\Sai\ripple-production-intelligence
git status
```

### Git remote

```bat
git remote -v
```

## GitHub workflow

Repository:

```text
https://github.com/vtejaswin1/ripple-production-intelligence
```

Typical workflow:

```bat
cd /d C:\Users\Sai\ripple-production-intelligence
git status
git add .
git commit -m "Update RIPPLE production intelligence workflow"
git push
```

Before pushing, always verify that `.env` is not staged.

The repository includes an **Apache-2.0** license.

## Demo scenario used during development

A demo production included scenes 10, 20, 30, 40, and 42 with actors, locations, availability, and constraints.

One example:

```text
Original Scene 42
INT. GRAND HOTEL SUITE - DAY
Characters: DANIEL, ALEX, MAYA
```

Revised:

```text
Scene 42
EXT. SKYLINE ROOFTOP - NIGHT
Characters: DANIEL, ALEX, MAYA, JORDAN
```

The demo exercised:

- screenplay change detection
- dependency resolution
- location/day-night conflicts
- cast changes
- recovery planning

A feasible recovery example in the development dataset used **Riverside Rooftop**, with a two-hour window and estimated location cost calculated from the location's hourly rate.

## Challenges we faced

### Connecting screenplay text to structured production data

The screenplay tells us what changed, but not whether production can actually execute that change. RIPPLE had to bridge unstructured screenplay information with structured schedules, actors, locations, availability, and constraints.

### Production isolation

Early development used a single demo production. We made the system production-aware by passing `production_id` through the engines and filtering ClickHouse queries by production.

### User ownership

We added Firebase authentication and `owner_uid` so users only access their own productions.

### Scene/location mapping

The scene table has no direct `location_id`, so the correct relationship is resolved through `production_dependencies`.

### Character-to-actor matching

Screenplays contain character names, so the system matches against `actors.character_name`, not `actor_name`.

### Recovery feasibility

A valid recovery option has to satisfy more than a location-name match. It must fit location type, day/night support, availability, required cast availability, and scene duration.

## Accomplishments we are proud of

RIPPLE goes beyond simple screenplay comparison. It can:

- use Gemini to understand screenplay scenes
- detect scene-level revision changes
- trace production dependencies
- detect operational conflicts
- generate ranked recovery alternatives
- calculate delay and estimated location cost
- assign recovery risk levels
- isolate productions by authenticated user
- import production logistics generically
- use ClickHouse Cloud as an operational intelligence layer
- integrate the official `mcp-clickhouse` MCP server with Google ADK

The biggest accomplishment is that RIPPLE does not stop at **“this scene changed.”** It tries to answer **“what does this change break, and what can we do next?”**

## What we learned

The main learning was that screenplay analysis alone is not enough for real production planning. The value comes from combining AI understanding with structured operational data.

Gemini helps RIPPLE understand the revision. ClickHouse provides the production context. The dependency, conflict, and recovery engines turn those two inputs into a decision-support workflow.

## Future improvements

- PDF screenplay ingestion
- Final Draft / FDX ingestion
- CSV and Google Sheets production-data imports
- production-data editing UI
- crew dependencies
- equipment dependencies
- permits
- travel constraints
- weather constraints
- richer location-constraint enforcement
- shooting-window enforcement
- advanced cost optimization
- multi-scene schedule optimization
- persist dynamic recovery plans
- multi-agent recovery planning
- human approval workflows
- notifications
- generic production-aware conversational Ask RIPPLE

## Hackathon compliance notes

RIPPLE was built for the **Google Cloud Agentic Cinema Hackathon – ClickHouse Track**.

The project uses:

```text
Gemini
Google Cloud
Google Agent Development Kit
ClickHouse Cloud
Official mcp-clickhouse MCP server
```

The code repository is intended to be public and open source and includes an Apache-2.0 license.

No non-Google AI model is required by the RIPPLE runtime.

## Quick start

Once Google Cloud, Firebase, ClickHouse, and `.env` are configured:

### CMD 1

```bat
cd /d C:\Users\Sai\ripple-production-intelligence
.venv\Scripts\python.exe -m uvicorn ripple_agent.api:app --reload
```

### CMD 2

```bat
cd /d C:\Users\Sai\ripple-production-intelligence\ripple-web
npm run dev
```

### CMD 3

```bat
cd /d C:\Users\Sai\ripple-production-intelligence
```

Then open:

```text
http://localhost:5173
```

Use the app in this order:

```text
Sign up / log in
→ Create or select production
→ Import production logistics if needed
→ Upload baseline screenplay
→ Upload revised screenplay
→ Analyze RIPPLE
→ Review changes
→ Review dependencies
→ Review conflicts
→ Review recovery options
```

## Team

Built collaboratively for the Google Cloud Agentic Cinema Hackathon across product ideation, architecture, AI workflows, data engineering, backend development, frontend development, authentication, testing, and demo preparation.

## License

Licensed under the **Apache License 2.0**. See `LICENSE` for details.

---

> **RIPPLE turns script changes into production decisions.**
