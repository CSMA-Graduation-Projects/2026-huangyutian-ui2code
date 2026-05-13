from vision.detector import UIDetector
from backend.core.layout_tree import LayoutTreeBuilder
from backend.core.generator import VueGenerator
from backend.core.html_preview_generator import HtmlPreviewGenerator
from backend.core.llm.llm_generator import LLMVueGenerator
from backend.core.llm.deepseek_generator import DeepSeekVueGenerator
from backend.core.evaluator import evaluate_similarity
from backend.core.llm.doubao_generator import DoubaoVueGenerator

from dotenv import load_dotenv
import os
import json
import re
from concurrent.futures import ThreadPoolExecutor
from backend.core.style_analyzer import analyze_image_style

def sanitize_preview_html(html: str) -> str:
    if not html:
        return html

    html = re.sub(r'overflow-y\s*:\s*auto\s*;?', 'overflow-y: visible;', html, flags=re.IGNORECASE)
    html = re.sub(r'overflow\s*:\s*auto\s*;?', 'overflow: visible;', html, flags=re.IGNORECASE)
    html = re.sub(r'overflow\s*:\s*scroll\s*;?', 'overflow: visible;', html, flags=re.IGNORECASE)
    html = re.sub(r'height\s*:\s*100vh\s*;?', 'min-height: auto;', html, flags=re.IGNORECASE)

    def replace_fake_img(match):
        src = match.group(1).strip().lower()

        fake_patterns = [
            "hero", "banner", "poster", "image", "img",
            ".jpg", ".jpeg", ".png", ".webp"
        ]

        if src.startswith("data:") or src.startswith("http://") or src.startswith("https://"):
            return match.group(0)

        if any(p in src for p in fake_patterns):
            return '<div class="img-fallback">图片占位</div>'

        return match.group(0)

    html = re.sub(
        r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>',
        replace_fake_img,
        html,
        flags=re.IGNORECASE
    )

    fallback_style = """
    <style>
      html, body {
        height: auto !important;
        min-height: 0 !important;
        overflow: visible !important;
      }

      body {
        margin: 0;
      }

      .img-fallback {
        width: 100%;
        min-height: 160px;
        border-radius: 8px;
        background: linear-gradient(135deg, #2b2f36, #454b57);
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
      }

      img {
        max-width: 100%;
        height: auto;
        object-fit: cover;
      }
    </style>
    """

    if "</head>" in html:
        html = html.replace("</head>", fallback_style + "\n</head>")
    else:
        html = fallback_style + html

    return html


def calculate_similarity_safely(image_path: str, preview_html: str) -> dict:
    """
    在独立线程中运行相似度评估，避免 FastAPI async 环境与 Playwright sync API 冲突。
    """
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                evaluate_similarity,
                image_path,
                preview_html
            )
            return future.result()
    except Exception as e:
        return {
            "enabled": False,
            "error": str(e)
        }


def is_ai_result_too_generic(preview_html: str) -> bool:
    """
    粗略判断大模型是否输出了过于模板化的页面。
    注意：这不是判定是否使用了大模型，只是辅助日志判断。
    """
    if not preview_html:
        return True

    generic_keywords = [
        "卡片1",
        "卡片2",
        "导航项1",
        "导航项2",
        "Button",
        "{{ logoText }}",
        "{{ pageTitle }}",
        "{{ buttonText }}"
    ]

    hit_count = sum(1 for word in generic_keywords if word in preview_html)

    return hit_count >= 2


