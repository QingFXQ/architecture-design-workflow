# Revit MCP 26 Tools：真实任务模式与可复用 C# 片段
> 参考环境：本仓库 `tools/revit-mcp/SETUP.md` 记录的 Mac → SSH stdio → Windows → Revit 2021 链路；本机执行时使用配置好的本机 MCP，重新核验当前能力。
> 核心原则：优先专用 tool；只有专用 tool 无法完成且规则明确、可验证、可回滚时，才用 `send_code_to_revit`。
> 重要边界：所有 Revit 写操作串行执行；`operate_element` 不支持 Move；不存在已注册的通用 `modify_element` 或 `create_view` tool。
## 目录
- 1. 连接、事务与单位合同
- 2. 26 tools 按任务场景组织
- 3. 真实任务编排
- 4. `send_code_to_revit` 安全合同
- 5. 可直接改用的 C# 代码模式
- 6. MCP 结果验收
- 7. 来源
## 1. 连接、事务与单位合同
### 1.1 调用前检查
1. 核当前Revit、插件配置、活动项目与实际服务状态；历史Revit 2021链路使用MCP Switch，不把特定端口、必须人工点击或重启方法泛化到所有版本。只读工作不要求目标可写。
2. 首次用当前视图／文档和必要统计建立基线；同版连续任务复用，后续只查相关范围，不每次全模型盘点。历史配置的连接检查见 [`smoke_revit_mcp.py`](../../../tools/revit-mcp/scripts/smoke_revit_mcp.py)。
3. `say_hello` 可作为人工可见的补充冒烟，不是写操作前的必要条件，也不替代两项只读前检。
4. 创建前调用 `get_available_family_types`，不硬编码别的项目的 ElementId。
5. 写操作逐个调用、不并行；保存 tool 输入、完整返回、ElementId、warnings 和截图。
MCP server 对单个 Revit 命令的内部超时约 120 秒；OpenClaw 设置采用 130 秒 request timeout，并关闭并行 tool calls。详见仓库 [`SETUP.md`](../../../tools/revit-mcp/SETUP.md)。
### 1.2 单位
- 专用创建 tools 的坐标、长度、厚度、高度和标高使用毫米；Revit API 内部长度使用英尺。
- `send_code_to_revit` 中把毫米除以 `304.8` 转为英尺。
- 代码片段统一提供 `Mm()` 辅助函数或显式 `/ 304.8`。
- 正式 Drawing 输入点来自已批准定位；Scheme 验证可用明确记录来源与单位的候选坐标。截图不能替代精确定位，面积、体积和角度按各自 API 单位处理。
### 1.3 事务模式
- `transactionMode: "auto"`：MCP 包装器负责一个事务；代码内不要再 `new Transaction(...)`。
- `transactionMode: "none"`：包装器不开事务，用于只读/导出；需要提交后读取或事务组试算时，可在代码内显式创建事务，必须安装失败处理并核对 Commit/RollBack 状态，不能留下未完成事务。
- 一次代码只承担一个可回滚目的。
- 不在一个动态代码中混合建模、删除、导出和数据库写入。
- 返回 success 后仍要用独立查询工具复核。
### 1.4 试算、恢复与跨层回查

- 试算也安装失败处理，出现警告应可撤回并清理；在事务组中提交后读取面积，再按试验目的回滚，不能用提交前的零面积断言设计失败。
- 超时先检查 Revit 模态、连接和事务，不连续重试写入。有限恢复仍失败时请求一次明确人工动作，恢复后核对残留、原构件、房间、warnings 和保存状态。
- 按实际竖向范围或实体筛选跨层墙柱、楼梯；所属 Level 不等于全部服务楼层。整体变换记录基点、方向、单位及包含/排除对象，并触发场地与关联模块复查。
- 明确二维布置、三维占位与原生 BIM 的区别；删除视图元素前识别家具图线、尺寸和标签依赖，优先更新已有对象。
- 执行[共同检查约定](../../../workflows/SCHEME_DRAWING_REVIEW.md)并分别记录软件、几何、建筑与视觉证据。

