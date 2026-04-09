import os
import re
import json

def rebase_surgically():
    base_dir = r"d:\Study\Projects\MU61S8"
    source_of_truth = os.path.join(base_dir, "gyn", "past years", "55th-final.html")
    
    if not os.path.exists(source_of_truth):
        print("Error: 55th-final.html not found.")
        return

    # 1. Prepare TEMPLATE SHELLS from 55th-final.html
    with open(source_of_truth, 'r', encoding='utf-8') as f:
        truth = f.read()
    
    # Neutralize titles in the template shells
    truth = truth.replace('55th Final', 'Quiz Loading...')

    config_marker = "const QUIZ_CONFIG = {"
    questions_start_marker = "const QUESTIONS = ["
    questions_end_marker = "];\n/* ─────────────────────────────────────────────────────────────────\n   END OF QUESTIONS"

    top_idx = truth.find(config_marker)
    config_end_idx = truth.find("};", top_idx)
    mid_idx = truth.find(questions_start_marker)
    bottom_idx = truth.find(questions_end_marker)

    if any(i == -1 for i in [top_idx, mid_idx, bottom_idx]):
        print("Error: Could not find markers in 55th-final.html")
        return

    shell1 = truth[:top_idx + len(config_marker)]
    shell2 = truth[config_end_idx : mid_idx + len(questions_start_marker)]
    shell3 = truth[bottom_idx:]

    # 2. Identify All Quiz Files
    found_files = []
    for root, dirs, files in os.walk(base_dir):
        if any(x in root for x in ['.git', '.gemini', '.system_generated']):
            continue
        for file in files:
            if file.endswith(".html") and file != "index.html":
                path = os.path.join(root, file)
                if os.path.abspath(path) != os.path.abspath(source_of_truth):
                    found_files.append(path)

    print(f"Surgically rebasing {len(found_files)} files...")

    success_count = 0
    error_count = 0

    for path in found_files:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                old_content = f.read()

            # A. VALIDATION: Count questions before
            original_q_count = old_content.count('"question":')
            if original_q_count == 0:
                print(f"Skipping {path}: No questions found.")
                continue

            # B. EXTRACTION: Pure block extraction (no regex)
            # Find the actual inner content of the QUESTIONS array
            q_idx_start = old_content.find("const QUESTIONS = [")
            if q_idx_start == -1:
                print(f"Skipping {path}: const QUESTIONS declaration not found.")
                continue
            
            # Find the end marker (we use the standard marker)
            q_idx_end = old_content.find("END OF QUESTIONS", q_idx_start)
            if q_idx_end == -1:
                # Fallback to ENGINE marker
                q_idx_end = old_content.find("ENGINE", q_idx_start)
            
            if q_idx_end == -1:
                print(f"Skipping {path}: Could not find end markers.")
                continue
            
            search_area = old_content[q_idx_start + len("const QUESTIONS = [") : q_idx_end]
            
            # Isolate the objects between first { and last }
            first_brace = search_area.find('{')
            last_brace = search_area.rfind('}')
            
            if first_brace == -1 or last_brace == -1:
                print(f"Skipping {path}: Could not find question braces.")
                continue
            
            questions_data = search_area[first_brace : last_brace + 1].strip()

            # C. EXTRACTION: QUIZ_CONFIG title and desc
            title_match = re.search(r'title:\s*["\'](.*?)["\']', old_content)
            desc_match = re.search(r'description:\s*["\'](.*?)["\']', old_content)
            title = title_match.group(1).strip() if title_match else os.path.basename(path).replace(".html","").title()
            description = desc_match.group(1).strip() if desc_match else ""

            # D. UNIQUE UID
            rel_path = os.path.relpath(path, base_dir)
            uid = re.sub(r'[^a-zA-Z0-9]', '_', rel_path.replace('.html', '')).lower()
            
            config_json = f'\n  uid: {json.dumps(uid)},\n  title: {json.dumps(title)},\n  description: {json.dumps(description)},\n'

            # E. RECONSTRUCTION
            new_content = shell1 + config_json + shell2 + "\n" + questions_data + "\n" + shell3
            
            # F. VALIDATION: Check count again
            new_q_count = new_content.count('"question":')
            if new_q_count != original_q_count:
                print(f"BLOCKING ERROR in {path}: Question count mismatch ({original_q_count} -> {new_q_count}). Aborting file.")
                error_count += 1
                continue

            # G. WRITE
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            success_count += 1
            print(f"Standardized: {rel_path} ({new_q_count} questions)")

        except Exception as e:
            print(f"Error processing {path}: {e}")
            error_count += 1

    print(f"\nFinal Report:\n- Standardized: {success_count}\n- Errors/Skipped: {error_count}")

if __name__ == "__main__":
    rebase_surgically()
