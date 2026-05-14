<template>
  <div class="page">
    <div class="main-card">
      <header class="header">
        <h1>UI2Code 系统</h1>
        <p class="subtitle">上传界面图片，自动生成页面，并支持生成后可视化编辑与结构还原度评估。</p>
      </header>

      <section class="upload-section">
        <div class="upload-box">
          <label class="file-label">
            <input ref="fileInput" type="file" accept="image/*" @change="handleFile" />
            <span>选择图片</span>
          </label>
          
          <span class="file-name" v-if="file">{{ file.name }}</span>
          <span class="file-name empty" v-else>尚未选择文件</span>
<button class="secondary-btn" @click="startScreenCapture">
               屏幕截图
          </button>
<select v-model="selectedModel" class="model-select">
 <option value="qwen-vl-plus">千问VL-Plus模型（默认）</option>
<option value="qwen-vl-max">千问VL-Max模型（高质量）</option>
<option value="doubao">豆包视觉模型</option>
<option value="deepseek">DeepSeek模型</option>
<option value="rule">规则生成（兜底）</option>
</select>
          <div class="action-group">
            <button class="primary-btn" @click="uploadImage" :disabled="!file || loading">
              {{ loading ? "识别中..." : "上传并识别" }}
            </button>
           
            <button class="secondary-btn" @click="resetAll">清空重置</button>
            <button class="secondary-btn" @click="downloadCode" :disabled="!code">下载 Vue 文件</button>
            <button class="secondary-btn" @click="downloadEditedHtml" :disabled="!previewHtml">
              下载编辑后 HTML
            </button>
            <button class="secondary-btn" @click="downloadMultiPageHtml" :disabled="pageList.length === 0">
              下载多页面 HTML
            </button>
          </div>
        </div>
      </section>

      <section v-if="imageUrl" class="panel">
        <h2>上传图片预览</h2>
        <div class="image-preview-wrap">
          <img :src="imageUrl" class="image-preview" />
        </div>
      </section>

      <section v-if="pageList.length" class="panel multi-page-panel">
        <h2>多页面截图队列</h2>
        <p class="multi-page-tip">
          每识别完成一个页面后，点击“加入页面队列”。队列中的页面可通过按钮切换预览，用于模拟多页面网站或应用的页面跳转关系。
        </p>
        <div class="page-list">
          <div v-for="(item, index) in pageList" :key="item.id" class="page-item" :class="{ active: currentPageIndex === index }">
            <div class="page-thumb" v-if="item.imageUrl">
              <img :src="item.imageUrl" />
            </div>
            <div class="page-info">
              <strong>{{ item.name }}</strong>
              <span>{{ item.modelText }}</span>
            </div>
            <div class="page-actions">
              <button class="secondary-btn small" @click="previewQueuePage(index)">切换预览</button>
              <button class="secondary-btn small danger" @click="removeQueuePage(index)">删除</button>
            </div>
          </div>
        </div>
      </section>

      <section v-if="code || previewHtml" class="panel">
        <div class="result-header">
          <div class="tabs">
            <button :class="{ active: tab === 'preview' }" @click="tab = 'preview'">预览</button>
            <button :class="{ active: tab === 'code' }" @click="tab = 'code'">代码</button>
            <button :class="{ active: tab === 'similarity' }" @click="tab = 'similarity'">结构还原度</button>
            <button :class="{ active: tab === 'layout' }" @click="tab = 'layout'">布局树</button>
            <button :class="{ active: tab === 'detect' }" @click="tab = 'detect'">检测结果</button>
          </div>

          <div class="edit-actions" v-if="previewHtml">
            <button class="secondary-btn" @click="addCurrentAsPage">加入页面队列</button>
            <button class="edit-btn" :class="{ active: editMode }" @click="toggleEditMode">
              {{ editMode ? "退出编辑模式" : "进入编辑模式" }}
            </button>
            <button class="secondary-btn" @click="undoEdit" :disabled="!editMode || editHistory.length === 0">
              撤销上一步
            </button>
            <button class="secondary-btn" @click="restoreDefaultPreview" :disabled="!editMode">
              恢复默认
            </button>
          </div>
        </div>

        <div v-if="editMode && tab === 'preview'" class="edit-tip">
          当前为编辑模式：先点击预览中的元素进行选中；需要移动时点击“开启拖动”，拖动完成后点击“确认位置”。
        </div>

        <div v-if="editMode && selectedTag" class="editor-panel">
          <h3>元素编辑</h3>

          <div class="editor-grid">
            <label>
              <span>文本内容</span>
              <input v-model="editText" type="text" placeholder="请输入新的文本" />
            </label>

            <label>
              <span>文字颜色</span>
              <input v-model="editColor" type="color" />
            </label>

            <label>
              <span>背景颜色</span>
              <input v-model="editBgColor" type="color" />
            </label>

            <label>
              <span>字号(px)</span>
              <input v-model="editFontSize" type="number" min="10" max="80" />
            </label>
          </div>

          <div class="editor-actions">
            <button class="primary-btn small" @click="applyElementEdit">应用修改</button>

            <button v-if="!dragMode" class="secondary-btn small" @click="startDragMode">
              开启拖动
            </button>

            <button v-if="dragMode" class="primary-btn small green" @click="confirmDrag">
              确认位置
            </button>

            <button v-if="dragMode" class="secondary-btn small danger" @click="cancelDrag">
              取消拖动
            </button>

            <button class="secondary-btn small" @click="clearSelection">取消选择</button>
          </div>

          <p v-if="dragMode" class="drag-tip">
            已开启拖动：请在预览区按住当前选中的元素进行移动，移动完成后点击“确认位置”。
          </p>
        </div>

        <div class="tab-content">
          <div v-if="tab === 'preview'">
            <iframe
              ref="previewFrame"
              class="frame auto-frame"
              :srcdoc="previewHtml"
              @load="handleFrameLoad"
            ></iframe>
          </div>

          <div v-if="tab === 'code'">
  <div class="code-mode-bar">
    <span>代码显示模式：</span>
    <button
      :class="{ active: codeTheme === 'dark' }"
      @click="codeTheme = 'dark'"
    >
      黑夜模式
    </button>
    <button
      :class="{ active: codeTheme === 'light' }"
      @click="codeTheme = 'light'"
    >
      白天模式
    </button>
  </div>

  <pre :class="['code-block', codeTheme === 'light' ? 'code-block-light' : 'code-block-dark']">
{{ code }}
  </pre>
