# CAD-02｜参数化墙线与重复块

等级：方法reference-reviewed；配套样例以实际[验证记录](../examples/cad-parametric/VERIFICATION.json)为准，离线测试不等于AutoCAD实机。

读[可运行小样](../examples/cad-parametric/README.md)，参数JSON生成12×8m简化平面：墙线在门窗处真实断开、20窗共享一个块定义、柱网及尺寸。不是用白色矩形盖住墙，也不是发20次MCP调用。

## 复用方法

- 同规格窗用共享块＋INSERT；规格不同分定义。块基点、单位、转角和缩放显式处理，内部图层／ByLayer／ByBlock规则要符合预期，不把所有对象一键归零。
- 参数更新在任务拥有的对象／文件范围内；已有用户图纸不得整图清空。样例采用专属目录的确定性重新生成，仅声称生成文件层面幂等。
- 标注用真实DIMENSION并生成所需表示，不用手打数字冒充关联尺寸；同时检查定义点、测量值与显示值。
- 对门窗墙线的空隙查几何区间，不能只数窗块。核数量、坐标、宽度、图层、定义复用，再渲染看图。
- 模型绘图按真实尺寸；最终图名／字体／比例应用项目预设，不把样例英文说明当正式交付。

来源：[ezdxf Blocks](https://ezdxf.readthedocs.io/en/stable/tutorials/blocks.html)、[Linear Dimensions](https://ezdxf.readthedocs.io/en/stable/tutorials/linear_dimension.html)。DXF不是DWG；实际编辑／发布DWG另需宿主验证。
