> 历史部署／验证资料，原日期与证据范围保留；不构成当前多Agent、模型分档或Gate的执行要求。当前入口：[工作流](../workflows/PIPELINE_WORKFLOW.md)。收录本文件不触发部署或安装。

# Multica 团队落地规划

> 状态：本地六角色资产和 9 个 Skill 已准备完毕；当前机器的 `multica` CLI 尚未配置 server，不能据此确认或写入远端工作区。本文保留可复现的同步命令，实际小队更新前须先完成连接并重新查询远端状态。
>
> 本文保留首次部署的命令级规划，供重建、审计或迁移使用。执行任何命令前必须重新查询远端状态，不得把本文中的历史计划当作当前远端事实。
>
> 探测环境：`multica v0.4.23`（2026-08-12）。所有下列 `multica` 参数均来自本机 `--help` 输出；变量（例如 `$RUNTIME_ID`）须替换为前一步 JSON 输出中记录的真实 ID。

## 结论与执行前决策

本地有效架构是 **1 个 Director + 5 个专业 Agent**，即下表六个 Agent。`docs/TEAM_ARCHITECTURE.md` 明确说旧 8 Agent / 3 Squad 已不再参与当前路由；`docs/SQUADS.md` 更标为 `ARCHIVED / DO NOT ROUTE`。这与本次“6 Agent + 9 Skills + 3 Squads”的目标冲突。

因此，本计划不会复活 `Architect`、`Critic`、`Researcher`、`Production`、`Graphic`、`QA` 或旧 Squad。若仍需 3 个 Squad，按本计划创建三个**新名称、只使用当前六个 Agent**的协作分组。执行创建 Squad 前，工作区负责人须确认这一例外；若不确认，完成 Agent 与 Skill 部署后停止，不创建任何 Squad。

首次探测时，本地 CLI 尚未配置，因而下列命令保留为重建或迁移时的安全预检。当前实际部署状态以 Multica 服务端查询结果为准。

## 当前资产与 Multica 映射

### Agent

Multica Agent 没有 `--role` 字段。下表的“角色契约”将作为 `--instructions` 的来源（完整读取对应 Markdown，含现有 frontmatter）；其 `role` 仍是团队语义，而不是 Multica 的独立字段。所有 Agent 初始设为 `private`，避免在权限未确认前向整个 workspace 公开。

| 本地资产 | Multica Agent 名称 | 角色契约 | 绑定 Skill |
| --- | --- | --- | --- |
| `agents/director.md` | `建筑设计总监` | Director；路由、Handoff、Gate A–D | 无必用 Skill |
| `agents/concept-design.md` | `概念设计 Agent` | Concept Design Agent；Gate A | `concept-design`；条件调用 `museum-design`、`kindergarten-design` |
| `agents/scheme-design.md` | `方案设计 Agent` | Scheme Design Agent；Gate B | `scheme-development`、`building-code-check`；条件调用 `museum-design`、`kindergarten-design` |
| `agents/drawing-production.md` | `图纸生产 Agent` | Drawing Production Agent；Gate C | `revit-expert`、`drawing-standard`、`revit-final-check` |
| `agents/visualization.md` | `可视化 Agent` | Visualization Agent；Gate D | `render-fidelity` |
| `agents/presentation.md` | `汇报表达 Agent` | Presentation Agent；只组织有效设计证据 | 无必用 Skill |

类型专项 Skill 同时分配给 Concept 与 Scheme 是有意设计：两个 Skill 的自身说明都限定为这两个角色使用，且不新增审批 Gate。Skill 是 workspace 共享对象；一个 Skill 只创建一次，再用 ID 分配给多个 Agent。

### Skill

