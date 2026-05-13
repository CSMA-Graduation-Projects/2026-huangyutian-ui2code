import base64
import json
import mimetypes
import re
from openai import OpenAI


class DoubaoVueGenerator:
    def __init__(self, api_key, base_url, model):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model

    def _image_to_data_url(self, image_path: str) -> str:
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/png"

        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        return f"data:{mime_type};base64,{encoded}"

    def _extract_between(self, text: str, start_tag: str, end_tag: str) -> str:
        pattern = re.escape(start_tag) + r"(.*?)" + re.escape(end_tag)
        match = re.search(pattern, text, re.S)
        return match.group(1).strip() if match else ""

    def _clean_code_block(self, text: str) -> str:
        text = (text or "").strip()

        if text.startswith("```vue"):
            text = text[len("```vue"):].strip()
        elif text.startswith("```html"):
            text = text[len("```html"):].strip()
        elif text.startswith("```"):
            text = text[len("```"):].strip()

        if text.endswith("```"):
            text = text[:-3].strip()

        return text.strip()

    def generate_from_image(
        self,
        image_path: str,
        layout_data=None,
        detections=None,
        style_data=None,
        user_config=None
    ) -> dict:
        image_data_url = self._image_to_data_url(image_path)

        layout_json = json.dumps(layout_data or [], ensure_ascii=False, indent=2)
        detections_json = json.dumps(detections or [], ensure_ascii=False, indent=2)
        style_json = json.dumps(style_data or {}, ensure_ascii=False, indent=2)
        config_json = json.dumps(user_config or {}, ensure_ascii=False, indent=2)

        prompt = f"""
你是一名资深 Vue3 前端工程师，任务是根据用户上传的 UI 截图生成高度还原的前端页面。

你可以看到原始 UI 截图，同时也会收到系统提供的布局树、目标检测结果和视觉风格分析结果。
请以截图为第一依据，layout_data、detections、style_data 为辅助依据。

====================
核心目标
====================
请生成：
1. 一个完整 Vue3 单文件组件；
2. 一个可直接打开预览的完整 HTML 页面。

必须尽量还原截图中的：
1. 页面整体布局；
2. 背景颜色和渐变；
3. 卡片位置；
4. 按钮、输入框、文字区域；
5. 字体大小和粗细；
6. 圆角、阴影、边框；
7. 元素之间的相对位置和间距。

====================
强约束
====================
1. 不要重新设计一个新页面。
2. 不要生成与截图无关的模板页面。
3. 不要把横向网页生成成竖向手机页面。
4. 不要把登录页生成成后台页、课程页或卡片列表。
5. 不要随意新增大量截图中不存在的模块。
6. 如果图片中文字无法完全识别，可以使用相近文本或占位文本，但布局必须保持接近。
7. 图片区域可以使用深色或浅色占位块，但尺寸、位置、圆角应接近截图。
8. 生成页面应优先保证“像原图”，其次才是代码美观。

====================
视觉风格参考
====================
style_data:
{style_json}

如果 style_data 中有 recommended_background，应优先用于页面背景。
dominant_colors 应优先用于按钮、卡片、标题和边框。

====================
布局树参考
====================
layout_data:
{layout_json}

====================
检测结果参考
====================
detections:
{detections_json}

====================
用户配置
====================
user_config:
{config_json}

====================
输出格式
====================
必须严格按照以下格式输出。
不要输出解释说明。
不要输出 markdown。
不要输出多余文字。

<<<VUE_CODE>>>
这里放完整 Vue3 单文件组件代码
<<<END_VUE_CODE>>>

<<<PREVIEW_HTML>>>
这里放完整 HTML 文档
<<<END_PREVIEW_HTML>>>
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个擅长 UI 截图还原为 Vue3 和 HTML 的前端工程师。"
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_url
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            temperature=0.05
        )

        content = response.choices[0].message.content.strip()

        vue_code = self._extract_between(
            content,
            "<<<VUE_CODE>>>",
            "<<<END_VUE_CODE>>>"
        )

        preview_html = self._extract_between(
            content,
            "<<<PREVIEW_HTML>>>",
            "<<<END_PREVIEW_HTML>>>"
        )

        vue_code = self._clean_code_block(vue_code)
        preview_html = self._clean_code_block(preview_html)

        if not preview_html:
            raise ValueError("豆包没有返回可用的 preview_html")

        return {
            "vue_code": vue_code,
            "preview_html": preview_html
        }