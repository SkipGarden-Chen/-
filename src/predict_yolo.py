from __future__ import annotations

import argparse
import json
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


def result_to_record(result, names: dict[int, str]) -> dict[str, object]:
    boxes = result.boxes
    detections: list[dict[str, object]] = []
    if boxes is not None:
        xyxy = boxes.xyxy.cpu().tolist()
        confs = boxes.conf.cpu().tolist()
        classes = boxes.cls.cpu().tolist()
        for bbox, confidence, class_id in zip(xyxy, confs, classes):
            cid = int(class_id)
            detections.append(
                {
                    "class": names.get(cid, str(cid)),
                    "confidence": round(float(confidence), 4),
                    "bbox": [round(float(v), 2) for v in bbox],
                    "source": "yolo_model",
                }
            )
    return {
        "image_path": str(result.path),
        "detections": detections,
    }


def predict(
    model_path: Path,
    source: Path,
    output_dir: Path,
    conf: float,
    imgsz: int,
    save_images: bool,
) -> Path:
    YOLO = require_ultralytics()
    model = YOLO(str(model_path))
    results = model.predict(
        source=str(source),
        conf=conf,
        imgsz=imgsz,
        save=save_images,
        project=str(output_dir),
        name="yolo_predict",
        exist_ok=True,
        verbose=False,
    )
    names = model.names
    records = [result_to_record(result, names) for result in results]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "yolo_predictions.json"
    output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Run YOLO prediction on images, folders, or videos.")
    parser.add_argument("--model", default=str(root / "models" / "geo_yolo.pt"))
    parser.add_argument("--source", required=True, help="Image, folder, or video path")
    parser.add_argument("--output", default=str(root / "outputs"))
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--save-images", action="store_true")
    args = parser.parse_args()

    output_path = predict(
        model_path=Path(args.model),
        source=Path(args.source),
        output_dir=Path(args.output),
        conf=args.conf,
        imgsz=args.imgsz,
        save_images=args.save_images,
    )
    print(output_path)


if __name__ == "__main__":
    main()