| 本地路径 | Multica Skill 名称 | 附加文件 |
| --- | --- | --- |
| `skills/concept-design/SKILL.md` | `concept-design` | 无 |
| `skills/scheme-development/SKILL.md` | `scheme-development` | 无 |
| `skills/building-code-check/SKILL.md` | `building-code-check` | 无 |
| `skills/revit-final-check/SKILL.md` | `revit-final-check` | 无 |
| `skills/render-fidelity/SKILL.md` | `render-fidelity` | 无 |
| `skills/drawing-standard/SKILL.md` | `drawing-standard` | 无 |
| `skills/revit-expert/SKILL.md` | `revit-expert` | `references/advanced-workflows.md`、`bim-competition-fastwork.md`、`fbx-export-render.md`、`revit-mcp-patterns.md`、`revit-mcp-revit2021-validated.md` |
| `skills/museum-design/SKILL.md` | `museum-design` | 无 |
| `skills/kindergarten-design/SKILL.md` | `kindergarten-design` | 无 |

`multica skill import` 的真实接口只接受 `--file <.skill|.zip>` 或 `--url`；它**不接受本地目录**。帮助页未说明压缩包内部目录格式，故不要假定把现有目录直接 zip 后必然可导入。推荐使用本计划的 `skill create --content-file` + `skill files upsert` 路径：它对现有文件逐个读取，且不需要猜测 archive 格式。若团队另有已验证的 `.skill` / `.zip` 打包规范，可改用文末的 archive 命令。

### 新 Squad（待负责人确认）

| 新 Multica Squad | leader | 成员 | 目的 |
| --- | --- | --- | --- |
| `Concept & Scheme` | `方案设计 Agent` | `概念设计 Agent` | Gate A 后的概念—方案连续深化；不替用户批准 Gate。 |
| `Drawing & Visualization` | `图纸生产 Agent` | `可视化 Agent` | Gate B 后的模型、图纸、确认几何与忠实渲染链。 |
| `Direction & Presentation` | `建筑设计总监` | `汇报表达 Agent` | 版本、Handoff、Gate 与当前有效证据的叙事组织。 |

上述是新的六角色适配，不是 `docs/SQUADS.md` 中的历史 `Research & Presentation`、`Design Studio`、`Production Studio` 的迁移。Squad 仅用于两个以上专业角色需要汇总成果的 Issue；单一责任 Agent 的 Issue 仍直接路由，且每个 Issue 只有一个主责任人。

## 落地步骤与命令

以下命令是**未来实际落地时**按顺序执行的清单。本文件本身没有执行它们。

### 1. 建立连接、完成认证、选择工作区和 runtime

**需要用户交互。** `multica setup cloud` 会进行 Cloud OAuth；自托管则必须由负责人提供 API 与 Web 地址。setup 的帮助说明它会配置 CLI、认证并启动 daemon。不得把 PAT 直接写入 shell history；如改用登录命令，应使用 `multica login --token` 让 CLI 交互提示 token。

```bash
# 先确认当前状态（只读）
multica config show
multica auth status
multica daemon status

# 二选一：Cloud（浏览器 OAuth）
multica setup cloud

# 二选一：自托管。URL 由工作区负责人提供。
multica setup self-host --server-url "https://<api-host>" --app-url "https://<app-host>"

# 认证完成后再次确认（只读）
multica auth status
multica daemon status
multica workspace list --output json
```

若 list 中已有目标工作区，选择其 slug 或 UUID 并切换；`workspace switch` 会改变当前 profile 的默认工作区，属于写操作。

```bash
multica workspace switch "<existing-workspace-slug-or-id>"
multica workspace get --output json
```

若确认不存在目标工作区，才创建。名称、slug、Issue 前缀必须由负责人确认；slug 一经创建不能改变。示例的 `multica-architecture` 是建议值，不是已保留资源。

```bash
multica workspace create \
  --name "Multica Architecture Studio" \
  --slug "multica-architecture" \
  --issue-prefix "MAS" \
  --description "Six-role architecture design team with human Gate A-D decisions." \
  --output json
multica workspace switch "multica-architecture"
multica workspace get --output json
```

最后列出已注册 runtime，记录将承载六个 Agent 的 `$RUNTIME_ID`。`agent create` 要求此 ID；CLI 本身没有 runtime create 子命令，不能凭空填写。

