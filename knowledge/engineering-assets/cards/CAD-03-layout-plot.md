# CAD-03｜布局、视口与纸面发布

等级：reference-reviewed；本轮不声称AutoCAD打印机／CTB／STB实测。

## 实际步骤

1. 先核模型真实单位与纸面单位。模型mm、纸面mm的1:100视口，比例为纸面／模型=0.01；模型用米时不能照抄这个比值。
2. 在布局组织图框、视口与必要纸面标注。视口边框用不打印层；需要时锁定显示比例，调整视口边界不能代替改比例。
3. 核当前工程CTB／STB、打印样式、线宽／线型、打印范围、纸幅方向及字体资源。尊重已有体系，不一律转换或全图归层。
4. 图缺件时查VP冻结、注释比例、打印开关、裁剪、块内部层和外参，不只查模型空间可见。
5. PDF按实际比例发布；Fit to Paper会改变比例，不得仍标原比例。布局整体1:1与视口比例分别检查。
6. 渲染查看PDF，量已知尺寸、核字体和图名、看线宽与缺件，再批量发布。文件非空或打印命令返回成功不算验收。

[Autodesk布局视口](https://help.autodesk.com/cloudhelp/2022/ENU/AutoCAD-Core/files/GUID-2B5D404A-DCAB-4AF6-A5C1-51593B38F519.htm)；
[Plot scale](https://help.autodesk.com/cloudhelp/2024/ENU/AutoCAD-Core/files/GUID-89604826-0B55-4994-8214-1CA93FA66985.htm)。

CAD样例的离线PDF用于检查DXF内容，不验证本机PC3、CTB、字体或AutoCAD原生发布结果。
