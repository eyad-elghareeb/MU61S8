# AGENTS.md — MU61S8 Quiz Site

> **Purpose:** This file is the complete reference for any LLM agent working on this repository. Read this before touching any file. It replaces the need to read all source files from scratch.

---

## 1. Project Identity

| Key | Value |
|-----|-------|
| **Type** | Static quiz site — no backend, no build step |
| **Deployment** | GitHub Pages via Jekyll (serves files as-is) |
| **Live URL** | `https://<username>.github.io/MU61S8/` |
| **Entry point** | `index.html` (root hub) |
| **Offline** | Full PWA — service worker caches everything |

---

## 2. Repository Layout

```
MU61S8/
├── index.html                  ← Root hub (lists subject folders)
├── index-engine.js             ← Hub/index page engine (shared)
├── index-engine.css            ← Hub/index page styles (shared)
├── quiz-engine.js              ← Quiz page engine (shared)
├── bank-engine.js              ← Question-bank page engine (shared)
├── sw.js                       ← Service worker (auto-updated by sync script)
├── manifest.webmanifest        ← PWA manifest
├── favicon.svg                 ← App icon (vector)
├── icon-{48,72,96,144,192,512}.png  ← PWA icons
│
├── gyn/                        ← Subject folder (Gynecology)
│   ├── index.html              ← Subject hub
│   ├── dep/                    ← Sub-folder
│   │   ├── index.html          ← Sub-folder hub
│   │   ├── l1-anatomy.html     ← Individual quiz file
│   │   ├── all-department-book.html  ← Bank file (aggregate)
│   │   └── ...
│   ├── past-years/
│   │   ├── index.html
│   │   ├── by-lecture/         ← Third-level nesting
│   │   │   ├── index.html
│   │   │   └── l1-anatomy.html
│   │   └── ...
│   ├── ai/
│   ├── mans/
│   └── extra/
│
├── Cardio/                     ← Another subject folder
│   ├── index.html
│   └── *.html
│
├── surg/
│   ├── index.html
│   ├── dr.-maf/                ← Sub-folder
│   │   └── ...
│   └── *.html
│
├── ped/
│   └── ...
│
└── scripts/
    ├── sync_quiz_assets.py     ← CI: auto-indexes new files + updates sw.js
    └── standardize_quiz_files.py  ← One-time formatter for quiz files
```

**Depth convention:** Folders can nest to any depth. The engine auto-detects its own path via `location.pathname`.

---

## 3. Engine Architecture

### Three engines — one per page type

| Engine | Used in | Loaded by |
|--------|---------|-----------|
| `quiz-engine.js` | Individual quiz files (`l1-anatomy.html`) | `document.write()` snippet in quiz file |
| `bank-engine.js` | Aggregate bank files (`all-department-book.html`) | `document.write()` snippet in bank file |
| `index-engine.js` | All `index.html` hub pages | `<script src="...index-engine.js">` tag |

### Engine path resolution — critical

Quiz/bank files resolve the engine path at runtime using:

```html
<script>
(function(){
  window.__QUIZ_ENGINE_BASE = '../'.repeat(
    Math.max(0, location.pathname.split('/').filter(Boolean).length - 2)
  );
  document.write('<scr'+'ipt src="'+window.__QUIZ_ENGINE_BASE+'quiz-engine.js"><\/scr'+'ipt>');
})();
</script>
```

Index pages use a relative `<script src="../../index-engine.js">` adjusted for depth.

**Rule:** Engines always live at the repo root. Never copy them into subfolders.

---

## 4. File Schemas

### 4a. Quiz File (`quiz-engine.js` consumer)

Minimal required structure — everything else is injected by the engine:

