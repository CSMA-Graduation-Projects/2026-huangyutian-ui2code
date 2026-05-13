from PIL import Image
from collections import Counter


def rgb_to_hex(color):
    r, g, b = color
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def get_brightness(color):
    r, g, b = color
    return 0.299 * r + 0.587 * g + 0.114 * b


def analyze_image_style(image_path, max_colors=6):
    """
    分析 UI 截图的基础视觉风格。
    输出主背景色、主要颜色、整体明暗风格等信息。
    """
    try:
        image = Image.open(image_path).convert("RGB")

        # 缩小图片，减少计算量
        small_img = image.resize((120, 120))

        pixels = list(small_img.getdata())

        # 简单过滤极端噪声点
        filtered_pixels = []
        for r, g, b in pixels:
            if r > 245 and g > 245 and b > 245:
                filtered_pixels.append((245, 245, 245))
            elif r < 10 and g < 10 and b < 10:
                filtered_pixels.append((10, 10, 10))
            else:
                filtered_pixels.append((r, g, b))

        color_counter = Counter(filtered_pixels)
        common_colors = color_counter.most_common(max_colors)

        dominant_colors = [rgb_to_hex(color) for color, _ in common_colors]

        # 取四角区域估算背景色
        width, height = small_img.size
        corner_pixels = []

        corner_size = 18
        regions = [
            (0, 0, corner_size, corner_size),
            (width - corner_size, 0, width, corner_size),
            (0, height - corner_size, corner_size, height),
            (width - corner_size, height - corner_size, width, height),
        ]

        for left, top, right, bottom in regions:
            for x in range(left, right):
                for y in range(top, bottom):
                    corner_pixels.append(small_img.getpixel((x, y)))

        background_rgb = Counter(corner_pixels).most_common(1)[0][0]
        background_color = rgb_to_hex(background_rgb)

        avg_brightness = sum(get_brightness(c) for c in pixels) / len(pixels)

        if avg_brightness < 85:
            theme_type = "dark"
            theme_desc = "整体偏深色背景"
        elif avg_brightness > 180:
            theme_type = "light"
            theme_desc = "整体偏浅色背景"
        else:
            theme_type = "medium"
            theme_desc = "整体明暗适中"

        # 粗略判断是否偏蓝 / 偏绿 / 偏红
        avg_r = sum(c[0] for c in pixels) / len(pixels)
        avg_g = sum(c[1] for c in pixels) / len(pixels)
        avg_b = sum(c[2] for c in pixels) / len(pixels)

        if avg_b > avg_r + 15 and avg_b > avg_g + 5:
            color_tendency = "blue"
            color_desc = "整体色调偏蓝"
        elif avg_g > avg_r + 15 and avg_g > avg_b + 5:
            color_tendency = "green"
            color_desc = "整体色调偏绿"
        elif avg_r > avg_g + 15 and avg_r > avg_b + 5:
            color_tendency = "red"
            color_desc = "整体色调偏红或偏暖"
        else:
            color_tendency = "neutral"
            color_desc = "整体色调较中性"

        if color_tendency == "blue":
            recommended_background = f"linear-gradient(135deg, {background_color}, #6bbcff)"
        elif color_tendency == "green":
            recommended_background = f"linear-gradient(135deg, {background_color}, #b9f6c6)"
        elif color_tendency == "red":
            recommended_background = f"linear-gradient(135deg, {background_color}, #ffd1d1)"
        else:
            recommended_background = background_color

        return {
            "enabled": True,
            "background_color": background_color,
            "dominant_colors": dominant_colors,
            "theme_type": theme_type,
            "theme_desc": theme_desc,
            "color_tendency": color_tendency,
            "color_desc": color_desc,
            "avg_brightness": round(avg_brightness, 2),
            "recommended_background": recommended_background,
            "style_instruction": f"页面整体背景应优先使用 {recommended_background}，整体色调应保持{color_desc}，不要随意改成其他色系。",
        }

    except Exception as e:
        return {
            "enabled": False,
            "error": str(e),
            "background_color": "",
            "dominant_colors": [],
            "theme_type": "",
            "theme_desc": "",
            "color_tendency": "",
            "color_desc": ""
        }