</div>

          <div v-if="tab === 'similarity'">
            <div v-if="similarity.enabled" class="similarity-user-panel">
              <div class="restore-overview">
                <div class="restore-circle" :style="{ background: scoreCircleBackground }">
                  <div class="restore-inner">
                    <strong>{{ structureScore.toFixed(2) }}%</strong>
                    <span>结构还原度</span>
                  </div>
                </div>

                <div class="restore-summary">
                  <h3>{{ restoreLevel.title }}</h3>
                  <p>{{ restoreLevel.desc }}</p>
                  <div class="restore-badge">{{ restoreLevel.badge }}</div>
                </div>
              </div>

              <div class="restore-detail-grid">
                <div class="restore-card">
                  <div class="restore-card-top">
                    <span>布局结构</span>
                    <strong>{{ layoutReadable.level }}</strong>
                  </div>
                  <div class="star-line">{{ layoutReadable.stars }}</div>
                  <p>{{ layoutReadable.desc }}</p>
                </div>

                <div class="restore-card">
                  <div class="restore-card-top">
                    <span>结构轮廓</span>
                    <strong>{{ outlineReadable.level }}</strong>
                  </div>
                  <div class="star-line">{{ outlineReadable.stars }}</div>
                  <p>{{ outlineReadable.desc }}</p>
                </div>

                <div class="restore-card">
                  <div class="restore-card-top">
                    <span>像素参考</span>
                    <strong>{{ pixelReadable.level }}</strong>
                  </div>
                  <div class="star-line">{{ pixelReadable.stars }}</div>
                  <p>{{ pixelReadable.desc }}</p>
                </div>
              </div>

              <div class="metric-explain">
                <h4>评估原理说明</h4>
                <p>
                  系统会先把生成出的预览页面渲染成截图，然后与原始 UI 图片缩放到相同尺寸。
                  主指标“结构还原度”会对两张图进行灰度化、模糊处理和边缘提取，弱化真实图片素材、
                  颜色和纹理细节的影响，重点比较页面区域划分、模块位置和整体布局轮廓。
                </p>
                <div class="raw-metrics">
                  <span>结构 SSIM：{{ similarity.structure_ssim ?? similarity.ssim ?? "-" }}</span>
                  <span>结构评分：{{ structureScore.toFixed(2) }}%</span>
                  <span>像素 SSIM：{{ similarity.pixel_ssim ?? "-" }}</span>
                  <span>MSE：{{ similarity.mse ?? "-" }}</span>
                  <span>PSNR：{{ similarity.psnr ?? "-" }} dB</span>
                  <span>原图尺寸：{{ originalSizeText }}</span>
                </div>
              </div>
            </div>

            <div v-else class="similarity-empty">
              <h3>结构还原度评估未生成</h3>
              <p>{{ similarity.error || "暂无评估数据" }}</p>
            </div>
          </div>

          <div v-if="tab === 'layout'">
            <div class="layout-tree-panel">
              <div class="layout-tree-header">
                <h3>布局树结构</h3>
                <p>该结构由检测结果与布局增强规则生成，用于表示页面区域、容器、表单、按钮等层级关系。</p>
              </div>

              <div v-if="layoutTree && layoutTree.length" class="tree-visual">
                <LayoutTreeNode
                  v-for="(node, index) in layoutTree"
                  :key="index"
                  :node="node"
                  :level="0"
                />
              </div>

              <div v-else class="empty-state">
                暂无布局树数据
              </div>
            </div>
          </div>

          <div v-if="tab === 'detect'">

          <div class="detect-result-wrapper">

  <div v-if="detectImageUrl" class="detect-image-box">
    <h3>YOLO检测结果图</h3>

    <img
      :src="detectImageUrl"
      alt="检测结果"
      class="detect-image"
    />
  </div>

<div :class="['detect-json-box', detectTheme === 'light' ? 'detect-json-light' : 'detect-json-dark']">
  <div class="detect-json-header">
    <h3>检测结果JSON</h3>

    <div class="code-mode-bar">
      <span>显示模式：</span>
      <button
        :class="{ active: detectTheme === 'dark' }"
        @click="detectTheme = 'dark'"
      >
        黑夜模式
      </button>
      <button
        :class="{ active: detectTheme === 'light' }"
        @click="detectTheme = 'light'"
      >
        白天模式
      </button>
    </div>
  </div>

  <pre>{{ JSON.stringify(detections, null, 2) }}</pre>
</div>

</div>
          </div>
        </div>
      </section>

      <section v-if="llmStatus" class="panel">
        <h2>生成方式</h2>
       <p v-if="llmUsed" class="ok-text">
  当前结果由{{ formatGenerationSource(generationSource) }}生成
</p>

<p v-else class="warn-text">
  当前结果由{{ formatGenerationSource(generationSource) }}生成
</p>

<p v-if="llmError" class="error-text">
  大模型错误信息：{{ llmError }}
</p>
      </section>

      <section v-if="error" class="panel error-panel">
        <h2>错误信息</h2>
        <p class="error-text">{{ error }}</p>
      </section>
    </div>
  </div>
  <div v-if="cropVisible" class="crop-mask">
  <div class="crop-modal">
    <div class="crop-header">
      <h3>框选截图区域</h3>
      <button class="secondary-btn small" @click="closeCrop">关闭</button>
    </div>

    <p class="crop-tip">
      请在截图上按住鼠标拖动，框选需要识别的UI区域。
    </p>

    <div
      class="crop-stage"
      ref="cropStageRef"
      @mousedown="startCrop"
      @mousemove="moveCrop"
      @mouseup="endCrop"
    >
      <img
        :src="screenImageUrl"
        ref="screenImageRef"
        class="crop-image"
      />

      <div
        v-if="cropBox.visible"
        class="crop-box"
        :style="{
          left: cropBox.x + 'px',
          top: cropBox.y + 'px',
          width: cropBox.width + 'px',
          height: cropBox.height + 'px'
        }"
      ></div>
    </div>

    <div class="crop-actions">
      <button class="primary-btn" @click="confirmCrop">确认裁剪并使用</button>
      <button class="secondary-btn" @click="closeCrop">取消</button>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, nextTick, watch, computed, defineComponent, h } from "vue"

