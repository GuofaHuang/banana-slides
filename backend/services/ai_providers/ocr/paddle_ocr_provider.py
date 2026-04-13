"""
PaddleOCR text recognition provider (local, no API key needed)
Drop-in replacement for BaiduAccurateOCRProvider with identical return format
"""

import logging
from typing import Dict, List, Any, Optional
from PIL import Image

logger = logging.getLogger(__name__)

_paddleocr_instance = None


def _get_paddleocr(use_gpu=True, lang="ch"):
    global _paddleocr_instance
    if _paddleocr_instance is not None:
        return _paddleocr_instance
    try:
        import os

        os.environ["FLAGS_use_mkldnn"] = "0"
        from paddleocr import PaddleOCR

        device = "gpu" if use_gpu else "cpu"
        init_kwargs = {
            "use_textline_orientation": True,
            "lang": lang,
            "device": device,
        }
        _paddleocr_instance = PaddleOCR(**init_kwargs)
        logger.info("PaddleOCR initialized (device=%s, lang=%s)", device, lang)
        return _paddleocr_instance
    except ImportError:
        raise ImportError(
            "paddleocr is not installed. "
            "Install with: pip install paddlepaddle paddleocr"
        )


class PaddleOCRProvider:
    """
    PaddleOCR text recognition provider - local, no API key needed.

    Return format is compatible with BaiduAccurateOCRProvider.recognize().
    """

    def __init__(self, use_gpu=True, lang="ch"):
        self._use_gpu = use_gpu
        self._lang = lang
        self._ocr = None
        logger.info(
            "PaddleOCR provider created (device=%s, lang=%s)",
            "gpu" if use_gpu else "cpu",
            lang,
        )

    def _ensure_ocr(self):
        if self._ocr is None:
            self._ocr = _get_paddleocr(use_gpu=self._use_gpu, lang=self._lang)

    def recognize(
        self,
        image_path: str,
        language_type: str = "CHN_ENG",
        recognize_granularity: str = "big",
        detect_direction: bool = False,
        vertexes_location: bool = False,
        paragraph: bool = False,
        probability: bool = False,
        char_probability: bool = False,
        multidirectional_recognize: bool = False,
        eng_granularity: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Recognize text in an image.

        Return format matches BaiduAccurateOCRProvider.recognize() exactly.
        Unsupported parameters (vertexes_location, paragraph, etc.) are
        accepted for interface compatibility but silently ignored.
        """
        logger.info("PaddleOCR recognizing: %s", image_path)
        try:
            self._ensure_ocr()

            original_width, original_height = 0, 0
            with Image.open(image_path) as img:
                original_width, original_height = img.size

            results = self._ocr.predict(image_path)

            text_lines = []
            words_result = []

            if results:
                ocr_result = results[0]
                rec_texts = ocr_result.get("rec_texts", [])
                rec_scores = ocr_result.get("rec_scores", [])
                rec_boxes = ocr_result.get("rec_boxes", [])

                for idx in range(len(rec_texts)):
                    text = rec_texts[idx]
                    confidence = float(rec_scores[idx])

                    box = rec_boxes[idx]
                    if hasattr(box, "tolist"):
                        box = box.tolist()
                    x0, y0, x1, y1 = int(box[0]), int(box[1]), int(box[2]), int(box[3])

                    bbox = [x0, y0, x1, y1]
                    location = {
                        "left": x0,
                        "top": y0,
                        "width": x1 - x0,
                        "height": y1 - y0,
                    }

                    line_info = {
                        "text": text,
                        "location": location,
                        "bbox": bbox,
                    }

                    if probability or char_probability:
                        line_info["probability"] = {
                            "average": confidence,
                            "min": confidence,
                            "variance": 0.0,
                        }

                    if recognize_granularity == "small":
                        line_info["chars"] = [
                            {"char": ch, "location": {}, "bbox": [0, 0, 0, 0]}
                            for ch in text
                        ]

                    text_lines.append(line_info)

                    words_result.append(
                        {
                            "words": text,
                            "location": location,
                        }
                    )

            log_id = f"paddle_{id(self)}"

            return {
                "log_id": log_id,
                "words_result_num": len(text_lines),
                "words_result": words_result,
                "text_lines": text_lines,
                "direction": None,
                "paragraphs_result_num": 0,
                "paragraphs_result": [],
                "paragraphs": [],
                "image_size": (original_width, original_height),
            }

        except Exception as e:
            logger.error("PaddleOCR recognize failed: %s", e)
            raise

    def _location_to_bbox(self, location: Dict[str, int]) -> List[int]:
        if not location:
            return [0, 0, 0, 0]
        left = location.get("left", 0)
        top = location.get("top", 0)
        width = location.get("width", 0)
        height = location.get("height", 0)
        return [left, top, left + width, top + height]

    def get_full_text(self, result: Dict[str, Any], separator: str = "\n") -> str:
        text_lines = result.get("text_lines", [])
        return separator.join([line.get("text", "") for line in text_lines])

    def get_text_with_positions(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        text_lines = result.get("text_lines", [])
        return [
            {
                "text": line.get("text", ""),
                "bbox": line.get("bbox", [0, 0, 0, 0]),
            }
            for line in text_lines
        ]


def create_paddle_ocr_provider(
    use_gpu: bool = True,
    lang: str = "ch",
) -> Optional[PaddleOCRProvider]:
    try:
        import paddleocr  # noqa: F401

        return PaddleOCRProvider(use_gpu=use_gpu, lang=lang)
    except ImportError:
        logger.warning("paddleocr not installed, skipping PaddleOCR provider")
        return None
