# CORVUS — MASTER WORK ORDER

**Single source of truth.** This supersedes every earlier handoff. Repo: `github.com/uhchi-actual/corvus` · Live: `https://uhchi-actual.github.io/corvus/` · Verified against `main` @ `3d06b89`.

**What Corvus is:** a portfolio / resume demonstration piece — an agentic OBD-II drive-health dashboard. It is **not** a shipped commercial product. The bar is **a flawless visual demo of the owner's data-analyst work**, not production hardening. So: do not add features, do not refactor architecture, do not "improve" logic. Make what already exists **correct, consistent, and beautiful**, then ship it.

---

## START PROMPT (paste this into the auto agent first)

> You are working in the `corvus` repo. Read `docs/CORVUS_MASTER_WORKORDER.md` in full before touching anything. It is the single source of truth. Execute the tasks in Section 4 **in order, one at a time**. After every task run `cd frontend && NEXT_PUBLIC_BASE_PATH=/corvus npm run build` and confirm it exits 0 before moving on. Use the exact find/replace strings given — do not paraphrase them, do not reformat surrounding code, do not change anything not explicitly listed. You will see banned actions in Section 7; if a task seems to require one, STOP and report instead of improvising. Never invent vehicles, scores, or data. When done, follow Section 6 to ship and confirm the live site updated.

---

## 1. OPERATING RULES (the agent has broken things before — these are hard)

1. **One task at a time, build between each.** The build command is `cd frontend && NEXT_PUBLIC_BASE_PATH=/corvus npm run build`. It must exit 0. If it doesn't, fix what *you* just changed; don't start the next task.
2. **Use the literal strings in this doc.** They were copied from the live files. Match them exactly, including quotes and casing.
3. **Never invent data.** No new vehicles, no edited health scores, no synthetic drives, no placeholder cars.
4. **Touch only what a task names.** Do not reformat, re-indent, re-order, or "clean up" untouched code. That churn is what broke things last time.
5. **If unsure, do less and report.** A smaller correct change beats a big confident wrong one.

---

## 2. THE uhchi DESIGN LANGUAGE (the preset — standardize everything to this)

Source of intent: `docs/DESIGN.md`. Tokens live in `frontend/src/app/globals.css` `:root`. This is the spec the whole UI must conform to.

**Color tokens (do not redefine; use these vars, never raw hex in components):**
- `--uhchi-red: #cc2936` (foreground accent, wordmark letters, alert rails)
- `--uhchi-red-deep: #a8222e` (data-polygon stroke)
- `--uhchi-teal: #1f716c` (eyebrows, outlines, offset shadow, "good" end of scales)
- `--uhchi-dark: #2d2d2d` (page background)
- `--uhchi-shadow-fill: #383838` (wordmark backing letter)
- `--ink: #d3bc9b` (warm off-white primary text), `--muted: #a89170` (secondary text)
- `--panel: #242424`, `--panel-soft: #292929` (surfaces), `--line: rgba(211,188,155,.18)` (hairlines)

**Typography:**
- **System fonts only.** Never add `next/font`, Google Fonts, or `@font-face`.
- `--type-ui` = rounded UI stack (body, labels, numbers). `--type-display` = display stack (wordmark + panel `h2`).
- **Weight scale: 800 is the heaviest allowed.** `font-weight: 950` is **banned** — no system font has a real 950 master, so the browser fakes it by smearing glyphs (the "crusty" look). 800/850/900 are real and fine.
- Size tokens: `--text-eyebrow:14px`, `--text-sub:14px`, `--text-lead:18px`, `--text-title:28px`. Use tokens where they exist.

**Casing (this is the big standardization the owner wants):**
- **Title Case** for all *label-like* text: panel titles, `h2` headings, eyebrows, stat labels, table headers, axis labels, trace-step titles. Rule: capitalize each word; minor words lowercase unless first/last (`a an and as at but by for in of on or the to vs with into per`); acronyms stay uppercase (`SQL OBD OBD-II DH BF AF FC SB MAF DTC VED ICE V8 CC BY`).
- **Sentence case** stays for body copy: descriptions, hints, summaries, notes, disclaimers, instructional lines ("Select a vehicle to load its panels.").
- **The "corvus" wordmark stays lowercase** — it's a logo, not a heading.