const LayoutTreeNode = defineComponent({
  name: "LayoutTreeNode",
  props: {
    node: { type: Object, required: true },
    level: { type: Number, default: 0 }
  },
  setup(props) {
    const getRoleText = (role) => {
      const roleMap = {
        page: "页面根节点",
        screen: "页面主体容器",
        "left-visual-panel": "左侧视觉区域",
        "right-form-panel": "右侧表单区域",
        "main-title": "主标题",
        "data-card-group": "数据卡片组",
        "stat-card": "统计卡片",
        "form-title": "表单标题",
        input: "输入框",
        button: "按钮",
        header: "顶部区域",
        "main-content": "主内容区域",
        banner: "横幅区域",
        "card-list": "卡片列表",
        card: "卡片",
        footer: "底部区域",
        "top-section": "上方区域",
        "content-section": "内容区域",
        "bottom-section": "底部区域",
        "detected-element": "检测元素"
      }
      return roleMap[role] || role || "未命名区域"
    }

    const formatBbox = (bbox) => {
      if (!bbox || !bbox.length) return "无"
      return bbox.map((item) => Math.round(Number(item))).join(", ")
    }

    const getNodeClass = (node) => [
      "tree-node",
      `tree-node-${node.type || "unknown"}`,
      node.children && node.children.length ? "has-children" : "is-leaf"
    ]

    return () =>
      h("div", { class: "tree-node-wrap" }, [
        h(
          "div",
          {
            class: getNodeClass(props.node),
            style: { marginLeft: `${props.level * 28}px` }
          },
          [
            h("div", { class: "tree-node-main" }, [
              h("span", { class: "tree-node-icon" }, props.node.children?.length ? "▾" : "•"),
              h("span", { class: "tree-node-role" }, getRoleText(props.node.role)),
              h("span", { class: "tree-node-type" }, props.node.type || "-"),
              props.node.direction
                ? h("span", { class: "tree-node-direction" }, props.node.direction)
                : null
            ]),
            h("div", { class: "tree-node-meta" }, [
              h("span", null, `bbox: [${formatBbox(props.node.bbox)}]`),
              props.node.confidence !== null && props.node.confidence !== undefined
                ? h("span", null, `置信度: ${Number(props.node.confidence).toFixed(3)}`)
                : null,
              props.node.class_id !== null && props.node.class_id !== undefined
                ? h("span", null, `类别: ${props.node.class_id}`)
                : null
            ])
          ]
        ),
        props.node.children && props.node.children.length
          ? h(
              "div",
              { class: "tree-children" },
              props.node.children.map((child, index) =>
                h(LayoutTreeNode, {
                  key: index,
                  node: child,
                  level: props.level + 1
                })
              )
            )
          : null
      ])
  }
})

const file = ref(null)
const fileInput = ref(null)
const cropVisible = ref(false)
const screenImageUrl = ref("")
const screenImageBlob = ref(null)
const cropStageRef = ref(null)
const screenImageRef = ref(null)
const selectedModel = ref("qwen-vl-plus")
const generationSource = ref("")
const cropBox = ref({
  visible: false,
  startX: 0,
  startY: 0,
  x: 0,
  y: 0,
  width: 0,
  height: 0,
  dragging: false
})
const previewFrame = ref(null)

const imageUrl = ref("")
const code = ref("")
const previewHtml = ref("")
const originalPreviewHtml = ref("")
const layoutTree = ref([])
const detections = ref([])
const detectImageUrl = ref('')
const similarity = ref({})
const error = ref("")
const tab = ref("preview")
const loading = ref(false)
const codeTheme = ref("dark")
const detectTheme = ref("dark")

const llmUsed = ref(false)
const llmError = ref("")
const llmStatus = ref(false)
const pageList = ref([])
const currentPageIndex = ref(-1)

const editMode = ref(false)
const selectedElement = ref(null)
const selectedTag = ref("")
const editText = ref("")
const editColor = ref("#000000")
const editBgColor = ref("#ffffff")
const editFontSize = ref(16)

const editHistory = ref([])
const dragMode = ref(false)
const dragOriginalHtml = ref("")
let dragState = null
let uploadController = null

const structureScore = computed(() => {
  return Number(
    similarity.value?.structure_score_percent ??
    similarity.value?.ssim_percent ??
    0
  )
})

const scoreCircleBackground = computed(() => {
  const score = structureScore.value
  return `conic-gradient(#1677ff ${score * 3.6}deg, #e2e8f0 0deg)`
})

const originalSizeText = computed(() => {
  const size = similarity.value?.original_size
  if (!size) return "-"
  return `${size.width} × ${size.height}`
})

const restoreLevel = computed(() => {
  const score = structureScore.value

  if (score >= 80) {
    return {
      title: "结构还原效果优秀",
      badge: "高度接近原图布局",
      desc: "生成页面与原图在整体区域划分、模块位置和布局轮廓上较为接近，适合作为最终页面基础。"
    }
  }

  if (score >= 60) {
    return {
      title: "结构还原效果良好",
      badge: "整体结构可用",
      desc: "页面主体结构与原图基本接近，局部模块比例或位置仍可通过编辑模式继续优化。"
    }
  }

  if (score >= 40) {
    return {
      title: "结构还原效果一般",
      badge: "需要局部调整",
      desc: "页面已经生成主要结构，但在区域比例、模块位置或内容排列上仍存在明显差异。"
    }
  }

  return {
    title: "结构还原效果偏低",
    badge: "建议重新生成或手动修正",
    desc: "生成页面与原图布局轮廓差异较大，建议重新识别，或使用编辑模式调整主要布局。"
  }
})

const layoutReadable = computed(() => {
  const score = structureScore.value

  if (score >= 75) {
    return {
      level: "较好",
      stars: "⭐⭐⭐⭐☆",
      desc: "页面整体布局与原图较接近，主要区域的位置关系基本正确。"
    }
  }

  if (score >= 45) {
    return {
      level: "一般",
      stars: "⭐⭐⭐☆☆",
      desc: "页面大体结构已生成，但部分区域的位置或比例仍有偏差。"
    }
  }

  return {
    level: "较弱",
    stars: "⭐⭐☆☆☆",
    desc: "页面结构与原图差距较明显，需要进一步调整主区域布局。"
  }
})

const outlineReadable = computed(() => {
  const score = structureScore.value

  if (score >= 75) {
    return {
      level: "清晰",
      stars: "⭐⭐⭐⭐☆",
      desc: "页面边缘轮廓与原图较一致，模块分布关系较清楚。"
    }
  }

  if (score >= 45) {
    return {
      level: "一般",
      stars: "⭐⭐⭐☆☆",
      desc: "页面轮廓有一定相似性，但模块边界和局部比例仍有偏差。"
    }
  }

  return {
    level: "较弱",
    stars: "⭐⭐☆☆☆",
    desc: "结构轮廓差异较大，可能存在模块位置、大小或层级不准确的问题。"
  }
})

