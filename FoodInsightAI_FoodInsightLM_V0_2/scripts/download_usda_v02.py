from __future__ import annotations
import hashlib, json, shutil, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "research" / "datasets" / "usda"
RAW.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "foundation_2026_04": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_json_2026-04-30.zip",
    "fndds_2021_2023": "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_fndds_2021-2023_json.zip",
}

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""): h.update(b)
    return h.hexdigest()

def main():
    manifest=[]
    for key,url in SOURCES.items():
        out=RAW/(key+".zip")
        if not out.exists():
            print("Downloading", key)
            urllib.request.urlretrieve(url, out)
        with zipfile.ZipFile(out) as z:
            z.extractall(RAW/key)
        manifest.append({
            "dataset": key,
            "url": url,
            "archive": str(out),
            "sha256": sha256(out),
            "license": "USDA FoodData Central public-domain/CC0 data",
        })
    (RAW/"download_manifest.json").write_text(
        json.dumps(manifest,indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest,indent=2))
    print("USDA V0.2 ACQUISITION: OK")

if __name__ == "__main__":
    main()
