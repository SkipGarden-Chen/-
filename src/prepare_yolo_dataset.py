from __future__ import annotations

import argparse
import random
import shutil
import subprocess
from pathlib import Path


GEO_CLASSES = [
    "outcrop",
    "bedding",
    "joint_fracture",
    "fault",
    "fold",
    "lithologic_boundary",
    "strata_line",
]


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def create_yolo_dirs(dataset_dir: Path) -> None:
    for split in ["train", "val", "test"]:
        (dataset_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (dataset_dir / "labels" / split).mkdir(parents=True, exist_ok=True)


def write_data_yaml(dataset_dir: Path, classes: list[str] | None = None) -> Path:
    classes = classes or GEO_CLASSES
    lines = [
        f"path: {dataset_dir.as_posix()}",
        "train: images/train",
        "val: images/val",
        "test: images/test",
        "",
        "names:",
    ]
    for index, name in enumerate(classes):
        lines.append(f"  {index}: {name}")
    output_path = dataset_dir / "data.yaml"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def extract_frames_opencv(video_path: Path, output_dir: Path, every_seconds: float, max_frames: int | None) -> int:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is not installed.") from exc

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_interval = max(1, int(round(fps * every_seconds)))
    saved = 0
    frame_index = 0
    output_dir.mkdir(parents=True, exist_ok=True)

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_index % frame_interval == 0:
            output_path = output_dir / f"{video_path.stem}_frame_{frame_index:06d}.jpg"
            cv2.imwrite(str(output_path), frame)
            saved += 1
            if max_frames is not None and saved >= max_frames:
                break
        frame_index += 1

    cap.release()
    return saved


def extract_frames_ffmpeg(video_path: Path, output_dir: Path, every_seconds: float, max_frames: int | None) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    fps = 1 / every_seconds
    output_pattern = output_dir / f"{video_path.stem}_frame_%06d.jpg"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"fps={fps}",
    ]
    if max_frames is not None:
        command.extend(["-frames:v", str(max_frames)])
    command.append(str(output_pattern))
    subprocess.run(command, check=True)
    return len(list(output_dir.glob(f"{video_path.stem}_frame_*.jpg")))


def extract_frames(video_path: Path, output_dir: Path, every_seconds: float = 1.0, max_frames: int | None = None) -> int:
    if every_seconds <= 0:
        raise ValueError("every_seconds must be greater than 0.")
    try:
        return extract_frames_opencv(video_path, output_dir, every_seconds, max_frames)
    except RuntimeError:
        return extract_frames_ffmpeg(video_path, output_dir, every_seconds, max_frames)


def split_annotated_dataset(
    source_images: Path,
    source_labels: Path,
    dataset_dir: Path,
    train_ratio: float = 0.7,
    val_ratio: float = 0.2,
    seed: int = 42,
) -> None:
    create_yolo_dirs(dataset_dir)
    images = sorted(path for path in source_images.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)
    pairs = [(image, source_labels / f"{image.stem}.txt") for image in images]
    pairs = [(image, label) for image, label in pairs if label.exists()]

    random.Random(seed).shuffle(pairs)
    train_count = int(len(pairs) * train_ratio)
    val_count = int(len(pairs) * val_ratio)
    splits = {
        "train": pairs[:train_count],
        "val": pairs[train_count: train_count + val_count],
        "test": pairs[train_count + val_count:],
    }

    for split, split_pairs in splits.items():
        for image, label in split_pairs:
            shutil.copy2(image, dataset_dir / "images" / split / image.name)
            shutil.copy2(label, dataset_dir / "labels" / split / label.name)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Prepare drone-video frames and YOLO dataset folders.")
    parser.add_argument("--dataset", default=str(root / "data" / "yolo_dataset"), help="YOLO dataset directory")
    parser.add_argument("--video", default="", help="Optional drone video path")
    parser.add_argument("--frames-output", default=str(root / "data" / "raw_frames"), help="Frame output directory")
    parser.add_argument("--every-seconds", type=float, default=1.0, help="Extract one frame every N seconds")
    parser.add_argument("--max-frames", type=int, default=0, help="Optional max extracted frames")
    parser.add_argument("--source-images", default="", help="Optional labeled image source directory")
    parser.add_argument("--source-labels", default="", help="Optional YOLO label source directory")
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    args = parser.parse_args()

    dataset_dir = Path(args.dataset)
    create_yolo_dirs(dataset_dir)
    yaml_path = write_data_yaml(dataset_dir)
    print(f"Dataset YAML: {yaml_path}")

    if args.video:
        saved = extract_frames(
            Path(args.video),
            Path(args.frames_output),
            every_seconds=args.every_seconds,
            max_frames=args.max_frames or None,
        )
        print(f"Extracted frames: {saved}")

    if args.source_images and args.source_labels:
        split_annotated_dataset(
            Path(args.source_images),
            Path(args.source_labels),
            dataset_dir,
            train_ratio=args.train_ratio,
            val_ratio=args.val_ratio,
        )
        print(f"Split annotated dataset into: {dataset_dir}")


if __name__ == "__main__":
    main()

