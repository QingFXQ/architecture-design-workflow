# Revit MCP 基础测试计划

## 1. 测试范围与环境

本计划验证 MCP stdio server、Revit 插件、命令集和 Revit API 的完整链路。目标为 Windows `YOUR_REVIT_HOST` 上的 Revit 2021，启动路径为 `C:\Program Files\Autodesk\Revit 2021\Revit.exe`。

测试须在一个可丢弃的新建筑项目中执行，项目单位不影响 MCP 参数：仓库创建类工具的坐标、长度、厚度、高度和标高均使用毫米。每次调用都记录：tool 名、输入、完整返回、创建的 ElementId、Revit 截图和结果判定。

### 前置检查

1. Revit 2021 已打开一个可写项目。
2. `Revit MCP Plugin` 的 `Settings` 已启用本计划涉及的命令。
3. 已点击 `Revit MCP Switch` 并看到 `Open Server`。
4. `say_hello` 成功。
5. `get_current_view_info` 返回当前楼层平面信息。
6. 当前项目至少有一个 0 mm 附近的标高、墙类型、门类型和楼板类型。用 `get_available_family_types` 读取实际类型 ID，不写死 ElementId。

## 2. 测试顺序

按 1–8 执行。第 1 项创建四面房间围护墙和一面独立移动测试墙；后续项目复用其返回的 ElementId。

## 3. 测试项

### 1. 创建墙

**实际 MCP tool**：`get_available_family_types`、`create_line_based_element`、`get_current_view_elements`

**步骤**：

1. 调用 `get_available_family_types`，`categoryList` 使用 `OST_Walls`，保存一个实际墙类型 ID。
2. 调用 `create_line_based_element` 创建四面闭合墙，依次连接 `(0,0,0)`、`(6000,0,0)`、`(6000,4000,0)`、`(0,4000,0)` 和起点；每面墙使用实际 `typeId`，`category` 为 `OST_Walls`，高度 3000 mm、厚度 200 mm、`baseLevel` 为 0、`baseOffset` 为 0。
3. 再创建一面独立测试墙，从 `(0,8000,0)` 到 `(4000,8000,0)`，参数同上；保存该墙 ID，供第 4 项使用。
4. 调用 `get_current_view_elements`，`modelCategoryList` 使用 `OST_Walls`，核对返回 ID。

**通过标准**：两次创建返回均为成功；总计返回 5 个非空、互不重复的 ElementId；当前视图可以查询到这些墙；围护墙在 Revit 中形成 6000×4000 mm 闭合矩形，独立墙位于其外。

**失败排查**：无返回 ID时检查墙类型 ID、0 mm 标高和 `OST_Walls` 拼写；若只创建部分墙，查看返回中的 warnings；若形状不闭合，核对相邻线段终点与下一段起点完全一致。

### 2. 创建门

**实际 MCP tool**：`get_available_family_types`、`create_point_based_element`、`get_current_view_elements`

**步骤**：

1. 调用 `get_available_family_types`，`categoryList` 使用 `OST_Doors`，保存一个实际门类型 ID。
2. 从第 1 项选择底边墙 ID作为 `hostWallId`。
3. 调用 `create_point_based_element`，`name` 为 `MCP Test Door`，位置为 `(3000,0,0)`，使用实际 `typeId` 和 `hostWallId`，宽 900 mm、高 2100 mm、`baseLevel` 为 0、`baseOffset` 为 0、`facingFlipped` 为 false。
4. 调用 `get_current_view_elements`，`modelCategoryList` 使用 `OST_Doors`，核对返回 ID 和宿主关系。

**通过标准**：创建返回成功且含 1 个 ElementId；当前视图能查询到该门；Revit 中门位于所选墙中部并切开墙体，不是无宿主实例。

**失败排查**：若提示没有可用族类型，先在 Revit 项目中载入门族；若宿主无效，确认使用的是第 1 项真实墙 ID；若位置异常，检查坐标单位为毫米。

