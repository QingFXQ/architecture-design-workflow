# RV-04｜单位、事务与超时：只读当前任务范围

等级：reference-reviewed；修正来源为Autodesk文档及图书馆项目采用说明。

直接读[API现场笔记](../../../skills/revit-model-hardening/references/revit-api-field-notes.md)。不再复制旧的Start前失败选项、同签名Ft(double)、IList警告当WarningSet等示例。

- 米／毫米／英尺明确；专用工具单位核当前schema。
- 包装器auto与显式事务不能冲突；显式Start后设失败选项，Committed方为提交。
- SetForcedModalHandling(false)不是消除警告；Pending不算完成，不盲Save或继续写。
- 初次未知方法小样；同版复用只做相关回读。批量依据当前性能，不机械限3或20。
- 写入超时以当前界面／日志／进程判断，读探活通不证明前次成功，不通不唯一证明模态。
- 保持单写入者，不自动强杀／关闭；端口取当前配置。
