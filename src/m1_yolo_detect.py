from __future__ import annotations

import json
from pathlib import Path

from section_drawer import TableSource, clean, to_float


def parse_yolo_result(raw: str) -> list[dict[str, object]]:
    detections: list[dict[str, object]] = []
    for item in clean(raw).split(";"):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            label, score = item.split(":", 1)
            confidence = to_float(score, None)
        else:
            label, confidence = item, None
        detections.append(
            {
                "class": label.strip(),
                "confidence": confidence,
                "bbox": None,
                "source": "observation_table",
            }
        )
    return detections


def run(input_path: Path, output_dir: Path, model_path: Path | None = None) -> Path:
    """M1: get YOLO-style geological feature detections.

    If a real YOLO model is available later, this module is the place to plug it in.
    For now it reads the yolo_result column from observations.csv/xlsx so the whole
    pipeline can run without a trained model.
    """

    source = TableSource(input_path)
    observations = source.read("observations")
    results = []

    for row in observations:
        detections = parse_yolo_result(row.get("yolo_result", ""))
        results.append(
            {
                "section_id": clean(row.get("section_id")),
                "point_id": clean(row.get("point_id")),
                "distance_m": to_float(row.get("distance_m"), None),
                "photo_id": clean(row.get("photo_id")),
                "photo_path": clean(row.get("photo_path")),
                "detections": detections,
                "model_path": str(model_path) if model_path else "",
                "mode": "table_fallback",
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "m1_yolo_results.json"
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    path = run(root / "data" / "tables", root / "outputs")
    print(path)

