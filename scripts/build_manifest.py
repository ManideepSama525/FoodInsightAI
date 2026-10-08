from pathlib import Path
import hashlib, json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
files = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or ".git" in path.parts or "artifacts" in path.parts:
        continue
    data = path.read_bytes()
    files.append({
        "path": str(path.relative_to(ROOT)),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })

manifest = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "file_count": len(files),
    "files": files,
}
out = ROOT / "artifacts"
out.mkdir(exist_ok=True)
(out / "build-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Manifest written: {len(files)} files")
