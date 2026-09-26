# 本机模型与环境目录

这些目录未纳入 Git，但不能按“未跟踪”直接删除。它们不属于共享研究结果；正式数值仍从 `artifacts/unified/library.sqlite3` 查询。

| 路径 | 本机内容 | 当前处理 |
|---|---|---|
| `.conda/` | 完整的本地 Conda 环境，含 Python 与依赖 | 保留；当前 Eval 文档指定的运行解释器是 `D:/anaconda3/envs/TSFIA/python.exe`，不要把 `.conda/` 当作研究数据迁移 |
| `.cache/hf_modules/` | Hugging Face 动态模块缓存 | 保留；模型加载可能依赖缓存，清理前需核对具体模型与离线可重建性 |
| `hf_models/VisionTSpp/` | VisionTSpp 的本地缓存和图片目录 | 保留；活跃适配器默认用 `Lefei/VisionTSpp`，代码未直接绑定本目录，不能据此断言缓存无用 |
| `tools/tsfm-1.0.1/` | 本地 TSFM 源码、构建目录和安装元数据 | 保留；先核对环境安装来源，再决定是否移出仓库工作目录 |

代码和实验结果使用各自的入口；不要把上述目录复制到 TFC 工作树或当作可共享数值缓存。
