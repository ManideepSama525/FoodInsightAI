from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DATASET_ROOT = ROOT / "research" / "datasets" / "usda"

DATASETS = {
    "foundation_2026_04": {
        "url": (
            "https://fdc.nal.usda.gov/fdc-datasets/"
            "FoodData_Central_foundation_food_json_2026-04-30.zip"
        ),
        "archive": "FoodData_Central_foundation_food_json_2026-04-30.zip",
    },
    "fndds_2021_2023": {
        "url": (
            "https://fdc.nal.usda.gov/fdc-datasets/"
            "FoodData_Central_survey_food_json_2024-10-31.zip"
        ),
        "archive": "FoodData_Central_survey_food_json_2024-10-31.zip",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading: {url}")
    print(f"Destination: {destination}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FoodInsightAI/0.2 dataset acquisition"
        },
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        total = response.headers.get("Content-Length")

        if total:
            total = int(total)

        with destination.open("wb") as handle:
            copied = 0

            while True:
                chunk = response.read(1024 * 1024)

                if not chunk:
                    break

                handle.write(chunk)
                copied += len(chunk)

                if total:
                    percent = copied * 100 / total
                    print(
                        f"\r  {copied:,} / {total:,} bytes "
                        f"({percent:.1f}%)",
                        end="",
                        flush=True,
                    )

    print()


def extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)

    print(f"Extracting: {archive.name}")

    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(destination)

    print(f"Extracted to: {destination}")


def main() -> None:
    DATASET_ROOT.mkdir(parents=True, exist_ok=True)

    manifest = {
        "project": "FoodInsightAI",
        "dataset_pipeline": "FoodInsight-LM V0.2",
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "USDA FoodData Central",
        "datasets": {},
    }

    for name, spec in DATASETS.items():
        destination = DATASET_ROOT / name
        archive = destination / spec["archive"]

        print()
        print("=" * 72)
        print(name)
        print("=" * 72)

        # Foundation was already extracted successfully.
        # Only download the archive if it is not already present.
        if not archive.exists():
            try:
                download(spec["url"], archive)
            except Exception as exc:
                print(f"DOWNLOAD FAILED: {exc}")
                print()
                print(
                    "The existing files were not deleted. "
                    "Fix the URL or network issue and rerun."
                )
                raise

        else:
            print(f"Archive already exists: {archive}")

        digest = sha256(archive)

        print(f"SHA-256: {digest}")

        extract_marker = destination / ".extracted"

        if not extract_marker.exists():
            extract_archive(archive, destination)
            extract_marker.write_text(
                datetime.now(timezone.utc).isoformat(),
                encoding="utf-8",
            )
        else:
            print("Archive already extracted.")

        manifest["datasets"][name] = {
            "url": spec["url"],
            "archive": str(archive.relative_to(ROOT)),
            "sha256": digest,
            "size_bytes": archive.stat().st_size,
            "extracted_directory": str(destination.relative_to(ROOT)),
            "publisher": "USDA Agricultural Research Service",
            "source": "USDA FoodData Central",
            "license": "USDA FoodData Central public-domain/CC0 data",
        }

    manifest_path = DATASET_ROOT / "download_manifest.json"

    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("USDA DATA ACQUISITION: OK")
    print("=" * 72)
    print(f"Manifest: {manifest_path}")
    print()
    print("Next step: inspect the downloaded files before normalization.")


if __name__ == "__main__":
    main()