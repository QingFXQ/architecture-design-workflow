> 公开版不附带原生资产库。下文数量与验证为历史记录；使用前准备有权使用的文件并设置 `REVIT_ASSET_ROOT` 或 `--root`，详见 [环境接入](../../docs/SETUP.md)。本机路径仅为示意。

# 原生 Revit 资产工具

实际库与来源见 [原生工程／族数据库](../../knowledge/engineering-assets/revit-library/README.md)。本工具不连接 Revit，不会修改用户当前模型。

本机库：`./local/resources\Revit-Asset-Library`。可用 `REVIT_ASSET_ROOT` 或全局 `--root` 改路径。示例：

```powershell
python tools/revit_assets/library.py --root E:\其他库 search "门" --revit 2021
```

## 依赖

- Python 标准库完成 SQLite、下载、散列、复制、检索及 HTML 索引。
- `olefile==0.47` 提取 Revit 原生容器元数据。本机隔离在库内 `tools/python-libs`；无需全局安装。
- Pillow 生成预览联系表；PyMuPDF 检查参考 PDF 页数。两者本机已有，不为日常检索安装渲染器或嵌入模型。

新机部署示例（仅实际部署时运行，修改文档不触发安装）：

```powershell
$env:TEMP='./local/resources\Temp'
$env:TMP=$env:TEMP
$env:PIP_CACHE_DIR='./local/resources\Cache\pip'
python -m pip install --target ./local/resources\Revit-Asset-Library\tools\python-libs olefile==0.47
```

本机执行器：`python`。资料源路径写在 `knowledge/engineering-assets/revit-library/sources.json`，换机须核实本地安装目录；源不存在就跳过并报告，不伪造已收录。

## 数据与操作

`collect-local` 复制官方安装内容；`collect-web` 只下载登记的公开来源，使用 `.part` 临时文件，核长度和原生文件头后改名；失败有记录，不留下假 RVT。既有下载复用，本地复制按 SHA-256 判断变化。`build` 刷新 SQLite 与 CSV／JSON，不修改原件。

SQLite 表：

- `sources`：来源、权限边界、获取方法。
- `assets`：路径、种类、真实年份、类别与类别依据、文件 SHA-256、大小、预览和验证等级。
- `family_types` / `type_parameters`：PartAtom 类型名称、可取得的参数、数值及单位。
- `auxiliary_files`：类型目录，关联同名族，不丢失 TXT。
- `reference_files`：实际取得的参考 PDF、页数和哈希。
- `candidates`：尚未取得原生文件的获奖／赛事线索，与可用资产分开。

`search` 只查原生资产，不返回待申请模型和海报。中文索引使用实际族类别及来源目录别名，非语义 embedding；PartAtom 类别优先，推断会标明。多词按全部匹配，查不到可改短关键词或英文名。参数是源文件可提取信息，不是全量 Revit API 模型数据。

`types --id ...` 查看某族可提取参数；`stage --id ... --dest ... --revit ...` 生成工作副本，带同名类型目录，不覆盖已改副本，不改原件。系统族用项目样板／工程内转移项目标准，不能假造独立 RFA。

`browser` 更新离线 HTML，无服务、无外部 CDN；直接双击打开。`contact-sheets` 生成代表族与全部工程的内嵌预览联系表，供看图选材，不等于宿主验收。

## 本机验收

```powershell
python -m unittest discover -s tools/revit_assets -p 'test_*.py' -v
python tools/engineering_assets/find_asset.py --check --self-test
```

8 个原生资产集成检查覆盖：数据库完整性、真实 RFA 的类别／类型／单位／预览、伪装 HTML 拒绝、新旧版过滤、中文及字面检索、配套目录复制和重跑、工作副本保护、比赛参考与原生文件分离。2026-10-30 实际通过；未在 Revit 内执行批量载入，不能据此宣称整库成图合格。
