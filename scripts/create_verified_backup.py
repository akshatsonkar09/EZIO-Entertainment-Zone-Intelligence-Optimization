import os
import sys
import shutil
import hashlib
import json
import time

PROJECT_ROOT = r"c:\Coding\Project Black Knight"
EXTERNAL_BACKUP_DIR = r"C:\AI_ML\Project\Project_Black_Knight_Backups\pre_quality_improvement_20261023_010900"
LOCAL_BACKUP_DIR = r"c:\Coding\Project Black Knight\backups\pre_quality_improvement_20261023_010900"

EXCLUDE_DIRS = {
    ".venv",
    "project_black_knight",
    ".pytest_cache",
    "backups",
    "__pycache__"
}

def sha256_file(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def main():
    print(f"Starting backup from {PROJECT_ROOT}...")
    start_time = time.time()
    
    os.makedirs(EXTERNAL_BACKUP_DIR, exist_ok=True)
    os.makedirs(LOCAL_BACKUP_DIR, exist_ok=True)
    
    files_to_backup = []
    
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Modify dirs in-place to avoid excluded dirs
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.endswith(".egg-info")]
        
        rel_root = os.path.relpath(root, PROJECT_ROOT)
        parts = rel_root.split(os.sep)
        if any(p in EXCLUDE_DIRS for p in parts):
            continue
            
        for f in files:
            if f.endswith(".pyc") or f == ".DS_Store":
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, PROJECT_ROOT)
            files_to_backup.append((full_path, rel_path))

    print(f"Identified {len(files_to_backup)} files to backup.")
    
    manifest = []
    failures = 0
    
    for full_path, rel_path in files_to_backup:
        ext_dest = os.path.join(EXTERNAL_BACKUP_DIR, rel_path)
        loc_dest = os.path.join(LOCAL_BACKUP_DIR, rel_path)
        
        os.makedirs(os.path.dirname(ext_dest), exist_ok=True)
        os.makedirs(os.path.dirname(loc_dest), exist_ok=True)
        
        shutil.copy2(full_path, ext_dest)
        shutil.copy2(full_path, loc_dest)
        
        orig_hash = sha256_file(full_path)
        ext_hash = sha256_file(ext_dest)
        loc_hash = sha256_file(loc_dest)
        
        size = os.path.getsize(full_path)
        
        if orig_hash == ext_hash and orig_hash == loc_hash:
            status = "VERIFIED"
        else:
            status = "FAILED"
            failures += 1
            print(f"VERIFICATION FAILURE: {rel_path}")
            
        manifest.append({
            "rel_path": rel_path,
            "external_backup_path": ext_dest,
            "local_backup_path": loc_dest,
            "size_bytes": size,
            "sha256": orig_hash,
            "status": status
        })

    elapsed = time.time() - start_time
    print(f"Backup completed in {elapsed:.2f}s with {failures} failures.")
    
    # Save manifest
    ext_manifest_path = os.path.join(EXTERNAL_BACKUP_DIR, "manifest.json")
    loc_manifest_path = os.path.join(LOCAL_BACKUP_DIR, "manifest.json")
    
    with open(ext_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    with open(loc_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Manifest written to {ext_manifest_path} and {loc_manifest_path}")
    print(f"Total files verified: {len(manifest) - failures} / {len(manifest)}")

if __name__ == "__main__":
    main()