const pixelReadable = computed(() => {
  const pixel = Number(
    similarity.value?.pixel_ssim_percent ??
    similarity.value?.ssim_percent ??
    0
  )

  if (pixel >= 70) {
    return {
      level: "较好",
      stars: "⭐⭐⭐⭐☆",
      desc: "像素层面也有较高相似性，颜色和素材差异相对较小。"
    }
  }

  if (pixel >= 40) {
    return {
      level: "参考",
      stars: "⭐⭐⭐☆☆",
      desc: "像素相似度受真实图片素材、颜色和文字细节影响，仅作为辅助参考。"
    }
  }

  return {
    level: "偏低",
    stars: "⭐⭐☆☆☆",
    desc: "像素差异较大，主要受原图真实素材、图片内容和颜色细节影响。"
  }
})

const handleFile = (e) => {
  const selected = e.target.files[0]
  file.value = selected || null
  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value)
  imageUrl.value = file.value ? URL.createObjectURL(file.value) : ""
}

const startScreenCapture = async () => {
  try {
    error.value = ""

    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: true,
      audio: false
    })

    const video = document.createElement("video")
    video.srcObject = stream
    video.play()

    await new Promise((resolve) => {
      video.onloadedmetadata = resolve
    })

    const canvas = document.createElement("canvas")
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const ctx = canvas.getContext("2d")
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    stream.getTracks().forEach((track) => track.stop())

    canvas.toBlob((blob) => {
      if (!blob) {
        error.value = "截图失败，请重新尝试"
        return
      }

      screenImageBlob.value = blob

      if (screenImageUrl.value) URL.revokeObjectURL(screenImageUrl.value)
      screenImageUrl.value = URL.createObjectURL(blob)

      cropVisible.value = true
      cropBox.value = {
        visible: false,
        startX: 0,
        startY: 0,
        x: 0,
        y: 0,
        width: 0,
        height: 0,
        dragging: false
      }
    }, "image/png")
  } catch (e) {
    error.value = "屏幕截图失败或用户取消了截图"
  }
}

const getCropPoint = (event) => {
  const stage = cropStageRef.value
  if (!stage) return { x: 0, y: 0 }

  const rect = stage.getBoundingClientRect()

  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top
  }
}

const startCrop = (event) => {
  const point = getCropPoint(event)

  cropBox.value = {
    visible: true,
    startX: point.x,
    startY: point.y,
    x: point.x,
    y: point.y,
    width: 0,
    height: 0,
    dragging: true
  }
}

const moveCrop = (event) => {
  if (!cropBox.value.dragging) return

  const point = getCropPoint(event)

  const x = Math.min(point.x, cropBox.value.startX)
  const y = Math.min(point.y, cropBox.value.startY)
  const width = Math.abs(point.x - cropBox.value.startX)
  const height = Math.abs(point.y - cropBox.value.startY)

  cropBox.value = {
    ...cropBox.value,
    x,
    y,
    width,
    height
  }
}

const endCrop = () => {
  cropBox.value.dragging = false
}

const confirmCrop = () => {
  const img = screenImageRef.value
  if (!img || !screenImageBlob.value) return

  if (cropBox.value.width < 20 || cropBox.value.height < 20) {
    error.value = "请选择有效的截图区域"
    return
  }

  const displayWidth = img.clientWidth
  const displayHeight = img.clientHeight
  const naturalWidth = img.naturalWidth
  const naturalHeight = img.naturalHeight

  const scaleX = naturalWidth / displayWidth
  const scaleY = naturalHeight / displayHeight

  const sx = cropBox.value.x * scaleX
  const sy = cropBox.value.y * scaleY
  const sw = cropBox.value.width * scaleX
  const sh = cropBox.value.height * scaleY

  const canvas = document.createElement("canvas")
  canvas.width = sw
  canvas.height = sh

  const ctx = canvas.getContext("2d")
  ctx.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh)

  canvas.toBlob((blob) => {
    if (!blob) {
      error.value = "裁剪失败，请重新尝试"
      return
    }

    const screenshotFile = new File(
      [blob],
      `screen_crop_${Date.now()}.png`,
      { type: "image/png" }
    )

    file.value = screenshotFile

    if (imageUrl.value) URL.revokeObjectURL(imageUrl.value)
    imageUrl.value = URL.createObjectURL(screenshotFile)

    cropVisible.value = false

    if (fileInput.value) fileInput.value.value = ""
  }, "image/png")
}

const closeCrop = () => {
  cropVisible.value = false
}


const addCurrentAsPage = () => {
  if (!previewHtml.value) {
    error.value = "请先上传并识别一个页面"
    return
  }

  const pageName = `页面${pageList.value.length + 1}`

  pageList.value.push({
    id: Date.now() + Math.random(),
    name: pageName,
    imageUrl: imageUrl.value,
    previewHtml: previewHtml.value,
    code: code.value,
    modelText: formatGenerationSource(generationSource.value)
  })

  currentPageIndex.value = pageList.value.length - 1
  error.value = ""
}

const removeQueuePage = (index) => {
  pageList.value.splice(index, 1)

  if (!pageList.value.length) {
    currentPageIndex.value = -1
    return
  }

  if (currentPageIndex.value >= pageList.value.length) {
    currentPageIndex.value = pageList.value.length - 1
  }
}

const previewQueuePage = (index) => {
  const item = pageList.value[index]
  if (!item) return

  currentPageIndex.value = index
  previewHtml.value = item.previewHtml
  originalPreviewHtml.value = item.previewHtml
  code.value = item.code || ""
  tab.value = "preview"
  llmStatus.value = true
  llmUsed.value = true
  llmError.value = ""
  generationSource.value = "multi-page"
}

const resetAll = () => {
  if (uploadController) {
  uploadController.abort()
  uploadController = null
}

loading.value = false
  file.value = null
  imageUrl.value = ""
  code.value = ""
  previewHtml.value = ""
  originalPreviewHtml.value = ""
  layoutTree.value = []
  detections.value = []
  similarity.value = {}
  error.value = ""
  llmUsed.value = false
  llmError.value = ""
  llmStatus.value = false
  pageList.value = []
  currentPageIndex.value = -1
  tab.value = "preview"

  editMode.value = false
  editHistory.value = []
  dragMode.value = false
  dragOriginalHtml.value = ""
  clearSelection()

  if (fileInput.value) fileInput.value.value = ""
}

