import urllib.request
import zipfile
import io
import os
import sys
from pathlib import Path

def setup_node():
    node_dir = Path.home() / ".nodejs"
    node_exe = node_dir / "node.exe"
    if node_exe.exists():
        print(f"Node already exists at: {node_exe}")
        return str(node_dir)
        
    url = "https://nodejs.org/dist/v22.14.0/node-v22.14.0-win-x64.zip"
    print(f"Downloading Node.js from {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    print(f"Downloaded {len(data):,} bytes. Extracting into {node_dir}...")
    
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for member in z.infolist():
            parts = Path(member.filename).parts
            if len(parts) > 1:
                target_path = node_dir / Path(*parts[1:])
                if member.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(member) as source, open(target_path, "wb") as target:
                        target.write(source.read())
                        
    print(f"Node.js is ready at {node_exe}")
    return str(node_dir)

if __name__ == "__main__":
    setup_node()
