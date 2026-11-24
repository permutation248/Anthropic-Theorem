# Anthropic × Theorem：软件工程与形式化验证研究工作区

围绕 Anthropic 于 **2026 年 10 月 22 日**发布的 [LLMs are making formal software verification feasible at a much larger scale](https://www.anthropic.com/research/formal-verification)，整理公开代码、研究路线和证明重放记录。

这是独立学习项目。已重放 **2 个入口的 5 条公开证明**；完整报告、所有公开证明及作者的原始 AI 证明生成流水线尚未全部复现。先读 [中文研究路线](docs/研究路线.md)，再查看 [本次验证证据](evidence/README.md)。

## 三个项目

三个目录使用 Git 子模块固定版本，保留上游完整源码、历史和许可证。

| 目录 | 内容 | 固定提交 |
|---|---|---|
| [oss-verify](https://github.com/theorem-labs/oss-verify) | 项目接入、构建规则与 Python CLI | `6b4c8dc308d96a0f290446a190c31d79cb8cee47` |
| [oss-verify-proofs](https://github.com/theorem-labs/oss-verify-proofs) | 已发布规格、RISC-V 二进制绑定、Rocq 证明与检查器 | `32c8baf6e92f173b445903857770da103ba307e0` |
| [rocq-linux-process-semantics](https://github.com/theorem-labs/rocq-linux-process-semantics) | 与证明配套的 Linux/RISC-V 模型和证明库 | `f1006fe8178338a499b5e5c41be83006c4edd058` |

证明基线覆盖 32 个库、90 个有证明入口，是后续公开快照。它与报告统计、上游新版本统计以及本仓库实际重放数量不同。准确环境见 [VERSIONS.json](VERSIONS.json)。

## 获取完整项目

```bash
git clone --recurse-submodules https://github.com/permutation248/Anthropic-Theorem.git
cd Anthropic-Theorem
```

已经普通克隆过的目录运行：

```bash
git submodule update --init --recursive
```

GitHub 的“Download ZIP”不会包含子模块源码。请使用以上 Git 命令。证明仓库规模较大，首次拉取和编译需要时间与磁盘空间。

## 重放公开证明

公开脚本使用官方固定摘要的 checker 镜像。需要 **Linux x86-64、Python 3.12、pip 和可访问的 Docker daemon**。官方镜像自带 Rocq 9.2、LPS、Dune 及证明依赖。默认 4 个编译 worker；可用 `OFT_JOBS` 调整。证明检查主要使用 CPU 和内存。

```bash
python3.12 -m venv .venv
.venv/bin/python scripts/study.py versions
.venv/bin/python scripts/study.py prepare
.venv/bin/python scripts/study.py fetch zlib
.venv/bin/python scripts/study.py verify zlib/checksum_fuzzer
.venv/bin/python scripts/study.py fetch cjson
.venv/bin/python scripts/study.py verify cjson/cjson_read_fuzzer
```

检查过程调用原版 `oft check --parts statements,proofs --proof-jobs 1`：验证二进制 SHA、编译声明和证明、检查顶层定理类型并审计允许公理。检查时容器断网；下载镜像、Python 依赖和二进制时需要网络。新运行写入忽略的 `runs/`，不会覆盖已发布证据。

公开 Docker 入口已做命令与参数验证；本仓库记录的服务器实际运行使用同一官方镜像中的无特权 namespace 适配器。两者的启动方式不同，不能把历史记录当成公开脚本刚执行的结果。原始服务器开发环境继续保留在部署机器。

## 本次实际结果

| 入口 | 已检查的公开证明 | 结果 | 耗时 |
|---|---:|---|---:|
| `zlib/checksum_fuzzer` | 2 条终止性证明 | 通过 | 264.86 秒 |
| `cjson/cjson_read_fuzzer` | 3 条 sanitizer 一致性证明 | 通过 | 732.20 秒 |

运行日期：2026-11-24。两次均复用了独立编译缓存，不能将耗时用作冷启动基准。wrapper 与允许公理审计均通过；可选 `rocqchk` 未执行。结果适用于指定入口、二进制、命题和 LPS 前提。

## VS Code 与阅读

打开仓库根目录，`.vscode/tasks.json` 提供两个证明重放任务。`examples/ModelSmoke.v` 是导入固定 LPS 的小型环境验收示例；运行 `.venv/bin/python scripts/study.py smoke` 可通过官方 checker 编译。它不计入上述 5 条研究证明。

交互式编辑需要匹配的 Rocq 9.2 与 VsRocq 语言服务器。服务器侧已验收 VsRocq 2.4.3；安装和依赖路径因机器而异，参见 [编辑器说明](docs/editor.md)。

建议依次阅读：

1. [中文研究路线与复现边界](docs/研究路线.md)。
2. `oss-verify-proofs/projects/zlib/checksum_fuzzer/README.md`、`Statements.v`、`proofs/`。
3. `oss-verify-proofs/projects/cjson/cjson_read_fuzzer/README.md` 与三个一致性证明。
4. `rocq-linux-process-semantics/SCOPE.md`，追踪模型假设和系统调用语义。

从源码重建被证明二进制还需对应源码、builder、OSS-Fuzz、static-asan 和构建材料。`oss-verify` 当前项目配置也可能与旧证明发布版不同；新构建不能直接继承旧二进制证明。

本仓库的研究文档和辅助代码使用 MIT；三个上游项目及其第三方内容保留原许可证，见 [第三方说明](THIRD_PARTY_NOTICES.md)。
