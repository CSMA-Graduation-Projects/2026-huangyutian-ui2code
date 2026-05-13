from ultralytics import YOLO
from pathlib import Path
import cv2


class UIDetector:

    def __init__(self):
        print("加载YOLO模型...")
        self.model = YOLO("yolov8n.pt")

    def detect(self, image_path, save_visual=True):
        print("开始UI元素检测...")

        results = self.model(image_path)

        detections = []

        for r in results:
            boxes = r.boxes

            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])

                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "class_id": cls_id,
                    "confidence": conf
                })

            if save_visual:
                output_dir = Path("data")
                output_dir.mkdir(exist_ok=True)

                image_name = Path(image_path).stem
                output_path = output_dir / f"{image_name}_detect.jpg"

                visual_img = r.plot()
                cv2.imwrite(str(output_path), visual_img)

                print(f"检测结果图片已保存：{output_path}")

        return detections