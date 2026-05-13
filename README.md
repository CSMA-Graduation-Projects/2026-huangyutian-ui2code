# 基于视觉理解的UI代码自动生成系统

基于多模态大模型与计算机视觉技术的 UI 代码自动生成系统，支持 UI 截图输入、界面结构分析、Vue 代码生成、HTML 预览生成、多模型切换以及多页面原型生成等功能，实现从 UI 图片到前端页面代码的自动化转换。

---

# 项目简介

本项目是一个面向前端开发场景的 UI 代码自动生成系统，主要用于解决传统前端开发过程中“设计稿需要人工转换为前端代码”的问题。

系统以 UI 界面截图作为输入，通过目标检测、布局分析、多模态大模型生成等方式，自动生成对应的 Vue 前端代码以及 HTML 页面预览结果，并支持布局树可视化、多模型切换、多页面原型生成等功能。

该系统适用于：

* 本科毕业设计演示
* UI 自动生成研究
* 前端开发辅助
* 原型页面快速生成
* 多模态代码生成实验

---

# 核心功能

* **UI 图片上传**

  * 支持本地 UI 截图上传
  * 支持图片预览

* **视觉解析**

  * YOLO 目标检测
  * OCR 文本提取
  * 布局关系分析
  * 布局树生成

* **多模态代码生成**

  * 基于大模型生成 Vue 页面代码
  * 自动生成 HTML 预览页面
  * 支持结构化 Prompt 输入

* **多模型切换**

  * Qwen-VL-Max
  * DeepSeek
  * 豆包视觉模型

* **结果展示**

  * Vue 代码展示
  * HTML 页面预览
  * iframe 渲染
  * JSON 中间结果展示

* **布局树可视化**

  * 页面结构树展示
  * 用户可读结构转换

* **多页面原型生成**

  * 页面队列管理
  * 页面切换预览
  * 多页面 HTML 导出

* **可视化编辑**

  * 页面局部修改
  * 结构调整
  * 结果重新渲染

---

# 技术栈

## 前端

* Vue3
* JavaScript
* HTML5
* CSS3

## 后端

* FastAPI
* Python

## 视觉解析

* YOLOv8
* OCR

## 大模型

* Qwen-VL-Max（阿里云百炼）
* DeepSeek
* 豆包视觉模型

## 数据处理

* JSON
* Layout Tree

---

# 系统整体架构

系统采用前后端分离架构：

* 前端负责：

  * 图片上传
  * 结果展示
  * 页面预览
  * 页面切换
  * 可视化交互

* 后端负责：

  * 图像处理
  * YOLO 检测
  * 布局分析
  * 大模型调用
  * 代码生成
  * HTML 生成

系统核心采用“双路径生成架构”：

1. 多模态大模型生成路径
2. 传统视觉解析辅助路径

---

# 项目目录结构

```bash
UI2Code_Project
│
├── backend                # 后端接口与服务
├── frontend               # Vue 前端项目
├── vision                 # YOLO 与视觉解析模块
├── uploads                # 上传图片目录
├── data                   # 中间 JSON 数据
│
├── GeneratedLayout.vue
├── GeneratedLayout_AI.vue
├── GeneratedLayout_DeepSeek.vue
├── GeneratedLayout_Doubao.vue
│
├── preview.html
├── preview_ai.html
├── preview_deepseek.html
├── preview_doubao.html
│
├── main.py
├── requirements.txt
├── .env
└── README.md
```

---

# 快速运行（本地开发）

# 一、环境准备

* Python 3.9+
* Node.js 18+
* npm
* YOLOv8
* API Key（Qwen / DeepSeek / 豆包）

---

# 二、后端运行

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置 `.env`

```env
QWEN_API_KEY=你的API_KEY
DEEPSEEK_API_KEY=你的API_KEY
DOUBAO_API_KEY=你的API_KEY
```

## 3. 启动后端

```bash
uvicorn main:app --reload
```

启动成功后：

```bash
http://127.0.0.1:8000
```

接口文档：

```bash
http://127.0.0.1:8000/docs
```

---

# 三、前端运行

进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动项目：

```bash
npm run dev
```

启动成功后：

```bash
http://localhost:5173
```

---

# 系统运行流程

1. 上传 UI 截图
2. YOLO 检测界面元素
3. OCR 提取文本内容
4. 构建布局树
5. 生成 Prompt
6. 调用多模态大模型
7. 生成 Vue 代码
8. 生成 HTML 预览
9. 前端展示结果

---

# 多模型支持说明

系统支持多模型切换：

| 模型          | 功能      |
| ----------- | ------- |
| Qwen-VL-Max | 主生成模型   |
| DeepSeek    | 代码优化与生成 |
| 豆包视觉模型      | 多模态页面理解 |

系统会根据选择自动调用对应接口。

---

# 多页面原型生成

系统支持：

* 页面队列管理
* 页面切换预览
* 多页面 HTML 导出
* 原型页面快速复刻

用户可以通过“加入页面队列”功能构建多个页面，并通过顶部导航按钮切换页面预览。

---

# 项目界面说明

## 1. 主界面

* UI 图片上传
* 模型选择
* 生成按钮

## 2. 中间结果展示

* YOLO 检测结果
* JSON 数据
* 布局树结构

## 3. 代码展示

* Vue 代码
* HTML 代码

## 4. 页面预览

* iframe 页面渲染
* 页面切换

## 5. 多页面原型

* 页面导航
* 页面队列
* 多页面导出

---

# 核心文件说明

| 文件                    | 作用           |
| --------------------- | ------------ |
| `main.py`             | FastAPI 后端入口 |
| `App.vue`             | 前端主页面        |
| `layout_tree.py`      | 布局树构建        |
| `llm_generator.py`    | 大模型调用        |
| `preview.html`        | HTML 预览      |
| `GeneratedLayout.vue` | Vue 代码生成结果   |
| `.env`                | API 配置       |

---

# 系统特色

* 多模态大模型生成
* YOLO + 布局树辅助解析
* 双路径生成结构
* 多模型切换
* 多页面原型生成
* HTML 实时预览
* 可视化布局展示

---

# 项目部署

## 前端打包

```bash
npm run build
```

## 后端部署

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## GitHub 部署建议

项目上传内容：

* frontend
* backend
* vision
* paper
* ppt
* README.md

不建议上传：

* venv
* yolov8n.pt
* node_modules

---

# 常见问题 FAQ

## Q1：模型调用失败怎么办？

检查 API Key 是否正确，网络是否正常。

## Q2：前端无法访问后端？

确认 FastAPI 已启动，端口一致。

## Q3：HTML 预览为空？

检查生成结果是否成功返回。

---

# 注意事项

* 本项目主要用于毕业设计与研究演示
* 生成结果仍可能需要人工调整
* 多模态模型生成结果会受到 Prompt 与输入图片影响
* 部分复杂页面可能存在布局偏差
需要自行配置 .env 文件中的 API Key 后运行系统
---

# 作者信息

* 作者：黄语田
* 学校：重庆邮电大学
* 专业：软件工程

---

# 致谢

感谢指导老师与相关开源项目提供的支持与帮助。

本项目仅用于毕业设计与学习研究。
