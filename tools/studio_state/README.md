# Project state check

`check_state.py` 核对 `project.yaml` 与 `DECISIONS.md`、`ARTIFACTS.csv` 及文件系统是否一致。它只读、不改图、不通过 Gate。

## 依赖

```bash
python -m pip install pyyaml
```

## 用法

在项目根目录运行：

```bash
python .workflow/multica-arch-studio/tools/studio_state/check_state.py
python .workflow/multica-arch-studio/tools/studio_state/check_state.py --verbose
python .workflow/multica-arch-studio/tools/studio_state/check_state.py --json
python .workflow/multica-arch-studio/tools/studio_state/check_state.py --strict
```

从工作流仓库运行，指向项目：

```bash
python tools/studio_state/check_state.py --root "D:/path/to/library-project"
```

| 参数 | 作用 |
|---|---|
| `--root` | 项目根目录，默认当前目录 |
| `--state` | 指定 `project.yaml`，默认 `<root>/project.yaml` |
| `--json` | 输出机器可读结果 |
| `--strict` | warning 视为 error |
| `--no-git` | 跳过 git HEAD 检查 |
| `--verbose` | 打印 info 项 |

## 检查项

1. **结构**：顶层字段、Gate A–D 状态、数组类型。
2. **面积**：各层相加 = `above_ground` / `physical_total`；`roof_m2` 不计入；硬区间与 tolerance 一致。
3. **Gate 与决策**：`Gate A/B = passed` 必须在 `DECISIONS.md` 有可核查记录；Gate B 通过时不能仍有 `blocking`。
4. **决策 ID**：`project.yaml` 引用的 `D-xxx` 必须在 `DECISIONS.md` 存在，且状态没有明显矛盾。
5. **Blocker**：severity 合法，evidence 路径存在。
6. **Next**：每项有 action、owner、boolean blocking。
7. **产物**：`ARTIFACTS.csv` 路径存在，文件字节数一致；`LOG_INDEX.csv` 行数与 summary 一致。
8. **仓库**：`repository.head` 与 `.workflow` 实际 HEAD 一致；浅克隆 HEAD 同步；`pushed` 状态。

## 退出码

- `0`：无 error（warning 允许）
- `1`：有 error
- `2`：状态文件或 PyYAML 加载失败

## 不做什么

- 不改 `1.rvt`、PDF、图纸或任何设计文件。
- 不判断方案好坏、不替代用户 Gate 决定。
- 不自动修复；发现不一致只报告，修复由人或执行器按记录规则完成。
