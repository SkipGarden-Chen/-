from __future__ import annotations

import json
from pathlib import Path

from section_drawer import TableSource, clean, to_float


def feature_names(detections: list[dict[str, object]]) -> str:
    names = [str(item.get("class", "")).strip() for item in detections if item.get("class")]
    return ";".join(names)


def build_interpretation(row: dict[str, str], detections: list[dict[str, object]]) -> dict[str, object]:
    lithology = clean(row.get("field_lithology"), "未定岩性")
    qwen_description = clean(row.get("qwen_description"), "暂无多模态解释")
    features = feature_names(detections)
    summary = f"{lithology}。{qwen_description}"
    if features:
        summary += f" AI识别到的主要现象包括：{features}。"

    return {
        "section_id": clean(row.get("section_id")),
        "point_id": clean(row.get("point_id")),
        "distance_m": to_float(row.get("distance_m"), None),
        "lithology_ai": lithology,
        "features": features,
        "qwen_description": qwen_description,
        "interpretation": summary,
        "human_note": clean(row.get("human_note")),
        "used_in_section": clean(row.get("used_in_section"), "yes"),
    }


def run(input_path: Path, m1_results_path: Path, output_dir: Path) -> Path:
    """M2: convert detections and observation notes into geological interpretation."""

    source = TableSource(input_path)
    observations = source.read("observations")
    yolo_results = json.loads(m1_results_path.read_text(encoding="utf-8"))
    detections_by_point = {item["point_id"]: item.get("detections", []) for item in yolo_results}

    interpretations = [
        build_interpretation(row, detections_by_point.get(clean(row.get("point_id")), []))
        for row in observations
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "m2_qwen_interpretations.json"
    output_path.write_text(json.dumps(interpretations, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    path = run(root / "data" / "tables", root / "outputs" / "m1_yolo_results.json", root / "outputs")
    print(path)

