import json
import re
from openai import OpenAI


class DeepSeekVueGenerator:
    def __init__(self, api_key, model="deepseek-chat"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = model

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

    def generate_from_structure(
        self,
        layout_data=None,
        detections=None,
        style_data=None,
        user_config=None
    ) -> dict:

        layout_json = json.dumps(layout_data or [], ensure_ascii=False, indent=2)
        detections_json = json.dumps(detections or [], ensure_ascii=False, indent=2)
        style_json = json.dumps(style_data or {}, ensure_ascii=False, indent=2)
        config_json = json.dumps(user_config or {}, ensure_ascii=False, indent=2)

        prompt = f"""
你是一名资深 Vue3 前端工程师，擅长根据结构化 UI 信息生成前端页面代码。

注意：你不能直接看到原始图片。
你只能根据系统提供的检测结果、布局树和视觉风格分析结果生成页面。
因此，你必须严格参考这些结构化信息，不要自由发挥。

====================
一、生成目标
====================
请根据 layout_data、detections、style_data 生成一个 Vue3 单文件组件和一个可直接预览的 HTML 页面。

生成结果应尽量满足：
1. 页面布局清晰；
2. 层级结构合理；
3. 颜色风格贴近 style_data；
4. 不使用外部图片；
5. 图片区域使用占位块；
6. 表单、按钮、卡片等元素要有基本样式；
7. 代码完整、可运行。
====================
重要约束：禁止自由设计
====================
1. 你不能重新设计一个新页面。
2. 你不能根据自己的审美生成新的卡片、手机壳、仪表盘或无关页面。
3. 必须严格根据 layout_data 中的层级、direction 和 bbox 生成页面。
4. 如果 layout_data 信息不足，也只能生成简化还原页面，不能凭空增加无关模块。
5. 页面元素数量应尽量接近 detections 和 layout_data 中的节点数量。
6. 不要生成“标题区域、Banner占位、卡片1、卡片2、底部信息”这种模板化页面，除非原始结构中确实存在。
7. 如果无法确定具体文本内容，可以使用“文本”“按钮”“输入框”等通用占位，但不能改变页面整体布局类型。
8. 生成页面必须以还原原图为目标，不是设计一个好看的新页面。
====================
二、视觉风格约束
====================
style_data:
{style_json}

要求：
1. 如果存在 recommended_background，页面主体背景必须优先使用它。
2. background_color 可作为页面背景参考。
3. dominant_colors 可用于按钮、标题、边框、卡片背景等。
4. 如果 theme_type 为 dark，则使用深色背景。
5. 如果 theme_type 为 light，则使用浅色背景。
6. 不要随意改变主色调。

====================
三、布局树信息
====================
layout_data:
{layout_json}

要求：
1. 根据 children 表示父子层级关系。
2. 根据 direction 判断 row 或 column 排列。
3. 根据 bbox 大致判断区域大小和相对位置。
4. 不要生成完全无关的页面。
布局还原要求：
1. bbox 表示元素在原图中的大致位置和尺寸，生成页面时应尽量保持相对比例。
2. 如果 direction 是 row，子元素应横向排列。
3. 如果 direction 是 column，子元素应纵向排列。
4. 容器不能随意居中成手机卡片，除非原图本身就是手机界面。
5. 不要把横向网页布局生成成竖向移动端页面。
6. 不要把登录页、后台页、课程页等页面类型随意改成其他类型。
====================
四、检测结果
====================
detections:
{detections_json}

====================
五、用户配置
====================
user_config:
{config_json}

====================
六、输出格式
====================
必须严格按以下格式输出。
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
                    "content": "你是一个严格根据结构化 UI 信息生成 Vue3 页面代码的前端工程师。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
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

        if not vue_code:
            vue_code = """
<template>
  <div class="page">
    <p>DeepSeek 已生成页面，请查看预览结果。</p>
  </div>
</template>

<script setup>
</script>

<style scoped>
.page {
  padding: 20px;
}
</style>
"""

        if not preview_html:
            raise ValueError("DeepSeek没有返回可用的 preview_html")

        return {
            "vue_code": vue_code,
            "preview_html": preview_html
        }