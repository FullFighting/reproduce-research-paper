# 科研论文复现：Codex Skill

这是一个面向带代码、数据和实验论文的证据优先 Codex Skill。

V1.2 不接受人工编写的 `observed-metrics.json`。只有从本次运行生成的 stdout、stderr、JSON、CSV、NumPy、Parquet 或文件哈希工件中，通过预先声明的机器提取规则得到的观测，才有资格进入比较。手工读取的表格、图片或曲线只能标记为 `MANUAL_REVIEW_REQUIRED`。

> 本结果只验证记录环境和协议下声明的计算 claim，不验证整篇论文的真实性、因果解释或一般化能力。

## 为什么需要 Codex

科研复现同时需要语义推理和确定性验证。Codex 负责通读论文、定位可执行 claim、映射官方代码/数据/命令、生成可评审的 preview-only 计划、诊断失败和提出回归测试；确定性 runtime 负责隔离执行、机器提取、provenance 校验、重新比较和生成 claim-scoped 报告。Codex 不负责给论文判定“科学真伪”。

[Codex 规划评估试点](docs/codex-evaluation/README.md)公开了 3 个论文/仓库案例的初始提示、草案计划、评审记录、修订计划、证据链接和 telemetry 限制。它来自本次 Codex desktop 工作流，不冒充经过独立人工评审的正式基准。

## 已完成的公开验证

[公开基准报告](benchmarks/benchmark-report.md)包含 15 个公开、关联论文、低成本、claim-level 的可执行案例，来源包括 Nature、Nature Methods、JMLR、KDD、NeurIPS、ICML、Journal of Financial Economics 和 Mathematical Programming Computation 等。

<!-- benchmark-facts:start -->
- 15 个公开、关联论文、claim-level 的可执行案例；
- 15/15 个 claim 在预声明容差内复现；
- 15/15 个 evidence bundle 通过重新哈希、重新比较和重新渲染报告；
- 确定性 runtime 使用 0 个 API token，估算外部 API 成本 $0；
<!-- benchmark-facts:end -->
- 每个 benchmark plan 均声明 GPU 预算为 0；
- 每个案例公开论文与代码链接、计划、环境锁、数据及许可说明、原始日志、观测、比较、最终报告、provenance 和偏差限制。

这些是边界清楚的 claim-level 可执行检查，不会把低成本烟雾测试冒充为原论文全部大型实验的完整复现。

## 主要安全边界

- schema v2 支持 scalar、array、带标签 table、ranking、categorical、string、artifact hash 和 distribution；
- 单位采用 `symbol + scale + semantic_type`，可表达 BLEU、F1、能耗、FLOPs、吞吐、货币、基点和自定义指标；
- 全量代码树、Git commit、dirty diff、submodule、数据、权重、配置和环境锁分别哈希；
- 执行前后检查原仓库与运行 workspace，未声明写入会使证据失效；
- 支持 copy、独立 Git worktree、只读源码挂载的 Docker container 三种模式；
- 网络、CPU、内存、磁盘、GPU、输出数量和写目录必须声明；
- 密钥默认只能通过环境变量 `secret_bindings` 注入；argv secret 默认拒绝，只有显式高风险兼容模式才允许并记录偏差；
- 最终报告从原始工件重新计算，不信任 comparison 中已有的 verdict；
- 修改任一已登记工件都会导致 bundle 校验失败。

## 使用

```text
使用 $reproduce-research-paper 阅读这篇论文的全部内容，识别可执行 claim，
盘点官方代码仓库并先生成只预览、不执行的复现计划。
未经我确认，不要下载数据或运行实验。
```

验证、预览、执行和校验：

```powershell
python skills/reproduce-research-paper/scripts/validate_reproduction_plan.py `
  --plan skills/reproduce-research-paper/assets/examples/reproduction-plan.json

python skills/reproduce-research-paper/scripts/run_reproduction.py `
  --plan skills/reproduce-research-paper/assets/examples/reproduction-plan.json `
  --output reproduction-output

python skills/reproduce-research-paper/scripts/run_reproduction.py `
  --plan skills/reproduce-research-paper/assets/examples/reproduction-plan.json `
  --output reproduction-output `
  --execute

python skills/reproduce-research-paper/scripts/build_report.py `
  --bundle reproduction-output
```

完整设计、开发命令和 V1.2 证据见 [英文 README](README.md)。
