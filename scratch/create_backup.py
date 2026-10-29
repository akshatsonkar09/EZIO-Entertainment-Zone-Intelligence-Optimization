import shutil
from pathlib import Path

backup_dir = Path("backups/pre_anime_deduplication_20261023_234000")
backup_dir.mkdir(parents=True, exist_ok=True)

# 1. Processed anime files
proc_dir = backup_dir / "data_processed"
proc_dir.mkdir(exist_ok=True)

for fname in ["anime_metadata_clean.csv", "anime_metadata.csv", "anime.pkl", "anime_tag2.pkl"]:
    src = Path("data/processed") / fname
    if src.exists():
        shutil.copy2(src, proc_dir / fname)
        print(f"Backed up {src} -> {proc_dir / fname}")

# 2. Embedding file
emb_dir = proc_dir / "embeddings"
emb_dir.mkdir(exist_ok=True)
src_emb = Path("data/processed/embeddings/anime_embeddings.npy")
if src_emb.exists():
    shutil.copy2(src_emb, emb_dir / "anime_embeddings.npy")
    print(f"Backed up {src_emb} -> {emb_dir / 'anime_embeddings.npy'}")

# 3. Chroma DB
chroma_backup = backup_dir / "chroma"
if not chroma_backup.exists():
    shutil.copytree("data/chroma", chroma_backup)
    print(f"Backed up data/chroma -> {chroma_backup}")

# 4. Source code files
code_dir = backup_dir / "code"
code_dir.mkdir(exist_ok=True)
for src_code in [Path("src/project_black_knight/retrieval.py"), Path("backend/services.py")]:
    if src_code.exists():
        shutil.copy2(src_code, code_dir / src_code.name)
        print(f"Backed up {src_code} -> {code_dir / src_code.name}")

print("Backup completed successfully!")
