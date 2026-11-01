# Architecture Case Ingestion

这是面向人工研究与本地案例扩库的极简流程，不是爬虫平台。支持 gooood、ArchDaily、Divisare、事务所官网及人工粘贴资料；优先保存项目 URL 和原始来源，未知事实绝不补写。

1. 在 `queue.jsonl` 增加项目 URL、来源和研究问题。
2. 从 `templates/case-template.md` 创建 Markdown；从项目页提取已证实的元数据、正文、图纸链接和访问日期。
3. 运行 `python3 ingestion/normalize_case.py /path/to/case.md`。它检查唯一 ID、必填 frontmatter、来源、图面、15 节模板和 canonical tags。
4. 运行 `python3 ingestion/ingest_case.py /path/to/case.md`。验证通过后复制到 `cases/`、重建 metadata 索引及 section-level semantic 索引。

若页面无法自动读取、图纸只有图片或资料不完整，仍可人工结构化文字案例：保留 URL 和 `images.kind`，相应字段留空，正文明确标记“资料未提供”。
