# Revit 2021 实机连接卡（已验证）

> 状态：2026-08-13 已在真实 Windows Revit 2021 会话完成**只读端到端验证**。这是连接和调用前检，不是建模、出图或 BIM Benchmark 通过证明。

## 适用配置

| 项目 | 已验证值 |
| --- | --- |
| Windows 主机 | `YOUR_REVIT_HOST`（若 IP 改变，使用当前主机地址） |
| SSH 用户 | `codex` |
| Revit | `C:\Program Files\Autodesk\Revit 2021\Revit.exe` |
| Node | v22.22.3 |
| 插件目录 | `C:\ProgramData\Autodesk\Revit\Addins\2021\` |
| 端口 | Revit 进程监听 `8080`；npm server 只连接同机 `localhost:8080` |

实际链路：

```text
执行器（Codex / DSH）
  → SSH stdio（跨机时；同机直连可省略）
  → Windows: npx -y mcp-server-for-revit
  → Windows localhost:8080
  → Revit MCP Plugin / Revit API
```

Mac 不应运行 npm server 后试图跨局域网直连 Revit；server 必须经 SSH 在 Windows 主机启动。执行器与 Revit 同机时不需要 SSH，直接连接 `localhost:8080`。

## 当前任务与链路边界

上表是历史只读证据。当前任务按[方案与画图共同约定](../../../workflows/SCHEME_DRAWING_REVIEW.md)区分 Scheme 验证与正式 Drawing。本机执行器使用配置好的本机 MCP，同样读取活动视图和模型统计；只有跨主机调用才采用下述 SSH 链路，不将 IP、路径或工具数量当作通用常量。写入能力与导出能力须另有本会话证据。

## 每次 Revit 会话的最小启动步骤

1. 打开一个可写的 `.rvt` 项目，关闭会阻塞 API 的模态窗口，激活实际项目平面或 3D 视图。
2. 在 `Revit MCP Plugin` 的 `Settings` 中只启用本次要用的命令并保存。
3. **若刚修改 Settings，完整退出再重开 Revit**；命令集配置在重启前不会可靠地更新。
4. 点击 `Revit MCP Switch`，确认出现 `Open Server`，而非 `Close Server`。
5. 在执行器项目根目录执行只读前检（Windows 用 `python`；其他平台按本机解释器）：

   ```bash
   python tools/revit-mcp/scripts/smoke_revit_mcp.py
   ```

前检同时调用 `get_current_view_info` 和 `analyze_model_statistics`。只有两项都有 MCP `content` 返回，Drawing Agent 才可进入任何写操作；否则停止并报告环境阻断。

## 已保存的实测证据

此连接卡对应的真实 Revit 空白项目返回：

- MCP server v1.0.0 初始化成功，发现 26 个已注册工具。
- `get_current_view_info`：活动视图为 `标高 1`（`FloorPlan`，比例 1:100，Id 312）。
- `analyze_model_statistics`：项目 `项目1`，返回 `success: true`、2 个标高、36 个视图、0 张图纸。

项目当时没有墙或其他待验证建筑构件。因此以下均**尚未验收**：Level 1 BIM 对象、楼梯/屋顶等 Level 2、图纸/PDF Level 3、完整小型公共建筑，以及任何 `send_code_to_revit` 写入模式。

> **2026-10-20 更新**：上述“尚未验收”是 2026-08-13 空白项目时点。2026-10-04 至 10-19 的 Wuchang library 项目已实际使用 `send_code_to_revit` 1,771 次，创建 123 个 Room、墙/门/楼梯/家具并导出 33 页 PDF，最新回读 0 非正面积、0 warnings。该实践覆盖了写入与出图的真实使用，但**不等于 TEST_PLAN 8 项逐项验收**；正式记录仍待补。

## 安装与恢复要点

- 当前生效 manifest 为 `mcp-servers-for-revit.addin`，并与 `revit_mcp_plugin/` 文件夹位于 all-user Addins 目录。
- 发布包含一个 GUID 相同的重复 manifest。为避免 Revit “已存在一个应用程序”错误，保留的重复文件被改名为 `revit-mcp.addin.disabled`；**不要同时启用两个 `.addin` 文件**。
- 看到工具但调用超时：先确认 Settings 已保存、Revit 已完整重启、没有模态对话框、并已激活项目视图；随后重新 Open Server，再跑前检。
- 功能区没有插件：核对 Revit 年份为 2021、manifest 与 DLL 是否同目录、且没有重复 active manifest。
- 8080 不监听：在 Windows PowerShell 运行 `Get-NetTCPConnection -LocalPort 8080 -State Listen`，然后重新 Open Server。

## 写入前的执行纪律

前检成功只证明连接可用，不证明模型可写或构件正确。写入前仍须：正式 Drawing 确认 Gate B，Scheme 验证确认任务授权与实验范围；保存可回退 RVT、读取 `revit-mcp-patterns.md`、先查询真实 Family/Type/Level、逐项串行调用并以查询和 Revit 平剖/三维视觉复核。空白项目可以作为可丢弃的后续 Level 1 测试项目，但不得把当前连接记录算作这些测试已通过。
