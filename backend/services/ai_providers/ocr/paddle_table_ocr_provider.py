"""
PaddleOCR table recognition provider (local, no API key needed)
Drop-in replacement for BaiduTableOCRProvider with identical return format
Uses PaddleOCR text detection + coordinate clustering to infer table structure
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


def _get_paddleocr(use_gpu=True, lang="ch"):
    from .paddle_ocr_provider import _get_paddleocr as _get_text_ocr

    return _get_text_ocr(use_gpu=use_gpu, lang=lang)


class PaddleTableOCRProvider:
    """
    PaddleOCR table recognition provider - local, no API key needed.

    Return format is compatible with BaiduTableOCRProvider.recognize_table().
    Uses PaddleOCR text detection + coordinate clustering for table structure.
    """

    def __init__(self, use_gpu=True, lang="ch"):
        self._use_gpu = use_gpu
        self._lang = lang
        self._ocr = None
        logger.info(
            "PaddleTableOCR provider created (device=%s, lang=%s)",
            "gpu" if use_gpu else "cpu",
            lang,
        )

    def _ensure_ocr(self):
        if self._ocr is None:
            self._ocr = _get_paddleocr(use_gpu=self._use_gpu, lang=self._lang)

    def recognize_table(
        self,
        image_path: str,
        cell_contents: bool = True,
        return_excel: bool = False,
    ) -> Dict[str, Any]:
        """
        Recognize table structure in an image.

        Return format matches BaiduTableOCRProvider.recognize_table() exactly.
        """
        logger.info("PaddleTableOCR recognizing: %s", image_path)
        try:
            self._ensure_ocr()

            original_width, original_height = 0, 0
            with Image.open(image_path) as img:
                original_width, original_height = img.size

            results = self._ocr.predict(image_path)

            cells = []
            tables_result = []

            if not results:
                return self._empty_result(original_width, original_height)

            ocr_result = results[0]
            rec_texts = ocr_result.get("rec_texts", [])
            rec_scores = ocr_result.get("rec_scores", [])
            rec_boxes = ocr_result.get("rec_boxes", [])

            if not rec_texts:
                return self._empty_result(original_width, original_height)

            text_items = []
            for i in range(len(rec_texts)):
                box = rec_boxes[i]
                if hasattr(box, "tolist"):
                    box = box.tolist()
                text_items.append(
                    {
                        "text": rec_texts[i],
                        "score": float(rec_scores[i]),
                        "bbox": [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
                        "cx": (int(box[0]) + int(box[2])) / 2,
                        "cy": (int(box[1]) + int(box[3])) / 2,
                    }
                )

            row_groups, col_groups = self._cluster_positions(text_items)

            max_row = len(row_groups) - 1
            max_col = len(col_groups) - 1

            for item in text_items:
                row_idx = self._assign_group(item["cy"], row_groups)
                col_idx = self._assign_group(item["cx"], col_groups)
                bbox = item["bbox"]

                cells.append(
                    {
                        "table_idx": 0,
                        "section": "body",
                        "row_start": row_idx,
                        "row_end": row_idx,
                        "col_start": col_idx,
                        "col_end": col_idx,
                        "text": item["text"],
                        "bbox": bbox,
                        "contents": [],
                    }
                )

            if max_row >= 0 and max_col >= 0:
                table_bbox = self._compute_table_bbox(text_items)
                tables_result.append(
                    {
                        "table_location": [
                            {"x": table_bbox[0], "y": table_bbox[1]},
                            {"x": table_bbox[2], "y": table_bbox[1]},
                            {"x": table_bbox[2], "y": table_bbox[3]},
                            {"x": table_bbox[0], "y": table_bbox[3]},
                        ],
                        "header": [],
                        "body": cells,
                        "footer": [],
                        "row_num": max_row + 1,
                        "col_num": max_col + 1,
                    }
                )

            logger.info(
                "PaddleTableOCR found %d tables, %d cells",
                len(tables_result),
                len(cells),
            )

            return {
                "log_id": f"paddle_table_{id(self)}",
                "table_num": len(tables_result),
                "tables_result": tables_result,
                "cells": cells,
                "image_size": (original_width, original_height),
                "excel_file": None,
            }

        except Exception as e:
            logger.error("PaddleTableOCR recognize_table failed: %s", e)
            raise

    def _cluster_positions(
        self, items: List[Dict[str, Any]]
    ) -> Tuple[List[float], List[float]]:
        """Cluster text item positions into row and column groups."""
        if not items:
            return [], []

        cy_values = sorted(set(item["cy"] for item in items))
        row_groups = self._merge_nearby(cy_values, threshold=15)

        cx_values = sorted(set(item["cx"] for item in items))
        col_groups = self._merge_nearby(cx_values, threshold=15)

        return row_groups, col_groups

    def _merge_nearby(self, values: List[float], threshold: float = 15) -> List[float]:
        """Merge nearby values into cluster centers."""
        if not values:
            return []

        groups = []
        current_group = [values[0]]

        for v in values[1:]:
            if v - np.mean(current_group) < threshold:
                current_group.append(v)
            else:
                groups.append(float(np.mean(current_group)))
                current_group = [v]
        groups.append(float(np.mean(current_group)))

        return groups

    def _assign_group(self, value: float, groups: List[float]) -> int:
        """Assign a value to the nearest group index."""
        if not groups:
            return 0
        distances = [abs(value - g) for g in groups]
        return int(np.argmin(distances))

    def _compute_table_bbox(self, items: List[Dict[str, Any]]) -> List[int]:
        """Compute overall bounding box from all text items."""
        if not items:
            return [0, 0, 0, 0]
        x0 = min(item["bbox"][0] for item in items)
        y0 = min(item["bbox"][1] for item in items)
        x1 = max(item["bbox"][2] for item in items)
        y1 = max(item["bbox"][3] for item in items)
        return [int(x0), int(y0), int(x1), int(y1)]

    def _empty_result(self, w: int, h: int) -> Dict[str, Any]:
        return {
            "log_id": f"paddle_table_{id(self)}",
            "table_num": 0,
            "tables_result": [],
            "cells": [],
            "image_size": (w, h),
            "excel_file": None,
        }

    def _location_to_bbox(self, location):
        if not location or len(location) < 2:
            return [0, 0, 0, 0]
        xs = [p["x"] for p in location]
        ys = [p["y"] for p in location]
        return [min(xs), min(ys), max(xs), max(ys)]

    def get_table_structure(self, cells: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not cells:
            return {"rows": 0, "cols": 0, "cells_by_position": {}}

        body_cells = [c for c in cells if c.get("section") == "body"]
        if not body_cells:
            return {"rows": 0, "cols": 0, "cells_by_position": {}}

        max_row = max(cell["row_end"] for cell in body_cells)
        max_col = max(cell["col_end"] for cell in body_cells)

        cells_by_position = {}
        for cell in body_cells:
            key = (cell["row_start"], cell["col_start"])
            cells_by_position[key] = cell

        return {
            "rows": max_row,
            "cols": max_col,
            "cells_by_position": cells_by_position,
        }


def create_paddle_table_ocr_provider(
    use_gpu: bool = True,
) -> Optional[PaddleTableOCRProvider]:
    try:
        import paddleocr  # noqa: F401

        return PaddleTableOCRProvider(use_gpu=use_gpu)
    except ImportError:
        logger.warning("paddleocr not installed, skipping PaddleTableOCR provider")
        return None
