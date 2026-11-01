# Revit MCP 集成目录

本目录保存 `mcp-servers-for-revit/mcp-servers-for-revit` 的固定浅克隆，以及针对当前 Multica 架构环境整理的安装、配置和人工测试说明。

## 当前状态

- 上游仓库：`https://github.com/mcp-servers-for-revit/mcp-servers-for-revit`
- 本地目录：`repo/`
- 克隆方式：`git clone --depth 1`
- 当前提交：`86cf7057785f2423fc0d0892c9a5d9c93deb1aa3`
- 当前分支：`main`
- 目标 Revit：Windows 笔记本 `YOUR_REVIT_HOST` 上的 Revit 2021
- Revit 可执行文件：`C:\Program Files\Autodesk\Revit 2021\Revit.exe`
- 当前阶段：配置和测试计划已就绪；未安装 .NET、未启动 Revit、未执行会修改模型的测试。

## 文件导航

- [`SETUP.md`](SETUP.md)：依赖、版本兼容、发布包安装、Multica/OpenClaw MCP 配置、验证方法和实际工具清单。
- [`TEST_PLAN.md`](TEST_PLAN.md)：创建墙、门、房间、移动构件、楼板、基本视图、尺寸和模型信息共 8 项测试。
- [`HUMAN_ACTION_REQUIRED.md`](HUMAN_ACTION_REQUIRED.md)：必须由人工在 Windows/Revit 图形界面完成的步骤。
- `repo/`：上游源码原样浅克隆，包含 TypeScript MCP server、C# Revit 插件、命令集和 Revit 2025/2026 集成测试。

## 边界

Mac mini 只负责保存源码、配置 MCP 客户端和发起 SSH stdio 会话。Revit 插件与 npm MCP server 必须在 Windows 侧配合运行，因为 npm server 的源码固定连接 `localhost:8080`，而 Revit 插件在 Revit 进程内监听该端口。