```bash
multica runtime list --output json
```

若 setup 后 daemon 仍是 stopped，负责人可启动它；否则不必重复启动。

```bash
multica daemon start
multica daemon status
```

### 2. 预检远端资源并建立 ID 台账

此步骤是幂等的关键。以 JSON 保存或人工记录每个同名资源的 ID；不根据名称猜测 ID。`--include-archived` 用于识别已经归档的旧 Agent。

```bash
multica agent list --include-archived --output json
multica skill list --output json
multica squad list --output json
```

只有名称不存在时才执行本节后续的 create。名称已存在时，先 `get` 核验它确实是本计划资源，再转入相应 update/set 命令；绝不对名称相似的历史资源覆盖。

```bash
multica agent get "$AGENT_ID" --output json
multica skill get "$SKILL_ID" --output json
multica squad get "$SQUAD_ID" --output json
```

### 3. 创建或更新九个 Skill

下列 `create` 使用 CLI 已确认的 `--content-file`；每次命令的 JSON 输出都要记录为对应 `$*_SKILL_ID`。现有 `SKILL.md` 的 frontmatter 是否会被服务端作为 metadata 解析，帮助页没有承诺；名称和 description 因而显式由 flags 给出，文件内容仍原样传入以保留角色指令。

```bash
multica skill create --name "concept-design" --description "用于建筑项目从任务书、场地与使用需求出发，形成多个明显不同、可比较且可继续深化的概念方向。" --content-file "skills/concept-design/SKILL.md" --output json
multica skill create --name "scheme-development" --description "用于用户已经选定建筑概念后，将其深化为经过案例、平剖体量与规范风险验证且可进入 Revit 的方案。" --content-file "skills/scheme-development/SKILL.md" --output json
multica skill create --name "building-code-check" --description "Scheme Design Agent 在 Gate B 前进行中国建筑规范风险自查。" --content-file "skills/building-code-check/SKILL.md" --output json
multica skill create --name "revit-final-check" --description "Drawing Production Agent 在 Gate C 前核查 Revit 模型、视图、图纸、标注与版本。" --content-file "skills/revit-final-check/SKILL.md" --output json
multica skill create --name "render-fidelity" --description "Visualization Agent 在图像生成时保持 Gate C 与 Gate D 已确认建筑设计。" --content-file "skills/render-fidelity/SKILL.md" --output json
multica skill create --name "drawing-standard" --description "建筑学课程设计制图标准与审查规则。" --content-file "skills/drawing-standard/SKILL.md" --output json
multica skill create --name "revit-expert" --description "Drawing Production Agent 将已批准方案转为可维护、可出图、可核查的 Revit/BIM 模型。" --content-file "skills/revit-expert/SKILL.md" --output json
multica skill create --name "museum-design" --description "Concept 或 Scheme 阶段的高校及文化类博物馆类型专项检查。" --content-file "skills/museum-design/SKILL.md" --output json
multica skill create --name "kindergarten-design" --description "Concept 或 Scheme 阶段的幼儿园类型专项检查。" --content-file "skills/kindergarten-design/SKILL.md" --output json
```

`revit-expert` 有四个引用文件，创建后必须逐个上传；不上传会破坏其中的相对引用。

```bash
multica skill files upsert "$REVIT_EXPERT_SKILL_ID" --path "references/advanced-workflows.md" --content-file "skills/revit-expert/references/advanced-workflows.md" --output json
multica skill files upsert "$REVIT_EXPERT_SKILL_ID" --path "references/bim-competition-fastwork.md" --content-file "skills/revit-expert/references/bim-competition-fastwork.md" --output json
multica skill files upsert "$REVIT_EXPERT_SKILL_ID" --path "references/fbx-export-render.md" --content-file "skills/revit-expert/references/fbx-export-render.md" --output json
multica skill files upsert "$REVIT_EXPERT_SKILL_ID" --path "references/revit-mcp-patterns.md" --content-file "skills/revit-expert/references/revit-mcp-patterns.md" --output json
multica skill files upsert "$REVIT_EXPERT_SKILL_ID" --path "references/revit-mcp-revit2021-validated.md" --content-file "skills/revit-expert/references/revit-mcp-revit2021-validated.md" --output json
multica skill get "$REVIT_EXPERT_SKILL_ID" --output json
```

