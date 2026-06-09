# Geo Section Generator

读取标准化 CSV 表格，自动生成地层/地质剖面图 SVG。

## 输入表格

默认读取 `data/tables/` 下的 5 个 CSV 表，也支持读取包含同名工作表的 `.xlsx` 工作簿：

- `section_info.csv`：剖面基本信息
- `topography.csv`：沿剖面地形点
- `units.csv`：岩性分层数据，包括岩层厚度 `thickness_m` 和产状 `dip_direction_deg`、`dip_angle_deg`
- `structures.csv`：断层、节理密集带等构造现象
- `observations.csv`：照片、标本与 AI 识别证据

真正用于绘图的核心表是：

- `section_info.csv`
- `topography.csv`
- `units.csv`
- `structures.csv`

`observations.csv` 暂时主要用于后续生成报告或追溯证据。

## 运行

在项目根目录运行以下命令。

一键运行 M1-M5 完整流程：

```powershell
python .\src\run_pipeline.py
```

指定表格目录、输出目录和可选 YOLO 模型：

```powershell
python .\src\run_pipeline.py --input .\data\tables --output .\outputs --model .\models\geo_yolo.pt
```

只运行最终绘图脚本：

```powershell
python .\src\section_drawer.py
```

指定表格目录和输出文件：

```powershell
python .\src\section_drawer.py --input .\data\tables --output .\outputs\section_D.svg
```

如果你把 5 张表放在一个 Excel 文件里，工作表名保持为 `section_info`、`topography`、`units`、`structures`、`observations`，也可以这样运行：

```powershell
python .\src\section_drawer.py --input .\GeoAgent_section_input.xlsx --output .\outputs\section_D.svg
```

## 输出

默认输出：

```text
outputs/section_D.svg
```

SVG 可以直接用浏览器打开，也可以插入 Word、PPT 或后续转换为 PNG/PDF。

## M1-M5 模块

当前流水线位于 `src/` 目录：

- `m1_yolo_detect.py`：M1，读取 YOLO 检测结果。当前无真实模型时读取 `observations.csv` 的 `yolo_result` 作为占位结果；后续真实 YOLO 模型接在这里。
- `m2_qwen_interpret.py`：M2，把 YOLO 结果、野外记录和照片说明整合成地质解释。
- `m3_fuse_tables.py`：M3，融合原始表格、YOLO 结果和解释结果，输出统一项目 JSON。
- `m4_build_section_model.py`：M4，检查剖面数据完整性，并生成可审查的剖面模型 JSON。
- `m5_draw_section.py`：M5，调用绘图引擎，输出最终地层剖面图 SVG。
- `run_pipeline.py`：一键串联 M1-M5。
- `section_drawer.py`：底层 SVG 绘图引擎。

M1-M5 的输出文件在 `outputs/`：

- `m1_yolo_results.json`
- `m2_qwen_interpretations.json`
- `m3_fused_project.json`
- `m4_section_model.json`
- `section_D.svg`

## 绘图规则

- 地形点之间使用平滑曲线连接，用于突出地形起伏。
- 每个岩性单元内部会绘制一组从地表曲线出露点开始的层面线。
- 不再绘制从图底或侧边“冒出”的层面线；层面线必须有一端落在地表曲线上。
- 层面线间距读取 `units.csv` 的 `thickness_m`，按剖面比例尺换算到图上。
- 层面线角度读取 `dip_angle_deg`，始终按真倾角绘制，不换算为剖面视倾角。
- 岩性花纹只填充在对应岩层范围内：该范围由地表出露段和两侧按倾角向下投影的接触线围成，并会随该岩层倾角旋转。
- `from_m` 和 `to_m` 控制岩性单元在剖面上的起止位置。

## 数据流

```text
YOLO 检测结果 + Qwen 解释 + 人工校核
        ↓
标准化 CSV 表格
        ↓
section_drawer.py
        ↓
地层/地质剖面图 SVG
```
