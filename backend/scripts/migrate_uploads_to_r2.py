"""One-off script: upload everything under UPLOAD_DIR to R2, preserving relative paths as keys."""

from pathlib import Path

from app.core.config import settings
from app.services.storage_service import save_file


def main() -> None:
    if not settings.r2_configured:
        print("R2 is not configured (check backend/.env) - aborting.")
        return

    root = Path(settings.UPLOAD_DIR)
    files = [p for p in root.rglob("*") if p.is_file()]
    print(f"Found {len(files)} files under {root}")

    for path in files:
        key = path.relative_to(root).as_posix()
        save_file(key, path.read_bytes())
        print(f"uploaded: {key}")

    print("Done.")


if __name__ == "__main__":
    main()
