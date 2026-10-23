import os
import hashlib
import json
import shutil
import platform
import subprocess
from pathlib import Path

# Paths to freeze
files_to_hash = [
    "src/project_black_knight/retrieval.py",
    "src/project_black_knight/query_parser.py",
    "src/project_black_knight/query_schema.py",
    "src/project_black_knight/metadata_filter.py",
    "src/project_black_knight/text_normalizer.py",
    "final_test_queries.csv",
    "final_test_labels.csv",
    "data/processed/movie_metadata_clean.csv",
    "data/processed/anime_metadata_clean.csv",
    "data/processed/book_metadata_clean.csv",
    "pyproject.toml",
    "uv.lock"
]

manifest_lines = []

for rel_path in files_to_hash:
    p = Path(rel_path)
    if p.exists():
        hasher = hashlib.sha256()
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        h = hasher.hexdigest()
        manifest_lines.append(f"{h}  {rel_path.replace('\\', '/')}")
    else:
        print(f"Warning: file {rel_path} not found!")

# Write final_test_manifest.sha256
with open("final_test_manifest.sha256", "w", encoding="utf-8") as f:
    f.write("\n".join(manifest_lines) + "\n")

print("Saved final_test_manifest.sha256")

# Backup to local and external
LOCAL_BACKUP = Path("backups/frozen_held_out_eval_20261023")
EXTERNAL_BACKUP = Path("C:/AI_ML/Project/Project_Black_Knight_Backups/frozen_held_out_eval_20261023")

for b_dir in [LOCAL_BACKUP, EXTERNAL_BACKUP]:
    b_dir.mkdir(parents=True, exist_ok=True)
    for rel_path in files_to_hash:
        src = Path(rel_path)
        if src.exists():
            dst = b_dir / src
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    shutil.copy2("final_test_manifest.sha256", b_dir / "final_test_manifest.sha256")
    print(f"Frozen backup created at {b_dir}")

# Collect environment metadata
env_info = {
    "os": platform.platform(),
    "python_version": platform.python_version(),
    "processor": platform.processor(),
    "machine": platform.machine(),
    "embedding_model": "all-MiniLM-L6-v2",
    "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "chroma_version": "0.5.x",
    "architectures_evaluated": ["domain_routed", "all_cross_encoder"],
    "deterministic_settings": {
        "bm25": "Deterministic token frequency",
        "chromadb": "Deterministic cosine similarity on frozen embeddings",
        "cross_encoder": "PyTorch CPU deterministic eval mode",
        "tie_breaking": "Ascending canonical item ID string"
    }
}

with open("scratch/frozen_environment_meta.json", "w", encoding="utf-8") as f:
    json.dump(env_info, f, indent=2)

print("Environment frozen and recorded.")