const uploadImage = async () => {
  if (!file.value) return

  loading.value = true
  error.value = ""
  editMode.value = false
  editHistory.value = []
  dragMode.value = false
  clearSelection()

  try {
    const formData = new FormData()
    formData.append("file", file.value)
    formData.append("model_name", selectedModel.value)

    uploadController = new AbortController()
    
   const res = await fetch("https://two026-huangyutian-ui2code.onrender.com/upload", {
      method: "POST",
      body: formData,
      signal: uploadController.signal
    })

    if (!res.ok) {
      const text = await res.text()
      throw new Error(`后端请求失败：${res.status} ${text}`)
    }

    const data = await res.json()

    code.value = data.code || ""
    previewHtml.value = data.preview_html || ""
    originalPreviewHtml.value = data.preview_html || ""
    layoutTree.value = data.layout_tree || []
    detections.value = data.detections || []
    detectImageUrl.value = data.detect_image_url || ''
    similarity.value = data.similarity || {}
    llmUsed.value = data.llm_used || false
    llmError.value = data.llm_error || ""
    generationSource.value = data.generation_source || data.model_name || ""
    llmStatus.value = true
    tab.value = "preview"
  } catch (e) {

  if (e.name === "AbortError") {
    error.value = ""
    return
  }

  error.value = e.message || "请求失败"

} finally {
  loading.value = false
  uploadController = null
}
}

const handleFrameLoad = () => {
  fixBrokenImages()
  resizePreviewFrame()
  if (editMode.value) enableFrameEditing()
}

const fixBrokenImages = () => {
  const iframe = previewFrame.value
  if (!iframe) return

  const doc = iframe.contentDocument || iframe.contentWindow?.document
  if (!doc) return

  const images = doc.querySelectorAll("img")

  images.forEach((img) => {
    img.onerror = null

    const width = img.getAttribute("width") || img.style.width || "100%"
    const height = img.getAttribute("height") || img.style.height || "120px"
    const altText = img.getAttribute("alt") || "图片占位"

    img.onerror = () => {
      const placeholder = doc.createElement("div")
      placeholder.className = "ui2code-image-placeholder"
      placeholder.innerText = altText
      placeholder.style.width = width
      placeholder.style.height = height
      placeholder.style.minHeight = "90px"
      placeholder.style.background = "#2f2f2f"
      placeholder.style.borderRadius = "8px"
      placeholder.style.display = "flex"
      placeholder.style.alignItems = "center"
      placeholder.style.justifyContent = "center"
      placeholder.style.color = "#aaa"
      placeholder.style.fontSize = "14px"
      placeholder.style.border = "1px solid #444"

      img.replaceWith(placeholder)
    }

    if (img.complete && img.naturalWidth === 0) {
      img.onerror()
    }
  })
}

const resizePreviewFrame = () => {
  nextTick(() => {
    const iframe = previewFrame.value
    if (!iframe) return

    try {
      const doc = iframe.contentDocument || iframe.contentWindow?.document
      if (!doc) return

      const bodyHeight = doc.body ? doc.body.scrollHeight : 0
      const htmlHeight = doc.documentElement ? doc.documentElement.scrollHeight : 0
      const finalHeight = Math.max(bodyHeight, htmlHeight, 500)
      iframe.style.height = `${finalHeight + 30}px`
    } catch (err) {
      console.error("预览区高度调整失败：", err)
    }
  })
}

watch(previewHtml, async () => {
  await nextTick()
  resizePreviewFrame()
})

const toggleEditMode = async () => {
  editMode.value = !editMode.value
  tab.value = "preview"
  await nextTick()

  if (editMode.value) {
    enableFrameEditing()
  } else {
    if (dragMode.value) cancelDrag()
    clearSelection()
    removeFrameEditingStyle()
    syncPreviewHtmlFromFrame()
  }
}

const saveHistory = () => {
  const current = getCurrentFrameHtml()
  if (!current) return
  editHistory.value.push(current)
  if (editHistory.value.length > 30) editHistory.value.shift()
}

const undoEdit = async () => {
  if (editHistory.value.length === 0) return
  const last = editHistory.value.pop()
  previewHtml.value = last
  dragMode.value = false

  await nextTick()
  clearSelection()
  if (editMode.value) enableFrameEditing()
}

const restoreDefaultPreview = async () => {
  if (!originalPreviewHtml.value) return

  saveHistory()
  previewHtml.value = originalPreviewHtml.value
  dragMode.value = false

  await nextTick()
  clearSelection()
  if (editMode.value) enableFrameEditing()
}

const enableFrameEditing = () => {
  const iframe = previewFrame.value
  if (!iframe) return

  const doc = iframe.contentDocument || iframe.contentWindow?.document
  if (!doc || !doc.body) return

  injectFrameEditingStyle(doc)

  doc.body.onclick = (event) => {
    if (!editMode.value || dragMode.value) return
    event.preventDefault()
    event.stopPropagation()

    const target = event.target
    if (!target || target === doc.body || target === doc.documentElement) return
    selectElement(target)
  }
}

const injectFrameEditingStyle = (doc) => {
  if (doc.getElementById("ui2code-edit-style")) return

  const style = doc.createElement("style")
  style.id = "ui2code-edit-style"
  style.innerHTML = `
    .ui2code-selected {
      outline: 3px solid #1677ff !important;
      outline-offset: 3px !important;
    }

    .ui2code-dragging {
      outline: 3px dashed #16a34a !important;
      outline-offset: 3px !important;
      cursor: move !important;
    }

    body * {
      cursor: pointer;
      user-select: none;
    }
  `
  doc.head.appendChild(style)
}

const removeFrameEditingStyle = () => {
  const iframe = previewFrame.value
  if (!iframe) return

  const doc = iframe.contentDocument || iframe.contentWindow?.document
  if (!doc) return

  const style = doc.getElementById("ui2code-edit-style")
  if (style) style.remove()

  const selected = doc.querySelector(".ui2code-selected")
  if (selected) selected.classList.remove("ui2code-selected")

  const dragging = doc.querySelector(".ui2code-dragging")
  if (dragging) dragging.classList.remove("ui2code-dragging")

  doc.body.onclick = null
  doc.onmousemove = null
  doc.onmouseup = null
}

const selectElement = (el) => {
  if (dragMode.value) return

  const iframe = previewFrame.value
  const doc = iframe?.contentDocument || iframe?.contentWindow?.document
  if (!doc) return

  const oldSelected = doc.querySelector(".ui2code-selected")
  if (oldSelected) oldSelected.classList.remove("ui2code-selected")

  el.classList.add("ui2code-selected")
  selectedElement.value = el
  selectedTag.value = el.tagName.toLowerCase()
  editText.value = el.innerText || el.textContent || ""

  const computedStyle = iframe.contentWindow.getComputedStyle(el)
  editColor.value = rgbToHex(computedStyle.color) || "#000000"
  editBgColor.value = rgbToHex(computedStyle.backgroundColor) || "#ffffff"
  editFontSize.value = parseInt(computedStyle.fontSize, 10) || 16
}