对已存在且核验为同一资源的 Skill，使用 update 而不是 create；引用文件仍可安全用 upsert 覆盖为本地版本。

```bash
multica skill update "$SKILL_ID" --description "<verified-description>" --content-file "skills/<skill-name>/SKILL.md" --output json
multica skill files list "$REVIT_EXPERT_SKILL_ID" --output json
```

archive 导入仅作为已验证打包规范时的替代方案。`--on-conflict` 是 CLI 帮助明确支持的冲突策略；推荐 `fail`，避免无意覆盖。

```bash
multica skill import --file "<verified-local-archive>.skill" --on-conflict fail --output json
# 或
multica skill import --file "<verified-local-archive>.zip" --on-conflict fail --output json
```

### 4. 创建或更新六个 Agent，并分配 Skill

**需要负责人选择 `$RUNTIME_ID`。** 本计划不强行指定 model、thinking level、service tier、MCP config 或 custom env，因为 CLI 可接受它们但本地资产没有授权这些运行时决策。命令中的 `sed` 在未来执行时只读取本地角色文件并将其作为 `--instructions` 值；并非 Multica 子命令。

```bash
multica agent create --name "建筑设计总监" --description "以轻量路由、交接和人工决策 Gate 管理极简建筑 AI 团队。" --instructions "$(sed -n '1,$p' agents/director.md)" --runtime-id "$RUNTIME_ID" --max-concurrent-tasks 6 --permission-mode private --output json
multica agent create --name "概念设计 Agent" --description "将任务书、场地与类型学证据转化为多个可选择的概念方向，并严格守住 Gate A。" --instructions "$(sed -n '1,$p' agents/concept-design.md)" --runtime-id "$RUNTIME_ID" --max-concurrent-tasks 6 --permission-mode private --output json
multica agent create --name "方案设计 Agent" --description "将用户在 Gate A 选定的概念深化为可实施、可审查、可进入 Revit 的方案确认包，并守住 Gate B。" --instructions "$(sed -n '1,$p' agents/scheme-design.md)" --runtime-id "$RUNTIME_ID" --max-concurrent-tasks 6 --permission-mode private --output json
multica agent create --name "图纸生产 Agent" --description "以 Revit 专家方式将已批准方案建模出图、管理版本并执行 Gate C 图纸检查。" --instructions "$(sed -n '1,$p' agents/drawing-production.md)" --runtime-id "$RUNTIME_ID" --max-concurrent-tasks 6 --permission-mode private --output json
multica agent create --name "可视化 Agent" --description "在忠实保持建筑几何的前提下执行 Revit 至高清效果图的可视化链，并守住 Gate D 摄像机检查。" --instructions "$(sed -n '1,$p' agents/visualization.md)" --runtime-id "$RUNTIME_ID" --max-concurrent-tasks 6 --permission-mode private --output json
multica agent create --name "汇报表达 Agent" --description "负责未来的建筑分析图、概念图、轴测表达与版面组织，并保持对已批准设计事实的忠实。" --instructions "$(sed -n '1,$p' agents/presentation.md)" --runtime-id "$RUNTIME_ID" --max-concurrent-tasks 6 --permission-mode private --output json
```

如果 Agent 已存在且已通过第 2 步核验，用 update 同步其契约。以下模板中的 `$AGENT_ID`、文件和文字替换为上表同一行的值；`agent update` 的帮助页确认支持每一个参数。

```bash
multica agent update "$AGENT_ID" --name "<verified-agent-name>" --description "<verified-description>" --instructions "$(sed -n '1,$p' agents/<agent-file>.md)" --runtime-id "$RUNTIME_ID" --max-concurrent-tasks 6 --permission-mode private --output json
```

