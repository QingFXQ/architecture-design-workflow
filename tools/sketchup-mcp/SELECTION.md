# SU连接器选型

核查日期2026-10-28。目标：Windows本机桌面SU、持续编辑当前模型、能截图回看、可用于通用MCP客户端；不是单张生图或云端下载一次性模型。以下测试声明来自各自上游，除验证记录中明确跑过的项目外，不代表本机实测。

| 方案 | 可取之处 | 当前未选作默认的原因／边界 |
| --- | --- | --- |
| **[2ez4gcx/sketchup-mcp](https://github.com/2ez4gcx/sketchup-mcp/tree/v1.3.0)** | 上游明确Windows与SU 2021/2023测试；常用建模、视图截图／恢复、文件管理；Node打包即可运行；每命令独立连接；MIT | 当前首选。社区规模较小，缺少本仓库真实SU验证，不宣称生产成熟。固定v1.3.0避免随latest漂移 |
| [zinin/sketchup-mcp2](https://github.com/zinin/sketchup-mcp2/tree/v0.4.0) | 维护活跃、Python/Ruby测试、版本握手、结构化查询、布尔及边处理；签名RBZ发布；MIT | 强备选。专门的视口截图工具明确要求SU 2026+，对旧SU的视觉回读不如当前首选直接；若明确统一SU 2026可重新比较 |
| [mhyrr/sketchup-mcp](https://github.com/mhyrr/sketchup-mcp) | 社区关注较多，原始本地桥实现 | 本次API显示无明确许可证元数据、无正式release；其他实现对其通信与挂起问题有修正说明。未选作可再分发默认包，不凭星数判最佳 |
| [Shattenjagger/sketchup-mcp-bridge](https://github.com/Shattenjagger/sketchup-mcp-bridge) | 简单、每命令独立连接、上游记录SU 2026 Windows运行、MIT | 主要只有Ruby执行／查询／截图，截图目录有额外要求；作为窄用途备选，不胜过常用工具更齐全的方案 |
| [PMajesty/sk_ruby_mcp](https://github.com/PMajesty/sk_ruby_mcp) | 原生HTTP MCP、建筑／立面专用命令、无需第二服务 | 上游明确Windows未验证；本次未见许可证元数据或release，不复制进本仓库 |
| [Trimble官方SketchUp Connector](https://investor.trimble.com/news/news-details/2026/Trimble-Links-SketchUp-with-Anthropics-Claude-Bringing-New-Conversational-AI-powered-Capabilities-to-3D-Modeling/default.aspx) | 官方云端概念建模，产生可下载SKP | 官方描述为Claude中的云端会话与下载模型；不等同于控制当前Windows本地SU模型。可另作工具选项，不能替代本连接 |

当前没有发现可直接连接的已安装SketchUp插件；插件目录搜索无结果。skills.sh/CLI检索有渲染和木作等少量技能，但它们不等于可靠连接器，本次不批量安装技能。

本次GitHub API快照：2ez4gcx 4 stars，zinin 54，mhyrr 518，Shattenjagger 3，PMajesty 5。星数是社区规模参考，不是兼容性或质量证明；当前首选的关键依据是旧版Windows兼容声明、实际功能和可在本机核验的发布包。

发布包来自固定release，原始SHA256SUMS同步保留。本地算出的SHA256与同一发布页清单一致，说明下载内容与该清单一致，不当作独立第三方签名认证。
