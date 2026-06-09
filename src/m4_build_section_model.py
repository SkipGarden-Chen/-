from __future__ import annotations

import json
from pathlib import Path

from section_drawer import SvgBuilder, Topography, load_project, to_float


def validate_units(units: list[dict[str, str]]) -> list[str]:
    warnings: list[str] = []
    required = ["unit_id", "from_m", "to_m", "lithology_final", "thickness_m", "dip_angle_deg"]
    for row in units:
        unit_id = row.get("unit_id", "UNKNOWN")
        for field in required:
            if not str(row.get(field, "")).strip():
                warnings.append(f"{unit_id} 缺少字段 {field}")
        start = to_float(row.get("from_m"), None)
        end = to_float(row.get("to_m"), None)
        if start is not None and end is not None and end <= start:
            warnings.append(f"{unit_id} 的 to_m 必须大于 from_m")
        thickness = to_float(row.get("thickness_m"), None)
        if thickness is not None and thickness <= 0:
            warnings.append(f"{unit_id} 的 thickness_m 必须大于 0")
    return warnings


def run(input_path: Path, output_dir: Path) -> Path:
    """M4: build a section model and validate the data before drawing."""

    section, topo, units, structures = load_project(input_path)
    builder = SvgBuilder(section, topo, units, structures)
    warnings = validate_units(units)

    model = {
        "section": section,
        "topography_point_count": len(topo.points),
        "unit_count": len(units),
        "structure_count": len(structures),
        "warnings": warnings,
        "units": [
            {
                "unit_id": row.get("unit_id"),
                "from_m": to_float(row.get("from_m"), None),
                "to_m": to_float(row.get("to_m"), None),
                "lithology": row.get("lithology_final"),
                "thickness_m": to_float(row.get("thickness_m"), None),
                "dip_angle_deg": to_float(row.get("dip_angle_deg"), None),
                "draw_dip_deg": builder.bedding_dip_for_render(
                    to_float(row.get("dip_direction_deg"), None),
                    to_float(row.get("dip_angle_deg"), 0.0) or 0.0,
                ),
            }
            for row in units
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "m4_section_model.json"
    output_path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    path = run(root / "data" / "tables", root / "outputs")
    print(path)

