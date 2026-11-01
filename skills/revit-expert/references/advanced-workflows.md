# Revit 高级工作流：基准、视图、协作、性能与参数治理

> 适用版本：原则适用于 Revit 2021—2026；界面名称可能随版本变化。
> 使用方式：遇到多楼层、大体量、链接协作、共享坐标或批量改参任务时按章节读取。
> 核心原则：基准、坐标、参数、显示和协作各有唯一责任层；不要用后一层修补前一层。
## 目录

- 1. 高手工作流总图
- 2. 轴网系统化建立与维护
- 3. 标高系统化建立与维护
- 4. Project Browser、工作集与阶段化的职责分离
- 5. 大模型性能优化
- 6. 链接文件与协作
- 7. 参数驱动批量修改、公式与族类型目录
- 8. 约束与锁定的正确使用
- 9. 图元共享坐标
- 10. 变更与交付检查清单
- 11. 来源
## 1. 高手工作流总图
### 1.1 五个控制面

1. **几何基准面**：Internal Origin、Project Base Point、Survey Point、标高、轴网、Scope Box。
2. **模型责任面**：原生类别、类型、实例、宿主、工作集、设计选项、阶段。
3. **数据责任面**：族参数、项目参数、共享参数、公式、类型目录、明细表。
4. **显示责任面**：View Template、Filter、Phase Filter、Revit Link Display、Crop、Scope Box。
5. **协作责任面**：中心模型、本地模型、链接、借用、同步、发布、坐标主文件。

把问题放回正确控制面：

- 位置错先查基准和链接定位，不先移动孤立构件。
- 多视图显示错先查模板和 Filter，不先逐元素覆盖。
- 同类型尺寸错先改类型或族公式，不逐实例改值。
- 只在某阶段显示错先查 Phase/Phase Filter，不用工作集冒充阶段。
- 多人冲突先查借用、同步和模型拆分，不让每人长期占有整工作集。

Autodesk 将复杂几何、多重参数关系、多重约束、复杂视图和链接文件列为 Revit 性能的主要影响因素；优化应覆盖整个控制链，而不是只盯文件大小。[Autodesk：Performance Optimization for Revit Models](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-Customize/files/GUID-269DCB99-AFA2-4D3F-8666-10E30C7415B6.htm)
### 1.2 建模前 30 分钟

- 写出坐标主文件和坐标责任人。
- 写出所有楼层标高、楼层用途、是否 Building Story。
- 写出主轴网、局部轴网、斜翼/塔楼轴网的命名空间。
- 写出模型拆分：建筑、结构、机电、场地、外部环境。
- 写出浏览器分类字段：专业、用途、区域、阶段、发布状态。
- 写出最少工作集：共享标高轴网、主体、链接、必要区域。
- 写出五类代表视图和对应模板。
- 写出关键共享参数的 GUID、数据类型、实例/类型归属和允许空值。
- 写出冻结点：何时停止改标高、何时冻结共享坐标、何时冻结图纸编号。
## 2. 轴网系统化建立与维护
### 2.1 建立顺序

1. 确认模型靠近 Internal Origin，且不会因真实测量坐标而把几何建到极远处。
2. 用总图/结构控制线确认建筑主方向，不从局部房间边猜主轴。
3. 先建两条正交主轴，核对原点、角度和总尺寸。
4. 再按模数建普通轴网，最后建斜轴、弧轴和局部轴网。
5. 命名分区明确，例如塔楼数字轴、裙房字母轴、局部轴带前缀。
6. 在一个总控平面和一个总控立面检查 3D Datum Extents。
7. 为大楼翼部、塔楼或独立分区建立 Scope Box。
8. 轴网赋给正确 Scope Box 后，再处理各视图 2D 端头。
9. 对平行/相似视图使用 Propagate Extents，减少逐视图拖拽。
10. 导出一张总平和一张立面核对轴号、顺序、间距和端头。

