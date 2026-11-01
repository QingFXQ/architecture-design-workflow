# 公开版验证范围

2026-11-01 在独立公开副本完成：

- 工程方法索引：9 条，15 个路由场景通过。
- 排版参考索引：6 条，结构与文件指向检查通过；排除不可公开的对话来源 PC-07。
- 从 Markdown 重建 128 个案例的文字索引，离线自然语言检索实际返回结果。
- 文字检索及明确回退行为：5 项测试通过。
- 交付清单与 PDF 检查：9 项测试通过，覆盖过期图、遗漏地下层、比例、纸幅、空文件与缩小文字等。
- Revit 连接脚本的只读调用约定：2 项离线测试通过。
- Python 语法检查通过；Markdown 相对链接、入口文件与公开包边界已核。

这里的验证不连接或修改 Revit、Blender、SketchUp、AutoCAD，也不代表这些软件在其他机器上已部署。未在公开包上逐件验收原生资产，未对旧案例事实和历史基准逐项重新研究。

GitHub Actions 使用 Python 标准库运行核心离线检查，不下载模型。PDF 相关测试需使用者按任务安装 PyMuPDF 后运行：

```bash
python tools/validate_public.py
python -m unittest discover -s tools/delivery -p test_delivery.py -v
```

GitHub 上实际运行结果以 Actions 页面为准；本文件不预先宣称远端检查通过。
