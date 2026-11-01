# HUMAN ACTION REQUIRED

下列动作必须由人工在 Windows/Revit 图形界面完成。2026-08-13 已完成插件安装、8080 监听及两项只读 MCP 验证；Level 1/2/3 与任何模型写入仍未执行。

## 1. 准备 Windows 运行时

1. 登录 Windows 笔记本 `YOUR_REVIT_HOST`。
2. 确认 Revit 2021 可执行文件存在：

   ```text
   C:\Program Files\Autodesk\Revit 2021\Revit.exe
   ```

3. 在 PowerShell 执行 `node --version` 和 `npx --version`。Node.js 必须为 20 或更高；若未安装或版本过低，人工安装当前 Node.js LTS。
4. 当前 Revit 2021 发布包工作流不需要 .NET SDK。不要为了本次测试安装 .NET 10：仓库的 .NET 10 测试工程只支持 Revit 2025/2026，不支持 R21。

## 2. 安装 Revit 2021 插件

1. 从 `https://github.com/mcp-servers-for-revit/mcp-servers-for-revit/releases` 下载名称以 `-Revit2021.zip` 结尾的发布资产。
2. 完全退出 Revit。
3. 解压并复制到（本机实测安装位置）：

   ```text
   C:\ProgramData\Autodesk\Revit\Addins\2021\
   ```

4. 人工核对以下文件存在：

   ```text
   C:\ProgramData\Autodesk\Revit\Addins\2021\mcp-servers-for-revit.addin
   C:\ProgramData\Autodesk\Revit\Addins\2021\revit_mcp_plugin\RevitMCPPlugin.dll
   C:\ProgramData\Autodesk\Revit\Addins\2021\revit_mcp_plugin\Commands\RevitMCPCommandSet\command.json
   C:\ProgramData\Autodesk\Revit\Addins\2021\revit_mcp_plugin\Commands\RevitMCPCommandSet\2021\RevitMCPCommandSet.dll
   ```

   发布包有重复 GUID 的第二个 manifest 时，只保留一个 active `.addin`；本机将 `revit-mcp.addin` 改名为 `revit-mcp.addin.disabled`。

## 3. 打开 Revit 并加载插件

1. 人工运行：

   ```text
   C:\Program Files\Autodesk\Revit 2021\Revit.exe
   ```

2. 如果 Revit 显示未知发布者/外部插件提示，确认来源为本仓库发布包后选择始终加载。
3. 新建一个可丢弃的建筑测试项目，不要打开生产模型。
4. 确认功能区出现 `Revit MCP Plugin` 面板。
5. 点击 `Settings`，启用 `TEST_PLAN.md` 所涉及的命令并保存。
6. 点击 `Revit MCP Switch`；出现 `Open Server` 对话框后确认。
7. 在 Windows PowerShell 执行：

   ```powershell
   Get-NetTCPConnection -LocalPort 8080 -State Listen
   ```

8. 保持 Revit 和测试项目打开，避免停留在会阻塞 API 的模态对话框。

## 4. 从 Mac 验证 MCP 链路

1. 确认 SSH 仍可用：

   ```bash
   ssh -T YOUR_REVIT_HOST "node --version && npx --version"
   ```

2. 将 `SETUP.md` 中的 Multica `mcp_config` 或 OpenClaw `mcp.servers` 配置载入对应客户端。
3. OpenClaw 使用者执行：

   ```bash
   openclaw mcp status --verbose
   openclaw mcp probe revit-windows --json
   ```

4. 确认客户端发现 `SETUP.md` 列出的 26 个工具。
5. 从仓库根目录运行 `python3 tools/revit-mcp/scripts/smoke_revit_mcp.py`；它只调用 `get_current_view_info` 和 `analyze_model_statistics`。
6. 两项均返回成功后才继续 `TEST_PLAN.md`。`say_hello` 是可选人工可见冒烟，不替代前检。

## 5. 人工执行 8 项测试

严格按 `TEST_PLAN.md` 顺序执行并记录结果：

1. 创建墙。
2. 创建门。
3. 创建房间。
4. 修改独立测试墙位置。
5. 创建楼板。
6. 创建基本视图。
7. 标尺寸。
8. 获取模型信息。

每项保留 MCP 完整返回和一张 Revit 结果截图。任何一项失败都先按该项的失败排查处理，不要在生产项目上复测。

## 6. 测试结束

1. 导出或保存测试证据。
2. 测试项目不需要留存时，关闭项目并选择不保存。
3. 点击 `Revit MCP Switch`，出现 `Close Server` 后确认。
4. 关闭 Revit。

## 7. 关于仓库自带 `dotnet test`

当前 Revit 2021 环境不要运行仓库 README 中的：

```text
dotnet test -c Debug.R25 -r win-x64 tests/commandset
dotnet test -c Debug.R26 -r win-x64 tests/commandset
```

原因是 `tests/commandset/RevitMCPCommandSet.Tests.csproj` 只定义 Revit 2025/2026 配置，并明确依赖 .NET 10 SDK。当前应以 `TEST_PLAN.md` 的 8 项端到端 MCP 测试作为验收。未来若另行安装 Revit 2025 或 2026，再人工安装 .NET 10 SDK并运行与该 Revit 主版本一致的测试命令。
