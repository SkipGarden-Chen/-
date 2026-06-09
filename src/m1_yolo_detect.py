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


def project_root_from_input(input_path: Path) -> Path:
    if input_path.is_file():
        return input_path.parent
    if input_path.name == "tables" and input_path.parent.name == "data":
        return input_path.parent.parent
    return input_path


def resolve_photo_path(project_root: Path, photo_path: str) -> Path | None:
    photo_path = clean(photo_path)
    if not photo_path:
        return None
    path = Path(photo_path)
    if path.is_absolute():
        return path
    return project_root / path


def load_yolo_model(model_path: Path | None):
    if model_path is None or not model_path.exists():
        return None
    try:
        from ultralytics import YOLO
    except ImportError:
        return None
    return YOLO(str(model_path))


def predict_one_image(model, image_path: Path, conf: float = 0.25, imgsz: int = 960) -> list[dict[str, object]]:
    results = model.predict(source=str(image_path), conf=conf, imgsz=imgsz, save=False, verbose=False)
    if not results:
        return []

    result = results[0]
    names = model.names
    boxes = result.boxes
    detections: list[dict[str, object]] = []
    if boxes is None:
        return detections

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
    return detections


def run(input_path: Path, output_dir: Path, model_path: Path | None = None) -> Path:
    """M1: get YOLO-style geological feature detections.

    If a real YOLO model is available, this module predicts on observation photos.
    Otherwise it reads the yolo_result column from observations.csv/xlsx so the
    pipeline can still run without a trained model.
    """

    source = TableSource(input_path)
    observations = source.read("observations")
    project_root = project_root_from_input(input_path)
    model = load_yolo_model(model_path)
    results = []

    for row in observations:
        photo_path = resolve_photo_path(project_root, row.get("photo_path", ""))
        mode = "table_fallback"
        if model is not None and photo_path is not None and photo_path.exists():
            detections = predict_one_image(model, photo_path)
            mode = "yolo_model"
        else:
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
                "mode": mode,
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