在记录完所有 Agent 与 Skill ID 后，使用 `set` 而非 `add`。`set` 会替换该 Agent 的全部 Skill 分配，故重复运行能收敛到本计划的准确集合；对无必用 Skill 的 Director 和 Presentation 不运行 `set`，以免无授权地清除将来人为分配的可选 Skill。

```bash
multica agent skills set "$CONCEPT_AGENT_ID" --skill-ids "$CONCEPT_DESIGN_SKILL_ID,$MUSEUM_DESIGN_SKILL_ID,$KINDERGARTEN_DESIGN_SKILL_ID" --output json
multica agent skills set "$SCHEME_AGENT_ID" --skill-ids "$SCHEME_DEVELOPMENT_SKILL_ID,$BUILDING_CODE_CHECK_SKILL_ID,$MUSEUM_DESIGN_SKILL_ID,$KINDERGARTEN_DESIGN_SKILL_ID" --output json
multica agent skills set "$DRAWING_AGENT_ID" --skill-ids "$REVIT_EXPERT_SKILL_ID,$DRAWING_STANDARD_SKILL_ID,$REVIT_FINAL_CHECK_SKILL_ID" --output json
multica agent skills set "$VISUALIZATION_AGENT_ID" --skill-ids "$RENDER_FIDELITY_SKILL_ID" --output json
multica agent skills list "$CONCEPT_AGENT_ID" --output json
multica agent skills list "$SCHEME_AGENT_ID" --output json
multica agent skills list "$DRAWING_AGENT_ID" --output json
multica agent skills list "$VISUALIZATION_AGENT_ID" --output json
```

### 5. 仅在已确认例外后创建三个新 Squad

`squad create` 只支持 name、leader、description；需额外写入 leader 工作约束时，随后用 `squad update --instructions`。创建后先 list members，确认 leader 已被表现为成员，再仅添加表中另一个 Agent；不臆测 create 是否会把 leader 以普通成员重复加入。

```bash
multica squad create --name "Concept & Scheme" --leader "$SCHEME_AGENT_ID" --description "Gate A 后的概念与方案连续深化；用户保留 Gate A 和 Gate B 决策。" --output json
multica squad create --name "Drawing & Visualization" --leader "$DRAWING_AGENT_ID" --description "Gate B 后的模型、图纸、确认几何与忠实可视化链；不改变已批准建筑。" --output json
multica squad create --name "Direction & Presentation" --leader "$DIRECTOR_AGENT_ID" --description "版本、Handoff、Gate 与当前有效设计证据的组织；不替用户作设计选择。" --output json
```

记录 `$CONCEPT_SCHEME_SQUAD_ID`、`$DRAWING_VISUALIZATION_SQUAD_ID`、`$DIRECTION_PRESENTATION_SQUAD_ID` 后，添加非 leader 成员并验证。

```bash
multica squad member list "$CONCEPT_SCHEME_SQUAD_ID" --output json
multica squad member add "$CONCEPT_SCHEME_SQUAD_ID" --member-id "$CONCEPT_AGENT_ID" --role member --type agent --output json
multica squad member list "$DRAWING_VISUALIZATION_SQUAD_ID" --output json
multica squad member add "$DRAWING_VISUALIZATION_SQUAD_ID" --member-id "$VISUALIZATION_AGENT_ID" --role member --type agent --output json
multica squad member list "$DIRECTION_PRESENTATION_SQUAD_ID" --output json
multica squad member add "$DIRECTION_PRESENTATION_SQUAD_ID" --member-id "$PRESENTATION_AGENT_ID" --role member --type agent --output json
```

可选地把关键边界写入 Squad instructions；这是当前 CLI 可用的 update 参数，仍不改变 Agent 自身契约。

