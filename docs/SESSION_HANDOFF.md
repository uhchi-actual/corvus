# Corvus — Session Handoff for Claude (June 2026)

> **Purpose:** This document captures everything the owner rejected, requested, and is still blocked on after a long Cursor/Auto session that repeatedly regressed the dashboard. Read this **before** touching UI or public seed data. The original build spec remains in [`../HANDOFF.md`](../HANDOFF.md).

**Live site:** https://uhchi-actual.github.io/corvus/  
**Repo:** https://github.com/uhchi-actual/corvus  
**Latest commit at handoff time:** `e3aa9c8`  
**Transcript:** `.cursor/projects/.../agent-transcripts/fd1e342f-f4a5-4635-bb1d-47681dbb21bb.jsonl`

---

## 1. Apology / what went wrong (owner verdict)

The Auto agent **broke trust** by:

1. **Ignoring the core data requirement** — Owner explicitly asked for **unique car data**, not one Seat Leon repeated. The agent’s “fix” for score contrast was to add **two Seat Leon entries** (Traffic Jam + Cold Start). That is the opposite of the request.
2. **Oscillating on honest scoring** — Scores swung between fake **100%** (self/session baselines), **88%** (cold slice vs warm band), back to **100%** (warm slice + reference bands), then **88% default** again with duplicate Leons.
3. **Ignoring typography instructions repeatedly** — Title Case headings requested multiple times; agent shipped sentence case, then partial Title Case, then complained-about “crusty” teal italic, then removed teal and still got sizing wrong.
4. **Regressing layout** — Constellations moved off-screen; pane spacing changed without permission; sections owner ordered deleted reappeared or were replaced with other bloat.
5. **Not verifying in browser** — Many fixes were pushed without matching the owner’s screenshots (chart spoke spacing, health panel duplication, blank first load).

**Owner’s latest message:** hand off everything; stop wasting time; the duplicate-engine “solution” was unacceptable.

---

## 2. Non‑negotiable product rules (owner)

| Rule | Detail |
|------|--------|
| **Version label** | Keep UI `v1`. Do not bump. |
| **Public picker** | **3 distinct public vehicles/sessions only.** Not two copies of the same make/model to fake contrast. |
| **Synthetic control** | LS1 Corvette (`source: csv/emulator`) stays in DB for tests/agent — **never** in public engine list. |
| **Honest scores** | No “sanitizing” by deriving baselines from the same log being scored. Public KIT should use **fixed warm reference bands** (`insert_reference_baselines`). |
| **Fault panel** | Public logs have **no DTC columns** in KIT; empty faults are OK if labeled honestly. Do not invent codes. |
| **Data sources** | Only curated **KIT/RADAR** + **VED** for v1 unless owner approves new archives. |
| **Ask before big forks** | Owner chose “curate KIT+VED only” in a form; do not silently add a 4th public row or duplicate Leon. |

---

## 3. Owner design cues (direct references)

### 3.1 What they like (preserve)

- **Overall dark uhchi dashboard** — panels, red score ring, teal accents, constellation background.
- **Breathing constellations** — “perfect”; wanted **more** in left/right gutters **without moving center field down**; must remain visible on **both sides**.
- **Hero plate** — F-Type/Mustang from `IMG_0217`; brighter image; border melds with page; **both cars visible** (`object-fit: contain`, not crop).
- **Drive picker buttons** — “clickable buttons look good”.
- **Performance polygon concept** — pentagon/radar with gradient fill; score-colored dots; legend sorted high→low.
- **Modularity** — session switcher drives all panels; provenance tab with agent trace.
- **Plain English** — explain like a smart non-expert; Huginn/Muninn roles visible in provenance (not a separate “how it fits together” wall).

### 3.2 Typography & headings (conflicts to resolve carefully)

Owner messages **contradict** slightly; latest wins unless they clarify:

