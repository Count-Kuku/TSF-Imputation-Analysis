# My-TSF-Research

本项目维护原始数据、基础预测模型、表格填补实现和共享研究产物。**两个项目的总体架构统一在 [TFC README](../../PycharmProjects/TFC/README.md)**（本机 `D:/Projects/PycharmProjects/TFC/README.md`）。接手研究先读该总览，再打开对应研究的 README。

## 本项目的工具入口

| 任务 | 入口 |
|---|---|
| 修改基础模型、读取旧评估结果 | [Eval](Eval/README.md) |
| 修改表格基础填补 | [Imputation](Imputation/README.md) |
| 分析窗口或绘图 | [Analysis](Analysis/README.md)、[Visualize](Visualize/README.md) |
| 生成旧 BM 缺失输入 | [Missing Value Injection](tools/Missing_Value_Injection/README.md) |
| 查看原始数据 | [data](data/README.md) |
| 查询公共数值、找到私有 run 和文稿 | [产物目录](artifacts/README.md)、[统一库](artifacts/unified/README.md) |
| 核对本机环境与模型缓存 | [本机资产](docs/LOCAL_ASSETS.md) |

各研究的代码、协议、状态和结论按主题放在 TFC 的研究目录。TFC 各工作树的 `artifacts` 均指向本项目的同一物理目录；换工作树无需复制数据。

## GitHub 仓库

日常开发和推送使用个人 fork 的 [`Count-Kuku/TSF-Imputation-Analysis`](https://github.com/Count-Kuku/TSF-Imputation-Analysis) 的 `main`。本地 `origin` 指向该 fork；`upstream` 指向[原仓库](https://github.com/Decadentvc/TSF-Imputation-Analysis)，仅用于查看和按需同步，不直接向其推送。当前 fork 的 `main` 采用原 `zyh_pic` 的研究状态，与原仓库 `main` 已分叉；以后引入上游改动时应先检查差异并测试。

GitHub 只保存 Git 跟踪的文件。`artifacts/unified/library.sqlite3` 等被忽略的共享研究数据仍保存在本机目录，不随 fork 的 `main` 推送。
