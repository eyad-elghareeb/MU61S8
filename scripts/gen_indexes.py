import os
import sys
from pathlib import Path

# Repository Root (parent of this scripts folder)
REPO_ROOT = Path(__file__).resolve().parent.parent

TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script>
(function(){{var t=localStorage.getItem('quiz-theme')||'dark';var s=document.createElement('style');
s.textContent='html,body{{background:'+(t==='light'?'#f3f0eb':'#0d1117')+';color:'+(t==='light'?'#1c1917':'#e6edf3')+';margin:0;padding:0;overflow:hidden;height:100%}}';
document.head.appendChild(s)}})();
</script>
<title>MU61 Quiz</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{engine_prefix}index-engine.css">
<!-- Meta tags for preview and favicon -->
<meta name="description" content="MU61 Interactive Quiz. Test your medical knowledge.">
<meta property="og:title" content="MU61 Quiz">
<meta property="og:description" content="MU61 Interactive Quiz. Test your medical knowledge.">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#0d1117">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="manifest" href="{engine_prefix}manifest.webmanifest">
<link rel="icon" href="{engine_prefix}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{engine_prefix}favicon.svg">
</head>
<body>
  <div class="topbar">
    <a href="../index.html" class="icon-btn back-btn" title="Back">←</a>
    <div class="topbar-title">MU61 Quiz</div>
    <button class="icon-btn btn-tracker" onclick="openTrackerDashboard()" title="Question Tracker">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 5-9"/></svg>
      <span class="tracker-badge" id="tracker-badge-count"></span>
    </button>
    <button class="icon-btn" id="theme-toggle" onclick="toggleTheme()" title="Toggle theme">☀</button>
  </div>
  <div class="container">
    <!-- HERO SECTION -->
    <header class="hero">
      <h1>Select your <span>Surgery exam</span></h1>
      <p>Test your knowledge across various Surgery topics.</p>
    </header>
    <!-- EXAMS GRID -->
    <div class="quiz-grid" id="quiz-grid"></div>
    <!-- FOOTNOTE -->
    <div class="footer-note">
      Made By: <a href="https://github.com/eyad-elghareeb/QuizTool" target="_blank" rel="noopener noreferrer">QuizTool</a>
    </div>
  </div>

<script>
const QUIZZES = [];
</script>

<script src="{engine_prefix}index-engine.js"></script>
<script>
(function(){{
  var s=localStorage.getItem('quiz-theme');
  if(s) document.documentElement.setAttribute('data-theme',s);
  if(window.__updateThemeIcon) window.__updateThemeIcon();
  if(window.renderQuizzes) window.renderQuizzes();
}})();
</script>
<script>
if ('serviceWorker' in navigator) {{
  window.addEventListener('load', function () {{
    navigator.serviceWorker.register('{engine_prefix}sw.js').catch(function () {{}});
  }});
}}
</script>
</body>
</html>
"""

def generate_index(target_dir_path: str):
    target_path = Path(target_dir_path).resolve()
    
    # Calculate depth relative to REPO_ROOT
    try:
        rel_path = target_path.relative_to(REPO_ROOT)
    except ValueError:
        print(f"Error: {target_dir_path} is not inside the repository root ({REPO_ROOT})")
        return

    depth = len(rel_path.parts)
    prefix = "../" * depth
    
    # Ensure directory exists
    target_path.mkdir(parents=True, exist_ok=True)
    
    index_file = target_path / "index.html"
    
    # Don't overwrite if it already exists and isn't empty? 
    # Actually, the user might want to force it. Let's provide a message.
    if index_file.exists():
        print(f"Overwriting existing {index_file.relative_to(REPO_ROOT)}")
    else:
        print(f"Creating {index_file.relative_to(REPO_ROOT)}")

    # Use simple replace to avoid {} escaping hell with .format()
    content = TEMPLATE.replace("{engine_prefix}", prefix)
    
    index_file.write_text(content, encoding="utf-8")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/gen_indexes.py <folder_path1> <folder_path2> ...")
        # Example targets from previous task if run without args
        print("Example: python scripts/gen_indexes.py surg/by-chapter surg/past-years")
        sys.exit(1)
    
    for folder in sys.argv[1:]:
        generate_index(folder)
    
    print("\nNext step: Run 'python scripts/sync_quiz_assets.py' to update index contents.")
