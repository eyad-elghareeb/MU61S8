import os
import re

def assign_unique_uids():
    base_dir = r"d:\Study\Projects\MU61S8"
    
    found_files = []
    for root, dirs, files in os.walk(base_dir):
        if any(x in root for x in ['.git', '.gemini', '.system_generated']):
            continue
            
        for file in files:
            if file.endswith(".html") and file != "index.html":
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        if "const QUIZ_CONFIG =" in f.read():
                            found_files.append(file_path)
                except Exception:
                    pass

    print(f"Assigning UIDs to {len(found_files)} quiz files...")
    
    count = 0
    for path in found_files:
        # Generate a unique slug from path
        # Example: Cardio\57th end round 1.html -> cardio_57th_end_round_1
        rel_path = os.path.relpath(path, base_dir)
        uid_slug = re.sub(r'[^a-zA-Z0-9]', '_', rel_path.replace('.html', '')).lower()
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Regex to match the QUIZ_CONFIG object and its content
        # We look for the opening brace of QUIZ_CONFIG
        config_pattern = re.compile(r'(const\s+QUIZ_CONFIG\s*=\s*\{)([\s\S]*?)(\};)')
        match = config_pattern.search(content)
        
        if match:
            header, body, footer = match.groups()
            
            # Check if UID already exists
            if 'uid:' in body:
                # If it already has a UID that isn't empty or generic, we might want to keep it
                # But to follow "assign a unique UID to every file", we'll ensure it's standardized
                # Unless it's 55th which we know is good.
                if "55th-final" in path:
                    continue
                
                # Replace existing UID
                new_body = re.sub(r'uid:\s*["\'].*?["\']\s*,?', f'uid: "{uid_slug}",', body)
            else:
                # Inject UID at the start of the body
                # Add a newline and indentation if possible
                new_body = f'\n  uid: "{uid_slug}",' + body
            
            new_content = content[:match.start()] + header + new_body + footer + content[match.end():]
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            count += 1

    print(f"Successfully assigned UIDs to {count} files.")

if __name__ == "__main__":
    assign_unique_uids()