```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script>
/* FOUC prevention — runs before paint */
(function(){var t=localStorage.getItem('quiz-theme')||'dark';var s=document.createElement('style');
s.textContent='html,body{background:'+(t==='light'?'#f3f0eb':'#0d1117')+';color:'+(t==='light'?'#1c1917':'#e6edf3')+';margin:0;padding:0;overflow:hidden;height:100%}';
document.head.appendChild(s)})();
</script>
<title>Quiz Title</title>
</head>
<body>
<script>

/* [QUIZ_CONFIG_START] */
const QUIZ_CONFIG = {
  "uid": "gyn_dep_l1_anatomy",   // REQUIRED — unique, snake_case, stable across edits
  title: "L1 Anatomy",           // Shown in quiz header and tab title
  description: "Department Book MCQs",  // Shown on start screen
};
/* [QUIZ_CONFIG_END] */

/* [QUESTIONS_START] */
const QUESTIONS = [
  {
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct": 2,           // 0-indexed — index of the correct option
    "explanation": "Why C is correct..."
  },
  // ...
];
/* [QUESTIONS_END] */

</script>
<script>
/* Engine loader — do NOT modify this block */
(function(){
  window.__QUIZ_ENGINE_BASE='../'.repeat(Math.max(0,location.pathname.split('/').filter(Boolean).length-2));
  document.write('<scr'+'ipt src="'+window.__QUIZ_ENGINE_BASE+'quiz-engine.js"><\/scr'+'ipt>');
})();
</script>
</body>
</html>
```

**QUIZ_CONFIG fields:**

| Field | Required | Notes |
|-------|----------|-------|
| `uid` | Yes | Unique ID for progress + tracker storage. Never change after deployment. Use `subjectfolder_filename` pattern. |
| `title` | Yes | Displayed on start screen and topbar |
| `description` | Yes | Sub-heading on start screen |

### 4b. Bank File (`bank-engine.js` consumer)

```html
<!-- Head is identical to quiz file -->
<script>

/* [BANK_CONFIG_START] */
const BANK_CONFIG = {
  "uid": "mnvufdyp7ukjx",        // REQUIRED — stable unique ID
  "title": "All Department Book",
  "description": "All department book questions in one bank file",
  "icon": "🗃️"                   // Optional — shown on start screen
};
/* [BANK_CONFIG_END] */

/* [QUESTION_BANK_START] */
const QUESTION_BANK = [
  {
    "question": "Question text?",
    "options": ["A", "B", "C", "D"],
    "correct": 2,
    "explanation": "Explanation here."
  },
  // ...  (can be hundreds of questions)
];
/* [QUESTION_BANK_END] */

</script>
<script>
(function(){
  window.__QUIZ_ENGINE_BASE='../'.repeat(Math.max(0,location.pathname.split('/').filter(Boolean).length-2));
  document.write('<scr'+'ipt src="'+window.__QUIZ_ENGINE_BASE+'bank-engine.js"><\/scr'+'ipt>');
})();
</script>
```

**Bank engine extras** (not in quiz engine):
- User selects question count (default: next N sequential, or random)
- Progress tracked across sessions — bank remembers which questions have been seen
- `SESSION_QUESTIONS` / `SESSION_QUESTION_INDICES` globals set at runtime
- Modes: `sequential` (cycles through bank in order) or `random`

### 4c. Index / Hub File (`index-engine.js` consumer)

