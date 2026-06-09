from __future__ import annotations

import argparse
from pathlib import Path


def require_ultralytics():
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: ultralytics\n"
            "Install dependencies first:\n"
            "  pip install -r requirements.txt\n"
        ) from exc
    return YOLO


def train(
    data_yaml: Path,
    base_model: str,
    epochs: int,
    imgsz: int,
    batch: int,
    project: Path,
    name: str,
    device: str,
    patience: int,
    workers: int,
) -> Path:
    YOLO = require_ultralytics()
    model = YOLO(base_model)

    kwargs = {
        "data": str(data_yaml),
        "epochs": epochs,
        "imgsz": imgsz,
        "batch": batch,
        "project": str(project),
        "name": name,
        "patience": patience,
        "workers": workers,
        "exist_ok": True,
    }
    if device:
        kwargs["device"] = device

    model.train(**kwargs)
    best_path = project / name / "weights" / "best.pt"
    return best_path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Train YOLO geological feature detector.")
    parser.add_argument("--data", default=str(root / "data" / "yolo_dataset" / "data.yaml"), help="YOLO data.yaml")
    parser.add_argument("--model", default="yolov8n.pt", help="Base YOLO model, e.g. yolov8n.pt/yolo11n.pt")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--project", default=str(root / "runs" / "train"))
    parser.add_argument("--name", default="geo_yolo")
    parser.add_argument("--device", default="", help="Examples: 0, cpu")
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    best_path = train(
        data_yaml=Path(args.data),
        base_model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=Path(args.project),
        name=args.name,
        device=args.device,
        patience=args.patience,
        workers=args.workers,
    )
    print(f"Best model: {best_path}")
    print("Recommended copy target: models/geo_yolo.pt")


if __name__ == "__main__":
    main()