### 3. 创建房间

**实际 MCP tool**：`create_room`、`export_room_data`

**步骤**：

1. 确认第 1 项四面墙闭合，且活动视图为其所在楼层平面。
2. 调用 `create_room`，房间 `name` 为 `MCP Test Room`、`number` 为 `MCP-101`，位置为 `(3000,2000,0)`；`department` 为 `MCP Validation`，`comments` 为 `Created by Revit MCP test`。
3. 调用 `export_room_data`，在导出结果中按房间编号 `MCP-101` 查找该房间。

**通过标准**：创建返回成功且含房间 ElementId；导出结果中存在 `MCP-101`，名称为 `MCP Test Room`，面积大于 0；Revit 楼层平面中房间位于围护墙内部。

**失败排查**：若返回 `not in a properly enclosed region` 一类错误，检查四墙连接和房间点是否位于边界内；若编号冲突，删除旧的测试房间后重试；若找不到标高，确认项目存在 0 mm 附近标高。

### 4. 修改构件位置

**实际 MCP tool**：`send_code_to_revit`、`ai_element_filter`

仓库没有名为 `modify_element` 的已注册 MCP tool，`operate_element` 的实际 action 也不含 Move。因此本项使用仓库真实提供的 `send_code_to_revit`。

**步骤**：

1. 取第 1 项独立测试墙的 ElementId。
2. 调用 `ai_element_filter`，`filterCategory` 使用 `OST_Walls`、`includeInstances` 为 true，记录该墙移动前的几何位置。
3. 调用 `send_code_to_revit`，`transactionMode` 使用 `auto`，`parameters` 依次传入墙 ElementId 的字符串和 `500`。`code` 使用以下已与仓库动态代码包装器匹配的内容：

   ```csharp
   var id = int.Parse((string)parameters[0]);
   var distanceMm = double.Parse((string)parameters[1], System.Globalization.CultureInfo.InvariantCulture);
   ElementTransformUtils.MoveElement(document, new ElementId(id), new XYZ(distanceMm / 304.8, 0, 0));
   return id;
   ```

4. 再次调用 `ai_element_filter`，核对该墙 X 方向位置相对移动前增加 500 mm。

**通过标准**：`send_code_to_revit` 返回 `success: true`；同一 ElementId 仍存在；墙的 X 坐标整体增加 500 mm，Y、Z 坐标及墙长度保持不变。

**失败排查**：编译错误时核对代码使用仓库包装器提供的变量名 `document`、`parameters`；事务错误时确认 `transactionMode` 为 `auto` 且代码没有自行创建 Transaction；查不到元素时确认使用独立墙 ID，而不是墙类型 ID。

### 5. 创建楼板

**实际 MCP tool**：`get_available_family_types`、`create_surface_based_element`、`get_current_view_elements`

**步骤**：

1. 调用 `get_available_family_types`，`categoryList` 使用 `OST_Floors`，保存一个实际楼板类型 ID。
2. 调用 `create_surface_based_element`，`name` 为 `MCP Test Floor`、`category` 为 `OST_Floors`、使用实际 `typeId`、厚度 200 mm、`baseLevel` 为 0、`baseOffset` 为 0。
3. `boundary.outerLoop` 使用四条首尾相接的线段，依次连接 `(0,0,0)`、`(6000,0,0)`、`(6000,4000,0)`、`(0,4000,0)` 和起点。
4. 调用 `get_current_view_elements`，`modelCategoryList` 使用 `OST_Floors`，核对返回 ID。

**通过标准**：创建返回成功且含 1 个 ElementId；当前视图能查询到该楼板；Revit 中楼板轮廓为闭合矩形，位于 0 mm 标高，尺寸为 6000×4000 mm。

**失败排查**：若提示曲线不闭合或不共面，检查四条线段顺序、重复端点和全部 Z=0；若没有楼板类型，先在项目中保留或载入至少一个 FloorType；确认 `category` 只能使用 schema 允许的 `OST_Floors`。