```html
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<!-- standard meta, fonts, index-engine.css, manifest, favicon -->
</head>
<body>
  <div class="topbar">
    <!-- Optional back button for sub-hubs: -->
    <a href="../index.html" class="icon-btn back-btn" title="Back">←</a>
    <div class="topbar-title">MU61 Quiz - Gynecology</div>
    <button class="icon-btn btn-tracker" onclick="openTrackerDashboard()">
      <svg ...></svg>
      <span class="tracker-badge" id="tracker-badge-count"></span>
    </button>
    <button class="icon-btn" id="theme-toggle" onclick="toggleTheme()">☀</button>
  </div>
  <div class="container">
    <header class="hero">
      <h1>Select your <span>Gynecology exam</span></h1>
      <p>Description text.</p>
    </header>
    <div class="quiz-grid" id="quiz-grid"></div>
    <div class="footer-note">Made By: <a href="...">QuizTool</a></div>
  </div>

<script>
const QUIZZES = [
  {
    title: "L1 Anatomy",
    description: "Pelvic anatomy MCQs",
    icon: "📘",
    tags: ["Lecture", "30 Questions"],
    url: "l1-anatomy.html"      // relative to this index.html
  },
  {
    title: "📁 Past Years",      // folder links use 📁 prefix
    description: "Past year exams",
    icon: "📅",
    tags: ["Folder"],
    url: "past-years/index.html"
  }
];
</script>

<!-- Tracker dashboard HTML (required exactly once) -->
<div class="dash-overlay" id="tracker-dashboard">
  <div class="dash-modal">
    <div class="dash-header">
      <h2 id="dash-title-text">📊 Question Tracker</h2>
      <button class="dash-close-btn" onclick="closeTrackerDashboard()">✕</button>
    </div>
    <div class="dash-scope-bar" id="dash-scope-bar"></div>
    <div class="dash-summary">
      <div class="dash-stat"><div class="ds-val red" id="dash-total-wrong">0</div><div class="ds-lbl">Wrong</div></div>
      <div class="dash-stat"><div class="ds-val blue" id="dash-total-flagged">0</div><div class="ds-lbl">Flagged</div></div>
      <div class="dash-stat"><div class="ds-val green" id="dash-total-quizzes">0</div><div class="ds-lbl">Quizzes</div></div>
    </div>
    <div class="dash-body" id="dash-body"></div>
    <div class="dash-footer">
      <button class="btn-dash-action" onclick="exportTrackerToPDF()">📄 Export PDF</button>
      <button class="btn-dash-action btn-dash-danger" onclick="confirmClearTrackerData()">🗑 Clear All</button>
      <button class="btn-dash-close" onclick="closeTrackerDashboard()">Close</button>
    </div>
  </div>
</div>

<script src="../index-engine.js"></script>  <!-- depth-adjusted path -->
<script>
(function(){
  var s=localStorage.getItem('quiz-theme');
  if(s) document.documentElement.setAttribute('data-theme',s);
  if(window.__updateThemeIcon) window.__updateThemeIcon();
  if(window.renderQuizzes) window.renderQuizzes();
})();
</script>
<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('../sw.js').catch(function () {});  // depth-adjusted
  });
}
</script>
</body>
</html>
```

---

## 5. localStorage Key Reference

| Key | Owner | Value |
|-----|-------|-------|
| `quiz-theme` | All pages | `'dark'` \| `'light'` |
| `quiz_progress_v1_<uid_sanitized>` | quiz-engine | JSON: `{version, current, answers, flagged, elapsed, timerSecs, mode, timestamp}` |
| `quiz_tracker_v2_<uid>` | quiz/bank-engine tracker | JSON: `{uid, title, wrong[], flagged[], path, folderPath, timestamp, ...}` |
| `quiz_tracker_keys` | tracker | JSON array of UIDs with saved tracker data |
| `bank_progress_<uid>` | bank-engine | JSON: `{seenIndices[], lastIdx}` — tracks sequential progress across sessions |

**Never rename `uid` values** — they are the primary key for all stored progress and tracker data. Renaming silently orphans user data.

---

## 6. Global Function API

### quiz-engine.js exposes globally:

| Function | Purpose |
|----------|---------|
| `startQuiz()` | Called by "Start Quiz" button |
| `goTo(idx)` | Jump to question index |
| `nextQuestion()` | Advance one question |
| `toggleFlag(idx)` | Flag/unflag a question |
| `attemptSubmit()` | Validate and show submit modal |
| `confirmSubmit()` | Finalize submission, save tracker |
| `restartQuiz()` | Return to start screen, clear progress |
| `filterResults(filter, btn)` | Filter result list (`'all'`/`'correct'`/`'wrong'`/`'skipped'`/`'flagged'`) |
| `exportToPDF()` | Export results to PDF via html2pdf CDN |
| `toggleTheme()` | Toggle dark/light mode |
| `navigateToIndex(event)` | Navigate to `index.html` (always relative to quiz file) |
| `showToast(msg, actions[])` | Show notification toast |
| `confirmResetProgress()` | Show reset modal |
| `saveTrackerData()` | Called on submit — saves wrong/flagged to tracker storage |
| `updateDashboardBadge()` | Refresh tracker badge count |
| `openTrackerDashboard(scope?)` | Open tracker panel |

