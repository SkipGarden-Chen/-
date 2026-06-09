from __future__ import annotations

import argparse
from pathlib import Path

import m1_yolo_detect
import m2_qwen_interpret
import m3_fuse_tables
import m4_build_section_model
import m5_draw_section


def run_pipeline(input_path: Path, output_dir: Path, model_path: Path | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    print("M1 YOLO detection...")
    m1_path = m1_yolo_detect.run(input_path, output_dir, model_path)
    print(f"  -> {m1_path}")

    print("M2 Qwen-style interpretation...")
    m2_path = m2_qwen_interpret.run(input_path, m1_path, output_dir)
    print(f"  -> {m2_path}")

    print("M3 table fusion...")
    m3_path = m3_fuse_tables.run(input_path, m1_path, m2_path, output_dir)
    print(f"  -> {m3_path}")

    print("M4 section model...")
    m4_path = m4_build_section_model.run(input_path, output_dir)
    print(f"  -> {m4_path}")

    print("M5 final drawing...")
    figure_path = m5_draw_section.run(input_path, output_dir / "section_D.svg")
    print(f"  -> {figure_path}")
    return figure_path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Run GeoAgent M1-M5 pipeline.")
    parser.add_argument("--input", default=str(root / "data" / "tables"), help="CSV table directory or xlsx workbook")
    parser.add_argument("--output", default=str(root / "outputs"), help="Output directory")
    parser.add_argument("--model", default="", help="Optional YOLO model path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    model_path = Path(args.model) if args.model else None
    run_pipeline(input_path, output_dir, model_path)


if __name__ == "__main__":
    main()

