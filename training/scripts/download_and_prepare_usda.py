from __future__ import annotations

import hashlib
import json
import random
import shutil
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "research" / "datasets" / "usda_fooddata_central"
RAW = DATA_ROOT / "raw"
META = DATA_ROOT / "metadata"
PROCESSED = DATA_ROOT / "processed"
LM = ROOT / "research" / "dataset" / "foodinsight_lm"

URL = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_json_2026-04-30.zip"
ARCHIVE = RAW / "FoodData_Central_foundation_food_json_2026-04-30.zip"
SEED = 20261001

TARGET_NUTRIENTS = {
    "Protein",
    "Water",
    "Total lipid (fat)",
    "Carbohydrate, by difference",
    "Fiber, total dietary",
    "Calcium, Ca",
    "Iron, Fe",
    "Magnesium, Mg",
    "Phosphorus, P",
    "Potassium, K",
    "Sodium, Na",
    "Zinc, Zn",
    "Vitamin C, total ascorbic acid",
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def download():
    RAW.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        print("Downloading official USDA Foundation Foods release...")
        urllib.request.urlretrieve(URL, ARCHIVE)
    print("USDA archive:", ARCHIVE)
    print("SHA-256:", sha256(ARCHIVE))

def extract() -> Path:
    extract_dir = RAW / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE) as z:
        z.extractall(extract_dir)
        candidates = list(extract_dir.rglob("*.json"))
    if not candidates:
        raise RuntimeError("No USDA JSON file found after extraction.")
    return candidates[0]

def normalize(src: Path) -> list[dict]:
    data = json.loads(src.read_text(encoding="utf-8"))
    foods = data.get("FoundationFoods", data if isinstance(data, list) else [])
    out = []
    invalid = 0
    for food in foods:
        if not isinstance(food, dict) or not food.get("fdcId") or not food.get("description"):
            invalid += 1
            continue
        nutrients = []
        for fn in food.get("foodNutrients", []):
            nutrient = fn.get("nutrient") or {}
            name = nutrient.get("name")
            if not name:
                continue
            nutrients.append({
                "id": fn.get("id"),
                "name": name,
                "number": nutrient.get("number"),
                "unit": nutrient.get("unitName"),
                "amount": fn.get("amount"),
                "data_points": fn.get("dataPoints"),
                "derivation": (fn.get("foodNutrientDerivation") or {}).get("description"),
                "min": fn.get("min"),
                "max": fn.get("max"),
                "median": fn.get("median"),
            })
        portions = []
        for p in food.get("foodPortions", []):
            portions.append({
                "amount": p.get("amount"),
                "unit": p.get("measureUnit", {}).get("name"),
                "gram_weight": p.get("gramWeight"),
                "modifier": p.get("modifier"),
                "sequence_number": p.get("sequenceNumber"),
            })
        category = (food.get("foodCategory") or {}).get("description")
        out.append({
            "food_id": str(food["fdcId"]),
            "fdc_id": food["fdcId"],
            "description": food["description"],
            "category": category,
            "data_type": food.get("dataType"),
            "publication_date": food.get("publicationDate"),
            "is_historical_reference": food.get("isHistoricalReference", False),
            "nutrients": nutrients,
            "portions": portions,
            "input_foods": [
                {"id": x.get("id"), "food_description": x.get("foodDescription"), "ingredient_description": x.get("ingredientDescription")}
                for x in food.get("inputFoods", []) if isinstance(x, dict)
            ],
            "provenance": {
                "publisher": "USDA Agricultural Research Service",
                "source": "FoodData Central Foundation Foods",
                "release": "2026-04-30",
                "url": "https://fdc.nal.usda.gov/download-datasets/",
                "license": "CC0 1.0 Universal / Public Domain",
            },
        })
    return out, invalid

def evidence_for(food: dict, nutrient_name: str) -> dict | None:
    for n in food["nutrients"]:
        if n["name"] == nutrient_name and n["amount"] is not None:
            return n
    return None

