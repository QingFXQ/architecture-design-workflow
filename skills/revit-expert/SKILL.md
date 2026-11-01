---
name: revit-expert
description: 把已确定尺寸与范围的建筑设计制作为可维护、可出图的Revit工程，按任务处理原生构件、族、宿主、约束、视图与导出；也支持明确范围的方案小样验证。
---

# Revit工程制作

采用[制图生产流程](../../workflows/DRAWING_PRODUCTION_WORKFLOW.md)。当前主控可直接执行，不以角色交接或四个人工Gate为开工条件；已授权范围内连续工作，重要冻结项仍有效。

## 按任务读方法

先用[工程资产入口](../../workflows/ENGINEERING_ASSET_WORKFLOW.md)定位当前问题，再按需读：

- 对象类别、族／组／Array、墙板门窗梯与模型深度：[工程方法资料](references/engineering-manual.md)的2—5节。
- 需要现成工程、RTE样板、RFA族或RFT族样板：查[原生数据库](../../knowledge/engineering-assets/revit-library/README.md)，先按当前Revit版本筛，再看类别／类型与预览；复制工作副本及同名类型目录后核一个实例。原件不升级保存，海报与待授权获奖模型不能当成已取得的原生资产。
- 模板、标注、图纸、导出及常见失败：同资料6—9节；其他详细源在[research/revit-materials](../../research/revit-materials/01-native-components.md)。
- 单位、事务、Pending、模态及恢复：[revit-model-hardening](../revit-model-hardening/SKILL.md)和[API现场笔记](../revit-model-hardening/references/revit-api-field-notes.md)。
- 结构切面／非承重墙、跨层筛选、剖切与图面：[图形层级](../revit-model-hardening/references/graphic-hierarchy-revit.md)与[drawing-standard](../drawing-standard/SKILL.md)。

不要默认把这份900行资料全文加载。先理解本任务类别／宿主／约束／单位，再选界面、专用工具或API；API可以创建原生对象，不等同于纯几何替代。

## 实际制作

先核当前文件与恢复点，做一个代表区／视图小样并实际导出看图，成立后再扩到全楼。重复构件共享族／组／参数，重跑按稳定标识更新，不叠加。保留正确语义；门真切墙、洞口真切板、梯段／平台和楼层高差正确。

同一模型一个写入者。事务与失败处理按已验证接口配置；错误回滚，Pending不当提交，超时先查状态不重放。不统一吞掉警告、不凭“没有Room／防火参数”擅判墙可拆。

重要变更另行回读关键对象，并看完整相关平面、剖面与三维／PDF；技术成功不是设计成功。按受影响范围调用[复核](../revit-final-check/SKILL.md)，未变化项复用证据。

用户要课程方案图就不自动加施工图深度。功能、结构、流线与可读性优先；家具整齐、不穿墙堵路即可，不擅自升级成逐件极限优化。

## 输出

保存当前工程、对应图件与简短未完成项。可随时导出明确版本给Blender／SU继续设计；发生建筑变化时同步受影响图纸，最终发布使用同版已核成果。新的工程经验回写原条目和示例，不重复建冲突skill。