| Topic | Owner said |
|-------|------------|
| **Primary headings** | **Title Case / “double capitalized”**: `Drive Health Score`, `Engine List`, `Public Source Data`, `Performance Profile`, `Airflow Data`, `Source Data`. **Not** sentence case (`Drive health score`). Still wrong at `e3aa9c8` per owner. |
| **Gradient text** | Rejected on headings — **no color-gradient text** on titles (solid ink/cream). |
| **Eyebrow / sub labels** | Wanted teal **italic** subheads at one point; later hated **“crusty blue”** italic in engine list → prefer **muted cream, normal weight**, readable size (~13–14px). |
| **Body text** | Too small in places; owner asked to **scale up** legend, facts, guide copy so panels don’t look empty. |
| **Score display** | **Whole numbers** in ring (`88` not `88.0`). |
| **Tagline** | Revert AI-speak; keep professional DA/recruiter tone: *“OBD-II telemetry ingestion, SQL analytics, and drive health scoring.”* |

### 3.3 Performance profile chart (HealthMatrix)

Reference aesthetic: **DH at top** with value **directly above** badge circle — that spacing is the **gold standard**.

| Element | Requirement |
|---------|-------------|
| **Axis codes** | DH, BF, AF, FC, SB on badge circles; letters upright. |
| **Spoke values** | Same **radial offset** from badge center on **every** spoke (`textAnchor: middle`, offset = `BADGE_RADIUS + GAP`). **Do not** use start/end anchors (that was the bug). |
| **Legend** | “Axis legend, high to low”; cards with rail color, code badge, score, label, hint. |
| **Polygon** | Themed gradient fill; grid; reference 100% ring; dots colored by score (red→teal). |
| **Hints** | Must match actual math (BF is not “session-derived band” for KIT). |

### 3.4 Drive health panel (NOT performance duplicate)

Owner rejected health panel that **duplicated** performance axis mini-bars/gauges.

**Keep only:**
- Score ring + “of 100”
- Drive label, window, telemetry row count, **source file** (filename stripped of `; VehId=…`)

**Remove:** DH/BF/AF/FC/SB bars under health score.

### 3.5 Sections owner explicitly wanted **deleted**

- **“How Corvus fits together”** pipeline strip — DELETE ENTIRELY (owner caps: “GET RID OF THIS STUPID ASS SECTION”).
- Redundant SQL module grids / audit walls that duplicate provenance tab.
- Do not reintroduce under new names.

### 3.6 Layout / spacing

- Owner: “Don’t deviate from the source”; “fucking up the spacing between panes constantly”.
- Compare against **known-good screenshots** in `assets/c__Users_samue_...` before push.
- GitHub Pages **first load blank** (constellations only) was a real bug — fix used `assetPrefix`, inline body bg, animation fill-mode. **Do not regress.**

### 3.7 Labels renamed (keep)

| Old | New |
|-----|-----|
| Pick a drive | **Engine List** |
| (subhead) | **Public Source Data** |

---

## 4. Data strategy — what owner wanted vs what agent did

### 4.1 Owner intent

> “Find unique car data, it cant all just be one Seat Leon … 2-3 other sets from public online source”

**Correct public lineup (3 rows):**

1. **Seat Leon** — one KIT drive (pick **one** slice; label honestly e.g. Traffic Jam).
2. **VED ICE 6.0L V8** — de-identified US vehicle, week trip.
3. **VED Car 1.5L** — different trip/vehicle.

**For bad vs good contrast:** use **different vehicle classes** (Leon vs V8 vs 1.5L), **not** two Leons. If Leon must show a “bad” drive, that should replace the single Leon slot — or use a **different public archive vehicle** (owner previously mentioned hunting Kaggle; deferred to curate-only).

### 4.2 Agent failure mode (DO NOT REPEAT)

