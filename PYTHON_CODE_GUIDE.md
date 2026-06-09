# Python 代码说明

本文档解释 `src/` 目录中各个 Python 文件的作用、输入输出和运行关系，方便交源码、录屏讲解或后续继续开发。

## 总体结构

项目采用 M1-M5 流水线：

```text
M1 YOLO检测
  ↓
M2 地质解释
  ↓
M3 数据融合
  ↓
M4 剖面模型检查
  ↓
M5 地层剖面图生成
```

主入口是：

```text
src/run_pipeline.py
```

一键运行：

```powershell
python .\src\run_pipeline.py
```

如果已经训练好 YOLO 模型：

```powershell
python .\src\run_pipeline.py --model .\models\geo_yolo.pt
```

## 文件说明

### 1. `section_drawer.py`

这是底层绘图引擎，负责把表格数据转换为 SVG 地层剖面图。

主要功能：

- 读取 `section_info`、`topography`、`units`、`structures` 表格。
- 平滑插值地形曲线。
- 绘制岩性单元、岩性花纹、层面线、断层、节理密集带。
- 根据 `thickness_m` 控制层面线间距。
- 根据 `dip_angle_deg` 真倾角控制层面线角度。
- 输出 SVG 文件。

关键类和函数：

```text
TableSource
  统一读取 CSV 文件夹或 Excel 工作簿。

Topography
  处理地形点，生成平滑地形曲线。

SvgBuilder
  主绘图类，生成 SVG。

load_project()
  读取完整剖面项目数据。
```

输入：

```text
data/tables/section_info.csv
data/tables/topography.csv
data/tables/units.csv
data/tables/structures.csv
```

输出：

```text
outputs/section_D.svg
```

单独运行：

```powershell
python .\src\section_drawer.py
```

### 2. `m1_yolo_detect.py`

M1 模块，负责地质现象检测。

赛前训练好模型后，比赛当天可以读取：

```text
models/geo_yolo.pt
```

然后对 `observations.csv` 中记录的照片进行 YOLO 推理。

如果没有安装 `ultralytics`，或者没有提供模型文件，程序会自动退回到 `observations.csv` 的 `yolo_result` 字段，保证整套流程仍然能跑通。

输入：

```text
data/tables/observations.csv
models/geo_yolo.pt，可选
```

输出：

```text
outputs/m1_yolo_results.json
```

输出内容包括：

```json
{
  "point_id": "P01",
  "photo_path": "data/photos/P01.jpg",
  "detections": [
    {
      "class": "bedding",
      "confidence": 0.86,
      "bbox": null,
      "source": "observation_table"
    }
  ]
}
```

### 3. `m2_qwen_interpret.py`

M2 模块，负责把 YOLO 检测结果和野外记录整理成地质解释。

当前版本没有直接调用在线 Qwen API，而是读取 `observations.csv` 中的 `qwen_description`、`field_lithology`、`human_note` 等字段，生成结构化解释结果。

这样设计的原因是：

- 比赛现场网络和 API 不一定稳定。
- 先保证本地流程可复现。
- 后续可以把真实 Qwen-VL 调用接到这个模块。

输入：

```text
outputs/m1_yolo_results.json
data/tables/observations.csv
```

输出：

```text
outputs/m2_qwen_interpretations.json
```

### 4. `m3_fuse_tables.py`

M3 模块，负责融合数据。

它把原始表格、M1 检测结果和 M2 解释结果合并成统一项目 JSON，方便后续审查、报告生成或调试。

输入：

```text
data/tables/*.csv
outputs/m1_yolo_results.json
outputs/m2_qwen_interpretations.json
```

输出：

```text
outputs/m3_fused_project.json
```

### 5. `m4_build_section_model.py`

M4 模块，负责检查剖面数据完整性，并生成剖面模型。

它会检查：

- 每个岩性单元是否有 `unit_id`
- 是否有 `from_m` 和 `to_m`
- 是否有 `lithology_final`
- 是否有 `thickness_m`
- 是否有 `dip_angle_deg`
- `to_m` 是否大于 `from_m`
- `thickness_m` 是否大于 0

输入：

```text
data/tables/section_info.csv
data/tables/topography.csv
data/tables/units.csv
data/tables/structures.csv
```

输出：

```text
outputs/m4_section_model.json
```

这个 JSON 中会列出每个岩层的绘图参数和数据警告。

### 6. `m5_draw_section.py`

M5 模块，负责最终出图。

它调用 `section_drawer.py` 的绘图引擎，生成最终地层剖面图。

输入：

```text
data/tables/*.csv
```

输出：

```text
outputs/section_D.svg
```

### 7. `run_pipeline.py`

完整流水线入口。

它依次执行：

```text
m1_yolo_detect.run()
m2_qwen_interpret.run()
m3_fuse_tables.run()
m4_build_section_model.run()
m5_draw_section.run()
```

运行：

```powershell
python .\src\run_pipeline.py
```

带模型运行：

```powershell
python .\src\run_pipeline.py --model .\models\geo_yolo.pt
```

### 8. `prepare_yolo_dataset.py`

赛前数据准备脚本。

主要功能：

- 创建 YOLO 标准目录。
- 写入 `data.yaml`。
- 从无人机视频中按时间间隔抽帧。
- 将已标注图片和标签划分为 train、val、test。

从视频抽帧：

```powershell
python .\src\prepare_yolo_dataset.py --video .\data\videos\drone.mp4 --frames-output .\data\raw_frames --every-seconds 1
```

划分已标注数据：

```powershell
python .\src\prepare_yolo_dataset.py --source-images .\data\labeled_images --source-labels .\data\labeled_labels
```

### 9. `train_yolo.py`

赛前训练脚本。

它基于 Ultralytics YOLO 训练地质现象检测模型。

训练命令：

```powershell
python .\src\train_yolo.py --data .\data\yolo_dataset\data.yaml --model yolov8n.pt --epochs 100 --imgsz 960 --batch 8
```

训练完成后，推荐把最佳模型复制为：

```text
models/geo_yolo.pt
```

### 10. `predict_yolo.py`

YOLO 推理脚本。

可以对图片、文件夹或视频进行推理。

示例：

```powershell
python .\src\predict_yolo.py --model .\models\geo_yolo.pt --source .\data\raw_frames --save-images
```

输出：

```text
outputs/yolo_predictions.json
```

如果设置 `--save-images`，还会保存带检测框的结果图。

## 赛前与赛中逻辑

本项目采用：

```text
赛前：人工标注一批训练集 → 训练 geo_yolo.pt
赛中：只用模型自动识别 → 不再标注
```

赛前：

```text
无人机视频 / 野外照片
  ↓
抽帧和筛选
  ↓
人工标注 YOLO 数据集
  ↓
训练 geo_yolo.pt
```

赛中：

```text
组委会无人机视频
  ↓
自动抽帧
  ↓
YOLO 推理
  ↓
Qwen/人工解释与校核
  ↓
标准化表格
  ↓
自动生成地层剖面图
```

## 当前默认 YOLO 类别

类别配置位于：

```text
data/yolo_dataset/data.yaml
```

默认类别：

```text
0 outcrop              露头范围
1 bedding              层理
2 joint_fracture       节理/裂隙
3 fault                断层
4 fold                 褶皱
5 lithologic_boundary  岩性界线
6 strata_line          地层线/层面线
```

## 依赖说明

基础剖面图生成只依赖 Python 标准库和 `openpyxl`。

YOLO 训练和视频抽帧需要：

```text
ultralytics
opencv-python
Pillow
numpy
pandas
openpyxl
```

安装：

```powershell
pip install -r requirements.txt
```

