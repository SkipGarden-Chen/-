# YOLO 数据集目录

推荐目录结构：

```text
data/yolo_dataset/
  data.yaml
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
```

每张图片对应一个同名 `.txt` 标注文件，采用 YOLO 格式：

```text
class_id x_center y_center width height
```

坐标均为 0-1 归一化坐标。

当前类别：

```text
0 outcrop              露头范围
1 bedding              层理
2 joint_fracture       节理/裂隙
3 fault                断层
4 fold                 褶皱
5 lithologic_boundary  岩性界线
6 strata_line          地层线/层面线
```

