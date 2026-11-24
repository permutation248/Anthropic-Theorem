# Rocq 编辑器环境

已验收的服务器开发环境使用 Rocq 9.2.0、OCaml 4.14.3、固定 LPS `f1006fe8` 和 VsRocq 2.4.3。

VS Code 扩展为 `rocq-prover.vsrocq`，必须同时安装兼容的语言服务器。将本机的 `vsrocqtop` 路径写入 VS Code 工作区配置：

```json
{
  "vsrocq.path": "/your/toolchain/bin/vsrocqtop",
  "vsrocq.proof.mode": 1
}
```

该配置应指向自己的安装位置。公开仓库不包含服务器的 rootfs、1.1 GiB 工具链归档、私有路径或全局机器设置。

`examples/ModelSmoke.v` 导入已安装的固定 LPS，`Proof.` 后应显示目标 `page_size = 4096%Z`。它仅验证编辑器与模型加载；大型公开证明还需要对应编译后的依赖树与正确的逻辑路径。

官方证明重放仍使用 `scripts/study.py verify ...` 和固定 checker。编辑器语言服务成功不等于所有工程证明通过。
