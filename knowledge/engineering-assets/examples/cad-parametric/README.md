# CAD参数化工程小样

原创建筑局部教学资产，不是图书馆方案，也不是完整施工图模板。长度mm，默认12×8m；含墙体实际断口、20个共享窗块实例、单扇门开启线、12柱与轴网、两条真实尺寸及分层线宽。墙体不填黑，剖切柱实心。

## 使用

在仓库根运行（依赖隔离在uv缓存，不安装AutoCAD或修改客户端）：

```powershell
uv run --with ezdxf==1.4.5 --with pymupdf==2.0 --with pillow==11.3.0 python knowledge/engineering-assets/examples/cad-parametric/generate.py --render
```

只生成DXF无需PyMuPDF；可用已有兼容环境运行。首次获取第三方依赖需网络，后续可复用本地缓存。查阅依赖自身许可，本仓库不再分发第三方包。

改params.json可改宽深、墙厚、柱截面、窗宽和门宽。也可通过--params指定副本、--out-dir指定专属输出目录。输出文件已存在却没有本样例owner标识时拒绝覆盖；不会读取或修改任何用户DWG。

out/保存实际可编辑DXF、窗坐标CSV和离线PDF／PNG。支持重复生成同一文件，不重复追加对象；**这不是在AutoCAD中原位改图的幂等验收**。

## 已核与未核

[VERIFICATION.json](VERIFICATION.json)记录当前实际验证，不能因本文件存在就说通过。测试包含真实读回、20实例共用定义、墙洞没有实墙遮挡、尺寸、零audit修复／错误、重跑与参数改变。

PNG／PDF由DXF渲染产生，可用于看本文件内容；字体、线型及尺寸渲染可能与AutoCAD不同。没有AutoCAD宿主、DWG保存或原生发布验收，不冒充DWT／DWG／CTB。样例英文说明可避免缺字体，不是正式项目的字体模板。

重复执行／参数更新测试入口：在同一依赖环境运行`python tools/engineering_assets/verify_cad_sample.py`，测试结果写回本目录VERIFICATION.json，测试中间件只放仓库忽略的`tools/engineering_assets/local/`。有意不清空用户目录、不修改DWG。

本次实际看图发现并修正两处示例问题：尺寸样式的显示倍率需显式为1；绘图后端导出后会改变内部记录，因此PNG从生成的PDF栅格化，避免二次变换缩成小黑点。它们属于本例／依赖版本的实测经验，不推广成所有渲染器的规则。

[ezdxf块](https://ezdxf.readthedocs.io/en/stable/tutorials/blocks.html)、
[尺寸表示](https://ezdxf.readthedocs.io/en/stable/tutorials/linear_dimension.html)、
[绘图后端](https://ezdxf.readthedocs.io/en/stable/addons/drawing.html)。