## 2. 26 tools 按任务场景组织
### 2.1 连接与活动上下文
| Tool | 真实用途 | 关键边界 |
| --- | --- | --- |
| `say_hello` | 端到端连接冒烟 | 不证明当前项目可写 |
| `get_current_view_info` | 读取活动视图名、类型、Id | 不证明视图内容正确 |
| `get_current_view_elements` | 读取当前视图模型/注释元素 | 受视图可见性和范围影响 |
| `get_selected_elements` | 读取人工选择，建立人机共同范围 | 选择可能为空或过时 |
### 2.2 模型查询与 QA
| Tool | 真实用途 | 关键边界 |
| --- | --- | --- |
| `ai_element_filter` | 按类别、类型、可见性、空间范围查元素 | 写操作前后使用同一条件对比 |
| `analyze_model_statistics` | 元素、类型、族、视图、图纸、类别、标高统计 | 是统计快照，不替代平剖视觉检查 |
| `get_available_family_types` | 获取项目实际类型 Id | 创建墙、板、门窗前必查 |
| `export_room_data` | 导出房间名、号、面积等 | 结果依赖封闭边界和正确 Phase |
| `get_material_quantities` | 读取材料面积、体积、数量 | 结果依赖正确构件和材料分配 |
### 2.3 基准与系统创建
| Tool | 真实用途 | 推荐顺序 |
| --- | --- | --- |
| `create_level` | 建标高，可同时建 Floor/Ceiling Plan | 先标高表，后主体 |
| `create_grid` | 建规则轴网 | 先少量核对命名/方向 |
| `create_line_based_element` | 建墙、梁、风管等线性对象 | 查类型 → 小样 → 批量 |
| `create_surface_based_element` | 建楼板、天花、屋面 | 闭合/共面边界先验证 |
| `create_structural_framing_system` | 建梁框架系统 | 只在结构任务明确时用 |
### 2.4 点式对象、房间与标注
| Tool | 真实用途 | 推荐顺序 |
| --- | --- | --- |
| `create_point_based_element` | 建门、窗、家具等点式对象 | 真实 typeId + hostWallId |
| `create_room` | 在封闭边界放 Room 并写名称编号 | 先墙闭合，再放房间点 |
| `create_dimensions` | 在 2D 视图建线性尺寸 | 先确认可提取 Reference |
| `tag_all_rooms` | 标注当前视图全部/指定房间 | 先核对 Room 数据和标签类型 |
| `tag_all_walls` | 标注当前视图墙 | 只在图纸规则需要时使用 |
| `color_elements` | 按类别/参数在当前视图着色 | 用于 QA/分析，不修模型 |
### 2.5 视图操作、删除与动态 API
| Tool | 真实用途 | 高风险点 |
| --- | --- | --- |
| `operate_element` | 选择、Section Box、着色、透明、隐藏、隔离、删除 | 不支持 Move；隐藏不是修复 |
| `delete_element` | 按 ElementId 删除 | 先查依赖、范围和备份 |
| `send_code_to_revit` | 动态编译执行 C# | 小样本、明确事务、独立回查 |
### 2.6 MCP server 本地 SQLite
| Tool | 真实用途 | 关键边界 |
| --- | --- | --- |
| `store_project_data` | 存项目元数据到 server 本地 SQLite | 不改变 Revit 模型 |
| `store_room_data` | 存房间元数据到本地 SQLite | 不替代 Revit Room |
| `query_stored_data` | 查已存项目/房间元数据 | 不是当前模型实时真相 |
### 2.7 26-tool 完整性
以上共 26 个已注册 tools：
```text
ai_element_filter, analyze_model_statistics, color_elements,
create_dimensions, create_grid, create_level, create_line_based_element,
create_point_based_element, create_room, create_structural_framing_system,
create_surface_based_element, delete_element, export_room_data,
get_available_family_types, get_current_view_elements,
get_current_view_info, get_material_quantities, get_selected_elements,
operate_element, query_stored_data, say_hello, send_code_to_revit,
store_project_data, store_room_data, tag_all_rooms, tag_all_walls
```
不要调用：
- `modify_element`：空文件，没有注册。
- `create_view`：不存在通用 tool。
- `search_modules`、`use_module`：空文件，没有注册。
- `operate_element(action=Move)`：实际 action 不支持。
## 3. 真实任务编排
### 3.1 新建一间房：墙 + 门 + 窗 + Room
推荐专用 tools 编排：
1. `get_current_view_info`：确认活动 FloorPlan 和标高。
2. `get_available_family_types`：查 `OST_Walls`、`OST_Doors`、`OST_Windows`。
3. `create_line_based_element`：四面闭合墙，保存四个墙 Id。
4. `get_current_view_elements`：按 `OST_Walls` 回查闭合范围。
5. `create_point_based_element`：门窗使用真实宿主墙 Id。
6. `create_room`：先查当前位置是否已有同阶段Room、再核闭合区域和单位，避免重复创建。
7. `export_room_data`：按 Room Number 回查面积大于 0。
8. `tag_all_rooms`：需要图纸标签时再标。
9. 平面 + 剖面 + 3D 人工视觉核对。
何时改用代码模式 1：
- 需要一个事务原子创建一组测试房间。
- 专用 tools 无法表达必要的 API 属性。
- 已在可丢弃项目验证 FamilySymbol、Level 和 WallType。
### 3.2 批量移动
1. `get_selected_elements` 或 `ai_element_filter` 明确目标 Id。
2. 保存移动前几何/边界快照。
3. 用代码模式 2，参数传 Id 列表和 XYZ 毫米位移。
4. `ai_element_filter` 用同一范围回查。
5. 检查宿主、标注、约束、组和链接未被误伤。
`operate_element` 不能移动，因此不得试造 `Move` action；仓库 `TEST_PLAN.md` 的移动测试也使用 `send_code_to_revit`。
### 3.3 批量写参数
1. `ai_element_filter` 确定类别、类型和空间范围。
2. 用 Schedule/查询保存旧值与目标计数。
3. 优先使用 BuiltInParameter 或共享参数 GUID，避免重名 `LookupParameter`。
4. 代码模式 3 先处理 3—10 个样本。
5. 回查只读、空值、失败和成功计数。
6. Tag/Schedule/Filter 联合验证。
### 3.4 建标高与基本平面
优先：
1. `create_level` 传入名称、高程、`createFloorPlan`、`createCeilingPlan`。
2. 人工激活新视图。
3. `get_current_view_info` 回查视图名和类型。
复杂情况用代码模式 4：
- 为既有标高批量补 FloorPlan。
- 按 ViewFamilyType 精确选择平面类型。
- 需要避免重名和重复视图。
### 3.5 批量建 Sheet 并放视图
没有专用 Sheet tool：
1. `analyze_model_statistics` 先记录已有视图/图纸数。
2. `get_available_family_types` 或动态 API 查 TitleBlock type。
3. 用代码模式 5 小样创建 Sheet/Viewport。
4. 再次 `analyze_model_statistics` 检查新增图纸数。
5. 人工检查视口位置、标题、比例和裁切。
### 3.6 导出 FBX
没有专用 FBX tool：
1. 建立并激活专用 3D 导出视图。
2. `get_current_view_info` 记录 View Id/Name。
3. `get_current_view_elements` 抽查范围。
4. 用代码模式 6，`transactionMode: "none"`。
5. 检查文件存在、大小非零。
6. 在 Blender 量测已知尺寸并检查轴向/材质。
### 3.7 模型盘点与 QA
只读快速链：
1. `analyze_model_statistics(includeDetailedTypes=true)`。
2. `export_room_data` 查零面积、空号、空名。
3. `ai_element_filter` 查目标类别和异常范围。
4. `get_material_quantities` 查材料数据。
5. `color_elements` 在 QA 视图突出异常。
6. `get_current_view_elements` 读当前 QA 视图元素。
7. 视觉检查后再决定是否写模型。
### 3.8 删除
1. `get_selected_elements` 或 `ai_element_filter` 解析精确 Id。
2. 记录类别、宿主、Level、Group、依赖和视图位置。
3. 保存可回退模型版本。
4. 单个/少量用 `delete_element`。
5. 大批量不直接循环删除；先返回依赖预览和计数。
6. 删除后回查同一 Id、统计、平剖和 warnings。
## 4. `send_code_to_revit` 安全合同
### 4.1 输入合同
调用前写明：
- 目标 Revit 版本。
- `transactionMode`。
- `parameters` 每项类型和单位。
- 目标 ElementId 或过滤规则。
- 预期创建/修改/导出计数。
- 明确不应改变的类别、楼层和区域。
- 回滚方式。
- 独立验收 tool。
### 4.2 代码合同
- 使用包装器变量 `document` 和 `parameters`。
- `auto` 模式不创建内部 Transaction。
- 代码中显式校验 Element、Type、View、Level 非空。
- 先 `WhereElementIsNotElementType()` 或明确查 Type。
- 使用 `ElementId` 而不是 UI 名称作为最终操作目标。
- 类型切换前检查类别兼容。
- 返回成功、跳过、失败的计数和 Id。
- 不吞异常；让调用返回明确错误。
- 不执行网络、进程、注册表或无关文件操作。
### 4.3 验收合同
- `success: true` 只表示代码完成。
- 创建后用元素查询和统计确认类别、数量、位置。
- 修改后用同一 Id 回查新值/几何。
- 导出后检查文件并在目标软件打开。
- 高风险操作还要人工平面、剖面、3D 视觉确认。
- 所有结果写入变更记录。
## 5. 可直接改用的 C# 代码模式

