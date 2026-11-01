# Revit API现场笔记：可复用方法与环境边界

2026-10-28修订。来源含图书馆项目经验与官方API参考；**不是所有片段均已在当前宿主编译**。先核Revit版本、动态编译器及MCP包装器，再用隔离小样验证。项目ElementId、端口和性能阈值不得跨项目照搬。

## 1. 连接与诊断

读取当前客户端和插件配置，核进程、活动文档及当前日志。过去本机8080为MCP、8088为另一服务，只是历史环境事实。

服务开关、持久化和UI自动化能力依插件／版本及当前权限决定，不普遍宣称只能人工点。请求人工动作应有当次界面或日志证据。不要对用户进程做自动关闭或强杀。

超时 → 一次有界只读探活 → 查当前进程/UI/日志/事务 → 核前次目标残留。探活通只说明当前可响应；不通可能是忙碌、队列、模态、连接或其他原因。不能连续重发写入。

## 2. 单位与基准

API内部长度使用英尺，面积／体积按其维度转换；专用MCP工具输入单位以当前schema为准。

```csharp
double MmToFt(double mm) => mm / 304.8;
double MToFt(double m) => m / 0.3048;
double FtToM(double ft) => ft * 0.3048;
double SqFtToSqM(double area) => area * 0.09290304;
```

这是动态代码体局部函数示意；若编译器不支持局部函数，改为封装允许的helper或显式表达式，不将两种换算写成同签名Ft(double)。

Room的UV也是内部长度；世界坐标和标高必须来自已核基准。LevelId只是线索，结合约束／偏移／实体Z范围判断跨层。

## 3. 事务与失败处理

1. 先确认由包装器还是代码开事务。已有顶层事务时不要再开另一个。
2. 显式Transaction.Start()后确认Started。
3. **Start后**获取并设置FailureHandlingOptions。预处理器应针对当前事务，不无故注册全局FailuresProcessing。
4. 使用已验证的失败预处理器记录FailureDefinitionId／描述／目标。未知警告或错误可保守回滚；仅明确允许且理解的警告才针对性处理，不全删警告。
5. 执行单一目的写入，Commit后核状态。Committed方可回读确认；RolledBack则记录未写入；Pending需等待失败处理结束，不接着写、不冒充成功。
6. 异常后的回滚也要核结果。不要把未完成事务留给下一次调用。
7. Commit后重取目标，查询受影响参数／边界及视图；不以写入时返回值替代实际结果。

SetForcedModalHandling(false)的含义是允许非模态处理，可能产生Pending；SetClearAfterRollback(true)是回滚后清理失败消息，不能拿来证明写入成功。

以上是事务合同而非未经验证的“防弹代码”。当前包装器无法装配预处理器时，先验证可用执行方式，不直接复制带占位类的片段到真实模型。

## 4. 批量与编译

- 小样确认后按耗时、载荷、失败影响调批量；过去3构件、20房间只是特定环境保守经验。
- 房间边界先按本层／本任务ID筛选、限制数量，再调用GetBoundarySegments；不能文档说限20但代码仍全量扫描。
- 数组、可空返回、方法重载、ElementId访问方式依编译器／API版本核查，不把某次编译失败泛化成C#语法规则。
- 常见点：FamilySymbol.Activate()而非给IsActive赋值；再按需要Regenerate。宿主族需用匹配其放置类型的重载。
- 门窗放置成功后查宿主、标高和真实切口；不能只因Host存在或实例有Id就算成立。
- 中文通过UTF-8文件／客户端传输，先做一个与实际字符串相同的探针；不要硬编码错误的“预期长度”。
- Id是当前模型定位手段，不替代稳定逻辑标识与任务范围；不前缀批删全部历史视图。

## 5. 只读片段（Revit 2021动态代码体示意）

调用时不创建事务；按当前包装器提供的document对象执行。IntegerValue适用于此旧版示例，迁移新版需核其ElementId API。

### 标高与当前范围

```csharp
var levels = new FilteredElementCollector(document).OfClass(typeof(Level)).Cast<Level>()
    .Select(x => new { id = x.Id.IntegerValue, name = x.Name, elevationM = x.Elevation * 0.3048 })
    .OrderBy(x => x.elevationM).ToArray();
return new { title = document.Title, path = document.PathName,
    modified = document.IsModified, levels = levels };
```

### 只读指定少量Room边界