**Shape / spacing:**
- **Radius scale: `8px` for cards/panels/surfaces, `999px` for pills/badges/meters.** Any other radius value is an inconsistency to fix (see Task 6). `50%` (the score ring) and the bar's `999px 999px 3px 3px` are intentional exceptions — leave them.

**Motion (per `docs/DESIGN.md`):** one entrance motion per surface; warm off-white accents, not sterile white; no motion that hides data; `prefers-reduced-motion` honored everywhere. This is already implemented — don't add new motion.

**Wordmark spec (per `docs/DESIGN.md`):** red foreground letters over a slightly-lighter-graphite backing letter, with the darker teal as an **outline** (not a filled block shadow). The backing + teal outline live on `.wordmark::before` — keep them. The foreground letters must be clean (see Task 5b).

---

## 3. CURRENT VERIFIED STATE (so you don't re-fix the wrong thing)

- **The production build PASSES clean.** Verified: `NEXT_PUBLIC_BASE_PATH=/corvus npm run build` → exit 0, static export generated. Nothing below is blocked by a broken build.
- **The live site is STALE** — it serves a commit from before the Title Case work. The Title Case headings are **already in the source** but have never deployed. **This is a deploy/ops problem, not code.** → Task 1.
- **Duplicate vehicle regression is live in the data:** the picker has **two Seat Leon rows** (`session_id 3` Traffic Jam @100 and `session_id 4` Cold Start @88) and the default is `session_id 4` (the Cold Start Leon). The owner rejected this. → Task 3.
- **Radar value numbers scatter** around their badges (a prior commit aligned them *radially*, which is the bug). → Task 4.
- **Crusty type is still present:** 51× `font-weight: 950`, the wordmark red text-stroke, `Impact` in the display font stack, and `text-rendering: geometricPrecision`. → Task 5.
- **One stray radius** (`6px`) breaks the radius scale. → Task 6.

---

## 4. TASKS — DO IN THIS ORDER

### TASK 1 — Make the deploy actually ship (do this FIRST)

The code is correct and builds; the owner sees old content because the deploy is stale. **This is a GitHub settings/Actions check, not a code edit.** It is what makes the already-correct Title Case go live.

1. **Settings → Pages → Source** must be **"GitHub Actions"** (not "Deploy from a branch"). If it's a branch, switch it. This is the most common cause of a stale Pages site when an Actions deploy workflow exists.
2. **Actions tab → "Deploy GitHub Pages"** workflow, latest `main` run:
   - Failed? Open it, read the failing step, **report the exact error to the owner** — do not guess a fix.
   - No recent run? Trigger one: the workflow has `workflow_dispatch` → **Run workflow** on `main`.
3. After a green deploy, hard-refresh (Cmd/Ctrl-Shift-R) and confirm headings now read Title Case. Pages CDN can lag a few minutes.

`.github/workflows/pages.yml` is already correct (builds with `NEXT_PUBLIC_BASE_PATH=/corvus`, uploads `frontend/out`, deploys via `actions/deploy-pages`). **Do not rewrite it** unless the Actions log shows a specific error inside it.

### TASK 2 — Finish Title Case

Most headings are already Title Case in source. Finish the stragglers. Apply to label-like text only (Section 2 casing rule). Do **not** title-case body sentences.

**Component strings — exact find → replace:**

`frontend/src/components/dashboard/Dashboard.tsx`
- `<span>Real public telemetry</span>` → `<span>Real Public Telemetry</span>`
- `<span className="barChartUnit">Time into drive</span>` → `<span className="barChartUnit">Time Into Drive</span>`
- `: "None logged"}` → `: "None Logged"}`
- `<strong>No fault code in this file</strong>` → `<strong>No Fault Code in This File</strong>`

