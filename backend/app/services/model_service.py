import ast

import onnxruntime as ort

from app.config import settings
from app.utils.image_utils import postprocess_output, preprocess_image


class ModelService:
    def __init__(self) -> None:
        model_path = settings.resolved_model_path
        if not model_path.exists():
            raise FileNotFoundError(f"ONNX model not found at {model_path}")

        available_providers = ort.get_available_providers()
        selected_providers = [
            provider for provider in settings.onnx_providers_list if provider in available_providers
        ] or ["CPUExecutionProvider"]

        self.session = ort.InferenceSession(str(model_path), providers=selected_providers)
        self.providers = selected_providers
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.class_names = self._load_class_names()

    def _load_class_names(self) -> list[str]:
        metadata_names = self.session.get_modelmeta().custom_metadata_map.get("names")
        if metadata_names:
            try:
                parsed = ast.literal_eval(metadata_names)
                if isinstance(parsed, dict):
                    ordered = [name for _, name in sorted(parsed.items(), key=lambda item: int(item[0]))]
                    if ordered:
                        return [str(name) for name in ordered]
                if isinstance(parsed, list) and parsed:
                    return [str(name) for name in parsed]
            except (ValueError, SyntaxError, TypeError):
                pass

        return settings.class_names_list

    def predict(self, image) -> list[dict]:
        tensor, scale = preprocess_image(image, settings.input_size)
        output = self.session.run([self.output_name], {self.input_name: tensor})[0]
        return postprocess_output(
            output,
            image.shape,
            scale,
            settings.conf_threshold,
            settings.iou_threshold,
            self.class_names,
        )


model_service = ModelService()