```csharp
// parameters[0]为当前任务Room ID逗号列表；parameters[1]为本次允许数量。
// 输入单位不涉及长度；不是全模型审计。
var ids = Convert.ToString(parameters[0]).Split(',')
    .Where(x => !String.IsNullOrWhiteSpace(x)).Select(x => int.Parse(x.Trim())).Distinct().ToList();
int limit = int.Parse(Convert.ToString(parameters[1]));
if (limit < 1 || ids.Count > limit) throw new InvalidOperationException("Bounded room IDs required");
var result = new List<object>();
foreach (int id in ids) {
    var room = document.GetElement(new ElementId(id)) as Autodesk.Revit.DB.Architecture.Room;
    if (room == null) throw new InvalidOperationException("Target is not a Room: " + id);
    var loops = room.GetBoundarySegments(new SpatialElementBoundaryOptions());
    result.Add(new { id = id, name = room.Name, areaM2 = room.Area * 0.09290304,
        loops = loops == null ? 0 : loops.Count });
}
return new { rooms = result };
```

这里不推断墙体内外，不删除零面积房间；边界的真实内环需保留。

### 警告回读

```csharp
var result = document.GetWarnings().Select(x => new {
    code = x.GetFailureDefinitionId().Guid.ToString(),
    message = x.GetDescriptionText(),
    ids = x.GetFailingElements().Select(id => id.IntegerValue).ToArray()
}).ToArray();
return new { warnings = result };
```

返回条数不是质量判断；核本次新增／改变的警告及其意义。不要把IList<FailureMessage>当旧WarningSet使用Size/get_Item。

### 疑似重复墙

先按当前任务目标筛选，再比较曲线、类型、厚度、底顶约束、偏移、阶段和实体范围。取整端点只能筛候选，不能据此自动删除；移除某条墙前核宿主与删除依赖。

## 6. 恢复与保存

Pending／错误模式下不能宣称“无未提交事务”。先恢复状态再独立查构件，不假定超时等于已成功或已回滚。只有软件可安全保存时才保存；错误模式里不盲按保存按钮。

恢复点注明磁盘／内存边界，保护未保存工作。API不可用时不能只靠旧SHA断言无改动，不将强杀当默认修复。

## 7. 依据

