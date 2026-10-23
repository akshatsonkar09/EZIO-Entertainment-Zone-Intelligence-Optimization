import os
import shutil
import hashlib
import json
from pathlib import Path

SOURCE_DIR = Path("C:/Coding/Project Black Knight")
BACKUP_LOCAL = Path("C:/Coding/Project Black Knight/backups/final_scope_corrected_audit_20261023_082500")
BACKUP_EXTERNAL = Path("C:/AI_ML/Project/Project_Black_Knight_Backups/final_scope_corrected_audit_20261023_082500")

EXCLUDE_DIRS = {".venv", ".git", "__pycache__", "backups", ".pytest_cache", ".ruff_cache"}

def sha256_file(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

print("Scanning files to backup...")
files_to_copy = []
for root, dirs, files in os.walk(SOURCE_DIR):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for file in files:
        src_path = Path(root) / file
        rel_path = src_path.relative_to(SOURCE_DIR)
        files_to_copy.append((src_path, rel_path))

print(f"Total files identified: {len(files_to_copy)}")

manifest = {}
total_bytes = 0

for src_path, rel_path in files_to_copy:
    file_hash = sha256_file(src_path)
    file_size = src_path.stat().st_size
    manifest[str(rel_path).replace("\\", "/")] = {
        "sha256": file_hash,
        "size_bytes": file_size
    }
    total_bytes += file_size

print(f"Total size: {total_bytes / (1024*1024):.2f} MB")

for dest_root in [BACKUP_EXTERNAL, BACKUP_LOCAL]:
    dest_root.mkdir(parents=True, exist_ok=True)
    print(f"Copying to {dest_root}...")
    for src_path, rel_path in files_to_copy:
        dest_path = dest_root / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest_path)
    
    # Write manifest
    manifest_path = dest_root / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    # Verify backup
    print(f"Verifying {dest_root}...")
    discrepancies = 0
    for rel_str, meta in manifest.items():
        backed_up_file = dest_root / Path(rel_str)
        if not backed_up_file.exists():
            print(f"Missing file: {rel_str}")
            discrepancies += 1
            continue
        backed_hash = sha256_file(backed_up_file)
        if backed_hash != meta["sha256"]:
            print(f"Hash mismatch for {rel_str}")
            discrepancies += 1
    if discrepancies == 0:
        print(f"SUCCESS: {dest_root} verified 100% with 0 discrepancies!")
    else:
        print(f"FAILED: {discrepancies} discrepancies found in {dest_root}!")

# Write recovery guide
recovery_guide = f"""# Recovery Procedure for Checkpoint final_scope_corrected_audit_20261023_082500

## Checkpoint Details
- Checkpoint ID: final_scope_corrected_audit_20261023_082500
- External Path: {BACKUP_EXTERNAL}
- Local Path: {BACKUP_LOCAL}
- Files Count: {len(files_to_copy)}
- Total Size: {total_bytes / (1024*1024):.2f} MB

## Restore Instructions
To restore Project Black Knight from this checkpoint:
1. Ensure the application is stopped.
2. Run PowerShell:
```powershell
$backupDir = "{BACKUP_EXTERNAL}"
$targetDir = "{SOURCE_DIR}"
Copy-Item -Path "$backupDir\\*" -Destination $targetDir -Recurse -Force
```
3. Verify integrity:
```powershell
python -c "
import json, hashlib
from pathlib import Path
manifest = json.load(open('$targetDir/manifest.json'))
for rel, meta in manifest.items():
    h = hashlib.sha256(open(Path('$targetDir')/rel, 'rb').read()).hexdigest()
    assert h == meta['sha256']
print('Restore verification successful!')
"
```
"""
with open(BACKUP_EXTERNAL / "RECOVERY.md", "w", encoding="utf-8") as f:
    f.write(recovery_guide)
with open(BACKUP_LOCAL / "RECOVERY.md", "w", encoding="utf-8") as f:
    f.write(recovery_guide)

print("Checkpoint creation and verification complete!")
