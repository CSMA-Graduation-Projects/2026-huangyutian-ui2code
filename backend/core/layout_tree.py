class LayoutNode:
    def __init__(
        self,
        node_type="element",
        bbox=None,
        class_id=None,
        confidence=None,
        direction=None,
        children=None,
        role=None
    ):
        self.node_type = node_type
        self.bbox = bbox or []
        self.class_id = class_id
        self.confidence = confidence
        self.direction = direction
        self.children = children or []
        self.role = role

    def to_dict(self):
        return {
            "type": self.node_type,
            "role": self.role,
            "bbox": self.bbox,
            "class_id": self.class_id,
            "confidence": self.confidence,
            "direction": self.direction,
            "children": [child.to_dict() for child in self.children]
        }


class LayoutTreeBuilder:
    def __init__(self, detections):
        self.detections = detections or []

    def build(self):
        boxes = self._normalize_detections(self.detections)

        if not boxes:
            return [
                LayoutNode(
                    node_type="root",
                    role="page",
                    bbox=[],
                    direction="column",
                    children=[]
                )
            ]

        root_bbox = self._get_root_bbox(boxes)

        root = LayoutNode(
            node_type="root",
            role="page",
            bbox=root_bbox,
            direction="column",
            children=[]
        )

        # 如果检测框太少，说明 YOLO 没有识别出细粒度 UI 组件
        # 此时启用 UI 结构增强，生成更有解释性的伪布局树
        if len(boxes) <= 2:
            enhanced_tree = self._build_enhanced_ui_tree(boxes)
            root.children = enhanced_tree
            return [root]

        nodes = [
            LayoutNode(
                node_type="element",
                role="detected-element",
                bbox=item["bbox"],
                class_id=item.get("class_id"),
                confidence=item.get("confidence"),
                direction=None,
                children=[]
            )
            for item in boxes
        ]

        nodes.sort(key=lambda node: self._area(node.bbox), reverse=True)

        used_children = set()

        for i, parent in enumerate(nodes):
            for j, child in enumerate(nodes):
                if i == j:
                    continue

                if j in used_children:
                    continue

                if self._is_parent(parent.bbox, child.bbox):
                    parent.children.append(child)
                    used_children.add(j)

        for index, node in enumerate(nodes):
            if index not in used_children:
                root.children.append(node)

        self._post_process(root)

        return [root]

    def _build_enhanced_ui_tree(self, boxes):
        """
        当 YOLO 只检测到一个或两个大框时，说明检测粒度不足。
        这里基于 bbox 的几何比例生成一个增强布局树，用于表达 UI 的大致结构。
        """

        main_box = boxes[0]["bbox"]

        x1, y1, x2, y2 = main_box
        width = x2 - x1
        height = y2 - y1

        screen = LayoutNode(
            node_type="container",
            role="screen",
            bbox=main_box,
            class_id=boxes[0].get("class_id"),
            confidence=boxes[0].get("confidence"),
            direction="row",
            children=[]
        )

        # 横向宽屏页面，例如登录页 / 大屏 / 首页
        if width >= height * 1.2:
            screen.children = self._split_wide_ui(main_box)

        # 纵向移动端或长页面
        elif height >= width * 1.2:
            screen.children = self._split_vertical_ui(main_box)

        # 接近方形的普通面板
        else:
            screen.children = self._split_balanced_ui(main_box)

        return [screen]

    def _split_wide_ui(self, bbox):
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1

        left_x1 = x1
        left_x2 = x1 + w * 0.52
        right_x1 = left_x2
        right_x2 = x2

        left_panel = LayoutNode(
            node_type="container",
            role="left-visual-panel",
            bbox=[left_x1, y1, left_x2, y2],
            direction="column",
            children=[
                LayoutNode(
                    node_type="leaf",
                    role="main-title",
                    bbox=[
                        left_x1 + w * 0.08,
                        y1 + h * 0.22,
                        left_x1 + w * 0.42,
                        y1 + h * 0.34
                    ],
                    direction=None,
                    children=[]
                ),
                LayoutNode(
                    node_type="container",
                    role="data-card-group",
                    bbox=[
                        left_x1 + w * 0.08,
                        y1 + h * 0.58,
                        left_x1 + w * 0.45,
                        y1 + h * 0.78
                    ],
                    direction="row",
                    children=[
                        LayoutNode(
                            node_type="leaf",
                            role="stat-card",
                            bbox=[
                                left_x1 + w * 0.08,
                                y1 + h * 0.60,
                                left_x1 + w * 0.18,
                                y1 + h * 0.75
                            ],
                            children=[]
                        ),
                        LayoutNode(
                            node_type="leaf",
                            role="stat-card",
                            bbox=[
                                left_x1 + w * 0.20,
                                y1 + h * 0.60,
                                left_x1 + w * 0.30,
                                y1 + h * 0.75
                            ],
                            children=[]
                        ),
                        LayoutNode(
                            node_type="leaf",
                            role="stat-card",
                            bbox=[
                                left_x1 + w * 0.32,
                                y1 + h * 0.60,
                                left_x1 + w * 0.42,
                                y1 + h * 0.75
                            ],
                            children=[]
                        )
                    ]
                )
            ]
        )

        right_panel = LayoutNode(
            node_type="container",
            role="right-form-panel",
            bbox=[right_x1, y1, right_x2, y2],
            direction="column",
            children=[
                LayoutNode(
                    node_type="leaf",
                    role="form-title",
                    bbox=[
                        right_x1 + w * 0.08,
                        y1 + h * 0.22,
                        right_x1 + w * 0.34,
                        y1 + h * 0.32
                    ],
                    children=[]
                ),
                LayoutNode(
                    node_type="leaf",
                    role="input",
                    bbox=[
                        right_x1 + w * 0.08,
                        y1 + h * 0.40,
                        right_x1 + w * 0.38,
                        y1 + h * 0.48
                    ],
                    children=[]
                ),
                LayoutNode(
                    node_type="leaf",
                    role="input",
                    bbox=[
                        right_x1 + w * 0.08,
                        y1 + h * 0.52,
                        right_x1 + w * 0.38,
                        y1 + h * 0.60
                    ],
                    children=[]
                ),
                LayoutNode(
                    node_type="leaf",
                    role="button",
                    bbox=[
                        right_x1 + w * 0.08,
                        y1 + h * 0.70,
                        right_x1 + w * 0.38,
                        y1 + h * 0.80
                    ],
                    children=[]
                )
            ]
        )

        return [left_panel, right_panel]

    def _split_vertical_ui(self, bbox):
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1

        header = LayoutNode(
            node_type="container",
            role="header",
            bbox=[x1, y1, x2, y1 + h * 0.15],
            direction="row",
            children=[]
        )

        main = LayoutNode(
            node_type="container",
            role="main-content",
            bbox=[x1, y1 + h * 0.15, x2, y1 + h * 0.85],
            direction="column",
            children=[
                LayoutNode(
                    node_type="leaf",
                    role="banner",
                    bbox=[
                        x1 + w * 0.08,
                        y1 + h * 0.20,
                        x2 - w * 0.08,
                        y1 + h * 0.38
                    ],
                    children=[]
                ),
                LayoutNode(
                    node_type="container",
                    role="card-list",
                    bbox=[
                        x1 + w * 0.08,
                        y1 + h * 0.42,
                        x2 - w * 0.08,
                        y1 + h * 0.78
                    ],
                    direction="column",
                    children=[
                        LayoutNode(
                            node_type="leaf",
                            role="card",
                            bbox=[
                                x1 + w * 0.08,
                                y1 + h * 0.42,
                                x2 - w * 0.08,
                                y1 + h * 0.52
                            ],
                            children=[]
                        ),
                        LayoutNode(
                            node_type="leaf",
                            role="card",
                            bbox=[
                                x1 + w * 0.08,
                                y1 + h * 0.55,
                                x2 - w * 0.08,
                                y1 + h * 0.65
                            ],
                            children=[]
                        ),
                        LayoutNode(
                            node_type="leaf",
                            role="card",
                            bbox=[
                                x1 + w * 0.08,
                                y1 + h * 0.68,
                                x2 - w * 0.08,
                                y1 + h * 0.78
                            ],
                            children=[]
                        )
                    ]
                )
            ]
        )

        footer = LayoutNode(
            node_type="container",
            role="footer",
            bbox=[x1, y1 + h * 0.85, x2, y2],
            direction="row",
            children=[]
        )

        return [header, main, footer]

    def _split_balanced_ui(self, bbox):
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1

        return [
            LayoutNode(
                node_type="container",
                role="top-section",
                bbox=[x1, y1, x2, y1 + h * 0.28],
                direction="row",
                children=[]
            ),
            LayoutNode(
                node_type="container",
                role="content-section",
                bbox=[x1, y1 + h * 0.28, x2, y1 + h * 0.82],
                direction="grid",
                children=[
                    LayoutNode(
                        node_type="leaf",
                        role="card",
                        bbox=[
                            x1 + w * 0.08,
                            y1 + h * 0.34,
                            x1 + w * 0.42,
                            y1 + h * 0.55
                        ],
                        children=[]
                    ),
                    LayoutNode(
                        node_type="leaf",
                        role="card",
                        bbox=[
                            x1 + w * 0.58,
                            y1 + h * 0.34,
                            x2 - w * 0.08,
                            y1 + h * 0.55
                        ],
                        children=[]
                    ),
                    LayoutNode(
                        node_type="leaf",
                        role="button",
                        bbox=[
                            x1 + w * 0.25,
                            y1 + h * 0.68,
                            x2 - w * 0.25,
                            y1 + h * 0.78
                        ],
                        children=[]
                    )
                ]
            ),
            LayoutNode(
                node_type="container",
                role="bottom-section",
                bbox=[x1, y1 + h * 0.82, x2, y2],
                direction="row",
                children=[]
            )
        ]

    def _normalize_detections(self, detections):
        result = []

        for item in detections:
            bbox = item.get("bbox")

            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = bbox

            if x2 <= x1 or y2 <= y1:
                continue

            width = x2 - x1
            height = y2 - y1

            if width < 8 or height < 8:
                continue

            result.append({
                "bbox": [float(x1), float(y1), float(x2), float(y2)],
                "class_id": item.get("class_id"),
                "confidence": item.get("confidence")
            })

        result.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))

        return result

    def _get_root_bbox(self, boxes):
        x1 = min(item["bbox"][0] for item in boxes)
        y1 = min(item["bbox"][1] for item in boxes)
        x2 = max(item["bbox"][2] for item in boxes)
        y2 = max(item["bbox"][3] for item in boxes)

        return [x1, y1, x2, y2]

    def _area(self, bbox):
        if not bbox or len(bbox) != 4:
            return 0

        return max(0, bbox[2] - bbox[0]) * max(0, bbox[3] - bbox[1])

    def _center(self, bbox):
        return [
            (bbox[0] + bbox[2]) / 2,
            (bbox[1] + bbox[3]) / 2
        ]

    def _is_inside(self, inner, outer):
        if not inner or not outer:
            return False

        ix1, iy1, ix2, iy2 = inner
        ox1, oy1, ox2, oy2 = outer

        return (
            ix1 >= ox1 and
            iy1 >= oy1 and
            ix2 <= ox2 and
            iy2 <= oy2
        )

    def _is_parent(self, parent_bbox, child_bbox):
        if not self._is_inside(child_bbox, parent_bbox):
            return False

        parent_area = self._area(parent_bbox)
        child_area = self._area(child_bbox)

        if parent_area <= 0 or child_area <= 0:
            return False

        return parent_area > child_area * 1.3

    def _infer_direction(self, items):
        if not items or len(items) <= 1:
            return None

        centers = []

        for item in items:
            bbox = item["bbox"] if isinstance(item, dict) else item.bbox
            centers.append(self._center(bbox))

        xs = [c[0] for c in centers]
        ys = [c[1] for c in centers]

        x_range = max(xs) - min(xs)
        y_range = max(ys) - min(ys)

        if x_range > y_range * 1.2:
            return "row"

        if y_range > x_range * 1.2:
            return "column"

        return "grid"

    def _post_process(self, node):
        if not node.children:
            if node.node_type != "root":
                node.node_type = "leaf"
            return

        if node.node_type != "root":
            node.node_type = "container"

        node.children.sort(key=lambda child: (child.bbox[1], child.bbox[0]))
        node.direction = self._infer_direction(node.children)

        for child in node.children:
            self._post_process(child)