### 6. 创建基本视图

**实际 MCP tool**：`create_level`、`get_current_view_info`

仓库没有通用的 `create_view` tool；`create_level` 是实际提供的基础视图创建入口，可随标高创建楼层平面和天花板平面。

**步骤**：

1. 调用 `create_level` 创建名称为 `MCP Test Level 3300`、标高 3300 mm 的标高；`isMainLevel` 和 `isBuildingStory` 为 true，`createFloorPlan` 为 true，`createCeilingPlan` 为 false。
2. 确认返回成功并记录创建结果。
3. 人工在 Revit Project Browser 中激活 `MCP Test Level 3300` 对应的楼层平面。
4. 调用 `get_current_view_info`。

**通过标准**：新标高存在且高程为 3300 mm；生成同标高的 FloorPlan；激活后 `get_current_view_info` 返回该视图名称和楼层平面类型。

**失败排查**：若标高名称已存在，删除旧测试标高后重试；若标高创建但无平面，确认 `createFloorPlan` 为 true 且项目包含 FloorPlan 的 ViewFamilyType；若返回的是其他视图，先人工激活新平面。

### 7. 标尺寸

**实际 MCP tool**：`create_dimensions`、`get_current_view_elements`

**步骤**：

1. 回到第 1 项矩形房间所在的楼层平面，取两面相对且平行的墙 ElementId。
2. 调用 `create_dimensions`，在 `dimensions` 数组内提供一项：`elementIds` 使用这两个墙 ID；`startPoint` 和 `endPoint` 位于两墙参考位置；`linePoint` 放在围护墙外侧；`dimensionType` 使用 `Linear`；`dimensionStyleId` 和 `viewId` 使用 schema 的默认值 `-1`。
3. 调用 `get_current_view_elements`，`annotationCategoryList` 使用 `OST_Dimensions`，核对新尺寸 ID。

**通过标准**：创建返回成功且含尺寸结果；当前视图可以查询到新的 `OST_Dimensions` 元素；尺寸线可见，引用两面目标墙，显示值与墙间实际距离一致。

**失败排查**：若无法提取 reference，确认目标为可标注的平行墙且当前为支持尺寸的 2D 视图；调整 `linePoint` 避免与墙重叠；若默认尺寸样式不可用，先在 Revit 中确认项目有线性尺寸样式。

### 8. 获取模型信息

**实际 MCP tool**：`analyze_model_statistics`

**步骤**：

1. 调用 `analyze_model_statistics`，`includeDetailedTypes` 为 true。
2. 保存完整 JSON 返回。
3. 对照前 7 项创建结果，检查 `categories` 中墙、门、房间、楼板和尺寸相关计数，并检查 `levels` 中出现 `MCP Test Level 3300`。

**通过标准**：返回 `success: true`；`projectName` 非空；`totalElements`、`totalTypes`、`totalViews` 大于 0；`categories` 和 `levels` 非空；新建元素对应类别计数不小于本计划成功创建的数量；`totalViews` 包含第 6 项新增的平面视图。

**失败排查**：大型模型超时时先在空白测试项目重试；如果 `includeDetailedTypes` 为 false，类别的详细 type/family 统计可能为空；若统计成功但缺少某类别，先用 `get_current_view_elements` 或 `ai_element_filter` 确认对应元素确实创建成功。

## 4. 总体通过标准

满足以下全部条件才判定基础集成通过：

- 26 个 MCP tools 可发现。
- `say_hello` 和 `get_current_view_info` 端到端成功。
- 8 项测试逐项达到通过标准。
- 所有创建/修改操作均返回成功，且在 Revit UI 或查询工具中得到独立复核。
- 未调用不存在的 `modify_element`；移动测试确实使用 `send_code_to_revit`。
- 测试完成后关闭而不保存测试项目，或明确保存为独立的测试 RVT，不能在生产模型中运行。

