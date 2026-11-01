# RV-05：选取真实工程样板与族

需要 RFA、RFT、RTE、RVT 或门窗／家具／结构族时，先查[原生库](../revit-library/README.md)，不要把工程经验 Markdown 当成实际文件。

本机 SQLite：`./local/resources\Revit-Asset-Library\database\revit-assets.sqlite`；原件在同目录上一级的 `originals`。`tools/revit_assets/library.py search "窗" --kind family --revit 2021` 返回真实路径、类别、年份和验证等级；离线浏览页带内嵌预览。先传实际宿主版本，2024 Snowdon 不送到 2021 打开。

选中后用 `types --id ...` 看类型尺寸／单位，`stage --id ... --dest <工作目录> --revit <年份>` 复制工作文件与同名类型目录。RFT 新建族、RTE 新建项目、RVT 学习组织与转移标准，三者不要混同；系统墙板屋顶不要求独立 RFA。

库已核文件容器、版本、SHA-256 和可取得的类别／类型，不等于宿主验收。实际复用先做一个小样：门切墙、柱归类别、窗台及朝向、家具不穿墙，最后看目标图面。普通门不能靠改名变成合格防火门。保留原件，不在库内升级保存。

竞赛原海报在 `references`，待授权获奖模型在候选表；默认查找不会把它们当可用工程。具体来源与权限看原生库说明，不为每次用族再建审批或交接包。
