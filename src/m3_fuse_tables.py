from __future__ import annotations

import json
from pathlib import Path

from section_drawer import TableSource, clean


def run(input_path: Path, m1_results_path: Path, m2_results_path: Path, output_dir: Path) -> Path:
    """M3: fuse raw tables, YOLO detections, and Qwen-style interpretations."""

    source = TableSource(input_path)
    section_info = source.read("section_info")
    topography = source.read("topography")
    units = source.read("units")
    structures = source.read("structures")
    observations = source.read("observations")

    yolo_results = json.loads(m1_results_path.read_text(encoding="utf-8"))
    interpretations = json.loads(m2_results_path.read_text(encoding="utf-8"))
    yolo_by_point = {clean(item.get("point_id")): item for item in yolo_results}
    interp_by_point = {clean(item.get("point_id")): item for item in interpretations}

    fused_observations = []
    for row in observations:
        point_id = clean(row.get("point_id"))
        fused_observations.append(
            {
                **row,
                "yolo": yolo_by_point.get(point_id, {}),
                "interpretation": interp_by_point.get(point_id, {}),
            }
        )

    project = {
        "section_info": section_info,
        "topography": topography,
        "units": units,
        "structures": structures,
        "observations": fused_observations,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "m3_fused_project.json"
    output_path.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    path = run(
        root / "data" / "tables",
        root / "outputs" / "m1_yolo_results.json",
        root / "outputs" / "m2_qwen_interpretations.json",
        root / "outputs",
    )
    print(path)