def make_tasks(foods: list[dict]) -> list[dict]:
    rng = random.Random(SEED)
    tasks = []
    for food in foods:
        usable = [(n, evidence_for(food, n)) for n in TARGET_NUTRIENTS]
        usable = [(n, e) for n, e in usable if e is not None]
        for nutrient_name, ev in usable:
            unit = ev.get("unit") or ""
            amount = ev.get("amount")
            context = (
                f"Food: {food['description']}\n"
                f"Category: {food.get('category') or 'Unknown'}\n"
                f"USDA nutrient: {nutrient_name} = {amount} {unit} per 100 g."
            )
            tasks.append({
                "id": f"qa_{food['food_id']}_{re.sub(r'[^a-z0-9]+','_',nutrient_name.lower()).strip('_')}",
                "source": "USDA FoodData Central Foundation Foods 2026-04-30",
                "food_fdc_id": food["food_id"],
                "task_family": "direct_evidence_qa",
                "question": f"How much {nutrient_name} does {food['description']} contain per 100 g?",
                "context": context,
                "answer": f"{food['description']} contains {amount} {unit} of {nutrient_name} per 100 g.",
                "claims": [f"{food['description']} contains {amount} {unit} of {nutrient_name} per 100 g."],
                "evidence_ids": [f"{food['food_id']}:{ev.get('id')}"],
                "provenance": food["provenance"],
            })
        if food.get("category"):
            tasks.append({
                "id": f"category_{food['food_id']}",
                "source": "USDA FoodData Central Foundation Foods 2026-04-30",
                "food_fdc_id": food["food_id"],
                "task_family": "food_category_evidence",
                "question": f"What USDA food category is {food['description']} listed under?",
                "context": f"Food: {food['description']}\nUSDA category: {food['category']}",
                "answer": f"{food['description']} is listed under {food['category']}.",
                "claims": [f"{food['description']} is listed under {food['category']}."],
                "evidence_ids": [food["food_id"]],
                "provenance": food["provenance"],
            })
        if food.get("portions"):
            p = next((p for p in food["portions"] if p.get("gram_weight")), None)
            if p:
                tasks.append({
                    "id": f"portion_{food['food_id']}",
                    "source": "USDA FoodData Central Foundation Foods 2026-04-30",
                    "food_fdc_id": food["food_id"],
                    "task_family": "portion_reasoning",
                    "question": f"What gram weight does the USDA record give for one listed portion of {food['description']}?",
                    "context": f"Food: {food['description']}\nPortion: {p}",
                    "answer": f"One listed portion has a gram weight of {p['gram_weight']} g.",
                    "claims": [f"One listed portion has a gram weight of {p['gram_weight']} g."],
                    "evidence_ids": [food["food_id"]],
                    "provenance": food["provenance"],
                })
    # exact question deduplication
    dedup = {}
    for t in tasks:
        dedup[t["question"].strip().lower()] = t
    tasks = list(dedup.values())
    rng.shuffle(tasks)
    return tasks

def split_by_food(tasks: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    groups = sorted({str(t["food_fdc_id"]) for t in tasks})
    rng = random.Random(SEED)
    rng.shuffle(groups)
    n = len(groups)
    n_train = max(1, int(n * 0.8))
    n_val = max(1, int(n * 0.1))
    train_ids = set(groups[:n_train])
    val_ids = set(groups[n_train:n_train+n_val])
    test_ids = set(groups[n_train+n_val:])
    train = [t for t in tasks if str(t["food_fdc_id"]) in train_ids]
    val = [t for t in tasks if str(t["food_fdc_id"]) in val_ids]
    test = [t for t in tasks if str(t["food_fdc_id"]) in test_ids]
    for rows, split in [(train,"train"),(val,"validation"),(test,"test")]:
        for t in rows: t["split"] = split
    return train, val, test

def write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def main():
    download()
    source = extract()
    foods, invalid = normalize(source)
    META.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    normalized = PROCESSED / "foodinsight_usda_foundation.jsonl"
    write_jsonl(normalized, foods)
    tasks = make_tasks(foods)
    train, val, test = split_by_food(tasks)
    write_jsonl(LM / "foodinsight_usda_v0_2.jsonl", train + val + test)
    write_jsonl(LM / "foodinsight_usda_train.jsonl", train)
    write_jsonl(LM / "foodinsight_usda_validation.jsonl", val)
    write_jsonl(LM / "foodinsight_usda_test.jsonl", test)
    report = {
        "release": "2026-04-30",
        "source_url": "https://fdc.nal.usda.gov/download-datasets/",
        "archive_sha256": sha256(ARCHIVE),
        "foods_normalized": len(foods),
        "invalid_food_records": invalid,
        "tasks": len(tasks),
        "train": len(train),
        "validation": len(val),
        "test": len(test),
        "food_level_split_isolation": True,
        "task_families": sorted({t["task_family"] for t in tasks}),
        "generated_seed": SEED,
    }
    (META / "download_and_task_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
