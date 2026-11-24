# 公开验证记录

本目录保存 2026-11-24 的两次实际证明重放记录，共 5 条已发布命题。证明源码位于固定版本的上游子模块；这里只保留验收摘要、检查器日志、生成的定理类型 wrapper 和 `Print Assumptions` 输出。

服务器的绝对路径、用户名目录、主机名和机器标识已替换成占位符。这些文件是脱敏副本；历史 `summary.json` 中的源日志/证据 SHA 标识原始未脱敏材料。公开文件本身的 SHA 以根目录 `PUBLICATION_MANIFEST.json` 为准。原始运行结果保留原服务器。

`setup-acceptance.json`：两次通过的范围与 VS Code 环境验收。

`logs/`：两次原始 checker 文本输出的脱敏副本。`COMPILED` 包括 Dune 缓存命中。

`audits/`：每条已通过定理的 `Wrapper.v`、`assumptions.out` 和编译日志；上游证明 `Proof.v` 通过子模块获取，避免重复发布。

`enrollment-environment.json`：Python 锁定环境和项目配置校验。配置校验与证明检查是不同步骤。

`rocq-editor-environment.json`：Rocq 9.2 / VsRocq 2.4.3 环境、小示例编译、归档恢复和交互视图验收。

本目录没有声称完整模型源码构建、全部公开证明、可选 `rocqchk` 或原始 AI 生成过程已通过。
