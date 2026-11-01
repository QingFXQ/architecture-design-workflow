# RV-02｜门窗切墙、楼梯与房间

等级：reference-reviewed；图书馆门593982等历史记录为project-evidence，不要求跨项目复用ID。

## 相关资产

[门窗／楼梯翻车与修复](../../../research/revit-materials/10-pitfalls.md)、[MCP任务模式](../../../skills/revit-expert/references/revit-mcp-patterns.md)、[事务与单位](../../../skills/revit-model-hardening/references/revit-api-field-notes.md)。

## 门窗

先查当前族的放置类型、宿主、标高、宽高与墙厚。试放后核真实洞口／实体变化及平剖，不能仅有Host和ElementId。不能切墙时先回滚分析，不把不合格实例留给下一批。没有防火性能的临时门可以诚实标记，不靠改名冒充性能。

## 楼梯

从起终标高、总高、踢面数、各跑与平台关系开始；区分踢面和踏面，按真实种子／剖面核最高踏面与楼面。核洞口、板底、逐段净高、门前平台及栏杆。不要以Stairs类别计数0断定没有梯段，也不要只画逐级实体却不核连续交通。细部深度按当前任务，不扩张为结构验算。

## Room

创建前查插入点处现有Room、阶段、上下限及边界，避免同闭合区域重放Room。米／毫米转英尺分别处理；提交完成后重取Room读面积。零面积先查位置与单位再查边界；保留内环，Room净面积不冒充建筑面积。