Scope Box 能同时控制 Datum 的 3D 范围和视图裁剪；对分翼、塔楼和重复楼层，比逐视图拖动轴线端头更稳定。[Autodesk：Create and Use Scope Boxes](https://help.autodesk.com/view/RVT/2024/ENU/?guid=GUID-7B299FE2-67FA-4BF9-B583-4F98A28341D7)

2D Datum Extents 可传播到相似的平行视图，但传播前要确认视图方向、Scope Box 和 3D 范围一致。[Autodesk：Propagate 2D Datum Extents](https://help.autodesk.com/view/RVT/2024/ENU/?guid=GUID-74EB2807-8377-4A24-A2B0-7C01163078CC)
### 2.2 命名规则

- 主轴避免 `Grid 1`、`Grid 2` 之类默认名残留。
- 数字和字母不要在同一方向混用，除非企业标准明确规定。
- 局部插轴采用可排序规则，如 `3.1`、`3.2` 或 `3A`，不要临时写 `X1`。
- 链接专业若已有轴网，宿主模型只复制/监控真正需要发布的共享轴网。
- 轴网名称改变是跨图纸变更；先查标签、视图和链接监控影响。
- 同名轴网在同一模型中必须能唯一解释，不靠视图隐藏区分。
### 2.3 维护规则

- 轴网的 3D 范围用于全局存在性，2D 范围只用于视图可读性。
- 需要多视图一致时改 3D 范围或 Scope Box；单图避让标注才改 2D 端头。
- 不锁所有轴网交点；只锁真正不可变的主控制关系。
- 不把轴网放进普通模型组。
- 不用工作集隐藏错位轴网；先修坐标或 Scope Box。
- 轴网被移动后，立即检查柱、墙、幕墙、尺寸和链接监控。
- 删除轴网前先用 Reveal Constraints 和相关视图查依赖。
### 2.4 轴网 QA

- 轴号连续且排序符合阅读方向。
- 所有主柱/核心筒能解释与轴网的关系。
- 立面与剖面能看到需要的轴网，不出现无意义跨翼轴线。
- 轴端符号不压尺寸、视图标题或裁剪边界。
- 斜轴角度来自明确基准，不由屏幕捕捉误差形成。
- 链接模型轴网没有与宿主重复显示。
- 传播范围后没有把局部 2D 例外覆盖掉。
## 3. 标高系统化建立与维护
### 3.1 建立顺序

1. 从批准剖面建立标高表：名称、高程、用途、是否 Building Story、是否生成平面。
2. 先建 ±0.000、主要楼层、屋面和场地控制标高。
3. 再建结构板面、吊顶、机房、女儿墙等辅助标高。
4. 只为需要独立模型/视图控制的高度建 Level；普通窗台、门头不滥建 Level。
5. 统一标高命名，例如 `L01_首层_FFL`、`L01_结构板面_SSL`。
6. 在总控立面检查高程和上下顺序。
7. 生成所需平面后立即套用 View Template 和浏览器分类字段。
8. 将标高纳入合适 Scope Box，整理 2D 端头。
9. 创建楼梯、核心筒和板洞前，先冻结主要层高。
10. 导出关键剖面核对总高、净高、板厚和屋顶关系。
### 3.2 标高分类

- **楼层标高**：承载 Floor Plan、Room、墙顶底、楼板等主要关系。
- **结构标高**：结构模型责任层，必要时与建筑完成面分开。
- **辅助标高**：屋脊、檐口、女儿墙、设备层等明确控制高度。
- **注释高程**：只需标注时优先用 Spot Elevation，不创建无语义 Level。
- **链接标高**：结构/机电模型中的标高不应全部复制进建筑宿主。
### 3.3 改层高协议

1. 保存可回退版本并记录变更来源。
2. 列出直接受影响元素：墙、柱、板、楼梯、栏杆、幕墙、竖井、房间。
3. 列出间接受影响成果：平面、剖面、立面、标高标注、面积表、Sheet。
4. 在一个测试副本或典型楼层先移动标高。
5. 处理约束警告，不盲目点“解除约束”。
6. 检查顶部约束、未连接高度、偏移和附着关系。
7. 检查楼梯总高、踏步数、平台、净高和板洞。
8. 检查链接模型、Copy/Monitor 和共享坐标未被误改。
9. 复查代表平面、剖面、立面、三维和 Schedule。
10. 重新导出 PDF，并把旧版标记为过期。
### 3.4 标高禁区

- 不用移动全部模型来“修”一个标高数字。
- 不创建重名 Level 再用视图名区分。
- 不把完成面、结构面和吊顶面混成一个模糊 `Level 1`。
- 不删除已承载视图和元素的标高后再补一个相同名字。
- 不用实例 Z 偏移长期补偿错误基准。
- 不在链接模型各自随意改零点；坐标和标高变更要走协调流程。
## 4. Project Browser、工作集与阶段化的职责分离
### 4.1 Project Browser 组织器

浏览器组织用于“找到成果”，不用于控制模型可见性。建议用可过滤的视图/图纸参数组织，而不是只依赖名称前缀。

推荐字段：

- `专业`：A/S/M/E/P/综合。
- `用途`：工作、协调、QA、发布、可视化。
- `视图类型`：总图、平面、天花、立面、剖面、三维、明细。
- `区域`：塔楼、裙房、地下、场地。
- `阶段`：现状、拆除、新建、未来。
- `发布状态`：WIP、Shared、Published、Archived。
- `图纸包`：方案、报审、竞赛、课程提交。

Project Browser 可按视图和图纸属性分组、排序和过滤；浏览器组织还可用于导出/打印顺序。[Autodesk：Managing Views](https://help.autodesk.com/cloudhelp/2016/ENU/Revit-DocumentPresent/files/GUID-73BDFC53-DDF5-4426-AFF9-FEE5C83BE9F6.htm) [Autodesk：Edit Print Order](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-DocumentPresent/files/GUID-95C483DA-84FF-47D8-84B2-30718E8183B6.htm)
### 4.2 工作集的正确职责

工作集用于多人协作、按模型块加载/卸载和控制内存，不应成为日常图形表达的主工具。

- 默认采用元素借用；不要让成员长期把整个工作集设为 Editable。
- 建议保留 `Shared Levels and Grids`。
- 大型链接可放独立工作集，以便关闭/卸载。
- 真正可独立加载的区域或系统才考虑独立工作集。
- 不按每层、每个人、每种构件机械建大量工作集。
- 视图可见性优先由 View Template、Category、Filter、Phase 和 Link Display 控制。
- 关闭无关工作集可释放 RAM；与只在 VG 中隐藏相比，它作用于加载层。

Autodesk 建议用户在本地副本工作、依赖元素借用、频繁同步并释放借用；也建议在内存密集的打印/导出前关闭不需要的工作集。[Autodesk：Best Practices: Working on a Team Project](https://help.autodesk.com/cloudhelp/2025/ENU/Revit-Collaborate/files/GUID-80D390B3-D751-4703-BC79-1A66497C1928.htm)
### 4.3 阶段化的正确职责

- Phase 表示时间状态，不是工作分工。
- 每个元素有 Phase Created；可拆除元素还有 Phase Demolished。
- View 的 Phase 与 Phase Filter 决定现状、拆除、新建、临时等显示。
- 同一真实阶段不要为不同图纸重复建多个近义 Phase。
- 改造模型先定义阶段矩阵，再批量放置元素。
- 房间、面积、门窗和明细表都要检查阶段过滤。
- Phase Filter 进入 View Template，避免同类图阶段表达漂移。
- 不用工作集、设计选项或 Comments 字段冒充时间阶段。
### 4.4 三者选择速查

| 需求 | 使用 | 不使用 |
| --- | --- | --- |
| 快速找到发布平面 | Browser Organization | Workset |
| 多人编辑同一模型 | Worksharing + Borrowing | Phase |
| 关闭大型外部链接以释放 RAM | Link Workset / Unload For Me | Hide in View |
| 显示现状、拆除、新建 | Phase + Phase Filter | Workset |
| 同类视图统一图形 | View Template + Filter | Browser Organization |
| 不同设计方案比选 | Design Options | Phase |
## 5. 大模型性能优化
### 5.1 先测后改

记录基线：

- 文件打开时间。
- 典型平面首次打开时间。
- 典型 3D 旋转/缩放响应。
- Synchronize with Central 时间。
- 代表 Sheet PDF 导出时间。
- 文件大小、链接数量、警告数量、族类型数量。
- 当前打开工作集、视图和链接状态。

优化后用同一机器、同一模型版本、同一代表视图复测；否则无法判断收益来自哪里。
### 5.2 高收益顺序

1. 关闭不需要的视图，避免同时更新大量图形窗口。
2. 在工作视图使用 Coarse/Medium、简化模板和裁剪区域。
3. 关闭不需要的链接工作集或使用 `Unload For Me`。
4. 减少不必要的导入 CAD、点云、图像和高面数 entourage。
5. 替换过重厂家族，删除不可见小五金和深层嵌套。
6. 减少不必要的锁定、阵列、公式和跨模型约束。
7. 清理不再使用的工作视图、测试族和导入类型。
8. 检查高频警告、重复实例、房间边界和宿主异常。
9. 在维护窗口执行 Audit、Purge/Compact，并保留备份。
10. 必要时按专业、建筑体量或区域拆分模型。

Autodesk 建议减少不必要的几何、视图和元素，并单独管理复杂视图、链接、工作集和工作共享性能。[Autodesk：Performance Optimization for Revit Models](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-Customize/files/GUID-269DCB99-AFA2-4D3F-8666-10E30C7415B6.htm)
### 5.3 族性能

- 族只建目标比例和视图真正可见的几何。
- 粗略/中等/精细可见性分层。
- 重复纹理用材质，不用密集几何刻纹。
- 2D 符号表达优先于不可见三维五金。
- 控制嵌套层数和共享嵌套数量。
- 控制族内 Array 的最大数量。
- 删除导入网格、无用连接器和重复材质。
- 对厂家族做三种尺寸 flex、文件大小和项目加载测试。
- 类型目录用于按需加载大量类型，不让项目一次吞下全部组合。
### 5.4 视图性能

- 工作视图与发布视图分开。
- 复杂阴影、透明度、景深和高细节只放在必要视图。
- Scope Box、Crop 和 Section Box 限制可见几何。
- 复杂链接显示使用 By Linked View 或受控 Custom，避免每视图临时调整。
- 未放图纸的协调视图也要有轻量模板。
- 3D 总览不同时显示所有专业、点云和高精度家具。
- 导出前关闭不需要的链接/工作集，而不是只把它们变透明。
### 5.5 Audit、Compact 与 Purge

- Audit 用于扫描、检测和修复损坏元素，不是一般性能按钮。
- Autodesk 建议定期 Audit；快速变化的模型可更频繁，但应在可中断的维护窗口执行。
- 工作共享模型 Audit 前让所有用户退出，选择中心模型并保存可回退副本。
- Compact 会重写文件并清理过时部分，耗时更长；不要每次同步都勾选。
- Purge Unused 分批执行，先审查将删除的类型、材质和资产。
- 任何清理后都要重开模型、检查链接、代表视图和 Sheet。

[Autodesk：Audit a Model](https://help.autodesk.com/cloudhelp/2022/ENU/Revit-GetStarted/files/GUID-5A8746C7-0AC9-41EE-BA21-37A386F2EEA2.htm) 明确说明 Audit 可能耗时且不逐项报告修复元素，因此必须保留审计版备份。
## 6. 链接文件与协作
### 6.1 链接而不是导入

- 跨专业、跨建筑、场地和顾问模型优先 Link Revit。
- CAD 底图优先 Link CAD，确认单位、定位、图层和更新责任。
- 不把顾问模型复制粘贴进宿主，避免失去版本和责任边界。
- 链接命名包含专业、区域、来源和版本。
- 维护 Link Register：文件名、路径、版本、坐标方式、责任人、刷新日期。
- 每次 Reload 后检查位置、标高、轴网、关键开洞和链接状态。
### 6.2 Overlay 与 Attachment

- `Overlay`：宿主再被链接到上级模型时，不继续带出该嵌套链接；通常用于专业协作。
- `Attachment`：宿主被链接时继续携带嵌套链接；只在上级模型确需看到时采用。
- 默认从 Overlay 开始，避免链接链条重复和循环。
- 使用 Attachment 前画清链接拓扑，确认不会在联合模型中重复加载。

Manage Links 会显示 Loaded、Not Loaded、Not Found、In Closed Workset、Reference Type、共享位置和路径等状态；发布前应逐项核对。[Autodesk：Manage Links Dialog](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-Collaborate/files/GUID-06B93886-3D55-4967-ABE2-4B6B262663CD.htm)
### 6.3 协作节奏

- 每位成员从最新中心模型建立本地模型。
- 开工先 Reload Latest，理解他人变更。
- 小批次完成后同步，默认释放借用元素。
- 同步注释写明区域和动作，不写“update”。
- 大批量改类型、移动轴网、改坐标前先广播。
- 打印、导出和长计算前关闭不需要的工作集和链接。
- 不在 Revit 模态对话框停留后让他人等待同步。
- 中心模型维护安排在团队可中断窗口。
### 6.4 Copy/Monitor 边界

- 只监控真正需要协调的标高、轴网、柱和其他关键对象。
- 不把所有顾问元素复制/监控进宿主。
- 监控警告必须有责任人和处理期限。
- 接受变更前确认它来自协调决定，不机械接受。
- 坐标、标高和轴网变更分开记录，避免一次 Accept 改变多个控制面。
## 7. 参数驱动批量修改、公式与族类型目录
### 7.1 参数治理表

每个关键参数至少定义：

- 显示名称和内部/共享参数身份。
- GUID（若为共享参数）。
- 数据类型与单位。
- 绑定类别。
- 类型参数或实例参数。
- 允许空值、默认值和枚举值。
- 数据所有者和更新方式。
- 是否进入 Tag、Schedule、Filter、导出。
- 旧参数迁移规则。
### 7.2 类型、实例与共享参数

- 同一类型必须一致的尺寸、材质和性能用类型参数。
- 每个实例可变的编号、房间、安装高度和状态用实例参数。
- 跨族、项目、Tag 和 Schedule 共用数据才使用共享参数。
- 不因“以后可能用”而把所有字段做共享参数。
- 不在同一类别创建同名不同 GUID 参数。
- 批量修改前确认目标是类型还是实例；改类型会影响全部实例。
- 先用 Schedule 显示旧值、新值、ElementId 和范围，再执行批量写入。
### 7.3 公式模式

推荐短公式和中间参数：

```text
Clear_Width = Width - 2 * Frame_Width
Panel_Count = if(Width < 2400 mm, 2, 3)
Panel_Width = Clear_Width / Panel_Count
Has_Transom = Height > 2400 mm
```

使用规则：

- 先用自然语言写不变量，再转公式。
- 参数名表达语义和单位，不使用 `A/B/C`。
- 所有除数检查零值，所有长度检查负值，所有 Array 数量设下限。
- 公式只编码确定规则，不补偿错误几何。
- 每加入一条公式就 flex 最小、典型、最大类型。
- 嵌套族参数通过 Associate Family Parameter 明确传递。
- 不用长链公式跨越多个不相关设计决策。
### 7.4 族类型目录 Type Catalog

- 当一个族有大量离散、预定义类型且项目只需少量类型时使用 Type Catalog。
- `.txt` 类型目录与 `.rfa` 同名同目录，列头必须匹配参数和单位类型。
- 类型目录用于“选择性加载类型”，不是运行时计算系统。
- 目录更新后检查旧项目中的已加载类型不会自动同步。
- 目录中只放经过 flex 的组合，不把所有理论排列都输出。
- 版本升级后重新测试加载、单位和公式。
### 7.5 Lookup Table 与 Type Catalog 的区别

- Lookup Table 通过 `size_lookup` 从 CSV 读取值，常用于管件/导管族尺寸逻辑。
- Type Catalog 定义可选择加载的离散 Family Types。
- Autodesk 明确说明：若用表格定义每种类型的唯一值，应创建 Type Catalog；`size_lookup` 主要面向实例参数查值。[Autodesk：About Lookup Tables](https://help.autodesk.com/cloudhelp/2022/ENU/Revit-Customize/files/GUID-91270AEF-225A-49D7-BF84-1F44D1E3E216.htm)
- 外部 CSV/目录是交付依赖；必须随族版本管理。
- 升级或换电脑后检查查找表路径，缺失文件不能靠缓存侥幸通过。
### 7.6 批量修改安全协议

1. 定义目标类别、过滤条件、目标参数和期望计数。
2. 导出/保存修改前 Schedule 或 JSON 快照。
3. 先处理 3—10 个样本。
4. 检查类型/实例归属、只读状态、分组、设计选项和链接边界。
5. 执行批量修改。
6. 用同一过滤条件回查新值和计数。
7. 抽查平面、剖面、三维、Tag、Schedule。
8. 保存新版本，不覆盖最后一个已验证版本。
## 8. 约束与锁定的正确使用
### 8.1 锁什么

- 锁设计不变量，不锁当前画面恰好对齐的所有东西。
- 族中优先锁几何到 Level、Reference Plane、Reference Line。
- 项目中只锁关键轴线、核心筒控制线、不可变退界等主关系。
- 使用标注锁定时保留可见、可理解的控制尺寸。
- 附着墙到屋顶、墙连接等隐含关系也属于约束系统的一部分。

Autodesk 明确建议族几何约束到标高、参照平面或参照线；直接几何对几何的约束在参数变化时可能不可预测。[Autodesk：Constrain Family Geometry](https://help.autodesk.com/cloudhelp/2018/ENU/Revit-Customize/files/GUID-26CE1E00-72C1-49D6-9295-A59F50BAA0EF.htm)
### 8.2 不锁什么

- 不锁临时捕捉边、导入 CAD 边和链接中不稳定几何。
- 不锁所有墙到所有轴网。
- 不用等距 EQ 链强迫真实不等距空间。
- 不把局部例外叠加在全局锁定上。
- 不在不理解警告时点击“Remove Constraints”批量解锁。
- 不用锁定替代正确宿主、类型和标高。
### 8.3 排查顺序

1. Reveal Constraints 查看显式约束。
2. 查临时/永久尺寸、Align Lock 和 EQ。
3. 查 Pin、Group、Array、Design Option。
4. 查墙连接、附着、宿主和 Copy/Monitor。
5. 查工作集可编辑性；约束涉及的可移动元素工作集需要可编辑。
6. 识别真正不变量，删除多余约束。
7. 小范围移动/flex，确认没有静默解除松散约束。

Autodesk 将“避免过约束、移除不需要约束、Reveal Constraints 排错”列为约束工作流的一部分。[Autodesk：Constraints](https://help.autodesk.com/cloudhelp/2019/ENU/Revit-Model/files/GUID-4AD7D371-F757-4BFF-9F3C-8321A77D3A02.htm)
## 9. 图元共享坐标
### 9.1 三个基准点

- **Internal Origin**：Revit 内部几何计算原点；项目几何应保持在其合理邻近范围。
- **Project Base Point**：项目局部坐标和建筑定位参考。
- **Survey Point**：测量/场地坐标参考。
- **Shared Coordinates**：不同模型对同一真实位置和方向的共同描述，不是第四个可随意拖动的点。
### 9.2 单一真源

- 选定一个坐标主文件，通常为场地/测量或经批准的建筑总控模型。
- 其他模型只从这一真源 Acquire 或由真源 Publish。
- 不从多个文件依次 Acquire；会形成互相矛盾的坐标历史。
- Autodesk 官方提示应只从一个文件派生共享坐标。[Autodesk：About Shared Coordinates](https://help.autodesk.com/cloudhelp/2024/CHS/Revit-Collaborate/files/GUID-B82147D6-7EAB-48AB-B0C3-3B160E2DCD17.htm)
### 9.3 建立流程

1. 确认测量单位、坐标系、北向和基准高程。
2. 在坐标主文件建立真实场地基准。
3. 将建筑模型以 Origin to Origin 或明确方式初次链接。
4. 在主文件中移动/旋转链接到批准位置，不移动建筑内部几何凑坐标。
5. 选择 Acquire Coordinates 或 Publish Coordinates 的责任方向。
6. 保存链接共享位置，并记录 Named Position。
7. 在各模型用 By Shared Coordinates 重载验证。
8. 用三个以上控制点核对东、北、高程和角度。
9. 用 Spot Coordinate、Spot Elevation、True North 交叉验证。
10. 冻结坐标并发布坐标报告。
### 9.4 链接定位选择

- `Auto - Origin to Origin`：初次技术核对或模型原点已协调。
- `Auto - Center to Center`：只用于临时查看，不作为正式坐标方案。
- `Auto - By Shared Coordinates`：共享坐标已建立并验证后的正式重载。
- `Manual`：建立初始关系时可用，但随后必须转为可复现共享定位。
- 不用屏幕目测把模型拖到“差不多重合”。
### 9.5 坐标变更协议

- 变更前冻结所有专业发布版本。
- 由坐标责任人发布变更说明：平移、旋转、高程、原因、控制点。
- 在副本验证所有链接 By Shared Coordinates。
- 逐模型核对 Internal/Project/Survey 三类基准。
- 检查场地、总平、结构、机电、IFC/DWG/FBX 导出影响。
- 变更后重新生成坐标报告和联合模型截图。
- 禁止每个专业独立修正后再“对齐截图”。
### 9.6 坐标交付卡

- 坐标主文件及版本。
- Revit 版本。
- Project Base Point 东/北/高程/角度。
- Survey Point 东/北/高程。
- Shared Site/Named Position 名称。
- True North 与 Project North 关系。
- 各链接定位方式和状态。
- 控制点坐标与验证截图。
- 导出格式的坐标约定。
- 坐标冻结日期、责任人和变更记录。
## 10. 变更与交付检查清单
### 10.1 基准

- 轴网和标高命名无默认残留。
- 主轴、局部轴、斜轴命名可排序。
- 标高表与关键剖面一致。
- Scope Box 责任清楚。
- 3D/2D Datum Extents 没有混乱。
- 改层高后楼梯、板洞、墙顶均已复查。
### 10.2 视图与协作

- Browser 可区分工作、QA、发布和归档。
- 所有发布视图有正确模板。
- Workset 数量可解释，没有按人机械拆分。
- Phase/Phase Filter 与改造图一致。
- 链接状态、路径、版本和 Reference Type 已核对。
- 本地模型来自当前中心模型。
- 所有借用在发布前释放。
### 10.3 性能

- 有代表视图性能基线和复测结果。
- 不需要的链接与工作集已关闭。
- 高面数族和导入对象已处理。
- 发布视图没有无意义高细节/透明度。
- Audit、Purge、Compact 有备份和维护记录。
- 清理后完成重开、同步、导出测试。
### 10.4 参数与约束

- 共享参数 GUID 和归属可追溯。
- 批量写参前后计数一致。
- Type Catalog/Lookup CSV 随族交付。
- 族已 flex 最小、典型、最大类型。
- 没有大量无法解释的锁定。
- Reveal Constraints 检查过关键区域。
### 10.5 坐标

- 只有一个坐标真源。
- 所有正式链接以可复现方式定位。
- By Shared Coordinates 重载通过。
- 三个以上控制点通过。
- True North、Project North 和高程已记录。
- Visualization/IFC/DWG/FBX 接收方拿到坐标卡。
## 11. 来源

- [Autodesk Help：Performance Optimization for Revit Models](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-Customize/files/GUID-269DCB99-AFA2-4D3F-8666-10E30C7415B6.htm)
- [Autodesk Help：Best Practices: Working on a Team Project](https://help.autodesk.com/cloudhelp/2025/ENU/Revit-Collaborate/files/GUID-80D390B3-D751-4703-BC79-1A66497C1928.htm)
- [Autodesk Help：Manage Links Dialog](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-Collaborate/files/GUID-06B93886-3D55-4967-ABE2-4B6B262663CD.htm)
- [Autodesk Help：About Shared Coordinates](https://help.autodesk.com/cloudhelp/2024/CHS/Revit-Collaborate/files/GUID-B82147D6-7EAB-48AB-B0C3-3B160E2DCD17.htm)
- [Autodesk Help：Propagate 2D Datum Extents](https://help.autodesk.com/view/RVT/2024/ENU/?guid=GUID-74EB2807-8377-4A24-A2B0-7C01163078CC)
- [Autodesk Help：Control Visibility of Datums Using Scope Boxes](https://help.autodesk.com/view/RVT/2025/ENU/?guid=GUID-57084384-4D1E-498A-A6F9-CE5C7260A088)
- [Autodesk Help：Audit a Model](https://help.autodesk.com/cloudhelp/2022/ENU/Revit-GetStarted/files/GUID-5A8746C7-0AC9-41EE-BA21-37A386F2EEA2.htm)
- [Autodesk Help：Constraints](https://help.autodesk.com/cloudhelp/2019/ENU/Revit-Model/files/GUID-4AD7D371-F757-4BFF-9F3C-8321A77D3A02.htm)
- [Autodesk Help：Constrain Family Geometry](https://help.autodesk.com/cloudhelp/2018/ENU/Revit-Customize/files/GUID-26CE1E00-72C1-49D6-9295-A59F50BAA0EF.htm)
- [Autodesk Help：About Lookup Tables](https://help.autodesk.com/cloudhelp/2022/ENU/Revit-Customize/files/GUID-91270AEF-225A-49D7-BF84-1F44D1E3E216.htm)
- [Autodesk University：The Ultimate BIM Workflow Guide for a Design-Build Project](https://www.autodesk.com/autodesk-university/class/Ultimate-BIM-Workflow-Guide-Design-Build-Project-2017)