const applyElementEdit = () => {
  const el = selectedElement.value
  if (!el) return

  saveHistory()

  const isTextOnlyElement =
    el.children.length === 0 ||
    ["p", "span", "h1", "h2", "h3", "h4", "button", "label", "a"].includes(el.tagName.toLowerCase())

  // 只有纯文本元素才允许修改文本，避免把容器内部结构清空
  if (isTextOnlyElement && editText.value.trim()) {
    el.innerText = editText.value
  }

  el.style.color = editColor.value
  el.style.backgroundColor = editBgColor.value
  el.style.fontSize = `${editFontSize.value}px`

  syncPreviewHtmlFromFrame()
  resizePreviewFrame()
}

const startDragMode = () => {
  const el = selectedElement.value
  if (!el) return

  dragOriginalHtml.value = getCurrentFrameHtml()
  dragMode.value = true

  el.classList.add("ui2code-dragging")
  bindDragEvents(el)
}

const bindDragEvents = (el) => {
  const iframe = previewFrame.value
  const doc = iframe?.contentDocument || iframe?.contentWindow?.document
  if (!doc) return

  el.onmousedown = (event) => {
    if (!dragMode.value) return

    event.preventDefault()
    event.stopPropagation()

    const computed = iframe.contentWindow.getComputedStyle(el)
    const currentTransform = el.style.transform || "translate(0px, 0px)"
    const match = currentTransform.match(/translate\((-?\d+\.?\d*)px,\s*(-?\d+\.?\d*)px\)/)

    const originX = match ? Number(match[1]) : 0
    const originY = match ? Number(match[2]) : 0

    el.style.position = computed.position === "static" ? "relative" : computed.position
    el.style.zIndex = "9999"
    el.style.willChange = "transform"

    dragState = {
      el,
      startX: event.clientX,
      startY: event.clientY,
      originX,
      originY
    }
  }

  doc.onmousemove = (event) => {
    if (!dragMode.value || !dragState) return

    const dx = event.clientX - dragState.startX
    const dy = event.clientY - dragState.startY

    dragState.el.style.transform = `translate(${dragState.originX + dx}px, ${dragState.originY + dy}px)`
  }

  doc.onmouseup = () => {
    dragState = null
  }
}

const confirmDrag = async () => {
  if (!dragMode.value) return

  if (dragOriginalHtml.value) {
    editHistory.value.push(dragOriginalHtml.value)
  }

  dragMode.value = false

  const el = selectedElement.value
  if (el) {
    el.classList.remove("ui2code-dragging")
    el.onmousedown = null
  }

  syncPreviewHtmlFromFrame()
  await nextTick()
  enableFrameEditing()
}

const cancelDrag = async () => {
  if (!dragMode.value) return

  dragMode.value = false

  if (dragOriginalHtml.value) {
    previewHtml.value = dragOriginalHtml.value
  }

  dragOriginalHtml.value = ""
  dragState = null

  await nextTick()
  clearSelection()
  if (editMode.value) enableFrameEditing()
}

const formatGenerationSource = (source) => {
  if (source === "qwen-vl-plus" || source === "qwen") {
    return "千问VL模型"
  }
if (source === "qwen-vl-max") {
  return "千问VL-Max模型"
}
if (source === "doubao") {
  return "豆包视觉模型"
}

  if (source === "deepseek") {
    return "DeepSeek模型"
  }

  if (source === "multi-page") {
    return "多页面交互预览"
  }

  if (source === "rule") {
    return "规则引擎"
  }

  return source || "未知模型"
}

const clearSelection = () => {
  try {
    const iframe = previewFrame.value
    const doc = iframe?.contentDocument || iframe?.contentWindow?.document
    const oldSelected = doc?.querySelector(".ui2code-selected")
    if (oldSelected) oldSelected.classList.remove("ui2code-selected")

    const dragging = doc?.querySelector(".ui2code-dragging")
    if (dragging) dragging.classList.remove("ui2code-dragging")
  } catch (e) {
    console.warn(e)
  }

  selectedElement.value = null
  selectedTag.value = ""
  editText.value = ""
  editColor.value = "#000000"
  editBgColor.value = "#ffffff"
  editFontSize.value = 16
}

const getCurrentFrameHtml = () => {
  const iframe = previewFrame.value
  if (!iframe) return ""

  const doc = iframe.contentDocument || iframe.contentWindow?.document
  if (!doc) return ""

  const clone = doc.documentElement.cloneNode(true)

  const editStyle = clone.querySelector("#ui2code-edit-style")
  if (editStyle) editStyle.remove()

  const selected = clone.querySelector(".ui2code-selected")
  if (selected) selected.classList.remove("ui2code-selected")

  const dragging = clone.querySelector(".ui2code-dragging")
  if (dragging) dragging.classList.remove("ui2code-dragging")

  return "<!DOCTYPE html>\n" + clone.outerHTML
}

const syncPreviewHtmlFromFrame = () => {
  const html = getCurrentFrameHtml()
  if (html) previewHtml.value = html
}

const rgbToHex = (rgb) => {
  if (!rgb || rgb === "transparent" || rgb === "rgba(0, 0, 0, 0)") return "#ffffff"
  if (rgb.startsWith("#")) return rgb

  const result = rgb.match(/\d+/g)
  if (!result || result.length < 3) return "#ffffff"

  return (
    "#" +
    result
      .slice(0, 3)
      .map((x) => {
        const hex = parseInt(x, 10).toString(16)
        return hex.length === 1 ? "0" + hex : hex
      })
      .join("")
  )
}

const downloadCode = () => {
  if (!code.value) return

  const blob = new Blob([code.value], { type: "text/plain;charset=utf-8" })
  const url = URL.createObjectURL(blob)

  const a = document.createElement("a")
  a.href = url
  a.download = "GeneratedLayout.vue"
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)

  URL.revokeObjectURL(url)
}

const downloadEditedHtml = () => {
  if (!previewHtml.value) return

  syncPreviewHtmlFromFrame()

  const blob = new Blob([previewHtml.value], { type: "text/html;charset=utf-8" })
  const url = URL.createObjectURL(blob)

  const a = document.createElement("a")
  a.href = url
  a.download = "EditedPreview.html"
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)

  URL.revokeObjectURL(url)
}

const encodeHtmlForDownload = (html) => {
  const safeHtml = html || ""
  return btoa(unescape(encodeURIComponent(safeHtml)))
}

