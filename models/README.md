# 模型目录

训练完成后建议把最佳模型复制到：

```text
models/geo_yolo.pt
```

之后 M1 模块和完整流水线可以这样调用：

```powershell
python .\src\run_pipeline.py --model .\models\geo_yolo.pt
```