```bash
multica squad update "$CONCEPT_SCHEME_SQUAD_ID" --instructions "仅协调概念与方案交接；不替用户通过 Gate A 或 Gate B。" --output json
multica squad update "$DRAWING_VISUALIZATION_SQUAD_ID" --instructions "仅在 Gate B 后协调建模、图纸与忠实可视化；不修改已批准建筑。" --output json
multica squad update "$DIRECTION_PRESENTATION_SQUAD_ID" --instructions "维护版本、Handoff、Gate 与汇报证据；不替用户作设计选择。" --output json
multica squad get "$CONCEPT_SCHEME_SQUAD_ID" --output json
multica squad get "$DRAWING_VISUALIZATION_SQUAD_ID" --output json
multica squad get "$DIRECTION_PRESENTATION_SQUAD_ID" --output json
```

### 6. 旧 prompts、旧 Agent 与历史 Squad 的处置

本地 `prompts/` 下的 8 份历史指令已经是方法论归档；保留在仓库，不导入 Multica，不移动、不删除。`docs/SQUADS.md` 同样保留为归档，不将其旧成员表转为新 Squad。

因当前未连服务器，不能断言远端是否已有历史 Agent/Squad。只有在第 2 步确认为旧角色且负责人明确授权后，才可归档远端对象；archive 是可恢复操作，ID 必须来自 list/get。

```bash
multica agent archive "$OLD_AGENT_ID" --output json
multica squad delete "$OLD_SQUAD_ID" --output json

# 回滚时恢复 Agent；Squad delete 的帮助页只说明 archive，恢复接口未在 squad 命令中暴露。
multica agent restore "$OLD_AGENT_ID" --output json
```

## 幂等、验证与回滚

| 对象 | 重复执行策略 | 回滚 / 恢复 |
| --- | --- | --- |
| CLI/认证/workspace | 每次先 `config show`、`auth status`、`workspace list`；不重复 setup 或 create。 | 切回原 workspace：`multica workspace switch <slug-or-id>`。本计划不提供 logout，因为那会影响当前用户的全部 CLI 会话。 |
| Skill | 同名先 `skill get`；存在则 `skill update` 与 `files upsert`，不存在才 create。archive import 采用 `--on-conflict fail`，不使用 overwrite。 | `skill delete` 存在但本计划未探测其参数，故执行前先查 `multica skill delete --help`；删除前导出/保留本地源。 |
| Agent | 同名先 get；存在则 update，缺失才 create。Skill 用 `agent skills set` 让四个必用集合收敛。 | 用 update 还原 instructions/description/runtime/权限；若是本次新建且确认无任务，再先查 delete 能力（本机 agent 命令未列 delete），通常 archive：`multica agent archive <id>`，需要时 `restore`。 |
| Squad | 同名先 get；存在则 update 并检查 member list，缺失才 create。成员添加前先 list，避免重复添加。 | 移除误加成员：`multica squad member remove <squad-id> --member-id <agent-id> --type agent`；归档误建 Squad：`multica squad delete <squad-id>`。当前帮助未暴露 Squad restore，故归档前必须确认。 |

每个写操作后至少执行相应 `get`、`list` 或 `member list`，核对 ID、名称、成员、契约、引用文件及 Skill 分配。发生认证、runtime 或服务端校验失败时停止在失败步骤：不以重跑整套 create 命令作为恢复方式，先查询当前状态，再只重试未完成的单项。

## 实测 CLI 摘要

已只读执行 `--help` 和状态/list/config 查询，未执行写操作。关键真实命令如下：

- `multica setup cloud` / `multica setup self-host`：配置、登录并启动 daemon；`multica login --token` 可交互读取 PAT。
- `multica workspace create --name --slug`、`workspace switch <workspace-id|slug|prefix>`；workspace create 的 slug 永久不可改。
- `multica runtime list --output json`：获取 Agent create 所需的 `--runtime-id`。
- `multica agent create --name --runtime-id --instructions`，`agent update <id>`，`agent skills set <agent-id> --skill-ids`。
- `multica skill create --name --content-file`，`skill files upsert <skill-id> --path --content-file`；archive 导入使用 `skill import --file <.skill|.zip> --on-conflict`。
- `multica squad create --name --leader`，`squad member add <squad-id> --member-id --role --type agent`，`squad update <squad-id> --instructions`。
