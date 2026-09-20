# AI-Assisted Cross-Border Tax & Compliance System

A decision-support prototype for Indian freelancers/consultants earning income from US clients: it classifies expenses, retrieves and cites the specific Indian tax (Section 44ADA) and India–US DTAA provisions that apply, and computes an estimated tax liability with DTAA relief through a deterministic, unit-tested rules engine. All arithmetic runs in code — the LLM only classifies and retrieves.

**This is an educational prototype (BTech AI minor project). It is not legally binding tax advice.**

## Start here

| Doc | What it's for |
|---|---|
| [`docs/System_Design_and_Requirements.md`](docs/System_Design_and_Requirements.md) | Requirements, architecture, data model, API surface, tech stack + rationale |
| [`docs/Implementation_Plan.md`](docs/Implementation_Plan.md) | Phased build order, timeline, evaluation plan |
| [`docs/SRS_SDS_Report_CrossBorderTax.docx`](docs/SRS_SDS_Report_CrossBorderTax.docx) | Formal SRS+SDS submission document |
| [`docs/WORKING_PRINCIPLES.md`](docs/WORKING_PRINCIPLES.md) | How we avoid guessing/hallucinating during development, and how decisions get documented |
| [`DECISIONS.md`](DECISIONS.md) | Running log of design decisions and why we made them |
| [`PROGRESS.md`](PROGRESS.md) | Current status, phase checklist, session log |

## Team

Prachi Sharma (BTECH/25189/23) · Shreya Verma (BTECH/25202/23) — B.Tech AI, 7th Semester, BIT Mesra, Jaipur Campus.

## Tech stack

Next.js · FastAPI · PostgreSQL + pgvector · a hosted LLM API (classification + citation-grounded generation) · Docker Compose. Full rationale in `docs/System_Design_and_Requirements.md` §6.

## Running locally

Docker-only workflow — no local Python venv or `npm install` needed on the host; everything runs inside the containers.

**First time, or after changing `requirements.txt` / `package.json` / a Dockerfile:**

```bash
docker compose up --build
```

**Every other time** (day-to-day code edits):

```bash
docker compose up
```

Your `backend/` and `frontend/` folders are mounted straight into the containers with hot reload on (`uvicorn --reload`, `next dev`), so a code edit shows up without rebuilding anything. `--build` is only needed again when a *dependency* changes — see ADR-011 in `DECISIONS.md` for why it's set up this way.

- Backend health check: `http://localhost:8000/health` (and interactive API docs at `http://localhost:8000/docs`)
- Frontend: `http://localhost:3000`
- Stop everything: `Ctrl+C`, then `docker compose down` (add `-v` only if you want to wipe the Postgres data volume too)

This currently brings up the Phase 0 hello-world skeleton (see `PROGRESS.md`) — not the full application yet.

**Two compose files, merged automatically (ADR-021):** `docker-compose.yml` is the production-shaped base (frontend built to its optimized `runner` stage, no source mounts, no dev servers); `docker-compose.override.yml` layers the dev-only settings above (source mounts, `--reload`/`next dev`, the frontend's pre-build `deps` stage) on top of it. Plain `docker compose up` — as shown above — merges both automatically, so nothing above changes for day-to-day dev. To run the production shape alone (e.g. to sanity-check it before a real deploy), explicitly exclude the override file:

```bash
docker compose -f docker-compose.yml up -d --build
```
