import base64

import cv2
import numpy as np

VIOLATION_CLASS_NAMES = {"without_mask", "mask_weared_incorrect"}


def decode_image_bytes(content: bytes) -> np.ndarray:
    image = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Cannot decode input image")
    return image


def preprocess_image(image: np.ndarray, input_size: int) -> tuple[np.ndarray, tuple[float, float]]:
    original_h, original_w = image.shape[:2]
    resized = cv2.resize(image, (input_size, input_size))
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    tensor = rgb.astype(np.float32) / 255.0
    tensor = np.transpose(tensor, (2, 0, 1))
    tensor = np.expand_dims(tensor, axis=0)

    scale_x = original_w / input_size
    scale_y = original_h / input_size
    return tensor, (scale_x, scale_y)


def clip_box(x1: float, y1: float, x2: float, y2: float, width: int, height: int) -> tuple[int, int, int, int]:
    return (
        int(max(0, min(width - 1, x1))),
        int(max(0, min(height - 1, y1))),
        int(max(0, min(width - 1, x2))),
        int(max(0, min(height - 1, y2))),
    )


def compute_iou(box_a: dict, box_b: dict) -> float:
    inter_x1 = max(box_a["x1"], box_b["x1"])
    inter_y1 = max(box_a["y1"], box_b["y1"])
    inter_x2 = min(box_a["x2"], box_b["x2"])
    inter_y2 = min(box_a["y2"], box_b["y2"])

    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    if inter_area <= 0:
        return 0.0

    area_a = max(0, box_a["x2"] - box_a["x1"]) * max(0, box_a["y2"] - box_a["y1"])
    area_b = max(0, box_b["x2"] - box_b["x1"]) * max(0, box_b["y2"] - box_b["y1"])
    union = area_a + area_b - inter_area
    if union <= 0:
        return 0.0
    return inter_area / union


def apply_nms(detections: list[dict], iou_threshold: float) -> list[dict]:
    kept: list[dict] = []
    remaining = sorted(detections, key=lambda item: item["confidence"], reverse=True)

    while remaining:
        current = remaining.pop(0)
        kept.append(current)
        remaining = [
            candidate
            for candidate in remaining
            if compute_iou(current, candidate) < iou_threshold
        ]

    return kept


def postprocess_output(
    output: np.ndarray,
    original_shape: tuple[int, int],
    scale: tuple[float, float],
    conf_threshold: float,
    iou_threshold: float,
    class_names: list[str],
) -> list[dict]:
    height, width = original_shape[:2]
    scale_x, scale_y = scale
    detections: list[dict] = []

    rows = output[0] if output.ndim >= 2 else output
    for row in rows:
        values = row.tolist()
        if len(values) < 6:
            continue

        x1, y1, x2, y2, score, class_id = values[:6]
        score = float(score)
        class_id = int(class_id)
        if score < conf_threshold or class_id < 0 or class_id >= len(class_names):
            continue

        x1 *= scale_x
        y1 *= scale_y
        x2 *= scale_x
        y2 *= scale_y
        x1, y1, x2, y2 = clip_box(x1, y1, x2, y2, width, height)
        if x2 <= x1 or y2 <= y1:
            continue

        detections.append(
            {
                "class_id": class_id,
                "class_name": class_names[class_id],
                "confidence": round(score, 4),
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            }
        )

    return apply_nms(detections, iou_threshold)


def count_violations(detections: list[dict]) -> int:
    return sum(1 for item in detections if item["class_name"] in VIOLATION_CLASS_NAMES)


def draw_detections(image: np.ndarray, detections: list[dict]) -> np.ndarray:
    output = image.copy()
    for item in detections:
        color = (0, 255, 0)
        if item["class_name"] == "without_mask":
            color = (0, 0, 255)
        elif item["class_name"] == "mask_weared_incorrect":
            color = (0, 165, 255)

        cv2.rectangle(output, (item["x1"], item["y1"]), (item["x2"], item["y2"]), color, 2)
        label = f"{item['class_name']} {item['confidence']:.2f}"
        cv2.putText(output, label, (item["x1"], max(20, item["y1"] - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return output


def encode_image_to_jpeg_bytes(image: np.ndarray) -> bytes:
    ok, buffer = cv2.imencode(".jpg", image)
    if not ok:
        raise ValueError("Cannot encode output image")
    return buffer.tobytes()


def encode_image_to_base64(image: np.ndarray) -> str:
    return base64.b64encode(encode_image_to_jpeg_bytes(image)).decode("utf-8")
