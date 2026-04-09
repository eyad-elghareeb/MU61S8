import os
import re
import json

def rebase_all_quizzes():
    base_dir = r"d:\Study\Projects\MU61S8"
    source_of_truth = os.path.join(base_dir, "gyn", "past years", "55th-final.html")
    
    if not os.path.exists(source_of_truth):
        print(f"Error: Source of truth not found at {source_of_truth}")
        return

    with open(source_of_truth, 'r', encoding='utf-8') as f:
        truth_content = f.read()
    
    # 1. Prepare TEMPLATE PARTS
    config_marker = "const QUIZ_CONFIG = {"
    questions_start_marker = "const QUESTIONS = ["
    questions_end_marker = "];\n/* ─────────────────────────────────────────────────────────────────\n   END OF QUESTIONS"

    top_idx = truth_content.find(config_marker)
    mid_idx = truth_content.find(questions_start_marker)
    bottom_idx = truth_content.find(questions_end_marker) + 1 # Point to ';'

    if any(i == -1 for i in [top_idx, mid_idx, bottom_idx]):
        print("Error: Markers not found in source of truth")
        return

    template_top = truth_content[:top_idx + len(config_marker)]
    config_end_idx = truth_content.find("};", top_idx)
    template_mid = truth_content[config_end_idx : mid_idx + len(questions_start_marker)]
    template_bottom = truth_content[bottom_idx:]

    # 2. Identify Files
    found_files = []
    for root, dirs, files in os.walk(base_dir):
        if any(x in root for x in ['.git', '.gemini', '.system_generated']):
            continue
        for file in files:
            if file.endswith(".html") and file != "index.html":
                found_files.append(os.path.join(root, file))

    print(f"Fixing and Rebasing {len(found_files)} files...")

    success_count = 0
    for path in found_files:
        if os.path.abspath(path) == os.path.abspath(source_of_truth):
            continue

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 3. ROBUST EXTRACTION
            # Find start of QUESTIONS array
            q_start_match = re.search(r'const\s+QUESTIONS\s*=\s*\[', content)
            if not q_start_match:
                continue
                
            # Find the END OF QUESTIONS marker (this is consistent across our files)
            q_end_marker_pos = content.find("END OF QUESTIONS")
            if q_end_marker_pos == -1:
                # Fallback to ENGINE marker
                q_end_marker_pos = content.find("ENGINE")
                if q_end_marker_pos == -1:
                    print(f"Skipping {path}: Could not find end markers.")
                    continue
            
            # Backtrack from marker to find the last ]
            # We look for the last ] before the marker
            search_area = content[q_start_match.end() : q_end_marker_pos]
            last_bracket = search_area.rfind(']')
            if last_bracket == -1:
                # If no closing bracket found, we might have a totally broken file
                # We'll just take the whole search area and let the recursive cleaner handle it
                raw_inner = search_area.strip()
            else:
                raw_inner = search_area[:last_bracket].strip()
            
            # 4. RECURSIVE DATA CLEANING
            # Strip any and all outer brackets until we reach the object list
            while raw_inner.startswith('[') or raw_inner.endswith(']'):
                raw_inner = raw_inner.strip()
                if raw_inner.startswith('['):
                    raw_inner = raw_inner[1:].strip()
                if raw_inner.endswith(']'):
                    raw_inner = raw_inner[:-1].strip()

            # Extract Title/Desc
            title_match = re.search(r'title:\s*["\'](.*?)["\']', content)
            desc_match = re.search(r'description:\s*["\'](.*?)["\']', content)
            title = title_match.group(1).strip() if title_match else os.path.basename(path).replace(".html", "")
            description = desc_match.group(1).strip() if desc_match else ""

            # 5. UID and Config
            rel_path = os.path.relpath(path, base_dir)
            uid = re.sub(r'[^a-zA-Z0-9]', '_', rel_path.replace('.html', '')).lower()
            
            config_json = f'\n  uid: {json.dumps(uid)},\n  title: {json.dumps(title)},\n  description: {json.dumps(description)},\n'
            
            # 6. RECONSTRUCT
            new_content = template_top + config_json + template_mid + "\n" + raw_inner + "\n" + template_bottom
            
            # Final Pass: Ensure IDs are unique and toast is clean
            new_content = re.sub(r'<div class="toast.*?" id="toast">.*?</div>', '<div class="toast" id="toast"></div>', new_content, flags=re.DOTALL)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            success_count += 1
        except Exception as e:
            print(f"Error {path}: {e}")

    print(f"Completed: {success_count} files fixed and rebased.")

if __name__ == "__main__":
    rebase_all_quizzes()