def start_project(image_path="test.png", use_llm=True, user_config=None, model_name="qwen-vl-plus"):
    if user_config is None:
        user_config = {}

    load_dotenv()

    qwen_api_key = os.getenv("QWEN_API_KEY")
    qwen_model = os.getenv("QWEN_MODEL", "qwen-turbo")

    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
   
    ark_api_key = os.getenv("ARK_API_KEY")
    ark_base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    doubao_model = os.getenv("DOUBAO_MODEL")

    print("🔥 前端选择模型:", model_name)
    print("🔥 环境默认千问模型:", qwen_model)
    print("🔥 用户配置:", user_config)
    print("=== Vision2Code 启动 ===")
    # 0. 视觉风格分析
    style_data = analyze_image_style(image_path)

    print("🎨 视觉风格分析结果 ↓↓↓")
    print(style_data)
    print("🎨 视觉风格分析结束 ↑↑↑")
    # 1. 目标检测
    detector = UIDetector()
    detections = detector.detect(image_path)
    print("🔥 检测结果 detections ↓↓↓")
    for d in detections:
        print(d)
    print("🔥 检测结束 ↑↑↑")

    os.makedirs("data", exist_ok=True)

    with open("data/detection.json", "w", encoding="utf-8") as f:
        json.dump(detections, f, indent=4, ensure_ascii=False)

    print("检测结果已保存到 data/detection.json")

    # 2. 布局树构建
    builder = LayoutTreeBuilder(detections)
    layout_nodes = builder.build()
    layout_data = [node.to_dict() for node in layout_nodes]

    with open("data/layout_tree.json", "w", encoding="utf-8") as f:
        json.dump(layout_data, f, indent=4, ensure_ascii=False)

    print("布局树已保存到 data/layout_tree.json")

    # 3. 规则生成，作为兜底结果
    generator = VueGenerator()
    vue_code_rule = generator.generate(layout_nodes)

    with open("GeneratedLayout.vue", "w", encoding="utf-8") as f:
        f.write(vue_code_rule)

    print("规则生成的 Vue3 组件已生成：GeneratedLayout.vue")

    # 4. 规则 HTML 预览，作为兜底结果
    preview_generator = HtmlPreviewGenerator()
    preview_html_rule = preview_generator.generate(layout_nodes)

    with open("preview.html", "w", encoding="utf-8") as f:
        f.write(preview_html_rule)

    print("规则 HTML 预览已生成：preview.html")

    final_vue_code = vue_code_rule
    final_preview_html = preview_html_rule
    llm_used = False
    llm_error = ""
    generation_source = "rule"
    actual_model = "rule"
    
    if model_name == "rule":
        use_llm = False
        llm_error = "用户选择规则生成，未调用大模型"
        generation_source = "rule"
    # 5. 优先尝试千问大模型

    actual_model = "rule"

    if model_name == "rule":
        use_llm = False
        llm_error = "用户选择规则生成，未调用大模型"
        generation_source = "rule"

    if use_llm and model_name == "doubao":

        if not ark_api_key:
            llm_error = "未读取到 ARK_API_KEY，回退到规则生成"
            generation_source = "rule"
            actual_model = "rule"
            print(llm_error)

        else:
            try:
                print("开始调用豆包视觉模型生成 Vue 代码和预览 HTML...")

                actual_model = doubao_model

                doubao = DoubaoVueGenerator(
                    api_key=ark_api_key,
                    base_url=ark_base_url,
                    model=doubao_model
                )

                ai_result = doubao.generate_from_image(
                    image_path=image_path,
                    layout_data=layout_data,
                    detections=detections,
                    style_data=style_data,
                    user_config=user_config
                )

                vue_code_ai = ai_result.get("vue_code", "")
                preview_html_ai = ai_result.get("preview_html", "")

                preview_html_ai = sanitize_preview_html(preview_html_ai)

                if vue_code_ai.strip():
                    with open("GeneratedLayout_Doubao.vue", "w", encoding="utf-8") as f:
                        f.write(vue_code_ai)
                    final_vue_code = vue_code_ai

                if preview_html_ai.strip():
                    with open("preview_doubao.html", "w", encoding="utf-8") as f:
                        f.write(preview_html_ai)
                    final_preview_html = preview_html_ai

                if vue_code_ai.strip() or preview_html_ai.strip():
                    llm_used = True
                    generation_source = "doubao"
                    print("豆包生成成功")
                else:
                    llm_error = "豆包返回为空"
                    generation_source = "rule"
                    actual_model = "rule"
                    print("豆包返回为空，回退到规则生成")

            except Exception as e:
                llm_error = f"豆包生成失败：{str(e)}"
                generation_source = "rule"
                actual_model = "rule"
                print(llm_error)

    elif use_llm and model_name == "deepseek":


        if not deepseek_api_key:
            llm_error = "未读取到 DEEPSEEK_API_KEY，回退到规则生成"
            generation_source = "rule"
            actual_model = "rule"
            print(llm_error)

        else:
            try:
                print("开始调用 DeepSeek 根据结构化信息生成 Vue 代码和预览 HTML...")

                actual_model = deepseek_model

                deepseek = DeepSeekVueGenerator(
                    api_key=deepseek_api_key,
                    model=deepseek_model
                )

                ai_result = deepseek.generate_from_structure(
                    layout_data=layout_data,
                    detections=detections,
                    style_data=style_data,
                    user_config=user_config
                )

                vue_code_ai = ai_result.get("vue_code", "")
                preview_html_ai = ai_result.get("preview_html", "")

                preview_html_ai = sanitize_preview_html(preview_html_ai)

                if vue_code_ai.strip():
                    with open("GeneratedLayout_DeepSeek.vue", "w", encoding="utf-8") as f:
                        f.write(vue_code_ai)

                    final_vue_code = vue_code_ai

                if preview_html_ai.strip():
                    with open("preview_deepseek.html", "w", encoding="utf-8") as f:
                        f.write(preview_html_ai)

                    final_preview_html = preview_html_ai

                if vue_code_ai.strip() or preview_html_ai.strip():
                    llm_used = True
                    generation_source = "deepseek"
                    print("DeepSeek生成成功")

                else:
                    llm_error = "DeepSeek返回为空"
                    generation_source = "rule"
                    actual_model = "rule"
                    print("DeepSeek返回为空，回退到规则生成")

            except Exception as e:
                llm_error = f"DeepSeek生成失败，已回退千问VL：{str(e)}"
                print(llm_error)

                try:
                    actual_model = "qwen-vl-plus"

                    llm = LLMVueGenerator(
                        api_key=qwen_api_key,
                        model=actual_model
                    )

                    ai_result = llm.generate_from_image(
                        image_path=image_path,
                        layout_data=layout_data,
                        user_config=user_config,
                        style_data=style_data
                    )

                    vue_code_ai = ai_result.get("vue_code", "")
                    preview_html_ai = ai_result.get("preview_html", "")

                    preview_html_ai = sanitize_preview_html(preview_html_ai)

                    if vue_code_ai.strip():
                        with open("GeneratedLayout_AI.vue", "w", encoding="utf-8") as f:
                            f.write(vue_code_ai)

                        final_vue_code = vue_code_ai

                    if preview_html_ai.strip():
                        with open("preview_ai.html", "w", encoding="utf-8") as f:
                            f.write(preview_html_ai)

                        final_preview_html = preview_html_ai

                    if vue_code_ai.strip() or preview_html_ai.strip():
                        llm_used = True
                        generation_source = "qwen-vl-plus"
                        print("DeepSeek失败后，千问VL回退生成成功")
                    else:
                        generation_source = "rule"
                        actual_model = "rule"
                        print("千问VL回退也返回为空，使用规则生成")

                except Exception as qe:
                    llm_error = f"DeepSeek和千问VL均生成失败：{str(qe)}"
                    generation_source = "rule"
                    actual_model = "rule"
                    print(llm_error)

    elif use_llm and qwen_api_key:

        try:
            print("开始调用千问模型直接生成 Vue 代码和预览 HTML...")

            actual_model = qwen_model

            if model_name == "qwen-vl-plus":
                actual_model = "qwen-vl-plus"
            elif model_name == "qwen-vl-max":
                actual_model = "qwen-vl-max"
            else:
                actual_model = qwen_model

            llm = LLMVueGenerator(
                api_key=qwen_api_key,
                model=actual_model
            )

            ai_result = llm.generate_from_image(
                image_path=image_path,
                layout_data=layout_data,
                user_config=user_config,
                style_data=style_data
            )

            vue_code_ai = ai_result.get("vue_code", "")
            preview_html_ai = ai_result.get("preview_html", "")

            preview_html_ai = sanitize_preview_html(preview_html_ai)

            if vue_code_ai.strip():

                with open("GeneratedLayout_AI.vue", "w", encoding="utf-8") as f:
                    f.write(vue_code_ai)

                final_vue_code = vue_code_ai

            if preview_html_ai.strip():

                with open("preview_ai.html", "w", encoding="utf-8") as f:
                    f.write(preview_html_ai)

                final_preview_html = preview_html_ai

            if vue_code_ai.strip() or preview_html_ai.strip():

                llm_used = True
                generation_source = model_name

                print("千问生成成功")

            else:
                llm_error = "模型返回为空"
                generation_source = "rule"

                print("千问返回为空，回退到规则生成")

        except Exception as e:

            llm_error = str(e)
            generation_source = "rule"

            print("千问生成失败，回退到规则生成:", llm_error)

    else:

        if not qwen_api_key:
            llm_error = "未读取到 QWEN_API_KEY，使用规则生成"

            print(llm_error)

    print("最终生成来源:", generation_source)
    print("是否使用千问:", llm_used)
    print("LLM错误信息:", llm_error)

    # 6. 真实相似度评估
    similarity = {
        "enabled": False,
        "error": ""
    }

    try:
        print("开始计算页面复原相似度...")

        similarity = calculate_similarity_safely(
            image_path=image_path,
            preview_html=final_preview_html
        )

        print("相似度评估完成:", similarity)

    except Exception as e:
        similarity = {
            "enabled": False,
            "error": str(e)
        }

        print("相似度评估失败:", e)


    return {
        "vue_code": final_vue_code,
        "preview_html": final_preview_html,
        "layout_tree": layout_data,
        "detections": detections,
        "llm_used": llm_used,
        "llm_error": llm_error,
        "generation_source": generation_source,
        "user_config": user_config,
        "similarity": similarity,
        "style_data": style_data,
        "model_name": model_name,
        "actual_model": actual_model
    }