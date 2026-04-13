"""OCR-related AI Providers"""

from services.ai_providers.ocr.baidu_table_ocr_provider import (
    BaiduTableOCRProvider,
    create_baidu_table_ocr_provider,
)
from services.ai_providers.ocr.baidu_accurate_ocr_provider import (
    BaiduAccurateOCRProvider,
    create_baidu_accurate_ocr_provider,
)

try:
    from services.ai_providers.ocr.paddle_ocr_provider import (
        PaddleOCRProvider,
        create_paddle_ocr_provider,
    )
except ImportError:
    PaddleOCRProvider = None
    create_paddle_ocr_provider = None

try:
    from services.ai_providers.ocr.paddle_table_ocr_provider import (
        PaddleTableOCRProvider,
        create_paddle_table_ocr_provider,
    )
except ImportError:
    PaddleTableOCRProvider = None
    create_paddle_table_ocr_provider = None

__all__ = [
    "BaiduTableOCRProvider",
    "create_baidu_table_ocr_provider",
    "BaiduAccurateOCRProvider",
    "create_baidu_accurate_ocr_provider",
    "PaddleOCRProvider",
    "create_paddle_ocr_provider",
    "PaddleTableOCRProvider",
    "create_paddle_table_ocr_provider",
]
