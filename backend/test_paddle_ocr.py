"""Test PaddleOCR provider return format compatibility"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_providers.ocr import create_paddle_ocr_provider, create_paddle_table_ocr_provider


def test_text_ocr():
    provider = create_paddle_ocr_provider(use_gpu=False)
    if provider is None:
        print("FAIL: text provider is None")
        return False

    # Create a test image with text
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (400, 200), "white")
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "Hello World", fill="black")
    draw.text((50, 100), "PaddleOCR Test", fill="black")
    img.save("test_ocr.png")

    print("=== Testing PaddleOCR text recognition ===")
    result = provider.recognize("test_ocr.png")

    # Validate top-level keys
    required_keys = [
        "log_id", "words_result_num", "words_result", "text_lines",
        "direction", "paragraphs_result_num", "paragraphs_result",
        "paragraphs", "image_size",
    ]
    for k in required_keys:
        assert k in result, f"Missing key: {k}"
        print(f"  {k}: OK ({type(result[k]).__name__})")

    # Validate text_lines structure
    for i, line in enumerate(result["text_lines"]):
        assert "text" in line, f"Missing text in line {i}"
        assert "bbox" in line, f"Missing bbox in line {i}"
        assert "location" in line, f"Missing location in line {i}"
        assert len(line["bbox"]) == 4, f"bbox length wrong: {len(line['bbox'])}"
        print(f"  line {i}: text={line['text']!r}, bbox={line['bbox']}")

    print(f"  image_size: {result['image_size']}")
    print(f"  words_result_num: {result['words_result_num']}")
    print("  ALL FORMAT CHECKS PASSED")

    # Cleanup
    os.remove("test_ocr.png")
    return True


def test_table_ocr():
    provider = create_paddle_table_ocr_provider(use_gpu=False)
    if provider is None:
        print("FAIL: table provider is None")
        return False

    # Create a test image with a simple table
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (400, 200), "white")
    draw = ImageDraw.Draw(img)
    # Draw table grid
    for y in [40, 80, 120, 160]:
        draw.line([(50, y), (350, y)], fill="black", width=2)
    for x in [50, 150, 250, 350]:
        draw.line([(x, 40), (x, 160)], fill="black", width=2)
    # Draw text in cells
    draw.text((70, 50), "Name", fill="black")
    draw.text((170, 50), "Age", fill="black")
    draw.text((270, 50), "City", fill="black")
    draw.text((70, 90), "Alice", fill="black")
    draw.text((170, 90), "30", fill="black")
    draw.text((270, 90), "NYC", fill="black")
    img.save("test_table.png")

    print("\n=== Testing PaddleOCR table recognition ===")
    result = provider.recognize_table("test_table.png")

    # Validate top-level keys
    required_keys = ["log_id", "table_num", "tables_result", "cells", "image_size", "excel_file"]
    for k in required_keys:
        assert k in result, f"Missing key: {k}"
        print(f"  {k}: OK ({type(result[k]).__name__})")

    # Validate cells structure
    for i, cell in enumerate(result["cells"]):
        assert "section" in cell, f"Missing section in cell {i}"
        assert "bbox" in cell, f"Missing bbox in cell {i}"
        assert len(cell["bbox"]) == 4, f"bbox length wrong: {len(cell['bbox'])}"
        if cell["section"] == "body":
            for field in ["row_start", "row_end", "col_start", "col_end", "text"]:
                assert field in cell, f"Missing {field} in body cell {i}"
        print(f"  cell {i}: section={cell['section']}, text={cell.get('text', '')!r}, bbox={cell['bbox']}")

    print(f"  image_size: {result['image_size']}")
    print(f"  table_num: {result['table_num']}")
    print(f"  cells count: {len(result['cells'])}")
    print("  ALL FORMAT CHECKS PASSED")

    # Cleanup
    os.remove("test_table.png")
    return True


def test_get_full_text():
    provider = create_paddle_ocr_provider(use_gpu=False)
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (400, 100), "white")
    draw = ImageDraw.Draw(img)
    draw.text((50, 30), "Test Helper", fill="black")
    img.save("test_helper.png")

    result = provider.recognize("test_helper.png")
    full_text = provider.get_full_text(result)
    print(f"\n=== Testing get_full_text ===")
    print(f"  Full text: {full_text!r}")
    assert isinstance(full_text, str), "get_full_text should return str"
    print("  OK")

    text_with_pos = provider.get_text_with_positions(result)
    assert isinstance(text_with_pos, list), "get_text_with_positions should return list"
    print("  get_text_with_positions OK")

    os.remove("test_helper.png")
    return True


if __name__ == "__main__":
    ok = True
    ok = test_text_ocr() and ok
    ok = test_table_ocr() and ok
    ok = test_get_full_text() and ok

    print("\n" + "=" * 50)
    if ok:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
