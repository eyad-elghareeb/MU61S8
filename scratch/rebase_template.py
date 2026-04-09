import os
import re

source_of_truth = r"d:\Study\Projects\MU61S8\gyn\past years\55th-final.html"
target_template = r"d:\Study\Projects\QuizTool\quiz-template.html"

if not os.path.exists(source_of_truth):
    print("Error: Source of truth not found.")
    exit(1)

with open(source_of_truth, 'r', encoding='utf-8') as f:
    content = f.read()

# Markers
config_start = 'const QUIZ_CONFIG = {'
questions_start = 'const QUESTIONS = ['
end_marker = '];\n/* ─────────────────────────────────────────────────────────────────\n   END OF QUESTIONS'

top_idx = content.find(config_start)
config_end_idx = content.find('};', top_idx)
mid_idx = content.find(questions_start)
bottom_idx = content.find(end_marker) + 1 # Point to ';'

if any(i == -1 for i in [top_idx, mid_idx, bottom_idx]):
    print("Error: Markers not found in source.")
    exit(1)

# Extract Shells
top_shell = content[:top_idx + len(config_start)]
mid_shell = content[config_end_idx : mid_idx + len(questions_start)]
bottom_shell = content[bottom_idx:]

# Construct Generic Data
generic_config = '\n  uid: "",\n  title: "General Knowledge Quiz",\n  description: "Test your knowledge across science, history, geography, and more.",\n'
generic_questions = """
  {
    question: "What is the chemical symbol for Gold?",
    options: ["Gd", "Go", "Au", "Ag"],
    correct: 2,
    explanation: "Gold's symbol 'Au' comes from the Latin word 'Aurum'. It has been used for thousands of years as currency and in jewellery."
  },
  {
    question: "Which planet in our solar system has the most moons?",
    options: ["Jupiter", "Saturn", "Uranus", "Neptune"],
    correct: 1,
    explanation: "As of 2023, Saturn has 146 confirmed moons, overtaking Jupiter."
  }
""".strip()

new_template = top_shell + generic_config + mid_shell + "\n" + generic_questions + "\n" + bottom_shell

# Fix absolute paths to relative
new_template = re.sub(r'href="\.\./index\.html"', 'href="index.html"', new_template)

with open(target_template, 'w', encoding='utf-8') as f:
    f.write(new_template)

print("Successfully rebased quiz-template.html on 55th-final structure.")
