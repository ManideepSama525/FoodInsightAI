from pathlib import Path
from uuid import uuid4
from app.core.security import sanitize_filename

class LocalFileStorage:
    def __init__(self, root: str = "data/uploads"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    async def save(self, filename: str, content: bytes) -> str:
        safe_name = sanitize_filename(filename)
        target = self.root / safe_name
        target.write_bytes(content)
        return str(target)
