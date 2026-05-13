import math
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
from skimage.metrics import structural_similarity as ssim


def evaluate_similarity(original_image_path: str, preview_html: str) -> dict:
    """
    基于原始 UI 截图与生成页面渲染截图，计算真实图像相似度指标。
    在 main.py 中会放到独立线程里执行，所以这里使用 Playwright 同步 API。
    """

    if not preview_html or not preview_html.strip():
        return {
            "enabled": False,
            "error": "preview_html 为空，无法计算相似度"
        }

    output_dir = Path("data/evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)

    original = Image.open(original_image_path).convert("RGB")
    original_width, original_height = original.size

    html_path = output_dir / "preview_eval.html"
    screenshot_path = output_dir / "preview_screenshot.png"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(preview_html)

    file_url = html_path.resolve().as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={
                "width": original_width,
                "height": original_height
            }
        )
        page.goto(file_url, wait_until="networkidle")
        page.screenshot(path=str(screenshot_path), full_page=False)
        browser.close()

    generated = Image.open(screenshot_path).convert("RGB")
    generated = generated.resize((original_width, original_height))

    original_arr = np.array(original).astype(np.float32)
    generated_arr = np.array(generated).astype(np.float32)

    mse_value = float(np.mean((original_arr - generated_arr) ** 2))

    if mse_value == 0:
        psnr_value = 100.0
    else:
        psnr_value = float(20 * math.log10(255.0 / math.sqrt(mse_value)))

    ssim_value = float(
        ssim(
            original_arr.astype(np.uint8),
            generated_arr.astype(np.uint8),
            channel_axis=2,
            data_range=255
        )
    )

    ssim_percent = round(max(0, min(1, ssim_value)) * 100, 2)

    return {
        "enabled": True,
        "ssim": round(ssim_value, 4),
        "ssim_percent": ssim_percent,
        "mse": round(mse_value, 2),
        "psnr": round(psnr_value, 2),
        "original_size": {
            "width": original_width,
            "height": original_height
        },
        "preview_screenshot": str(screenshot_path)
    }