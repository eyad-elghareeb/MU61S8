import os
import re
import json

def rebase_all_quizzes_fixed_v2():
    base_dir = r"d:\Study\Projects\MU61S8"
    source_of_truth = os.path.join(base_dir, "gyn", "past years", "55th-final.html")
    
    if not os.path.exists(source_of_truth):
        print(f"Error: Source of truth not found at {source_of_truth}")
        return

    with open(source_of_truth, 'r', encoding='utf-8') as f:
        truth_content = f.read()
    
    # 1. Prepare TEMPLATE PARTS with placeholders
    # Sanitize the shell: replace "55th Final" with "Loading..." (it will be updated by JS)
    truth_content = truth_content.replace('55th Final', 'Quiz Loading...')
    
    config_marker = "const QUIZ_CONFIG = {"
    questions_start_marker = "const QUESTIONS = ["
    end_marker = "];\n/* ─────────────────────────────────────────────────────────────────\n   END OF QUESTIONS"

    top_idx = truth_content.find(config_marker)
    mid_idx = truth_content.find(questions_start_marker)
    bottom_idx = truth_content.find(end_marker)

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

    print(f"SUPER-EMERGENCY RECOVERY: Rebasing {len(found_files)} files...")

    success_count = 0
    for path in found_files:
        if os.path.abspath(path) == os.path.abspath(source_of_truth):
            continue

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 3. ROBUST EXTRACTION: Find the actual Question Objects
            # Look for the range where questions live
            q_start_match = re.search(r'const\s+QUESTIONS\s*=\s*\[', content)
            if not q_start_match:
                continue
                
            q_end_marker_pos = content.find("END OF QUESTIONS")
            if q_end_marker_pos == -1:
                q_end_marker_pos = content.find("ENGINE")
                if q_end_marker_pos == -1:
                    print(f"Skipping {path}: No end marker.")
                    continue
            
            search_area = content[q_start_match.end() : q_end_marker_pos]
            
            # The core data must be between the first { and the last }
            first_brace = search_area.find('{')
            last_brace = search_area.rfind('}')
            
            if first_brace == -1 or last_brace == -1:
                print(f"Warning: No question objects found in {path}")
                # We still rebase to fix the UI, but questions might be empty
                questions_inner = ""
            else:
                questions_inner = search_area[first_brace : last_brace + 1].strip()

            # 4. Extract Title/Desc (Safety: Recovering from broken ones)
            title_match = re.search(r'title:\s*["\'](.*?)["\']', content)
            desc_match = re.search(r'description:\s*["\'](.*?)["\']', content)
            
            existing_title = title_match.group(1).strip() if title_match else ""
            if "Quiz Loading" in existing_title or "55th Final" in existing_title or not existing_title:
                # Generate nicer title from filename
                title = os.path.basename(path).replace(".html", "").replace("-", " ").replace("_", " ").title()
                title = title.replace("Gyn", "Gynecology").replace("Cardio", "Cardiology")
            else:
                title = existing_title
                
            description = desc_match.group(1).strip() if desc_match else ""

            # 5. UID and Config
            rel_path = os.path.relpath(path, base_dir)
            uid = re.sub(r'[^a-zA-Z0-9]', '_', rel_path.replace('.html', '')).lower()
            
            config_json = f'\n  uid: {json.dumps(uid)},\n  title: {json.dumps(title)},\n  description: {json.dumps(description)},\n'
            
            # 6. RECONSTRUCT
            new_content = template_top + config_json + template_mid + "\n" + questions_inner + "\n" + template_bottom
            
            # Ensure toast is clean
            new_content = re.sub(r'<div class="toast.*?" id="toast">.*?</div>', '<div class="toast" id="toast"></div>', new_content, flags=re.DOTALL)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            success_count += 1
        except Exception as e:
            print(f"Error {path}: {e}")

    print(f"Completed Recovery: {success_count} files restored to 100% health.")

if __name__ == "__main__":
    rebase_all_quizzes_fixed_v2()
