import base64
import json
import re
from openai import OpenAI


class LLMVueGenerator:
    def __init__(self, api_key, model="qwen-vl-plus"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = model

    def _encode_image_to_data_url(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        ext = image_path.split(".")[-1].lower()
        mime_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
        }
        mime_type = mime_map.get(ext, "image/png")
        return f"data:{mime_type};base64,{image_base64}"

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

    def _fallback_extract_html(self, text: str) -> str:
        html_match = re.search(r"<!DOCTYPE html>.*?</html>", text, re.S | re.I)
        if html_match:
            return html_match.group(0).strip()

        html_match = re.search(r"<html.*?</html>", text, re.S | re.I)
        if html_match:
            return html_match.group(0).strip()

        return ""

    def _fallback_extract_vue(self, text: str) -> str:
        vue_match = re.search(r"<template>.*?</style>", text, re.S | re.I)
        if vue_match:
            return vue_match.group(0).strip()

        return ""

    def generate_from_image(self, image_path: str, layout_data=None, user_config=None, style_data=None) -> dict:
        image_data_url = self._encode_image_to_data_url(image_path)

        layout_json = json.dumps(
            layout_data or [],
            ensure_ascii=False,
            indent=2
        )

        config_json = json.dumps(
            user_config or {},
            ensure_ascii=False,
            indent=2
        )
        style_json = json.dumps(
            style_data or {},
            ensure_ascii=False,
            indent=2
        )
        prompt = f"""
你是一名资深 UI 还原工程师和 Vue3 前端工程师。

你的任务是根据用户上传的 UI 截图生成对应的前端页面。
请注意：你不是自由设计页面，而是尽量还原截图中的页面结构、模块位置、布局比例和视觉风格。

====================
一、整体生成目标
====================
1. 优先还原页面“大结构”，包括：
   - 顶部区域
   - 左侧区域
   - 右侧内容区
   - 中间主体区
   - 表单区
   - 卡片区
   - banner 区
   - 底部区域

2. 其次还原：
   - 颜色风格
   - 字号层级
   - 间距比例
   - 按钮样式
   - 表单样式
   - 卡片样式

3. 不要求完全复原真实图片素材。
   如果截图中存在图片、海报、头像、banner、缩略图，而你无法准确获得素材，请使用灰色或深色占位块代替。

====================
二、页面结构判断规则
====================
请先观察截图属于哪种结构，再生成对应布局：

1. 如果是登录页：
   - 通常包含左右分栏或居中卡片
   - 表单区域包含标题、输入框、记住我、按钮等
   - 背景可以使用渐变或纯色

2. 如果是后台管理页：
   - 通常包含顶部栏、侧边栏、内容区
   - 主体区域可能包含卡片、表格、统计模块

3. 如果是门户/视频网站/内容首页：
   - 可能包含顶部导航
   - 可能包含左侧分类菜单
   - 主体区域包含 banner、推荐区、卡片网格

4. 如果是数据大屏：
   - 通常是深色背景
   - 多个图表卡片分布在左右或上下区域
   - 中间可能有地图或主视觉区域

5. 如果是普通表单页：
   - 表单项应纵向排列
   - 按钮位于表单底部或右侧

不要把所有图片都生成成同一种模板。
必须根据上传截图判断页面类型。

====================
三、通用布局约束
====================
1. 如果截图有顶部导航，顶部导航必须横向排列：
   display: flex;
   flex-direction: row;
   align-items: center;

2. 如果截图有左侧菜单，页面主体必须使用左右布局：
   display: flex;
   flex-direction: row;
   左侧菜单固定宽度，右侧内容 flex: 1;

3. 如果截图是左右分栏，必须保持左右分栏，不要上下堆叠。

4. 如果截图是卡片网格，卡片应使用 grid 或 flex-wrap，不要全部竖向堆成一列。

5. 不要给页面主体设置固定 height: 100vh 导致内容被裁剪。
   页面高度应自然撑开。

6. 不要生成内部滚动条。
   页面内容应该自然撑开，除非原图明显是滚动容器。

====================
四、通用文本排版规则【非常重要】
====================
这是所有页面都必须遵守的规则：

1. 所有标题、按钮、导航、标签、菜单文字默认必须横向排版。

2. 禁止中文文本出现“一字一行”的竖向堆叠。
   

3. 除非原图明确是竖排文字设计，否则不要生成竖排中文。

4. 如果文本因为容器太窄导致换行，应优先：
   - 扩大容器宽度
   - 减小字号
   - 缩短文本
   - 使用省略号
   而不是让文字一个字一行。

5. 标题、导航、按钮、菜单文字应尽量添加：
   white-space: nowrap;
   word-break: keep-all;

6. 普通段落可以自然换行，但不得每个字单独换行。

7. 大标题区域必须有足够宽度。
   标题容器宽度不要小于 240px。
   如果空间不足，应该缩小字号或只保留核心标题。

8. 导航栏文字不允许竖向排列。
   导航项之间应有合理 gap。

====================
五、图片与占位块规则【非常重要】
====================
1. 不要使用无效图片链接。
   禁止生成：
   hero.jpg
   banner.png
   poster.webp
   avatar.jpg
   /images/xxx.png
   这类本地不存在的路径。

2. 如果无法确认图片可用，必须用 div 占位块代替 img。

3. 占位块要保持图片区域比例，例如：
   - banner：大横向矩形
   - 卡片封面：矩形
   - 头像：圆形或小方块
   - 图标：小方块

4. 占位块可以显示简短文字：
   - 图片占位
   - Banner
   - Cover
   - Avatar

5. 占位块样式示例：
   background: #2f2f2f;
   border-radius: 8px;
   display: flex;
   align-items: center;
   justify-content: center;
   color: #aaa;

6. 不允许出现破损图片图标。
   如果需要图片区域，请直接使用 div，不要用 img。

====================

六、侧边栏布局强约束
====================
如果页面中存在纵向菜单、分类栏、目录栏、侧边导航等区域：

1. 必须将侧边栏和主内容区放在同一个父容器中。
2. 父容器必须使用横向布局：
   display: flex;
   flex-direction: row;

3. 侧边栏必须位于左侧：
   flex-shrink: 0;
   width: 160px 到 260px;

4. 主内容区必须位于右侧：
   flex: 1;

5. 禁止将主内容区放到侧边栏下方。
6. 禁止出现“左侧菜单在上方，主内容在下方”的布局。
7. 如果截图中左侧菜单从顶部延伸到页面下方，则生成结构必须类似：

<div class="layout-body">
  <aside class="sidebar">左侧菜单</aside>
  <main class="main-content">右侧内容</main>
</div>

8. sidebar 和 main-content 必须是同级元素。
====================
七、CSS 质量要求
====================
1. 使用语义化 class 名：
   .page
   .top-header
   .sidebar
   .main-content
   .hero
   .card-grid
   .card
   .login-panel
   .form-area

2. 布局必须清晰，避免大量无意义 div。

3. 样式写完整，不要依赖外部 CSS。

4. preview_html 的 CSS 必须写在 <style> 中。

5. Vue 代码使用 <style scoped>。

6. 不要输出 Vue 占位变量，例如：
   {{{{ logoText }}}}
   {{{{ pageTitle }}}}
   {{{{ buttonText }}}}

7. 生成内容要直接可运行，不要留下模板变量。

====================
八、视觉风格分析结果【必须参考】
====================
以下是系统从原始UI截图中提取到的视觉风格信息，包括背景色、主色调、整体明暗风格等。
生成页面时必须优先参考这些信息，尽量保持与原图一致。

style_data:
{style_json}

生成要求：
1. 如果 theme_type 为 dark，页面整体必须使用深色背景，不要生成白色页面。
2. 如果 theme_type 为 light，页面整体应保持浅色背景，不要生成深色大屏风格。
3. background_color 是原图估算背景色，应优先作为页面主体背景色参考。
4. dominant_colors 是原图主要颜色，应优先用于按钮、卡片、标题、边框、渐变等样式。
5. 如果 color_tendency 显示整体偏蓝、偏绿或偏暖，应在页面主色调中体现出来。
6. 不要随意更换原图整体色调。
7. 背景色、按钮色、卡片色、文字色要尽量贴近截图，不要自由发挥。
8. 如果 style_data 中存在 recommended_background，页面 body 或最外层容器必须优先使用该背景。
9. 如果原图整体色调偏蓝，禁止生成绿色、黄色或暖色主背景。
10. 如果原图存在渐变背景，必须保留渐变效果，不允许改成纯色背景。
11. 背景颜色、按钮颜色、卡片颜色必须优先参考 dominant_colors。
12. 不允许为了“美观”擅自修改原图主色调。
13. 颜色还原优先级高于创意设计。
14. 页面最终视觉效果应尽量接近上传截图，而不是自由发挥。
====================
九、用户配置
====================
如果 user_config 中存在 logo、标题、按钮文字、主题色等配置，可适当应用。
如果没有配置，就根据截图内容生成。

user_config:
{config_json}

====================
十、布局树辅助信息
====================
以下是系统视觉解析得到的布局树或检测信息。
它只是辅助参考，不一定完全准确。
如果布局树和截图冲突，以截图视觉内容为准。

layout_data:
{layout_json}

====================
十一、输出格式
====================
必须严格按以下格式输出。
不要输出解释说明。
不要输出 markdown。
不要输出多余文字。
请严格按照 style_data 中的颜色信息生成页面样式。
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
                    "content": (
                        "你是一个严格根据 UI 截图还原网页布局的前端工程师。"
                        "你必须优先保证布局结构正确，文本横向排版，图片使用占位块避免破图。"
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_url}
                        }
                    ]
                }
            ],
            temperature=0.01
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
            preview_html = self._fallback_extract_html(content)

        if not vue_code:
            vue_code = self._fallback_extract_vue(content)

        if not preview_html:
            raise ValueError("模型没有返回可用的 preview_html，说明本次视觉生成失败")

        if not vue_code:
            vue_code = """
<template>
  <div class="page">
    <p>页面已生成，请查看预览结果。</p>
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

        return {
            "vue_code": vue_code,
            "preview_html": preview_html
        }