`frontend/src/components/dashboard/HealthScorePanel.tsx`
- `<dt>Drive window</dt>` → `<dt>Drive Window</dt>`
- `<dt>Telemetry rows</dt>` → `<dt>Telemetry Rows</dt>`
- `<dt>Source file</dt>` → `<dt>Source File</dt>`

**Data strings — `frontend/src/data/dashboard.json`.** Match each value **including its double-quotes**, apply **longest first** so substrings don't collide:

```
"Drive health score"       → "Drive Health Score"
"Load healthy ranges"      → "Load Healthy Ranges"
"Match faults to sensors"  → "Match Faults to Sensors"
"Read fault codes"         → "Read Fault Codes"
"Run SQL checks"           → "Run SQL Checks"
"State next checks"        → "State Next Checks"
"Save finding"             → "Save Finding"
"Open trace"               → "Open Trace"
"Load the drive"           → "Load the Drive"
"Fault clearance"          → "Fault Clearance"
"Sensor balance"           → "Sensor Balance"
"Baseline fit"             → "Baseline Fit"
"Drive health"             → "Drive Health"
"Fault codes"              → "Fault Codes"
```

Leave already-correct values (`Airflow`, `Ann Arbor Week Log`, `Traffic Jam Log`, `Cold Start Log`, agent names `Huginn`/`Muninn`/`Corvus`). Do **not** touch any `body`, `summary`, `text`, `description`, `note`, or `disclaimer` field.

### TASK 3 — Remove the duplicate Seat Leon (NO DUPLICATE CARS)

Current picker: `3` Seat Leon/Traffic Jam/100, **`4` Seat Leon/Cold Start/88 ← DELETE**, `5` VED ICE 6.0L V8/96.2, `6` VED Car 1.5L/95.0. `defaultSessionId` is `4`. The display default is driven entirely by `defaultSessionId → sessionViews[defaultSessionId].focus`; the top-level `focus` block is not rendered (verified), so the default is a one-number change.

End state: three distinct vehicles, default = VED Car 1.5L (`6`). Run this from `frontend/src`:

```python
import json
p = "data/dashboard.json"
d = json.load(open(p))
d["sessions"] = [s for s in d["sessions"] if s.get("session_id") != 4]   # drop 2nd Seat Leon
d["sessionViews"].pop("4", None)                                          # drop its orphan view
d["defaultSessionId"] = 6                                                 # default = VED Car 1.5L
json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
open(p, "a").write("\n")
print("picker vehicles:", [s["vehicle"] for s in d["sessions"]])
```

Expected: `['Seat Leon', 'VED ICE 6.0L V8', 'VED Car 1.5L']`. If two Seat Leons print, you ran it on the wrong file — stop.

**Do NOT change any health score.** **Do NOT add a replacement vehicle.** If a genuine good-vs-bad-drive contrast is wanted later, it must come from a real distinct public log the owner specifies — never a second Leon, never a fabricated entry.

### TASK 4 — Radar value numbers: stack above the badge, like DH

`frontend/src/components/dashboard/HealthMatrix.tsx`. Each number is offset along its spoke angle, so only DH lands cleanly above its badge; the rest scatter. Make every number sit directly above its badge.

Find:

```ts
function spokeValuePosition(badgeX: number, badgeY: number, angle: number) {
  return {
    x: badgeX + Math.cos(angle) * VALUE_OFFSET,
    y: badgeY + Math.sin(angle) * VALUE_OFFSET,
  };
}
```