### bank-engine.js adds:

| Function | Purpose |
|----------|---------|
| `selectSessionQuestions(count, order)` | Pick N questions from bank (`'sequential'`\|`'random'`) |
| `getBankProgress()` | Read sequential progress from localStorage |
| `saveBankProgress(progress)` | Persist sequential progress |
| `resetBankProgress()` | Clear sequential progress |
| `adjustCount(delta)` | ±N question count on start screen |
| `setCount(n)` | Set exact question count |
| `autoSetTime(n)` | Auto-calculate time based on count |

### index-engine.js exposes globally:

| Function | Purpose |
|----------|---------|
| `renderQuizzes()` | Render `QUIZZES` array into `#quiz-grid` |
| `toggleTheme()` | Toggle theme |
| `showToast(msg)` | Toast notification |
| `openTrackerDashboard()` | Open tracker dashboard |
| `closeTrackerDashboard()` | Close tracker dashboard |
| `confirmClearTrackerData()` | Show scoped clear modal |
| `closeClearTrackerModal()` | Close clear modal |
| `clearAllTrackerData()` | Execute clear (called by modal confirm button only) |
| `removeTrackerItem(uid, qIdx)` | Remove a single question from tracker |
| `exportTrackerToPDF()` | Export tracker to PDF |
| `updateDashboardBadge()` | Refresh badge count |

---

## 7. Tracker System

The tracker persists wrong and flagged questions **across sessions** for review.

### Data flow:
1. Quiz/bank submitted → `confirmSubmit()` → `saveTrackerData()`
2. `saveTrackerData()` merges with existing data for that quiz UID
3. Tracker reads `SESSION_QUESTION_INDICES` if present (bank files) to track by global index; otherwise tracks by question text
4. Tracker data stored under `quiz_tracker_v2_<uid>`; UID list under `quiz_tracker_keys`
5. Index pages read all tracker data and display grouped by folder scope

### Scope tabs in tracker dashboard:
- **This Quiz** — only data for current page's UID
- **All Quizzes** — all stored tracker data
- **Folder tabs** — data from all quizzes within a path prefix (auto-generated from URL depth)

### Clear behavior:
`confirmClearTrackerData()` shows a modal. The modal's "Clear Now" calls `clearAllTrackerData()` which deletes **only within the current scope tab** — not all data globally.

---

## 8. Service Worker (`sw.js`)

**Never edit `sw.js` manually.** It is fully managed by `scripts/sync_quiz_assets.py`.

The sync script:
1. Scans all `.html` files (skipping `SKIP_DIRS`: `.git`, `.github`, `__pycache__`, `_site`, `scripts`, `node_modules`)
2. Puts engine files first in `PRECACHE_REL_PATHS`: `quiz-engine.js`, `bank-engine.js`, `index-engine.js`
3. Computes a content hash → writes `CACHE_VERSION = 'quiz-cache-<hash>'`
4. Updates `PRECACHE_REL_PATHS` array in `sw.js`

To trigger manually: `python scripts/sync_quiz_assets.py` from repo root.

**Cache strategy:**
- HTML navigation: network-first → cache fallback → hub fallback
- Assets/JS/CSS: cache-first → network on miss
- Google Fonts + html2pdf CDN: fetched and cached at install time

---

## 9. CI/CD Workflows

### `.github/workflows/sync-quiz-assets.yml`
**Trigger:** push to `main`
**Does:** runs `scripts/sync_quiz_assets.py`, commits changes to `index.html` files and `sw.js` (excludes `scripts/` folder from commit)

### `.github/workflows/jekyll-gh-pages.yml`
**Trigger:** after `Sync Quiz Assets` completes successfully
**Does:** builds with Jekyll, deploys to GitHub Pages

**Flow:** `git push` → sync workflow auto-indexes + updates SW → deploy workflow publishes

---

## 10. Common Tasks

### Add a new quiz file to an existing folder

