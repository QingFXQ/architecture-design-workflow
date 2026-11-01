# 验证记录

记录日期：2026-10-28。

| 项目 | 结果 | 依据／边界 |
| --- | --- | --- |
| 上游版本与来源 | 已核 | v1.3.0，源码提交见upstream.json；执行未来部署时须重新核稳定版本 |
| 两个原版发布包 | 已下载并校验 | mcpb及rbz与上游同release SHA256SUMS一致；哈希见upstream.json |
| 配套Ruby文件 | 已核一致 | 独立rbz内loader／main.rb与mcpb内bridge文件逐字节相同 |
| 许可 | 已保留 | MIT及运行包第三方许可均在vendor/ |
| 本地运行包准备 | 完成 | 只在仓库忽略目录runtime/解包，没有安装SU插件或改全局配置 |
| MCP离线初始化与工具发现 | 通过 | scripts/probe.mjs实际启动固定版本，返回v1.3.0及29项工具，live_verified=false |
| SU安装／启用Ruby Bridge | 未进行 | 用户明确本机没有SU，要求仅存部署提示词 |
| 客户端全局MCP注册 | 未进行 | 只保存示例，没有修改用户配置 |
| 真实建模／截图／保存／幂等 | 未测 | 没有真实SU会话，不用离线成功代替 |

没有运行上游修改模型的smoke，也没有执行Ruby建模。仓库资料和运行包可用不等于Windows SU端到端接入通过。

实际部署请使用[通用提示词](../../prompts/SKETCHUP_MCP_DEPLOYMENT.md)，依据当时环境验收。
