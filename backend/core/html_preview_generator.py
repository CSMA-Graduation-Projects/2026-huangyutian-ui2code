class HtmlPreviewGenerator:
    def generate(self, layout_nodes):
        body = []

        body.append('<div class="preview-root">')
        for node in layout_nodes:
            body.append(self._render_node(node, depth=1))
        body.append("</div>")

        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>UI Preview</title>
  <style>
    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      padding: 20px;
      font-family: Arial, sans-serif;
      background: #f8fafc;
    }}

    .preview-root {{
      min-height: 100vh;
      padding: 16px;
      background: white;
      border: 1px solid #dbe3ee;
      border-radius: 12px;
    }}

    .node-box {{
      border: 1px solid #94a3b8;
      background: #f8fbff;
      margin: 8px;
      padding: 8px;
      border-radius: 8px;
      min-height: 40px;
    }}

    .row {{
      display: flex;
      flex-direction: row;
      gap: 8px;
      align-items: stretch;
    }}

    .column {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .leaf {{
      background: #dbeafe;
      border: 1px dashed #60a5fa;
      min-height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #1e3a8a;
      font-size: 12px;
    }}

    .label {{
      display: inline-block;
      margin-bottom: 6px;
      font-size: 12px;
      color: #475569;
      background: #e2e8f0;
      padding: 2px 8px;
      border-radius: 999px;
    }}
  </style>
</head>
<body>
  {''.join(body)}
</body>
</html>
"""
        return html

    def _render_node(self, node, depth=0):
        direction = node.direction if node.direction in ["row", "column"] else ""
        label = node.direction if node.direction else "leaf"

        if not node.children:
            return f"""
<div class="node-box leaf">
  <button style="padding:6px 12px;">Button</button>
</div>
"""

        children_html = "".join([self._render_node(child, depth + 1) for child in node.children])

        return f"""
<div class="node-box {direction}">
  <div class="label">{label}</div>
  {children_html}
</div>
"""