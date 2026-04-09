import os
import re

def standardize_persistence():
    base_dir = r"d:\Study\Projects\MU61S8"
    template_path = r"d:\Study\Projects\QuizTool\quiz-template.html"
    
    # 1. Extract Golden Block from Template
    with open(template_path, 'r', encoding='utf-8') as f:
        template_text = f.read()
    
    # Look for the start of the persistence block
    start_marker = "/* ── TOAST ───────────────────────────────────────────────── */"
    end_marker = "checkSavedProgress();"
    
    start_idx = template_text.find(start_marker)
    end_idx = template_text.find(end_marker, start_idx) + len(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print(f"Error: Could not find golden block in template at {template_path}")
        return

    golden_block = template_text[start_idx:end_idx]
    
    # 2. Iterate through all quiz files
    found_files = []
    for root, dirs, files in os.walk(base_dir):
        # Only skip hidden folders or system folders
        if any(x in root for x in ['.git', '.gemini', '.system_generated']):
            continue
            
        for file in files:
            if file.endswith(".html") and file != "index.html":
                file_path = os.path.join(root, file)
                # Check if it's a quiz (has QUESTIONS array)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        if "const QUESTIONS =" in f.read():
                            found_files.append(file_path)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    print(f"Processing {len(found_files)} quiz files...")
    
    success_count = 0
    failure_files = []
    for path in found_files:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find the persistence block start
            target_start_idx = content.find("/* ── TOAST")
            if target_start_idx == -1:
                target_start_idx = content.find("function showToast")
                
            if target_start_idx == -1:
                failure_files.append((path, "Persistence marker not found"))
                continue
                
            last_script_end = content.find("</script>", target_start_idx)
            if last_script_end == -1:
                failure_files.append((path, "Script end not found"))
                continue
                
            new_content = content[:target_start_idx] + golden_block + "\n" + content[last_script_end:]
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            success_count += 1
        except Exception as e:
            failure_files.append((path, str(e)))

    print(f"Successfully standardized: {success_count} / {len(found_files)}")
    if failure_files:
        print(f"\nFailed/Skipped files ({len(failure_files)}):")
        for f, reason in failure_files:
            print(f"  - {f}: {reason}")

if __name__ == "__main__":
    standardize_persistence()
