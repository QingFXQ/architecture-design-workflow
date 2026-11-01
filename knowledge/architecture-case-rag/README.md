# Architecture Case RAG

Architecture Case RAG 是面向建筑设计问题的本地案例知识库。案例 Markdown 是唯一事实来源；检索以“问题相似度优先于类型相同”为原则，并保留来源、图纸质量和不可照搬条件。

案例数量、标签统计与索引状态由脚本生成，不在文档中写死。运行 `python3 scripts/build_index.py` 可获得当前案例数。

## 检索管线

```text
自然语言问题 → query normalization → section-level semantic retrieval
                                   + metadata/tag/keyword evidence
                                   → hybrid scoring → case aggregation
                                   → optional local LLM rerank
```

- 当前默认`auto`：优先embedding章节语义检索，失败时明确提示并回退`lexical`离线文字检索。可显式选semantic／hybrid，失败则报错；语义使用本机Ollama的qwen3-embedding:0.6b，不调用生成式LLM。未来部署可安装该小型模型／依赖，文档编辑不触发本机部署。
- `quality mode`：先取当前 semantic/hybrid Top 20，再让本机 LLM 复核最多 5 个案例的前三段证据；只在需要额外判断时使用。LLM 不可用时自动回退 fast 结果。
- `baseline`：保留既有精确过滤与排序，用于兼容和Benchmark；不接受自然语言query，避免忽略问题返回同一列表。`lexical`才是无需服务的自然语言文字匹配回退。

每个section携带来源／案例与章节信息。文字命中不证明图片已查看；查看原始图面后在Blender／SU或平剖试验，按[当前使用约定](../../docs/RAG.md)记录实际设计变化。不强制每阶段重搜或填卡。以下索引构建命令在明确部署／更新任务中使用，不要求每次检索重建。

## 使用

从仓库根目录运行：

```bash
# 首次或案例变化后：先建文字 metadata；离线 lexical 只需要这一项
python3 knowledge/architecture-case-rag/scripts/build_index.py
# 可选：明确启用语义检索且已配置模型服务后，再构建 embeddings
python3 knowledge/architecture-case-rag/scripts/build_semantic_index.py

# 默认auto：自然语言优先语义，连接失败明确回退离线文字
python3 knowledge/architecture-case-rag/scripts/search_cases.py \
  --query "三层幼儿园如何让每个班级方便到达室外，同时避免长走廊" --max 8

# 输出可直接附入 Concept→Scheme 的交接卡
python3 knowledge/architecture-case-rag/scripts/search_cases.py \
  --query "坡地文化建筑如何利用高差形成连续参观路径" --max 5 --format card

# 叠加明确类型与资料质量过滤
python3 knowledge/architecture-case-rag/scripts/search_cases.py \
  --query "坡地文化建筑如何利用高差形成连续参观路径" --mode hybrid --type museum --quality 4

# 可选 evidence rerank（本机 qwen3.5 模型）
python3 knowledge/architecture-case-rag/scripts/search_cases.py \
  --query "遗产工业建筑如何转化为公共文化空间" --quality-mode --rerank-top 5 --max 5

# 保留旧式可复现 metadata/keyword 检索
python3 knowledge/architecture-case-rag/scripts/search_cases.py \
  --mode baseline --problem indoor-outdoor --type kindergarten --quality 3
```

`--type`、`--site`、`--strategy` 是精确过滤；`--quality` 是最低星级；`--year-from/--year-to` 包含边界；`--keyword` 为全文 AND。`--query` 默认auto（语义失败明确回退lexical），也可显式指定 `--mode semantic` 或 `--mode hybrid`；结果会显示 evidence sections，而不是把整篇案例误当作相关。

## 标签与入库

- 受控词表：[`ontology/tags.json`](ontology/tags.json)
- 同义映射：[`ontology/aliases.json`](ontology/aliases.json)
- 仅预览旧标签可归一的提案：`python3 scripts/enhance_tags.py`
- 模板：[`templates/case-template.md`](templates/case-template.md)
- 入库流程：[`ingestion/README.md`](ingestion/README.md)

标签只协助召回，不能替代正文、图纸或来源。未知数字留空，正文写“资料未提供”；质量星级衡量证据完整度，不评价项目优劣。

## Benchmark

[`benchmarks/queries.json`](benchmarks/queries.json) 含人工定义的真实建筑问题、`must_hit`、强相关、可接受与反例。运行：

```bash
python3 knowledge/architecture-case-rag/benchmarks/run_benchmark.py --mode baseline
python3 knowledge/architecture-case-rag/benchmarks/run_benchmark.py --mode semantic
python3 knowledge/architecture-case-rag/benchmarks/run_benchmark.py --mode hybrid
python3 knowledge/architecture-case-rag/benchmarks/run_benchmark.py --mode rerank
```

输出 Recall@3/5/10、MRR、must-hit coverage 与 false-positive rate。选择默认模式必须依据结果，并回看 false positive/negative 的正文证据；检索结果应转为本次模型／图纸的具体操作，按需在现有记录简写依据和验证；不强制写卡或角色交接，不向上下文倾倒整篇案例。

运行 `python3 scripts/audit_case_quality.py --output benchmarks/results/case-quality-audit.json` 可审计四星以上案例是否登记 floor plan、section 与 photo；五星还必须有 site plan。该报告是数据修复队列，不会静默降低星级。
