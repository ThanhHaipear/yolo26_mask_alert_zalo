from pathlib import Path
import argparse

import onnxruntime as ort

from app.config import settings
from app.utils.image_utils import decode_image_bytes, preprocess_image


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect raw ONNX detections for one image.")
    parser.add_argument("image_path", help="Path to the input image")
    parser.add_argument("--topk", type=int, default=20, help="Number of top rows to print")
    args = parser.parse_args()

    image_path = Path(args.image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = decode_image_bytes(image_path.read_bytes())
    tensor, _ = preprocess_image(image, settings.input_size)

    session = ort.InferenceSession(str(settings.resolved_model_path), providers=["CPUExecutionProvider"])
    output_name = session.get_outputs()[0].name
    input_name = session.get_inputs()[0].name

    output = session.run([output_name], {input_name: tensor})[0]
    rows = output[0]
    rows = sorted(rows.tolist(), key=lambda row: float(row[4]), reverse=True)

    print("Model:", settings.resolved_model_path)
    print("Image:", image_path)
    print("Output shape:", output.shape)
    print()
    print(f"Top {min(args.topk, len(rows))} rows by score:")
    for index, row in enumerate(rows[: args.topk], start=1):
        print(f"{index:02d}: {row}")


if __name__ == "__main__":
    main()