**状态纠正（2026-10-28）：** 以下旧片段是特定封装下的算法参考，不是已配好幂等、失败处理及目标守卫的生产模板。当前宿主先核语法／API、事务归属、稳定目标与失败处理；事务／警告的修订以[API现场笔记](../../revit-model-hardening/references/revit-api-field-notes.md)为准。模式1仅在隔离测试项目使用，不在已有工程重复造房。API可以创建原生构件，不与原生建模优先级冲突。
> 片段均写给 `send_code_to_revit` 的代码体，不包含 `using`、类或方法外壳。
> `auto` 模式下不要再创建事务；正式项目先在可丢弃模型或 3—10 个样本验证。
### 模式 1：一个事务创建墙 + 门 + 窗 + 房间
**调用：** `transactionMode: "auto"`
**parameters：** `wallTypeId, doorTypeId, windowTypeId, levelId`（均为字符串 ElementId）。
```csharp
double Mm(double value) => value / 304.8;
var wallType = document.GetElement(new ElementId(int.Parse((string)parameters[0]))) as WallType;
var doorType = document.GetElement(new ElementId(int.Parse((string)parameters[1]))) as FamilySymbol;
var windowType = document.GetElement(new ElementId(int.Parse((string)parameters[2]))) as FamilySymbol;
var level = document.GetElement(new ElementId(int.Parse((string)parameters[3]))) as Level;
if (wallType == null || doorType == null || windowType == null || level == null)
    throw new InvalidOperationException("WallType, DoorType, WindowType or Level is invalid.");
var points = new[] {
    new XYZ(Mm(0), Mm(0), 0), new XYZ(Mm(6000), Mm(0), 0),
    new XYZ(Mm(6000), Mm(4000), 0), new XYZ(Mm(0), Mm(4000), 0)
};
var walls = new List<Wall>();
for (int i = 0; i < 4; i++) {
    var curve = Line.CreateBound(points[i], points[(i + 1) % 4]);
    walls.Add(Wall.Create(document, curve, wallType.Id, level.Id, Mm(3000), 0, false, false));
}
if (!doorType.IsActive) doorType.Activate();
if (!windowType.IsActive) windowType.Activate();
document.Regenerate();
var door = document.Create.NewFamilyInstance(
    new XYZ(Mm(3000), Mm(0), 0), doorType, walls[0], level,
    Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
var window = document.Create.NewFamilyInstance(
    new XYZ(Mm(6000), Mm(2000), Mm(900)), windowType, walls[1], level,
    Autodesk.Revit.DB.Structure.StructuralType.NonStructural);
document.Regenerate();
var room = document.Create.NewRoom(level, new UV(Mm(3000), Mm(2000)));
room.Number = "MCP-101";
room.Name = "MCP Test Room";
return new { wallIds = walls.Select(x => x.Id.IntegerValue).ToArray(),
    doorId = door.Id.IntegerValue, windowId = window.Id.IntegerValue,
    roomId = room.Id.IntegerValue };
```
验证：`get_current_view_elements(OST_Walls/OST_Doors/OST_Windows)` + `export_room_data` + Revit 平面。
不适用：生产项目中已有专用 tools 足以安全逐项创建时；专用 tools 更易记录每一步。
### 模式 2：按 Id 批量移动
**调用：** `transactionMode: "auto"`
**parameters：** `"123,456,789", dxMm, dyMm, dzMm`。
```csharp
double Mm(string value) => double.Parse(value, System.Globalization.CultureInfo.InvariantCulture) / 304.8;
var ids = ((string)parameters[0]).Split(',')
    .Where(x => !string.IsNullOrWhiteSpace(x))
    .Select(x => new ElementId(int.Parse(x.Trim()))).ToList();
var delta = new XYZ(Mm((string)parameters[1]), Mm((string)parameters[2]), Mm((string)parameters[3]));
var moved = new List<int>();
foreach (var id in ids) {
    var element = document.GetElement(id);
    if (element == null || element.Pinned) continue;
    ElementTransformUtils.MoveElement(document, id, delta);
    moved.Add(id.IntegerValue);
}
return new { requested = ids.Count, moved = moved.Count, ids = moved };
```
风险：组成员、宿主构件、约束元素和监控元素可能无法独立移动；先小样本。
### 模式 3：按 BuiltInParameter 批量写实例 Comments
**调用：** `transactionMode: "auto"`
**parameters：** `"123,456,789", "QA_Checked"`。
```csharp
var ids = ((string)parameters[0]).Split(',')
    .Where(x => !string.IsNullOrWhiteSpace(x))
    .Select(x => new ElementId(int.Parse(x.Trim()))).ToList();
var value = (string)parameters[1];
var updated = new List<int>();
var skipped = new List<int>();
foreach (var id in ids) {
    var element = document.GetElement(id);
    var parameter = element?.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS);
    if (parameter == null || parameter.IsReadOnly || parameter.StorageType != StorageType.String) {
        skipped.Add(id.IntegerValue); continue;
    }
    parameter.Set(value);
    updated.Add(id.IntegerValue);
}
return new { updated, skipped };
```
优点：BuiltInParameter 避免 `LookupParameter("Comments")` 的语言和同名风险。
不适用：需要共享参数 GUID 或类型参数时；应显式按 GUID/Type 取参数。
### 模式 4：为既有标高补建 Floor Plan
**调用：** `transactionMode: "auto"`
**parameters：** `"Level 1,Level 2,Level 3"`。
```csharp
var names = new HashSet<string>(((string)parameters[0]).Split(',').Select(x => x.Trim()));
var planType = new FilteredElementCollector(document).OfClass(typeof(ViewFamilyType))
    .Cast<ViewFamilyType>().FirstOrDefault(x => x.ViewFamily == ViewFamily.FloorPlan);
if (planType == null) throw new InvalidOperationException("No FloorPlan ViewFamilyType found.");
var existingLevelIds = new HashSet<int>(new FilteredElementCollector(document)
    .OfClass(typeof(ViewPlan)).Cast<ViewPlan>()
    .Where(v => !v.IsTemplate && v.GenLevel != null)
    .Select(v => v.GenLevel.Id.IntegerValue));
var created = new List<int>();
foreach (var level in new FilteredElementCollector(document).OfClass(typeof(Level)).Cast<Level>()) {
    if (!names.Contains(level.Name) || existingLevelIds.Contains(level.Id.IntegerValue)) continue;
    var view = ViewPlan.Create(document, planType.Id, level.Id);
    view.Name = $"A-PLAN-{level.Name}-WIP";
    created.Add(view.Id.IntegerValue);
}
return new { createdCount = created.Count, viewIds = created };
```
验证：人工激活新视图后 `get_current_view_info`；再查浏览器命名和模板。
### 模式 5：创建 Sheet 并放置一个视图
**调用：** `transactionMode: "auto"`
**parameters：** `titleBlockTypeId, viewId, sheetNumber, sheetName, xMm, yMm`。
```csharp
double Mm(string value) => double.Parse(value, System.Globalization.CultureInfo.InvariantCulture) / 304.8;
var titleBlockId = new ElementId(int.Parse((string)parameters[0]));
var viewId = new ElementId(int.Parse((string)parameters[1]));
var view = document.GetElement(viewId) as View;
if (view == null || view.IsTemplate)
    throw new InvalidOperationException("View cannot be placed on a sheet.");
var sheet = ViewSheet.Create(document, titleBlockId);
sheet.SheetNumber = (string)parameters[2];
sheet.Name = (string)parameters[3];
if (!Viewport.CanAddViewToSheet(document, sheet.Id, viewId))
    throw new InvalidOperationException("View is already placed or incompatible.");
var viewport = Viewport.Create(document, sheet.Id, viewId,
    new XYZ(Mm((string)parameters[4]), Mm((string)parameters[5]), 0));
return new { sheetId = sheet.Id.IntegerValue, viewportId = viewport.Id.IntegerValue };
```
注意：`Viewport.CanAddViewToSheet` 必须针对已创建的真实 Sheet；失败时 `auto` 事务应整体回滚。Schedule 需用 `ScheduleSheetInstance`，不能用本片段的 `Viewport`。
### 模式 6：导出一个 3D View 为 FBX
**调用：** `transactionMode: "none"`
**parameters：** `view3dId, outputFolder, fileBaseName, useLod, withoutBoundaryEdges`。
```csharp
var view = document.GetElement(new ElementId(int.Parse((string)parameters[0]))) as View3D;
if (view == null || view.IsTemplate) throw new InvalidOperationException("A non-template View3D is required.");
var folder = (string)parameters[1];
var fileName = (string)parameters[2];
if (!System.IO.Directory.Exists(folder)) throw new System.IO.DirectoryNotFoundException(folder);
var views = new ViewSet();
views.Insert(view);
var options = new FBXExportOptions {
    UseLevelsOfDetail = bool.Parse((string)parameters[3]),
    WithoutBoundaryEdges = bool.Parse((string)parameters[4]),
    StopOnError = true
};
var ok = document.Export(folder, fileName, views, options);
return new { exported = ok, viewId = view.Id.IntegerValue,
    expectedPath = System.IO.Path.Combine(folder, fileName + ".fbx") };
```
验证：检查 FBX 存在且非空；Blender 导入后量测已知尺寸。详见 [`fbx-export-render.md`](fbx-export-render.md)。
### 模式 7：创建隔离 QA 3D View
**调用：** `transactionMode: "auto"`
**parameters：** `viewName, "123,456,789"`（目标元素 Id）。
```csharp
var type = new FilteredElementCollector(document).OfClass(typeof(ViewFamilyType))
    .Cast<ViewFamilyType>().FirstOrDefault(x => x.ViewFamily == ViewFamily.ThreeDimensional);
if (type == null) throw new InvalidOperationException("No 3D ViewFamilyType found.");
var view = View3D.CreateIsometric(document, type.Id);
view.Name = (string)parameters[0];
var ids = ((string)parameters[1]).Split(',')
    .Where(x => !string.IsNullOrWhiteSpace(x))
    .Select(x => new ElementId(int.Parse(x.Trim()))).ToList();
view.IsolateElementsTemporary(ids);
return new { viewId = view.Id.IntegerValue, isolatedCount = ids.Count };
```
风险：Temporary Hide/Isolate 是临时状态，不应作为发布视图永久规则；用于 QA 后人工检查并决定 Filter/Template。
## 6. MCP 结果验收
### 6.1 创建类
- 返回 ElementId 非空且互不重复。
- 实际类别与目标类别一致。
- Family/Type 与查询结果一致。
- Level、Offset、坐标和尺寸正确。
- 门窗真实依附墙并切洞。
- 楼板/屋面边界闭合、共面。
- Room 面积大于 0，名称编号正确。
- 平面、剖面、3D 同时可见。
### 6.2 修改类
- 同一 ElementId 仍存在。
- 修改前后差值等于输入。
- 未修改对象计数为 0 或有明确解释。
- 类型修改没有误伤其他实例。
- 宿主、约束、Group、Dimension、Tag 未失效。
- warnings 没有出现新的严重问题。
### 6.3 视图/图纸类
- 新视图/Sheet 名称唯一。
- ViewFamily、Level、Scale、Template 正确。
- 视图未重复放置。
- TitleBlock 类型正确。
- 视口位置、标题和裁剪可读。
- `analyze_model_statistics` 的 View/Sheet 计数符合预期。
### 6.4 导出类
- 返回 true 不是唯一证据。
- 文件存在、大小非零、文件名正确。
- 目标软件可打开。
- 单位、坐标、轴向和三个控制点通过。
- 几何、材质槽和相机范围符合导出视图。
- 文件版本与 Revit 模型版本一致。
### 6.5 失败时
- 保存完整 tool 输入、返回、编译错误和 Revit warnings。
- 不立即扩大参数范围重试。
- 先确认 Revit 版本、API 类型、ElementId、FamilySymbol、Level、View。
- 先确认 transactionMode。
- 先在可丢弃项目复现。
- 若专用 tool 能完成，退回专用 tool。
- 若代码造成部分写入，回退模型版本，不靠第二段代码猜修。
## 7. 来源
- [本仓库 Revit MCP 安装与配置](../../../tools/revit-mcp/SETUP.md)
- [本仓库 Revit MCP 基础测试计划](../../../tools/revit-mcp/TEST_PLAN.md)
- [Revit MCP 上游来源与固定版本](../../../tools/revit-mcp/README.md)
- [Autodesk Revit API Developers Guide：Export](https://help.autodesk.com/cloudhelp/2019/ITA/Revit-API/files/Revit_API_Developers_Guide/Advanced_Topics/Revit_API_Revit_API_Developers_Guide_Advanced_Topics_Export_html.html)
- [Revit API Docs：FBXExportOptions](https://www.revitapidocs.com/2019/0ecc67db-1f7a-cc97-df7d-af681e1cd1b2.htm)
- [Autodesk Help：About Constraints](https://help.autodesk.com/cloudhelp/2023/ENU/Revit-Model/files/GUID-91CBCCF3-66D1-496B-80B3-D893065D1A50.htm)
