> 历史参考，不作为当前执行指令。以根 AGENTS.md 与 PIPELINE_WORKFLOW 为准。

# 人工动作清单

以下事项必须由用户、教师或 Windows/Blender 图形界面的操作者完成。AI 可以准备材料、解释步骤和记录结果，但不能假装已替人完成确认、软件界面操作或 Gate 决策。完成后应在相应项目 `DECISIONS.md`、`ARTIFACTS.md`、Issue 或工具测试记录中留下日期、版本、操作者和证据。

| 编号 | 必须动作 | 为什么需要人工 | 可查文件 | 如何验证完成 |
| --- | --- | --- | --- | --- |
| H-01 | 请老师/课程负责人确认具体课程的制图覆盖规则 | `skills/drawing-standard/SKILL.md` 已由用户提供并基于国标填充为 V0.1（2026-08-11）；具体课程的纸张、图纸清单、比例、线宽、字体、标注、图框与交付偏好仍须由教师确认；teacher_override 待具体课程/老师确认 | `skills/drawing-standard/SKILL.md`、`agents/drawing-production.md`、课程任务书、`docs/TOOLS.md` | 老师给出书面/批注/样图依据；在 `teacher_override` 记录适用字段与例外；Drawing 按确认规则导出一张样图并获确认 |
| H-02 | 在 Windows 上对 Revit 2021 完成插件安装与实机测试：`C:\Program Files\Autodesk\Revit 2021\Revit.exe` | Revit 插件必须在目标版本的图形界面加载；源码、MCP 工具发现和 SSH 连通都不能证明插件真正控制 Revit | `tools/revit-mcp/SETUP.md`、`tools/revit-mcp/TEST_PLAN.md`、`tools/revit-mcp/HUMAN_ACTION_REQUIRED.md` | add-in 文件位于 `%AppData%\Autodesk\Revit\Addins\2021\`；插件面板出现、点击 Switch 后 8080 监听；`say_hello` 与 `get_current_view_info` 成功；在可丢弃测试模型执行 TEST_PLAN 的 8 项并保存前后截图/文件 |
| H-03 | 确认 Windows Revit 环境的 .NET 状态和安装路径 | Revit 2021 发布包运行目标为 .NET Framework 4.8；普通安装不应臆测需要 SDK，若改为源码构建或运行其他版本测试则依赖不同 | `tools/revit-mcp/SETUP.md` 第 2 节 | 记录“使用 2021 发布 ZIP，.NET Framework 4.8 运行时满足/不满足”的实际检查结果；只有计划源码构建或 Revit 2025/2026 测试时，再记录对应 SDK 与命令，不把 .NET 10 当作 2021 的必装项 |
| H-04 | 安装并启用 Blender addon，确认 Windows Steam Blender 4.3 的监听与 SSH 隧道 | `ahujasid/blender-mcp` addon 需 Blender GUI 启用并在本机 loopback 监听；该环节不能用无界面渲染替代 | `research/blender-upscale/blender-mcp-survey.md`、`docs/TOOLS.md` | 在 `/path/to/user-home Foundation\Blender\4.3\scripts\addons\` 检查安装结果，且在 Preferences 中启用；N 面板显示 BlenderMCP，点击 Connect 后监听 `localhost:9876`；Mac 隧道建立后完成一次 MCP 查询/截图 |
| H-05 | 在每个项目 Gate 作出真实选择：Gate A 概念、Gate B 方案、Gate C Revit 图纸、Gate D 相机/人工摆机位 | 项目架构明确用户是唯一最终设计决策者。AI 推荐不能冻结概念、方案、图纸或机位 | `docs/TEAM_ARCHITECTURE.md`、`workflows/PIPELINE_WORKFLOW.md`、各 agent 文件 | `DECISIONS.md` 记录用户原话、所选版本、Gate、日期和保留/修改项；下游 Handoff 引用该决策；未选择时项目状态明确写“等待 Gate”，不得继续下游生产 |
| H-06 | 选择超分工具档位，并对一张代表性效果图确认可接受性 | 三档工具在质量、速度、硬件和“是否允许生成式细化”上不同；当前没有已安装、已跑图的本地超分链 | `research/blender-upscale/upscaler-survey.md`、`docs/TOOLS.md` | 选择 waifu2x（保守）、chaiNNer（Mac 质量）或 ComfyUI + Ultimate（Windows 生成式细化）；保存原图、参数/模型或 workflow、输出图和 100% 对照结论；任何伪影则回退原图或基础 SR |

## 状态更新（2026-10-20）

- H-01：`drawing-standard` 已由用户资料填到 V0.1（2026-08-11）；课程特定字段与 `teacher_override` 仍待教师确认。原“受控占位”表述已从 `docs/PROJECT_DOCUMENTATION.md` 修正。
- H-02：Revit 2021 插件、8080、26 工具发现、只读端到端已在 2026-08-13 完成；2026-10-04 至 10-19 的真实课程项目已实际写入 1,771 次 `send_code_to_revit`，创建 123 个 Room、墙/门/楼梯/家具并导出 33 页 PDF，最新回读 0 非正面积、0 warnings。**但 TEST_PLAN 的 8 项逐项记录仍未按原计划留证**，因此 H-02 只能记为“实机能力已被项目实践覆盖，正式测试记录待补”，不能记为全项验收完成。
- H-04/H-06：Blender MCP 与超分链仍未实机验证/选型。
- H-05：Wuchang library 已发生 Gate A；Gate B 尚未通过；Gate C/D 未开始。

## 执行顺序建议

H-01 应在首次正式 Revit 出图前完成。H-02 与 H-03 在首次需要 MCP 建模前完成，并只在可丢弃测试模型中执行会修改模型的测试。H-04 在 Gate C 通过、需要可视化前完成。H-05 随每个真实课程项目发生，不能一次预签所有 Gate。H-06 在 Gate D 选定基础渲染后、批量出高清图之前完成。

未完成以上任一事项时，系统应记录“待人工动作”，而不是将相应工具、标准或 Gate 写作已通过。