- [Autodesk Transaction.Start](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/1146fa87-127d-c432-0f51-79a5eb102031.htm)：Start重置失败处理选项；这是2026文档，旧版实际封装仍需小样核验。
- [Revit 2021 Failure Handling Options](https://help.autodesk.com/cloudhelp/2021/ENU/Revit-API/files/Revit_API_Developers_Guide/Basic_Interaction_with_Revit_Elements/Transactions/Revit_API_Revit_API_Developers_Guide_Basic_Interaction_with_Revit_Elements_Transactions_Failure_Handling_Options_html.html)：非模态可能Pending及事务级预处理。
- [Autodesk Transaction Classes](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-API/files/Revit_API_Developers_Guide/Basic_Interaction_with_Revit_Elements/Transactions/Revit_API_Revit_API_Developers_Guide_Basic_Interaction_with_Revit_Elements_Transactions_Transaction_Classes_html.html)：状态语义。
- 图书馆2026-10项目采用说明与故障记录：项目经验，非通用API规范。本轮只读资料核对，没有启动Revit实机重验。

## 8. 2026-10-30补充：Revit 2021原生平面生产实测

验证范围：第二个图书馆作业 `D:\我的文档\2.rvt`，Revit 2021。首层原生墙门房间、两块楼板、三部首层至二层原生楼梯已实际运行、回读及看导出图；不是全楼建筑验收，也不直接推广到其他Revit版本。上述第7节“只读资料核对”描述2026-10-28的文档修订，本节为后续新证据。

- **楼梯栏杆要同时核参照。** 仅关闭RailingType的TopRailType，若BalusterPattern及起终／转角柱仍以Top Rail作顶部参照，会出现“顶参照低于底参照”、栏杆族不能拉伸等失败。应在独立克隆类型上按设计更新BalusterInfo的BaseReferenceName／TopReferenceName及偏移；本次样板采用Host到Host加正高度。高度是项目参数，不固化为通用阈值。连续扶手仍须另外设计，不能将柱杆生成成功说成完整扶手完成。
- **StairsEditScope异常可能留下模态和编辑状态。** Commit抛异常或Scope.Cancel调用返回不等于UI已退出。不要继续排队Transaction／Save；先查看真实警告和功能区、取消未完成编辑，再用一次有界查询确认无活动事务及构件残留。此次最终三部楼梯在完整失败处理下提交，独立回读均为36踢面、两跑、0→3→6m；最终路径没有DeleteWarning。实际看过楼梯剖面，不把零警告当消防／净空验收。
- **房间面积不证明有完整楼板。** 此次50㎡卫生间样板的净面积正确，但导出图发现它碰到固定模型地坪凹口，随后移动到完整地坪范围并重新核面积。扩展前同时检查房间、宿主洞口和实际楼板／图面。门洞通过回滚删除门前后宿主墙体积差0.42m³核实，之后门已恢复。
- **合并中心线后仍需查实体厚度。** 精度归整和去重不能排除相距小于墙厚的平行墙重叠。本次200mm墙在相距178mm处触发原生重叠警告，已回滚并按固定凹口调整。先查近距离平行段及功能／井道矩形交叠，再建原生墙；不得删警告冒充修复。
- **注释图元不一定有Comments参数。** TextNote、尺寸或详图线不能假定可用ALL_MODEL_INSTANCE_COMMENTS作任务标识；参数为空时应采用ExtensibleStorage或经过验证的稳定ID台账。否则标签函数静默无效，重跑会留下重复文字与尺寸。清理只针对本任务明确拥有的对象，不能全删用户注释。
- **ViewPlan.GenLevel需判空。** 过滤FloorPlan后仍要排除模板并检查GenLevel非空，不能假定所有项目／场地平面均有关联Level。

项目证据入口：第二图书馆目录的`PROJECT.md`、`03_接收检查/首层制作核验.json`、首层平面和B-B楼梯剖面、`04_制作脚本/RevitProduction.cs`。楼板与梯段的布尔检查曾在重合接缝处失败，结论为未确定，未记录为无碰撞。

### 同日续验：多层交通、房间高度与正式平面

下列为同一Revit 2021项目后续宿主实测，证据在第二图书馆`14_五层同版核图`、`15_五层空间剖面`及当前制作脚本；仍不是结构计算或消防合规结论。

- **楼梯梯段的两种标高不要混用。** 本机RevitAPI.xml明确：CreateStraightRun的locationPath.Z取模型绝对标高，而StairsRun.TopElevation相对该楼梯底标高。非零底层的第二跑用`stairsBaseElevation + run1.TopElevation`，不能直接把相对TopElevation当世界Z。原0m首层样板会掩盖此问题；随后9部3.2m上层梯已提交并回读，三层间均20踢面。
- **栏杆柱成功后还要看真实横杆。** 本次在正确Host参照样板上通过NonContinuousRailStructure添加已验证的圆管轮廓横杆，C-C剖面已看到坡道和平台的杆件；独立连续扶手系统与规范仍须另核。室外楼梯顶端也实际增加2m到达平台，不能让最后一级踏步直接撞入口门线。
- **Room上限标高与偏移必须一起设置。** 此样板NewRoom仍保留默认8英尺上限偏移；单设ROOM_UPPER_LEVEL后，下层Room越入上一层，门的FromRoom/ToRoom会错误返回下一层房间，平面净面积仍可全为正。显式设置下偏移0、正确上限Level及上偏移0，再核实际高度、代表门两侧归属。修正后五层消防门均正确关联本层公共厅与本层楼梯间；通高中庭单独采用屋面控制Level为上限。
- **墙不重叠仍可能堵住通道。** 两道200mm墙中心线相距200mm会贴合，零重叠预检不表示之间有可通行走道。本次原消防梯外的相邻房间墙封住连接；按整条公共路径让出走道并重绘，不能靠门箭头或正面积Room验收。
- **读得到的参数不保证能用于视图筛选。** 本机2021以WALL_BASE_CONSTRAINT创建墙类别ParameterFilterElement被宿主拒绝，事务已回滚。应先核可筛选参数，不推广为所有版本的通用能力。本任务正式平面最终按实际墙基标高、门窗Level及柱是否穿过剖切面处理本任务图元的视图可见性，保留完整剖面／三维；不是删除下层构件。衬图已关闭时，层末墙等仍可能在下一层出现半色调投影，应实际看图确认。
- **先检查编译退出码，再加载程序集。** 失败编译后不要继续Revit加载；本机曾在同一路径首次FileNotFound后继续保留失败绑定，改用新的已编译版本路径恢复。输入生成多步命令也须逐步判断退出码，不能让后一步成功掩盖前一步失败。
