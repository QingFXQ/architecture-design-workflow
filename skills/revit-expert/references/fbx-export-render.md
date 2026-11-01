# Revit → FBX → Blender / 渲染工作流
> 适用范围：导出一次明确版本的Revit几何快照给Blender，用于设计继续深化或正式图像基底，不要求固定Gate／角色交接。
> 版本说明：Revit 2021—2026 的 FBX 核心逻辑相近；导出对话框和 Blender 导入器会随版本变化。
> 核心原则：FBX是交换快照，不能自动回写原生BIM；建筑、场地与立面的当前依据按范围记录。Blender可设计，新变化同步受影响工程图，不能冒充RVT已经更新。
## 目录
- 1. 先理解原生 FBX 的能力边界
- 2. 导出前模型与视图检查
- 3. Revit 原生导出设置
- 4. Blender 导入与校准
- 5. 材质、贴图与灯光
- 6. 常见问题排查
- 7. 替代路径对比
- 8. Visualization Agent 交接约定
- 9. 验收清单
- 10. 来源
## 1. 先理解原生 FBX 的能力边界
### 1.1 原生 FBX 实际传递什么
Autodesk 将 Revit → FBX → 3ds Max 定位为设计可视化工作流，并说明 FBX 可传递当前 3D 视图的几何、灯光、渲染外观、天空设置、材质分配和相机等信息。[Autodesk：Exporting to 3ds Max](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-DocumentPresent/files/GUID-870FBFA0-D8EB-4FBD-93D6-B2A4B8A194C2.htm)
对 Blender 要保守理解：
- 几何通常可用，但会变成渲染网格，不再保留 Revit 系统构件编辑能力。
- 材质“分配关系”比材质“视觉完全一致”更可靠。
- Revit/Autodesk 材质模型与 Blender Principled BSDF 不是一一对应。
- 相机、灯光和层级可能导入，但名称、强度、单位和方向都需复核。
- Room、参数、Schedule、Workset、Phase 不是 Blender 渲染数据主链。
- FBX 往返不能替代 Revit 中的正式修改。
### 1.2 只导出 3D 视图
- Revit 原生 FBX 以 3D View 为导出范围。
- FBX 菜单变灰时先激活非模板 3D 视图。
- Revit API 的 `Document.Export(..., ViewSet, FBXExportOptions)` 也只允许 3D views。[Revit API：FBX Export](https://www.revitapidocs.com/2015/02b2efba-9d7c-88bc-b43e-a541e169d832.htm)
- 当前视图的可见类别、裁剪、Section Box、阶段和链接显示会影响导出范围。
- 因此必须建立专用、命名明确的 `VIZ_EXPORT_*` 视图，不能随手导出当前工作 3D。
### 1.3 原生选项没有什么
Revit 原生 FBX 的核心选项是文件命名、Use LOD 和 Without Boundary Edges；API 也主要暴露 LOD、边界边和 StopOnError。它没有像 DWG 那样完整的单位、图层和坐标导出设置。[Autodesk：Export to FBX](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-DocumentPresent/files/GUID-C8038EFE-FB14-4591-85A1-8407B2BDDD0A.htm) [Revit API：FBXExportOptions](https://www.revitapidocs.com/2019/0ecc67db-1f7a-cc97-df7d-af681e1cd1b2.htm)
结论：
- 不写“导出单位选择毫米”这类不存在的 UI 步骤。
- 不写“勾选 Shared Coordinates”这类不存在的 FBX 选项。
- 单位与坐标必须通过导入校准、控制点和交接卡证明。
- 需要显式单位/图层/坐标选择时评估 DWG、IFC 或版本相关的 OBJ。
## 2. 导出前模型与视图检查
### 2.1 冻结条件
- 明确本次导出用途、来源版本和已核／未核范围；发布图使用已核快照，设计预览可提前进行。
- Revit 模型版本和批准方案版本一致。
- 标高、主轴、共享坐标和建筑位置已冻结。
- 主要墙、板、屋顶、门窗、楼梯和幕墙已通过平剖检查。
- 可以在Blender设计分支研究修复，但正式Revit几何错误须同步修正，不能只修显示。
- 导出后发生模型改动，必须生成新 FBX 版本。
Autodesk 建议所有设计修改仍在 Revit 完成，以保持 Revit 为项目数据单一仓库。[Autodesk：Before Exporting a 3D View to 3ds Max](https://help.autodesk.com/cloudhelp/2023/ENU/Revit-DocumentPresent/files/GUID-E9B48E5F-F915-4939-8300-DCFB5DE46860.htm)
### 2.2 建立专用视图
建议名称：
```text
VIZ_EXPORT_EXT_FBX_v07
VIZ_EXPORT_INT_LOBBY_FBX_v07
VIZ_EXPORT_COORD_CHECK_v07
```
视图设置：
- 复制一个干净 3D 视图，不覆盖正式 QA 视图。
- 套专用 View Template。
- 设正确 Phase 和 Phase Filter。
- 明确 Revit Links 是否显示、按宿主或链接视图显示。
- 隐藏注释、轴网、标高、Section/Callout 标记等不需几何。
- 用 Section Box 只保留渲染范围。
- 对室内图只导出相关楼层和相邻外壳。
- 对外观图保留建筑、场地和必要环境，卸载无关专业链接。
- 不用逐元素隐藏管理大量导出规则；优先类别、Filter 和链接显示。
Autodesk 建议用 Coarse/Medium、隐藏不需要类别、裁剪和 Section Box 限制导出几何，以减少对象和数据量。[Autodesk：About Limiting Model Geometry Before Exporting](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-DocumentPresent/files/GUID-7C4D89EF-01B9-490E-90CC-0CE96F496F12.htm)
### 2.3 几何清理
- 删除或隐藏测试构件、重复实例、临时体块和废弃选项。
- 替换高面数人物、树木、家具和厂家设备族。
- 将只服务 2D 的细节留在 Revit 图纸，不转成三维几何。
- 检查弧形幕墙、栏杆、圆柱、曲面屋顶的细分需求。
- 检查镜像族法向、负尺度和翻转构件。
- 检查链接是否重复嵌套。
- 检查远离主体的意外图元；它们会扩大场景边界并制造原点问题。
- 检查导入 CAD、SAT、网格和点云是否真的需要。
- 对大项目分外部、内部、场地或楼层导出，不追求一个 FBX 包含一切。
### 2.4 已知尺寸和控制点
导出前记录：
- 一段已知墙长，例如 6000 mm。
- 一层已知层高，例如 3300 mm。
- 建筑控制角点 A 的东、北、高程。
- 建筑控制角点 B 的东、北、高程。
- 第三个不共线点 C，供旋转/镜像判断。
- Project North 与 True North 夹角。
- Revit Internal Origin、Project Base Point、Survey Point 的交接值。
这些数据用于 Blender 进口后验证比例、原点、轴向和旋转，不能省略。
### 2.5 材质预检
- 所有可见主体对象有明确 Material，而不是长期使用 `<By Category>` 模糊继承。
- 材质名称唯一、可搜索、避免 `Material 1`。
- 名称推荐 ASCII 或中英对照，避免下游工具编码差异。
- 相同视觉材质复用同一 Revit Material，避免几百个近似材质槽。
- 检查 Appearance Asset，不只看 Graphics/Shading 颜色。
- 检查贴图文件存在、路径可访问、分辨率合理。
- 检查透明玻璃、发光、自发光、金属和法线贴图的下游风险。
- 先在 Revit 做一张低成本测试渲染，验证基本材质和灯光。
Autodesk 建议 FBX 前在 Revit 先检查材质渲染外观、灯光位置和初步渲染结果。[Autodesk：About Preparing the 3D View for Rendering](https://help.autodesk.com/cloudhelp/2016/ENU/Revit-DocumentPresent/files/GUID-A92C949B-0CA2-40AD-899B-7D01C60FEBCC.htm)
## 3. Revit 原生导出设置
### 3.1 手工导出步骤
1. 打开并激活专用 `VIZ_EXPORT_*` 3D 视图。
2. 确认 View Template、Section Box、Phase、Links 和可见类别。
3. 保存 Revit 模型。
4. `File > Export > FBX`。
5. 使用手工、可追溯文件名。
6. 决定是否启用 `Use LOD`。
7. 决定是否启用 `Without boundary edge`。
8. 导出到独立版本目录。
9. 记录导出时间、Revit 版本、视图名和文件大小。
10. 立即在 Blender 测试导入，不把“成功生成文件”当验收。
### 3.2 文件命名
推荐：
```text
[项目]_[区域]_[视图用途]_[Revit版本]_[模型版本]_[日期].fbx
StudioA_Tower_EXT_R21_M072_20260812.fbx
```
- 不使用 `final.fbx`、`final2.fbx`。
- 文件名与 Revit 模型版本、视图版本一致。
- 内外景分文件时写 `EXT/INT`。
- 坐标/材质试验写 `TEST`，不得混入正式交接目录。
### 3.3 Use LOD
Autodesk 说明：启用 LOD 会生成更分面、文件更小的模型；关闭则更平滑、更接近原几何，但文件更大。[Autodesk：Export to FBX](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-DocumentPresent/files/GUID-C8038EFE-FB14-4591-85A1-8407B2BDDD0A.htm)
选择建议：
- 城市尺度、远景、初轮预览：启用 LOD。
- 室内近景、曲面外皮、圆形扶手：先关闭 LOD 测试。
- 大模型先启用 LOD 导出一小块，比较面数和轮廓。
- LOD 与 Revit View Detail Level 不是同一设置；两者都要记录。
- 不为了一处曲面把整个城市模型导成最高细分；拆分导出。
### 3.4 Without Boundary Edges
Autodesk 说明：启用后隐藏曲面相接处的边界线，使导入 3ds Max 后外观更少“网格化”。[Autodesk：Export to FBX](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-DocumentPresent/files/GUID-C8038EFE-FB14-4591-85A1-8407B2BDDD0A.htm)
选择建议：
- 纯渲染默认启用，减少多余边线。
- 需要排查分面、材质边界或几何接缝时关闭。
- 该选项不会减少核心三角面数量，也不会修复破面。
- Blender 中是否显示线框主要仍由对象、法线和显示设置决定。
### 3.5 单位
- Revit 内部长度单位是英尺。
- Autodesk 3ds Max 教程明确指出 Revit 导出的 FBX 以 feet 为单位。[Autodesk：Linking a 3ds Max Scene to the FBX File](https://help.autodesk.com/cloudhelp/2015/ENU/3DSMax-Tutorial/files/GUID-8A19E2ED-D900-48E5-A0CE-3561F2B81C4D.htm)
- 原生 Revit FBX 对话框没有单位下拉框。
- Blender 导入器可能读取 FBX 单位元数据并转换；不同版本/插件行为要实测。
- 第一次导入以 `Scale = 1.0` 开始，量取已知 6000 mm 墙长。
- 若导入器未转换且 1 FBX unit 被当成 1 m，feet → metre 的数学系数是 0.3048。
- 若尺寸以毫米数被当成 metre，数学系数是 0.001。
- 不在未量测前盲目套 0.3048、100、304.8 或 0.001。
- 校准后 Apply Scale，并记录对象变换；后续同版本保持同一策略。
### 3.6 坐标与原点
- Revit 原生 FBX 没有 `Shared Coordinates` 复选框。
- 不声称 FBX 自动满足测量坐标交付。
- 以导出视图、Revit 内部几何和 FBX 单位元数据为基础进行校准。
- 建筑离 Internal Origin 很远时，Blender 浮点精度、视口裁剪和材质可能异常。
- 正式交接优先保留建筑近原点的可视化工作坐标，并附共享坐标变换矩阵/控制点。
- 多专业文件必须用同一导出策略和同一三个控制点。
- 不在 Blender 手工“摆到差不多”；用数值平移/旋转并保存父级 Empty 变换。
## 4. Blender 导入与校准
### 4.1 导入前场景
- 保存空白 `.blend` 模板。
- Scene Units 设为 Metric；Unit Scale 是否为 1.0 由团队标准决定。
- 建立 `00_RAW_FBX`、`10_CLEAN`、`20_MATERIALS`、`30_LIGHTS` 集合。
- 建立一个根 Empty，所有原始 FBX 对象置于其下。
- 不在原始集合直接破坏性编辑；复制或实例到清理集合。
- 记录 Blender 版本和 FBX importer 版本。
### 4.2 导入设置
Blender FBX 手册说明 Blender 使用 Y Forward、Z Up，并提供 Forward/Up Axis、Scale、Manual Orientation 和 Apply Transform 等导入控制。[Blender Manual：FBX](https://docs.blender.org/manual/en/4.4/addons/import_export/scene_fbx.html)
建议顺序：
1. 首次保持 `Scale 1.0`。
2. 先让导入器使用 FBX 元数据/默认轴转换。
3. 不确定时不要同时改 Scale、Forward、Up 和 Apply Transform。
4. 导入后检查已知墙长、层高、第三控制点。
5. 若模型躺倒/镜像，再只改轴映射进行第二次测试。
6. 若比例错，只改 Scale 进行第二次测试。
7. 校准通过后保存为团队 Import Preset/说明。
### 4.3 三步校准
**比例：**
- 量测 6000 mm 已知墙长，目标应为 6 m（Metric Unit Scale 1.0 时）。
- 再量测 3300 mm 层高，排除只校准单轴的错误。
- 对根 Empty 统一缩放，不逐对象缩放。
**轴向：**
- Z 应为竖直向上。
- 用入口、北向或不对称立面判断前后/镜像。
- 检查对象 Transform 是否含意外负 Scale。
**位置：**
- 核对 A/B/C 三控制点。
- 需要真实坐标时在根 Empty 上施加记录过的变换。
- 场地、建筑、结构分别导入时必须落在同一父坐标体系。
### 4.4 导入后几何检查
- 外墙、楼板、屋顶无明显缺面。
- 玻璃朝向和法线正确。
- 圆柱、曲墙、栏杆的分面可接受。
- 门窗没有漂浮或重复。
- 链接模型没有重复导入。
- Section Box 没有裁掉渲染需要的对象。
- 远离主体的孤立对象已定位来源。
- 对象数量、三角面数、材质槽数量已记录。
## 5. 材质、贴图与灯光
### 5.1 材质转换原则
- 保留 Revit 材质分配作为“对象该用哪类材质”的映射。
- 在 Blender 重建最终 Principled BSDF，不依赖自动转换达到最终质量。
- 建立 `Revit Material Name → Blender Material Name` 对照表。
- 同名 Revit 材质只映射到一个 Blender 主材质。
- 通过链接材质/资产库复用，不逐对象复制材质。
- 玻璃、金属、发光、半透明和复合贴图必须人工复核。
Blender 手册指出 FBX 使用固定管线式材质，而 Blender 使用复杂节点材质，导入器只能进行转换；这解释了“材质槽在但外观不一致”。[Blender Manual：FBX](https://docs.blender.org/manual/en/4.4/addons/import_export/scene_fbx.html)
### 5.2 贴图交接
- FBX 文件不被视为贴图的唯一载体。
- 交接目录包含原始 albedo、normal、roughness、opacity、emission 等图片。
- 使用相对路径或 Blender Asset Library 统一路径。
- 文件名不含难以跨平台处理的特殊字符。
- 记录色彩空间：颜色贴图通常 sRGB，数据贴图通常 Non-Color。
- 检查 Revit 的真实尺度贴图在 Blender 中是否被拉伸。
- 缺贴图时先按材质清单定位，不在对象上随意补相似图片。
### 5.3 灯光与相机
- 导入相机作为 Revit 构图参考，不承诺焦距/裁剪完全一致。
- 记录 Revit 导出视图名、相机类型和目标点。
- 导入灯光只作位置参考，重新校准强度、颜色和阴影。
- 日光、天空和曝光在 Blender 渲染器中重新建立。
- 保留一台锁定的 `CAM_REVT_REF` 用于几何回归比较。
- 最终相机另建，不覆盖参考相机。
## 6. 常见问题排查
### 6.1 模型躺倒或轴翻转
症状：建筑横躺、前后镜像、旋转 90°。
排查：
1. 检查 Blender 是否 Z Up。
2. 恢复 Scale 1.0，只改变 Forward/Up Axis。
3. 用不对称立面和三控制点判断镜像。
4. 检查根 Empty 是否有负 Scale。
5. 不逐对象旋转修补。
### 6.2 单位错 3.28084、100、304.8 或 1000 倍
原因通常是 feet、metres、centimetres、millimetres 被重复或未转换。
排查：
1. 记录 Blender Scene Units。
2. 重新导入到空场景，Scale 1.0。
3. 量测两个已知尺寸。
4. 只在根 Empty 或 Import Scale 做一次转换。
5. Apply Scale 后再次量测。
### 6.3 模型离原点极远
症状：视口裁剪、闪烁、导航困难、阴影/纹理精度异常。
原因：建筑使用真实大地坐标直接进入渲染场景，或 Revit 内有孤立远端图元。
处理：
- 在 Revit 查远端图元和坐标设置。
- 对渲染建立近原点父坐标，保留共享坐标变换记录。
- 用同一变换处理所有专业文件。
- 不丢弃真实坐标；把它放在交接矩阵，而不是让 GPU 直接承受极大数值。
### 6.4 材质丢失或全灰
- 检查 Revit 对象是否有 Material Assignment。
- 检查 Appearance Asset 和贴图路径。
- 检查 FBX 导入是否创建材质槽。
- 在 Blender 按材质映射表批量替换。
- 检查贴图相对路径和文件权限。
- 不把 Shading Color 当作最终 PBR 材质。
### 6.5 纹理尺度错误
- 检查 Revit 贴图真实尺寸。
- 检查 Blender UV 和 Mapping 节点。
- 检查根对象是否尚未 Apply Scale。
- 圆形服务/曲面优先使用导入 UV，不随意重新平面投影。
- 对重复砖、木纹、面板用已知构件尺寸校准。
### 6.6 三角面过多
症状：导入慢、`.blend` 巨大、视口卡顿、渲染占内存。
处理顺序：
1. 回 Revit 限制 3D 视图范围。
2. 隐藏高面数家具、树、人、机电小件。
3. 使用 Coarse/Medium。
4. 测试启用 Use LOD。
5. 按区域/楼层拆分导出。
6. 在 Blender 对重复对象实例化、合并静态远景或受控 Decimate。
7. 不对轮廓关键曲面无差别 Decimate。
### 6.7 破面、黑面和法线
- 检查 Revit 源几何是否自交或零厚度。
- 在 Blender 显示 Face Orientation。
- 对副本 Recalculate Outside；保留原始 FBX 集合。
- 检查镜像和负 Scale。
- 检查玻璃双面/单面渲染设置。
- 破面涉及主体几何时回 Revit 修复并重导。
### 6.8 链接缺失或重复
- 在 Revit 导出视图检查 Revit Links 可见性。
- 检查嵌套链接是 Overlay 还是 Attachment。
- 决定“一次由宿主带出”还是“各专业分别导出”，不能两者同时。
- 各专业分别导出时统一单位、轴向、控制点和版本。
- 在 Blender 用集合按专业管理，避免不可追溯合并。
## 7. 替代路径对比
| 格式 | 适用 | 优点 | 风险/限制 | Revit 2021 注意 |
| --- | --- | --- | --- | --- |
| FBX | 视图驱动渲染、相机/材质分配交接 | 原生、3D 视图范围、Autodesk 可视化链成熟 | 单位/共享坐标 UI 少，网格重，Blender 材质需重建 | 可原生导出 |
| DWG | 需要图层、单位、实体/网格控制的几何交换 | 单位和图层设置明确，CAD/3ds Max 兼容好 | 材质/相机语义弱，Blender 导入链可能需插件/中转 | 可原生导出 |
| IFC | 跨 BIM 平台、类别/属性和坐标语义 | 开放标准，构件语义和属性优于纯网格 | 渲染材质、细分和导入结果随实现变化 | 建议使用匹配版本 IFC exporter |
| OBJ | 轻量静态网格、MTL 材质、广泛 DCC 支持 | 简单、易检查、Blender 友好 | 不含 BIM 语义/灯光/复杂层级；版本支持不同 | Revit 2021 原生支持有限，可能需插件/中转 |
选择规则：
- 需要相机、灯光参考和 Autodesk 材质分配：先试 FBX。
- 需要明确图层、单位、实体/网格选项：评估 DWG。
- 需要 BIM 类别、属性、跨平台协调：评估 IFC。
- 只要静态网格和简单材质：版本支持时评估 OBJ。
- 不把格式选择当信仰；用一个典型区域做 A/B 测试。
Autodesk 的 CAD 导出说明指出 DWG/DXF 可配置 Layer Mapping、视图范围和单位，并列出 OBJ 作为 3D 几何格式；具体可用性以 Revit 版本为准。[Autodesk：About Exporting to CAD Formats](https://help.autodesk.com/view/RVT/2025/ENU/?guid=GUID-EA2B51E1-C28A-4410-AF01-836377581968)
## 8. Visualization Agent 交接约定
### 8.1 文件结构
```text
VIZ_HANDOFF_M072/
  00_manifest/
  10_fbx/
  20_textures/
  30_reference_png/
  40_coordinate_control/
  90_superseded/
```
### 8.2 Manifest 必填字段
- 项目名。
- 当前设计／导出修订。
- Revit 文件名、Revit 版本、保存时间。
- 导出 FBX 文件名、导出时间、文件大小。
- 导出 3D View Name 和 View Id。
- View Detail Level、Use LOD、Without Boundary Edges。
- 包含/排除的 Revit Links、Worksets、Phases 和 Categories。
- Revit 内部单位与 Blender 目标单位。
- 已验证的 Import Scale。
- Forward/Up Axis 和 Apply Transform 设置。
- A/B/C 三控制点及其 Revit/Blender 坐标。
- Shared Coordinates 变换说明。
- Project North / True North 关系。
- 已知尺寸验证值。
- 材质映射表和贴图目录。
- 参考相机、灯光和预览 PNG。
- 已知问题、允许修复范围、禁止修改范围。
- 下一版替换规则和责任人。
### 8.3 修改责任边界
Visualization Agent 可以：
- 重建 Blender 材质、灯光、环境和相机。
- 组织集合、实例化重复物和非破坏性优化。
- 删除明确标记为渲染无关的副本/辅助对象。
- 按交接矩阵应用单位和坐标变换。
本次仅润色／出图快照时不可：
- 在不更新设计依据的情况下，悄悄改变墙板门窗、楼梯、屋面和主要空间关系；获授权的新设计应另存可编辑分支并同步图纸。
- 用 Blender 补洞后把结果当 Revit 已修复。
- 擅自改变建筑位置、层高、轴线或 True North。
- 覆盖原始 FBX 集合而失去回归比较。
- 用旧 FBX 继续渲染并声称对应新模型版本。
### 8.4 回退条件
- 发现主体缺面、错位、漂浮、穿插或错误开口：退回 Drawing Production Agent。
- 发现单位/轴向/坐标无法由交接卡解释：暂停并退回确认。
- 发现材质槽存在但贴图缺失：可按材质清单补路径；清单也缺失则退回。
- 发现三角面过多：先按可见范围建议 Revit 重导，再考虑 Blender 优化。
- 发现设计变化：在可编辑设计分支完成并记录依据，更新受影响工程图和表现底图；不继续用旧FBX声称对应新方案。
## 9. 验收清单
### 9.1 Revit 侧
- 专用 3D 导出视图已命名并冻结。
- Phase、Links、Worksets、Categories 和 Section Box 已记录。
- 关键平面、剖面、3D 与导出模型同版本。
- 一段已知长度、一个层高、三个控制点已记录。
- 材质名称、Appearance Asset 和贴图路径已检查。
- Use LOD 与 Without Boundary Edges 已记录。
- 文件名包含项目、区域、版本和日期。
### 9.2 Blender 侧
- 导入 Scale 经过两个尺寸验证。
- Z Up、前向和镜像经过第三控制点验证。
- 根 Empty 变换有记录。
- 建筑、场地、结构文件能对齐。
- 关键曲面分面可接受。
- 主体无缺面、黑面和重复链接。
- 材质映射表覆盖所有主要可见材质。
- 原始 FBX 集合只读保留。
### 9.3 交接包
- Manifest 无空项。
- FBX、贴图、预览和坐标文件齐全。
- 已知问题和责任边界明确。
- 旧版本移入 `90_superseded`。
- Visualization Agent 能在空白 Blender 场景复现导入。
- 最终截图与 Revit 参考视图的几何关系一致。
## 10. 来源
- [Autodesk Help：Exporting to 3ds Max](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-DocumentPresent/files/GUID-870FBFA0-D8EB-4FBD-93D6-B2A4B8A194C2.htm)
- [Autodesk Help：Before Exporting a 3D View to 3ds Max](https://help.autodesk.com/cloudhelp/2023/ENU/Revit-DocumentPresent/files/GUID-E9B48E5F-F915-4939-8300-DCFB5DE46860.htm)
- [Autodesk Help：About Limiting Model Geometry Before Exporting](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-DocumentPresent/files/GUID-7C4D89EF-01B9-490E-90CC-0CE96F496F12.htm)
- [Autodesk Help：Export to FBX](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-DocumentPresent/files/GUID-C8038EFE-FB14-4591-85A1-8407B2BDDD0A.htm)
- [Autodesk Help：About Preparing the 3D View for Rendering](https://help.autodesk.com/cloudhelp/2016/ENU/Revit-DocumentPresent/files/GUID-A92C949B-0CA2-40AD-899B-7D01C60FEBCC.htm)
- [Autodesk 3ds Max Tutorial：Linking a 3ds Max Scene to the FBX File](https://help.autodesk.com/cloudhelp/2015/ENU/3DSMax-Tutorial/files/GUID-8A19E2ED-D900-48E5-A0CE-3561F2B81C4D.htm)
- [Autodesk Help：About Exporting to CAD Formats](https://help.autodesk.com/view/RVT/2025/ENU/?guid=GUID-EA2B51E1-C28A-4410-AF01-836377581968)
- [Revit API Docs：FBXExportOptions Members](https://www.revitapidocs.com/2019/0ecc67db-1f7a-cc97-df7d-af681e1cd1b2.htm)
- [Revit API Docs：Document.Export FBX](https://www.revitapidocs.com/2015/02b2efba-9d7c-88bc-b43e-a541e169d832.htm)
- [Blender 4.4 Manual：FBX Import/Export](https://docs.blender.org/manual/en/4.4/addons/import_export/scene_fbx.html)