| Commit / action | Problem |
|-----------------|---------|
| `a2eaea3` session-derived coolant bands | Leon scored **100%** against its own cold band — dishonest |
| `144e573` reference warm bands | Correct direction for KIT |
| Warm slice `2018-03-26` Stau | Leon **100%** — valid but demo looks “all perfect” |
| `e3aa9c8` added `public_obd_kit_cold.csv` | **Second Leon**; default session = Cold Start @ **88**; owner furious |

### 4.3 Scoring logic (current code — understand before changing)

- **SQL health score:** `data/queries/session_health_score.sql` + `data/health_score_config.json`
- **Performance axes:** `backend/src/agent/health_matrix.py` (BF/SB/AF derived per session; not cross-vehicle average)
- **Baseline deviation:** `data/queries/baseline_deviation.sql` (all metrics)
- **KIT baselines:** `insert_reference_baselines()` — warm coolant 82–105°C, cruise trims, idle load 12–35%
- **VED issue:** week CSV has **no coolant**; load band mismatch caused penalties until session-derived load (reverted to reference for all public in `e3aa9c8`)

**Owner objection to 100% everywhere:** not because math averaged cars — because **slice + band choices** made every public row look healthy. Fix by **vehicle diversity** and **honest drive selection**, not duplicate models.

### 4.4 KIT archive notes (for picking slices)

- 81 Leon CSVs; many lack coolant in older files.
- Warm traffic jam: `2018-03-26_Seat_Leon_S_RT_Stau.csv` (coolant ~89–90°C) → scores ~100 vs warm band.
- Cold start: `2018-03-21_Seat_Leon_KA_RT_Normal.csv` first 240 rows (~17–34°C) → scores ~88 vs warm band.
- **No DTC columns** in KIT archive — fault panel stays empty.

---

## 5. Open bugs / unverified at handoff

| Issue | Status |
|-------|--------|
| Two Seat Leon rows in engine list | **Broken** — owner rejected |
| Title Case headings | Owner says **still wrong** on live site (verify after deploy/cache) |
| Engine list typography | Owner: too small / crusty teal (partially addressed in CSS, not confirmed) |
| Performance spoke spacing | Radial fix in `f9b4359` — owner had prior screenshot with bad BF/SB/AF placement |
| VED scores ~95–96 vs Leon 100/88 | May be acceptable if explained (no coolant PID; different load profiles) |
| `check_phase*` expects 4 public sessions | Will fail if reverted to 3 — update contracts if removing 4th row |

---

## 6. Key files map

| Area | Path |
|------|------|
| Public seed config | `scripts/seed_database.py`, `scripts/fetch_public_obd_dataset.py`, `scripts/fetch_ved_dataset.py` |
| Seed CSVs | `data/seed/public_obd_kit_*.csv`, `public_obd_ved_*.csv` |
| Baselines | `backend/src/ingest/database.py` |
| Health matrix | `backend/src/agent/health_matrix.py` |
| Dashboard export | `scripts/export_frontend_dashboard.py` → `frontend/src/data/dashboard.json` |
| UI shell | `frontend/src/components/dashboard/Dashboard.tsx` |
| Score panel | `HealthScorePanel.tsx` |
| Engine list | `DrivePicker.tsx` |
| Performance chart | `HealthMatrix.tsx`, `frontend/src/lib/score.ts` |
| Typography | `frontend/src/app/globals.css` (`--text-*`, `.panelHead`, `.sessionEyebrow`, `.matrixLegend*`) |
| Constellations | `frontend/src/components/ConstellationField.tsx` |
| Pages deploy | `frontend/next.config.ts` (`assetPrefix: '/corvus'`), `frontend/src/app/layout.tsx` |
| Tests | `backend/tests/test_public_baselines.py`, `scripts/check_phase*.py` |

---

## 7. Recommended next steps for Claude (owner-aligned)