const downloadMultiPageHtml = () => {
  if (!pageList.value.length) {
    alert("页面队列为空")
    return
  }

  const pages = pageList.value.map((page, index) => {
    return {
      name: page.name || `页面${index + 1}`,
      html: encodeHtmlForDownload(page.previewHtml || page.html || "")
    }
  })

  const pagesJson = JSON.stringify(pages)

  const finalHtml = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>多页面原型预览</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #f4f7fb;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      color: #0f172a;
    }
    .nav-bar {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 9999;
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px 18px;
      background: #ffffff;
      border-bottom: 1px solid #e2e8f0;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
    }
    .nav-title {
      font-weight: 700;
      margin-right: 10px;
      color: #0f172a;
    }
    .nav-bar button {
      padding: 9px 18px;
      border: 1px solid #1677ff;
      border-radius: 10px;
      cursor: pointer;
      background: #ffffff;
      color: #1677ff;
      font-size: 14px;
    }
    .nav-bar button.active {
      background: #1677ff;
      color: #ffffff;
      box-shadow: 0 6px 14px rgba(22, 119, 255, 0.22);
    }
    .page-wrapper {
      padding-top: 76px;
      width: 100%;
      min-height: 100vh;
    }
    iframe {
      width: 100%;
      min-height: calc(100vh - 76px);
      border: 0;
      display: block;
      background: #ffffff;
    }
  </style>
</head>
<body>
  <div class="nav-bar" id="navBar">
    <span class="nav-title">多页面预览</span>
  </div>
  <div class="page-wrapper">
    <iframe id="pageFrame"></iframe>
  </div>

  <script>
    const pages = ${pagesJson};

    function decodeHtml(base64) {
      try {
        return decodeURIComponent(escape(atob(base64 || "")));
      } catch (e) {
        return "<p>页面内容解析失败</p>";
      }
    }

    function showPage(index) {
      const frame = document.getElementById("pageFrame");
      const buttons = document.querySelectorAll(".nav-bar button");
      buttons.forEach((btn) => btn.classList.remove("active"));
      if (buttons[index]) buttons[index].classList.add("active");
      frame.srcdoc = decodeHtml(pages[index] && pages[index].html);
    }

    const navBar = document.getElementById("navBar");
    pages.forEach((page, index) => {
      const button = document.createElement("button");
      button.textContent = page.name || ("页面" + (index + 1));
      button.onclick = () => showPage(index);
      navBar.appendChild(button);
    });

    showPage(0);
  <\/script>
