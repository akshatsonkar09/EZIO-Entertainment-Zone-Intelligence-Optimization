import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(r"c:\Coding\Project Black Knight")
TIMESTAMP = "20261023_080500"
BACKUP_NAME = f"pre_scope_corrected_audit_{TIMESTAMP}"
EXT_DIR = Path(r"C:\AI_ML\Project\Project_Black_Knight_Backups") / BACKUP_NAME
LOCAL_DIR = WORKSPACE / "backups" / BACKUP_NAME

EXT_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

INCLUDED_DIRS = {
    "concepts_learned",
    "data",
    "evaluation",
    "notebooks",
    "reports",
    "scratch",
    "scripts",
    "src",
    "tests",
}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

manifest = []
total_files = 0
total_bytes = 0

print(f"Creating verified checkpoint: {BACKUP_NAME}...")

# 1. Back up root files
for item in WORKSPACE.iterdir():
    if item.is_file() and not item.name.endswith((".tmp", ".log")):
        rel_path = item.name
        ext_dest = EXT_DIR / rel_path
        local_dest = LOCAL_DIR / rel_path
        
        shutil.copy2(item, ext_dest)
        shutil.copy2(item, local_dest)
        
        orig_hash = sha256_file(item)
        ext_hash = sha256_file(ext_dest)
        local_hash = sha256_file(local_dest)
        size = item.stat().st_size
        
        assert orig_hash == ext_hash, f"Hash mismatch for {rel_path}"
        assert orig_hash == local_hash, f"Hash mismatch for {rel_path}"
        
        manifest.append({
            "rel_path": rel_path,
            "size_bytes": size,
            "sha256": orig_hash,
            "external_backup": str(ext_dest),
            "local_backup": str(local_dest),
            "verified": True,
        })
        total_files += 1
        total_bytes += size

# 2. Back up included directories
for top_dir in sorted(INCLUDED_DIRS):
    dir_path = WORKSPACE / top_dir
    if not dir_path.exists():
        continue
    for root, dirs, files in os.walk(dir_path):
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".pytest_cache"}]
        for file in files:
            if file.endswith((".pyc", ".tmp", ".log")):
                continue
            src_path = Path(root) / file
            rel_path = src_path.relative_to(WORKSPACE)
            
            ext_dest = EXT_DIR / rel_path
            local_dest = LOCAL_DIR / rel_path
            
            ext_dest.parent.mkdir(parents=True, exist_ok=True)
            local_dest.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src_path, ext_dest)
            shutil.copy2(src_path, local_dest)
            
            orig_hash = sha256_file(src_path)
            ext_hash = sha256_file(ext_dest)
            local_hash = sha256_file(local_dest)
            size = src_path.stat().st_size
            
            assert orig_hash == ext_hash, f"Hash mismatch for {rel_path}"
            assert orig_hash == local_hash, f"Hash mismatch for {rel_path}"
            
            manifest.append({
                "rel_path": str(rel_path),
                "size_bytes": size,
                "sha256": orig_hash,
                "external_backup": str(ext_dest),
                "local_backup": str(local_dest),
                "verified": True,
            })
            total_files += 1
            total_bytes += size

manifest_data = {
    "backup_name": BACKUP_NAME,
    "created_at": datetime.now().isoformat(),
    "total_files": total_files,
    "total_bytes": total_bytes,
    "status": "VERIFIED_MATCH",
    "files": manifest,
}

with open(EXT_DIR / "manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest_data, f, indent=2)

with open(LOCAL_DIR / "manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest_data, f, indent=2)

print(f"Successfully backed up and verified {total_files} files ({total_bytes / (1024*1024):.2f} MB).")
print(f"External: {EXT_DIR}")
print(f"Local:    {LOCAL_DIR}")