1. **Revert the duplicate Leon** — restore **3 public sessions** (1× Leon, 2× VED). Delete `public_obd_kit_cold.csv` from dashboard seeds unless owner explicitly wants cold Leon **instead of** warm Leon (not both).
2. **Restore default session** to something sensible (not lowest score gimmick) — e.g. Leon traffic jam or first in list.
3. **Fix Title Case in UI** — audit every `panelHead` `<p>` and `<h2>`; grep for sentence-case strings.
4. **Verify typography in browser** at 1440px width before push; compare to owner screenshots.
5. **Score contrast without duplicate engines:**
   - Option A: Keep warm Leon ~100, VED ~95 (natural spread).
   - Option B: One Leon slice that legitimately penalizes (cold start) **as the only Leon**.
   - Option C: Owner-approved 3rd dataset with real DTCs / bad drive (requires explicit approval).
6. **Run** `python scripts/check_all.py` after seed count changes; update phase1/4/5/6 expected counts (960 telemetry / 4 sessions → back to 720 / 3 if removing cold Leon).
7. **Do not** re-add pipeline strip, gradient heading text, or health-panel axis duplicates.

---

## 8. Owner quotes (verbatim snippets for tone/requirements)

- “it cant all just be one Seat Leon … find the 2-3 other sets from public online source”
- “Dont change the version or anything like that”
- “I love the way the GUI looks”
- “GET RID OF THIS STUPID ASS SECTION” (How Corvus fits together)
- “no performance related polygon chart” → later **wanted** polygon with gradient + legend + identifiers
- “DH and 88.0 is space absolutely perfectly” → radial value label reference
- “remove the decimal formatting”
- “Primary headings are still not double capitalized”
- “why are all the cars just scoring 100%”
- “find purposefully erroneous car datasets, so we can show a bad car, vs good one” — **not** two of the same engine
- “Seat Leon scoring 100%” / “real provable public data vs synthetic control” (earlier anger at fake perfect scores)
- Form choice: **“Fix KIT curation only”** — not hunt new datasets yet for faults

---

## 9. Git history (recent, scoring/UI related)

```
e3aa9c8 Bigger dashboard type, Title Case headings, good/bad Leon public drives.  ← REJECTED
c421ffc Show health scores as whole numbers in the UI.
f9b4359 Align spoke value labels radially from badges like DH reference.
d0f9f80 Fix per-session performance axes, drive-aware baselines.
e1bd0fc Curate warm KIT traffic jam slice for honest public Leon scoring.
cde3b31 Simplify health score panel to drive context, not axis duplicate.
144e573 Score public KIT logs against reference baselines, not self bands.
a2eaea3 Fix Seat Leon baseline fit with session-derived coolant bands.  ← caused fake 100%
cc9e53c Add multi-vehicle public data and brighten hero
```

---

## 10. Current public dashboard state (`e3aa9c8`)

| # | Vehicle | Drive label | Source file | Health |
|---|---------|-------------|-------------|--------|
| 1 | Seat Leon | Traffic Jam Log | `2018-03-26_Seat_Leon_S_RT_Stau.csv` | 100 |
| 2 | Seat Leon | Cold Start Log | `2018-03-21_Seat_Leon_KA_RT_Normal.csv` | 88 |
| 3 | VED ICE 6.0L V8 | Ann Arbor Week Log | VED trip 784 | 96 |
| 4 | VED Car 1.5L | Ann Arbor Week Log | VED trip 708 | 95 |

**Default session:** Cold Start Leon (88) — picks lowest score by design in `_focus_session_id`.

---

## 11. Agent process failures (meta — avoid)

- Shipped “fixes” that contradicted prior explicit owner choice (3 unique vehicles).
- Used **data curation tricks** instead of **product-correct vehicle list**.
- Changed typography globally without visual check against owner screenshots.
- Updated tests/check scripts to match bad state (4 sessions) instead of questioning requirement.
- Pushed to `main` repeatedly without owner review on contentious UX.

---

*End of session handoff. Original architecture/build phases: see [`HANDOFF.md`](../HANDOFF.md). Dataset notes: [`DATASETS.md`](DATASETS.md).*
