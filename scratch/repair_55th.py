import os, re

target_file = r'd:\Study\Projects\MU61S8\gyn\past years\55th-final.html'
template_file = r'd:\Study\Projects\QuizTool\quiz-template.html'

with open(target_file, 'r', encoding='utf-8') as f:
    target_content = f.read()

# Extract QUESTIONS array
q_start_marker = 'const QUESTIONS = ['
q_end_marker = '];'
start_idx = target_content.find(q_start_marker)
end_idx = target_content.find(q_end_marker, start_idx) + len(q_end_marker)

if start_idx == -1 or end_idx == -1:
    print('Error: Could not find QUESTIONS array.')
    exit(1)

questions_array = target_content[start_idx:end_idx]

# Read template
with open(template_file, 'r', encoding='utf-8') as f:
    template_content = f.read()

# 1. Update titles and metadata in template
new_content = template_content
new_content = re.sub(r'<title>.*?</title>', '<title>Gynecology - 55th Final</title>', new_content)
new_content = re.sub(r'<h1 id="quiz-title">.*?</h1>', '<h1 id="quiz-title">55th Final</h1>', new_content)
new_content = re.sub(r'<div class="topbar-title" id="topbar-title">.*?</div>', '<div class="topbar-title" id="topbar-title">55th Final</div>', new_content)

# 2. Inject QUIZ_CONFIG (Standardized)
new_config = 'const QUIZ_CONFIG = {\n  uid: "gyn_55th_final",\n  title: "55th Final",\n  description: "Gynecology 55th Final Exam",\n};'
new_content = re.sub(r'const\s+QUIZ_CONFIG\s*=\s*\{[\s\S]*?\};', new_config, new_content)

# 3. Inject QUESTIONS
new_content = re.sub(r'const\s+QUESTIONS\s*=\s*\[[\s\S]*?\];', questions_array, new_content)

# 4. Master Persistence Block Injection (with pendingRestoreData fix)
# Template might have let pendingRestoreData = null; elsewhere if edited
# We ensure it's at the top of the block
if 'let pendingRestoreData = null;' not in new_content:
    new_content = new_content.replace('/* ── TOAST ───────────────────────────────────────────────── */', 'let pendingRestoreData = null;\n\n/* ── TOAST ───────────────────────────────────────────────── */')

with open(target_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Success: 55th-final.html rebuilt and standardized.')