1. Create `gyn/dep/l10-pcos.html` using the quiz file schema (Section 4a)
2. Set a unique `uid` (e.g. `"gyn_dep_l10_pcos"`)
3. Push to `main` — `sync_quiz_assets.py` will automatically add it to `gyn/dep/index.html` and update `sw.js`

No manual index editing required.

### Add a new sub-folder

1. Create the folder, e.g. `gyn/special/`
2. Create `gyn/special/index.html` using the index file schema (Section 4c)
   - Set `engine_prefix` to `../../` (two levels deep)
   - Add back button pointing to `../index.html`
3. Add quiz files inside it
4. Push — sync script adds `gyn/special/index.html` to `gyn/index.html` automatically

### Add a new top-level subject folder

1. Create `newsubject/index.html`
2. Push — sync script adds it to root `index.html` automatically

### Manually force a re-index

```bash
python scripts/sync_quiz_assets.py
```

### Changing a quiz title/description

Edit the `QUIZ_CONFIG` `title` / `description` fields in the quiz file. The sync script will update the parent index.html automatically on next push. **Never change `uid`.**

---

## 11. CSS / Theme Variables

All styling uses CSS custom properties defined in `quiz-engine.js` (injected `<style>`) and `index-engine.css`.

| Variable | Dark | Light |
|----------|------|-------|
| `--bg` | `#0d1117` | `#f3f0eb` |
| `--surface` | `#161b22` | `#ffffff` |
| `--surface2` | `#1c2330` | `#f8f6f1` |
| `--border` | `#30363d` | `#d0ccc5` |
| `--text` | `#e6edf3` | `#1c1917` |
| `--text-muted` | `#8b949e` | `#78716c` |
| `--accent` | `#f0a500` | `#c27803` |
| `--correct` | `#2ea043` | `#16a34a` |
| `--wrong` | `#da3633` | `#dc2626` |
| `--flagged` | `#58a6ff` | `#2563eb` |

Theme persists via `localStorage.getItem('quiz-theme')`. Applied to `<html data-theme="dark|light">`.

---

## 12. What NOT To Do

- **Never edit `sw.js` manually** — always run `sync_quiz_assets.py` instead
- **Never change a `uid`** — breaks all stored user progress and tracker data silently
- **Never copy engine files into subfolders** — the runtime path detection handles depth automatically
- **Never use `clearAllTrackerData()` directly in a button `onclick`** — always call `confirmClearTrackerData()` which shows the scoped modal first
- **Never hardcode `../` paths for the engine** — the `__QUIZ_ENGINE_BASE` snippet computes depth automatically
- **Never omit the `/* [QUIZ_CONFIG_START] */` markers** — the sync script parses these to extract metadata
- **Never put quiz files directly in the repo root** — all content lives inside subject subfolders
- **Never add `<head>` CSS/JS of your own** — the engine injects all styles, fonts, and links. Adding your own risks conflicts
- **Never commit binary files** (except `icon-*.png`) — everything else is plain text

---

## 13. File Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Quiz files | `kebab-case.html` | `l1-anatomy.html`, `60th-final.html` |
| Bank files | `all-*.html` or `*-bank.html` | `all-department-book.html`, `mans-mcq-bank.html` |
| Subject folders | lowercase, short | `gyn/`, `surg/`, `Cardio/` |
| Sub-folders | lowercase, descriptive | `dep/`, `past-years/`, `by-lecture/` |
| `uid` values | `folder_subfolder_filename` snake_case | `gyn_dep_l1_anatomy` |

---

## 14. Dependency Map

```
index.html
  └── index-engine.js   (loads CSS, builds tracker dashboard, renders QUIZZES)
  └── index-engine.css  (layout: topbar, grid, cards, tracker overlay)
  └── sw.js             (offline caching — managed by sync script)
  └── manifest.webmanifest

gyn/dep/l1-anatomy.html
  └── quiz-engine.js    (injects all CSS, HTML, logic — full SPA)

gyn/dep/all-department-book.html
  └── bank-engine.js    (injects all CSS, HTML, logic — full SPA with session control)
```

No npm. No bundler. No build step. All files are served as written.
