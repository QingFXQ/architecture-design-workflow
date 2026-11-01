# 成套交付检查

只读辅助检查，不改模型／图纸，不批准设计，不评价美感。不要求启动新服务。

```powershell
python tools/delivery/check_delivery.py path/to/DELIVERY.json
python tools/delivery/check_delivery.py path/to/DELIVERY.json --json
python -m unittest discover -s tools/delivery -p "test_*.py"
```

从[清单模板](../../templates/DELIVERY_TEMPLATE.json)取用，填真实文件和当前修订。模板中的路径是待制作占位，不是已经交付的成果，直接检查应报告缺件。

## 检查范围

- 必交图有没有登记、实际存在、放进最终板面。
- 场地／设计／立面等来源修订是否过期，过期上游是否污染下游图件。
- 登记纸幅、方向、张数和实际PDF页数、纸幅是否相符。
- 图件是否出纸面；已登记净几何跨度、最终比例和版面宽度是否互相矛盾。
- 按登记像素与宽度估算有效PPI；最终图内字高、PDF可提取文字的小字及字体嵌入风险。
- 是否已记录实际看整图、整版和局部。未记录只提示，不冒充检查完成。

核心文件／版本／几何关系检查只用标准库。PDF实测需已有PyMuPDF；缺少时明确报告未检查，不偷偷安装。字体检查无法证明转曲字、整页光栅或视觉替换效果可靠，仍需渲染看图。每张独立正式图的required_font_family只用于图纸，不限制展板主标题使用其他字体。

## 字段要点

`scale`写最终真实比例分母，例如300。`model_width_m`与placement的`width_mm`必须同时指对应的净建筑跨度；带标注边的整张图片宽度不能冒充净几何宽。无法可靠量取时省略model_width_m，并另做实际量尺检查，不能填假数让程序通过。

`source_revisions`按范围填写，例如design／facade／site；纯配景更改不需要使所有平面过期。`depends_on`用于分析／效果图等下游关系。指标真假、路线完整、构图好坏与图纸符合任务书的建筑内容，均不由该工具推断。

默认有实质错误返回1；文件／JSON不可读返回2。提示不会自动变成阻断；只有主动选择--strict才将提示也视为失败。正常绘图任务不新增人工审批。

运行记录见[本轮修订](../../docs/WORKFLOW_REVISION_20261029.md)。测试使用临时新文件，不操作用户原PDF或设计模型。