</body>
</html>`

  const blob = new Blob([finalHtml], { type: "text/html;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "multi-page-preview.html"
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
</script>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

.page {
  min-height: 100vh;
  padding: 40px 20px;
  background: linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
}

.main-card {
  width: min(1080px, 100%);
  margin: 0 auto;
  background: #ffffff;
  border: 1px solid #dde7f2;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  padding: 36px;
}

.header {
  text-align: center;
  margin-bottom: 32px;
}

.header h1 {
  margin: 0;
  font-size: 52px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 1px;
}

.subtitle {
  margin-top: 12px;
  color: #64748b;
  font-size: 16px;
}

.upload-section {
  margin-bottom: 28px;
}

.upload-box {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  justify-content: center;
  padding: 24px;
  border: 1px dashed #bfd0e4;
  border-radius: 16px;
  background: #f8fbff;
}

.file-label {
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 18px;
  border-radius: 10px;
  background: #ffffff;
  border: 1px solid #c9d7e6;
  color: #0f172a;
  font-size: 14px;
  cursor: pointer;
}

.file-label input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.file-name {
  min-width: 140px;
  color: #334155;
  font-size: 14px;
}

.file-name.empty {
  color: #94a3b8;
}

.action-group,
.edit-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.primary-btn,
.secondary-btn,
.edit-btn {
  padding: 11px 18px;
  border-radius: 10px;
  font-size: 14px;
  cursor: pointer;
}

.primary-btn {
  border: none;
  background: linear-gradient(135deg, #1677ff 0%, #0f5fd7 100%);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 8px 18px rgba(22, 119, 255, 0.22);
}

.primary-btn:disabled,
.secondary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.secondary-btn,
.edit-btn {
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
}

.edit-btn.active {
  background: #16a34a;
  color: white;
  border-color: #16a34a;
}

.green {
  background: #16a34a !important;
}

.danger {
  color: #dc2626;
  border-color: #fecaca;
}

.small {
  padding: 8px 14px;
}

.panel {
  margin-top: 24px;
  padding: 22px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: #ffffff;
}

.panel h2 {
  margin: 0 0 14px;
  font-size: 24px;
  color: #1e293b;
  text-align: center;
}


.multi-page-tip {
  margin: 0 0 14px;
  color: #64748b;
  text-align: center;
  line-height: 1.7;
}

.page-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 14px;
}

.page-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #dbe5f0;
  border-radius: 14px;
  background: #f8fbff;
}

.page-item.active {
  border-color: #1677ff;
  background: #eef6ff;
  box-shadow: 0 8px 18px rgba(22, 119, 255, 0.12);
}


.page-thumb {
  width: 72px;
  height: 52px;
  border-radius: 10px;
  overflow: hidden;
  background: #e2e8f0;
  flex: 0 0 auto;
}

.page-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.page-info {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-info strong {
  color: #0f172a;
  font-size: 15px;
}

.page-info span {
  color: #64748b;
  font-size: 12px;
}

.page-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.image-preview-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 12px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.image-preview {
  max-width: 100%;
  max-height: 340px;
  border-radius: 10px;
  object-fit: contain;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.tabs {
  display: flex;
  gap: 10px;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.tabs button {
  padding: 8px 16px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
  border-radius: 8px;
  cursor: pointer;
}

.tabs .active {
  background: #1677ff;
  color: white;
  border-color: #1677ff;
}

.edit-tip {
  margin-bottom: 14px;
  padding: 12px 14px;
  border-radius: 10px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
  font-size: 14px;
}

.drag-tip {
  margin: 12px 0 0;
  padding: 10px 12px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #15803d;
  border-radius: 8px;
  font-size: 13px;
}

.editor-panel {
  margin-bottom: 14px;
  padding: 16px;
  border: 1px solid #dbeafe;
  border-radius: 14px;
  background: #f8fbff;
}

.editor-panel h3 {
  margin: 0 0 12px;
  font-size: 18px;
  color: #1e293b;
}

.editor-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.editor-grid label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #334155;
  font-size: 13px;
}

.editor-grid input[type="text"],
.editor-grid input[type="number"] {
  height: 36px;
  padding: 0 10px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
}

.editor-grid input[type="color"] {
  width: 70px;
  height: 36px;
  padding: 4px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
}

.editor-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.tab-content {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px;
  background: #f8fbff;
}

.frame {
  width: 100%;
  min-height: 500px;
  border: 1px solid #dbe3ee;
  border-radius: 12px;
  background: #fff;
}

.code-mode-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  color: #334155;
  font-size: 14px;
}

.code-mode-bar button {
  padding: 7px 14px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
  cursor: pointer;
}

.code-mode-bar button.active {
  background: #1677ff;
  color: #ffffff;
  border-color: #1677ff;
}

.code-block {
  margin: 0;
  padding: 18px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.7;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.code-block-dark {
  background: #0f172a;
  color: #e2e8f0;
}

.code-block-light {
  background: #ffffff;
  color: #0f172a;
  border: 1px solid #e2e8f0;
}

.similarity-user-panel {
  padding: 18px;
  background: #ffffff;
  border-radius: 16px;
}

.restore-overview {
  display: grid;
  grid-template-columns: 230px 1fr;
  gap: 28px;
  align-items: center;
  margin-bottom: 22px;
}

.restore-circle {
  width: 190px;
  height: 190px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.restore-inner {
  width: 132px;
  height: 132px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 1px #e2e8f0;
}

.restore-inner strong {
  font-size: 34px;
  color: #0f172a;
}

.restore-inner span {
  margin-top: 4px;
  color: #64748b;
  font-size: 14px;
}

.restore-summary {
  padding: 22px;
  border-radius: 16px;
  background: linear-gradient(135deg, #eff6ff, #f8fbff);
  border: 1px solid #bfdbfe;
}

.restore-summary h3 {
  margin: 0 0 10px;
  color: #0f172a;
  font-size: 24px;
}

.restore-summary p {
  margin: 0;
  color: #475569;
  line-height: 1.8;
}

.restore-badge {
  display: inline-block;
  margin-top: 14px;
  padding: 6px 12px;
  border-radius: 999px;
  background: #1677ff;
  color: white;
  font-size: 13px;
  font-weight: 600;
}

.restore-detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.restore-card {
  padding: 18px;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
}

.restore-card-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.restore-card-top span {
  color: #64748b;
  font-size: 14px;
}

.restore-card-top strong {
  color: #0f172a;
  font-size: 18px;
}

.star-line {
  margin: 12px 0;
  font-size: 18px;
}

.restore-card p {
  margin: 0;
  color: #64748b;
  line-height: 1.7;
  font-size: 14px;
}

.metric-explain {
  margin-top: 18px;
  padding: 16px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.metric-explain h4 {
  margin: 0 0 8px;
  color: #1e293b;
  font-size: 16px;
}

.metric-explain p {
  margin: 0;
  color: #475569;
  line-height: 1.8;
}

.raw-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.raw-metrics span {
  padding: 6px 10px;
  border-radius: 999px;
  background: #e2e8f0;
  color: #334155;
  font-size: 12px;
}

.layout-tree-panel {
  background: #ffffff;
  border-radius: 14px;
  padding: 18px;
}

.layout-tree-header {
  margin-bottom: 18px;
  padding: 16px;
  border-radius: 12px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}

.layout-tree-header h3 {
  margin: 0 0 8px;
  color: #1e293b;
  font-size: 20px;
}

.layout-tree-header p {
  margin: 0;
  color: #475569;
  font-size: 14px;
}

.tree-node {
  margin: 10px 0;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #dbeafe;
  background: #f8fbff;
}

.tree-node-root {
  border-color: #93c5fd;
  background: #dbeafe;
}

.tree-node-container {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.tree-node-leaf {
  border-color: #e2e8f0;
  background: #ffffff;
}

.tree-node-main {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.tree-node-icon {
  color: #1677ff;
  font-weight: 700;
}

.tree-node-role {
  font-weight: 700;
  color: #0f172a;
}

.tree-node-type,
.tree-node-direction {
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 12px;
}

.tree-node-type {
  background: #e2e8f0;
  color: #334155;
}

.tree-node-direction {
  background: #dcfce7;
  color: #15803d;
}

.tree-node-meta {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #64748b;
  font-size: 12px;
}

.tree-children {
  border-left: 2px dashed #cbd5e1;
  margin-left: 14px;
}

.empty-state,
.similarity-empty {
  padding: 30px;
  text-align: center;
  color: #64748b;
}

.ok-text {
  color: #16a34a;
  font-weight: 600;
  text-align: center;
}

.warn-text {
  color: #d97706;
  font-weight: 600;
  text-align: center;
}

.error-panel {
  border-color: #fecaca;
  background: #fff7f7;
}

.error-text {
  margin: 0;
  color: #dc2626;
  text-align: center;
  font-size: 16px;
}

@media (max-width: 768px) {
  .main-card {
    padding: 22px;
  }

  .header h1 {
    font-size: 36px;
  }

  .tabs,
  .result-header {
    flex-wrap: wrap;
  }

  .editor-grid,
  .restore-overview,
  .restore-detail-grid {
    grid-template-columns: 1fr;
  }
}
.detect-result-wrapper {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detect-image-box {
  background: #ffffff;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #dbeafe;
}

.detect-image-box h3 {
  margin-bottom: 16px;
  color: #1e3a8a;
}

.detect-image {
  width: 100%;
  border-radius: 12px;
  border: 2px solid #93c5fd;
}

.detect-json-box {
  border-radius: 16px;
  padding: 20px;
  overflow-x: auto;
}

.detect-json-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.detect-json-header h3 {
  margin: 0;
}

.detect-json-box pre {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.8;
}

.detect-json-dark {
  background: #0f172a;
}

.detect-json-dark h3,
.detect-json-dark pre {
  color: #e2e8f0;
}

.detect-json-dark .code-mode-bar {
  color: #e2e8f0;
}

.detect-json-light {
  background: #ffffff;
  border: 1px solid #e2e8f0;
}

.detect-json-light h3,
.detect-json-light pre {
  color: #0f172a;
}

.detect-json-light .code-mode-bar {
  color: #334155;
}
.crop-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.72);
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.crop-modal {
  width: min(1100px, 96vw);
  max-height: 92vh;
  overflow: auto;
  background: #ffffff;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
}

.crop-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
}

.crop-header h3 {
  margin: 0;
  color: #0f172a;
  font-size: 22px;
}

.crop-tip {
  margin: 0 0 14px;
  color: #64748b;
  font-size: 14px;
}

.crop-stage {
  position: relative;
  width: 100%;
  max-height: 68vh;
  overflow: auto;
  border-radius: 14px;
  border: 1px solid #cbd5e1;
  background: #0f172a;
  cursor: crosshair;
}

.crop-image {
  display: block;
  width: 100%;
  user-select: none;
  pointer-events: none;
}

.crop-box {
  position: absolute;
  border: 2px solid #1677ff;
  background: rgba(22, 119, 255, 0.18);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.35);
  pointer-events: none;
}

.crop-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}
.model-select {
  height: 48px;
  padding: 0 16px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  background: #ffffff;
  color: #0f172a;
  font-size: 15px;
  cursor: pointer;
}

.model-select:focus {
  outline: none;
  border-color: #1677ff;
  box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.12);
}
</style>