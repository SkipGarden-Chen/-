from __future__ import annotations

from pathlib import Path

from section_drawer import SvgBuilder, load_project


def run(input_path: Path, output_path: Path) -> Path:
    """M5: draw the final geological section SVG."""

    section, topo, units, structures = load_project(input_path)
    svg = SvgBuilder(section, topo, units, structures).render()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    path = run(root / "data" / "tables", root / "outputs" / "section_D.svg")
    print(path)

