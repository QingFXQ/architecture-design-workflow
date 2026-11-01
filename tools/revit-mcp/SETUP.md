# Revit MCP 安装与配置指南

## 1. 已核实的系统结构

仓库由三部分组成：

1. `server/`：TypeScript MCP server，通过 stdio 向 MCP 客户端暴露工具。
2. `plugin/`：载入 Revit 的 C# 插件，启动 TCP listener。
3. `commandset/`：在 Revit API 中执行实际命令的 C# 命令集。

数据链路为：

```text
Multica/OpenClaw（Mac）
  -> SSH stdio
  -> mcp-server-for-revit（Windows）
  -> TCP localhost:8080
  -> Revit MCP Plugin（Revit 进程内）
  -> RevitMCPCommandSet
  -> Revit API
```

这一部署位置不是可选细节：`server/src/utils/ConnectionManager.ts` 固定连接 `localhost:8080`，所以 npm server 必须运行在装有 Revit 的 Windows 主机上。Mac 侧不能直接运行 npm server 后跨网络连接 Revit。

## 2. 前置依赖

### 2.1 Windows 运行环境

- 目标主机：`YOUR_REVIT_HOST`。
- Revit 2021：`C:\Program Files\Autodesk\Revit 2021\Revit.exe`。
- Node.js：使用 20 或更高版本。根 README 写的是 Node.js 18+，但 `server/package.json` 的实际引擎约束是 `node >=20.0.0`，因此以更严格的包约束为准。
- npm/npx：随 Node.js 安装，用于运行已发布的 `mcp-server-for-revit` npm 包。
- Windows OpenSSH Server：当前环境已可 SSH；Mac 侧配置使用 `YOUR_REVIT_HOST`，不另建代理服务。
- 本机已验证的 all-user Revit add-ins 目录：`C:\ProgramData\Autodesk\Revit\Addins\2021\`。`%AppData%` 是用户级替代位置，不应与 all-user 目录同时放置相同 GUID 的 manifest。

### 2.2 .NET 要求

发布 ZIP 已包含编译好的插件和命令集，普通安装与 8 项 MCP 冒烟测试不需要 .NET SDK。

| 用途 | Revit 版本 | 仓库目标框架或 SDK 要求 | 本项目处理方式 |
| --- | --- | --- | --- |
| 使用发布 ZIP | 2020–2024 | 插件和命令集源码目标为 `.NET Framework 4.8`（`net48`） | Revit 2021 使用对应发布 ZIP，不在 Mac 或 Windows 上编译 |
| 使用发布 ZIP | 2025–2026 | 插件和命令集源码目标为 `.NET 8`（`net8.0-windows10.0.19041.0`） | 当前不采用 |
| 从源码构建 | 2020–2024 | 项目目标为 `net48`；仓库未在 README 中给出独立 SDK 版本号 | 当前不构建，不推断额外 SDK 版本 |
| 从源码构建 | 2025–2026 | 项目目标为 `net8.0-windows10.0.19041.0` | 当前不构建 |
| 运行仓库自带测试 | 2025 或 2026 | `.NET 10 SDK`；`tests/commandset` 只定义 `Debug.R25`、`Debug.R26` | 不适用于当前 Revit 2021；改跑 `TEST_PLAN.md` 的 MCP 冒烟测试 |

仓库 README 给出的 .NET 10 安装命令是 `winget install Microsoft.DotNet.SDK.10`，但只有在另有 Revit 2025/2026 环境并运行仓库测试工程时才需要执行。

### 2.3 Revit 兼容性

| Revit | 仓库构建配置 | 目标框架 | 发布包可用性 | 当前状态 |
| --- | --- | --- | --- | --- |
| 2020 | R20 | .NET Framework 4.8 | 支持 | 未使用 |
| 2021 | R21 | .NET Framework 4.8 | 支持 | 当前目标 |
| 2022 | R22 | .NET Framework 4.8 | 支持 | 未使用 |
| 2023 | R23 | .NET Framework 4.8 | 支持 | 未使用 |
| 2024 | R24 | .NET Framework 4.8 | 支持 | 未使用 |
| 2025 | R25 | .NET 8 | 支持；仓库测试支持 | 未使用 |
| 2026 | R26 | .NET 8 | 支持；仓库测试支持 | 未使用 |

插件、命令集和 Revit 主版本必须一致。Revit 2021 只能使用发布页中名称以 `-Revit2021.zip` 结尾的资产。

## 3. 安装 Revit 插件

以下操作须由人工在 Windows 上执行，完整检查表见 `HUMAN_ACTION_REQUIRED.md`。

1. 从上游仓库 Releases 页面下载名称以 `-Revit2021.zip` 结尾的发布资产。
2. 退出所有 Revit 进程。
3. 解压后将发布包内容复制到本机实测目录：

   ```text
   C:\ProgramData\Autodesk\Revit\Addins\2021\
   ```

4. 完成后必须存在：

   ```text
   C:\ProgramData\Autodesk\Revit\Addins\2021\mcp-servers-for-revit.addin
   C:\ProgramData\Autodesk\Revit\Addins\2021\revit_mcp_plugin\RevitMCPPlugin.dll
   C:\ProgramData\Autodesk\Revit\Addins\2021\revit_mcp_plugin\Commands\RevitMCPCommandSet\command.json
   C:\ProgramData\Autodesk\Revit\Addins\2021\revit_mcp_plugin\Commands\RevitMCPCommandSet\2021\RevitMCPCommandSet.dll
   ```

   发布包含有第二个、GUID 相同的 manifest 时，不要同时保留两个 active `.addin`。本机将重复的 `revit-mcp.addin` 改名为 `revit-mcp.addin.disabled`。

5. 人工启动 `C:\Program Files\Autodesk\Revit 2021\Revit.exe`。遇到未知发布者提示时选择始终加载。
6. 在 Revit 的 `Revit MCP Plugin` 面板打开 `Settings`，启用本测试需要的命令并保存。
7. 点击 `Revit MCP Switch`。源码中的该按钮会初始化命令集并启动端口 `8080`；成功时 Revit 显示 `Open Server`。

注意：插件不会随 Revit 启动自动打开 socket。每次启动 Revit 后都要人工点击 `Revit MCP Switch`。

Settings 的命令集变更需要完整退出再重启 Revit；重开后重新点击 Switch，并先运行本仓库的只读前检：

```bash
python3 tools/revit-mcp/scripts/smoke_revit_mcp.py
```

## 4. MCP server 启动方式

### 4.1 发布包方式

仓库推荐直接运行 npm 包：

```powershell
npx -y mcp-server-for-revit
```

该进程必须在 Windows 侧启动。它使用 stdin/stdout 与 MCP 客户端通信，并在收到 Revit 工具调用时连接同机的 `localhost:8080`。

### 4.2 源码开发方式

仓库给出的开发命令为：

```powershell
cd server
npm install
npm run build
```

也可从仓库根目录以 `npx tsx server/src/index.ts` 运行源码。当前集成不执行这一路径，因为发布 npm 包已满足需求。

### 4.3 transport 限制

`server/src/index.ts` 只创建 `StdioServerTransport`。仓库没有 SSE、Streamable HTTP 或 HTTP listener 实现，因此本集成只配置 stdio；不能写一个 URL 就把它当成 SSE server。Mac 与 Windows 之间通过 SSH 透明转发 stdio。

## 5. Multica agent `mcp_config`

将 [`drawing-production-mcp-config.json`](drawing-production-mcp-config.json) 作为 Drawing Production Agent 的 `mcp_config`。它采用标准 `mcpServers` 格式；SSH 在 Windows 上启动 npm server，并把其 stdin/stdout 接回 Mac：

```json
{
  "mcpServers": {
    "revit-windows": {
      "command": "ssh",
      "args": [
        "-T",
        "-l",
        "codex",
        "YOUR_REVIT_HOST",
        "cmd.exe /d /s /c \"npx -y mcp-server-for-revit\""
      ]
    }
  }
}
```

前提是 `ssh -T -l codex YOUR_REVIT_HOST` 已能使用当前账户登录。不要把 `command` 改成 Mac 本机的 `npx`，否则 npm server 会尝试连接 Mac 自己的 `localhost:8080`。首次连接和每次 Revit 重启后，先运行本仓库 `smoke_revit_mcp.py` 的两个只读检查，再允许 Agent 写模型。

## 6. OpenClaw 配置

OpenClaw 的保存结构为 `mcp.servers`。在 Mac 的 OpenClaw 配置中加入：

```json
{
  "mcp": {
    "servers": {
      "revit-windows": {
        "command": "ssh",
        "args": [
          "-T",
          "-l",
          "codex",
          "YOUR_REVIT_HOST",
          "cmd.exe /d /s /c \"npx -y mcp-server-for-revit\""
        ],
        "enabled": true,
        "connectionTimeoutMs": 10000,
        "requestTimeoutMs": 130000,
        "supportsParallelToolCalls": false
      }
    }
  }
}
```

也可用 OpenClaw CLI 保存同一条目：

```bash
openclaw mcp set revit-windows '{"command":"ssh","args":["-T","-l","codex","YOUR_REVIT_HOST","cmd.exe /d /s /c \"npx -y mcp-server-for-revit\""],"enabled":true,"connectionTimeoutMs":10000,"requestTimeoutMs":130000,"supportsParallelToolCalls":false}'
```

`requestTimeoutMs` 设为 130 秒，是因为仓库 socket client 对单个 Revit 命令的内部超时为 120 秒。`supportsParallelToolCalls` 关闭，是因为仓库自身把 Revit 连接串行化，且 Revit API 操作适合按顺序执行。

## 7. 分层验证

### 7.1 Windows 运行时

在 Mac 上通过现有 SSH 验证 Windows Node.js：

```bash
ssh -T -l codex YOUR_REVIT_HOST "node --version && npx --version"
```

Node 版本必须是 20 或更高。

### 7.2 MCP 初始化和工具发现

Multica agent 重新加载 `mcp_config` 后，应发现本文件第 9 节的 26 个工具。OpenClaw 可执行：

```bash
openclaw mcp status --verbose
openclaw mcp probe revit-windows --json
```

即使 Revit 尚未打开，stdio server 仍应完成初始化并列出工具；此时调用依赖 Revit 的工具会报连接失败，这是预期现象。

### 7.3 Revit 插件端口

人工启动 Revit 并点击 `Revit MCP Switch` 后，在 Windows PowerShell 检查：

```powershell
Get-NetTCPConnection -LocalPort 8080 -State Listen
```

应看到 Revit 进程监听端口。源码将端口硬编码为 `8080`，配置文件中的其他端口值不会生效。

### 7.4 端到端连接

1. 保持 Revit 项目打开，确认 `Revit MCP Switch` 已显示过 `Open Server`。
2. 调用 `say_hello`，参数可为空。
3. Revit 应显示问候对话框，MCP 调用返回成功。
4. 再调用 `get_current_view_info`，应返回当前视图名称、类型等信息。
5. 继续执行 `TEST_PLAN.md` 的 8 项模型测试。

## 8. 常见故障定位

| 现象 | 核查点 |
| --- | --- |
| MCP server 启动后立刻退出 | Windows `node --version` 是否达到 20；`npx` 是否可用；SSH 远程命令是否能执行 |
| 工具能列出，但所有 Revit 工具报连接失败 | Revit 是否已打开；是否点击 `Revit MCP Switch`；`Get-NetTCPConnection` 是否看到 8080 |
| `Method not found` | Revit `Settings` 中对应命令是否启用；`command.json` 与 `2021\RevitMCPCommandSet.dll` 是否在正确目录 |
| 插件未出现在 Revit 功能区 | `.addin` 文件和 `revit_mcp_plugin` 文件夹位置是否正确；是否使用 Revit 2021 发布资产 |
| SSH 启动成功但调用超时 | npm server 是否确实在 Windows 而非 Mac；Revit 是否停留在模态对话框；模型操作是否超过 120 秒 |
| 8080 被占用 | 关闭重复 Revit 实例或占用端口的进程，再重新点击 `Revit MCP Switch` |
| 某工具返回成功但未创建元素 | 检查返回的 `response` 元素 ID 数量和 `warnings`；确认项目内存在匹配类别/族类型与标高 |

## 9. 实际 MCP tool 清单

以下名称来自 `server/src/tools/*.ts` 中实际的 `server.tool(...)` 注册，共 26 个。空文件 `modify_element.ts`、`search_modules.ts`、`use_module.ts` 没有注册函数，不是可调用工具。

| MCP tool | 实际能力 |
| --- | --- |
| `ai_element_filter` | 按类别、类型、可见性和空间范围查询元素 |
| `analyze_model_statistics` | 返回元素、类型、族、视图、图纸、类别和标高统计 |
| `color_elements` | 按类别和参数值给当前视图元素着色；内部 Revit command 为 `color_splash` |
| `create_dimensions` | 在当前或指定视图创建线性尺寸 |
| `create_grid` | 创建带自动命名和间距的轴网 |
| `create_level` | 创建标高，并可同时创建楼层平面和天花板平面 |
| `create_line_based_element` | 创建墙、梁、风管等线性构件 |
| `create_point_based_element` | 创建门、窗、家具等点式构件 |
| `create_room` | 在封闭边界内创建房间并设置名称、编号等属性 |
| `create_structural_framing_system` | 创建结构梁框架系统 |
| `create_surface_based_element` | 创建楼板、天花板或屋面 |
| `delete_element` | 按 ElementId 删除元素 |
| `export_room_data` | 导出项目内房间数据 |
| `get_available_family_types` | 查询当前项目可用族/类型 ID |
| `get_current_view_elements` | 查询当前视图中的模型和注释元素 |
| `get_current_view_info` | 获取当前活动视图信息 |
| `get_material_quantities` | 计算材料面积、体积和数量 |
| `get_selected_elements` | 获取 Revit 当前选中元素 |
| `operate_element` | 选择、剖切框、着色、透明、删除、隐藏、隔离等；不支持移动 |
| `query_stored_data` | 查询 MCP server 本地 SQLite 中保存的项目/房间数据 |
| `say_hello` | 在 Revit 显示问候对话框，用于连接测试 |
| `send_code_to_revit` | 在 Revit 中动态编译执行 C#，支持自动事务或无事务模式 |
| `store_project_data` | 将项目元数据写入 MCP server 本地 SQLite |
| `store_room_data` | 将房间元数据写入 MCP server 本地 SQLite |
| `tag_all_rooms` | 标注当前视图全部或指定房间；内部 command 为 `tag_rooms` |
| `tag_all_walls` | 标注当前视图中的墙；内部 command 为 `tag_walls` |

## 10. 核实来源

- `repo/README.md`：架构、Revit 2020–2026、发布包安装、测试和构建目标。
- `repo/server/README.md`：stdio MCP 配置和支持工具说明。
- `repo/server/package.json`：Node.js `>=20.0.0`。
- `repo/server/src/index.ts`：仅使用 `StdioServerTransport`。
- `repo/server/src/tools/*.ts`：实际 MCP tool 名称和参数 schema。
- `repo/server/src/utils/ConnectionManager.ts`：固定 `localhost:8080`。
- `repo/server/src/utils/SocketClient.ts`：单命令 120 秒超时。
- `repo/plugin/Core/SocketService.cs`：插件监听端口 8080。
- `repo/plugin/RevitMCPPlugin.csproj`、`repo/commandset/RevitMCPCommandSet.csproj`：Revit 版本和目标框架。
- `repo/tests/commandset/RevitMCPCommandSet.Tests.csproj`：测试只含 R25/R26。