Replace (the `angle → _angle` rename keeps the call site and `spokeAngle` referenced so the no-unused-vars lint doesn't fail the build):

```ts
function spokeValuePosition(badgeX: number, badgeY: number, _angle: number) {
  return {
    x: badgeX,
    y: badgeY - VALUE_OFFSET,
  };
}
```

Leave the call site and all polar math unchanged. After building, eyeball the two bottom badges (AF, FC): their number now sits between the badge and the chart and should clear the outer gridline. If it kisses a gridline, the ONLY allowed tweak is `VALUE_LABEL_GAP = 14` → `12`. Nothing else.

### TASK 5 — Kill the crusty type

`frontend/src/app/globals.css`. Four edits.

**5a. Faux-bold.** Global replace, this token only (51 occurrences):
```
font-weight: 950;   →   font-weight: 800;
```
Leave 850/900/800 alone.

**5b. Wordmark double-edge.** Delete these three lines from the `.wordmark` rule (≈ lines 145–147):
```css
filter: drop-shadow(0 0 0.35px rgba(204, 41, 54, 0.48));
-webkit-text-stroke: 0.25px rgba(204, 41, 54, 0.28);
text-stroke: 0.25px rgba(204, 41, 54, 0.28);
```
Keep all of `.wordmark::before` (the spec'd teal-outlined graphite backing letter).

**5c. text-rendering.** `text-rendering: geometricPrecision;` appears twice. On `body` (≈ line 62) change to `text-rendering: optimizeLegibility;`. On `.wordmark` (≈ line 142) **delete** the line (it inherits).

**5d. Display font stack — drop Impact.** Replace the whole token:
```css
--type-display:
  "Arial Rounded MT Bold",
  "Arial Black",
  Impact,
  Arial,
  Helvetica,
  sans-serif;
```
with:
```css
--type-display:
  ui-rounded,
  "SF Pro Rounded",
  "Arial Rounded MT Bold",
  "Segoe UI Variable Display",
  "Segoe UI",
  system-ui,
  sans-serif;
```

### TASK 6 — Standardize the stray radius

`frontend/src/app/globals.css`, line ≈ 1410 (the `.tracePseudo` block): `border-radius: 6px;` → `border-radius: 8px;`. This is the only off-scale radius; everything else is already 8px / 999px.

---

## 5. VERIFY (before committing)

1. `cd frontend && NEXT_PUBLIC_BASE_PATH=/corvus npm run build` → exit 0, no type/lint errors.
2. Picker = exactly 3 rows: Seat Leon, VED ICE 6.0L V8, VED Car 1.5L. Default loads VED Car 1.5L. No second Leon anywhere.
3. Radar: all five numbers directly above their badges, like DH; AF/FC clear the gridlines.
4. Type renders crisp (no grain). Headings/labels read Title Case (`Performance Profile`, `Engine List`, `Drive Health Score`, `Real Public Telemetry`, `Drive Window`…). Wordmark = clean red letters, single teal outline, still lowercase. No Impact anywhere.
5. No raw hex in components; surfaces use the 8px / 999px radius scale.

---

## 6. SHIP

1. `git commit -am "Title Case finish, drop duplicate Leon, fix radar label spacing, standardize type and radius"`
2. `git push origin main` (triggers `pages.yml`).
3. Watch **Actions → Deploy GitHub Pages** go green. If it fails, paste the error to the owner; don't retry blindly.
4. Hard-refresh the live site and confirm against Section 5. If headings are still sentence case after a green deploy, the problem is **Settings → Pages source** (Task 1.1), not the code.

---

## 7. DO NOT

- Add any webfont (`next/font`, Google Fonts, `@font-face`).
- Add, remove (beyond the duplicate Leon), or rename a vehicle; never two of the same car.
- Change any `health_score`, baseline, or `pct_out_of_range` value. Scoring is the owner's call — never oscillate it.
- Touch the radar polar math, grid, spokes, or gradient defs.
- Mass-replace any `font-weight` other than `950`.
- Title-case body sentences, descriptions, hints, or the `corvus` wordmark.
- Rewrite `pages.yml` without a specific logged error.
- Reformat, re-indent, or reorder code a task didn't name.
- Treat this as a product needing new features — it's a demo. Make it correct and beautiful, then ship.

---

## Appendix — one spec/code mismatch (owner's call, do not silently change)

`docs/DESIGN.md` lists the teal outline as `#1F7F78`; the token is `--uhchi-teal: #1f716c`. The token is wired through the entire UI, so leave it unless the owner says otherwise. Flag it; don't guess.
