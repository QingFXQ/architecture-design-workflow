# SketchUp 本地连接工具

2026-10-28选型。**Blender与SketchUp并列保留**：按项目和使用者选择概念建模工具，不要求互相转换；本用户当前优先Blender。本目录只增补SU连接，不提前实施尚在讨论的工作流改版。

## 当前选择与实际状态

当前首选：[2ez4gcx/sketchup-mcp](https://github.com/2ez4gcx/sketchup-mcp)，固定 **v1.3.0**、源码提交`8f74d4817ef411317c2867acf06601d340f100c5`，MIT许可。这是针对Windows桌面SU、可编辑概念与视觉回读的选型，不声称已经证明它是所有SU版本的最佳连接器。

- 上游声明支持桌面SU 2017+，测试过Windows SU 2021、2023；本仓库尚未验证真实SU会话。
- 29项工具覆盖模型查询、基础体量／多边形拉伸、变换、群组／组件、材料／标签、截图、视图、保存与导出，以及Ruby API扩展。
- 通用MCP stdio客户端使用Node.js 18+；不必使用Claude，也不需要另装Python。`.mcpb`只是发布包，解开后可由Node直接启动。
- 已保存上游原版`.mcpb`和`.rbz`、许可与SHA256；无需构建即可准备运行。核验结果见[验证记录](VERIFICATION.md)。
- **没有自动安装到SketchUp、改客户端全局配置、启动SU或修改任何建筑模型。**

## 快速接入

交给Agent执行完整部署时，使用[SketchUp MCP通用安装部署提示词](../../prompts/SKETCHUP_MCP_DEPLOYMENT.md)。以下是固定版本资料的手动入口；阅读或收录不代表要求现在安装。本轮用户明确电脑没有SU，因此未安装插件、未注册客户端、未进行实机验收。

1. 在仓库根执行`powershell -NoProfile -File tools/sketchup-mcp/scripts/prepare.ps1`。仅校验包并解压到本目录`runtime/`；不会安装SU扩展。
2. 在SketchUp扩展管理器安装`vendor/su_mcp-1.3.0.rbz`。上游包未签名；按本机现有扩展策略处理，不自动降低全局策略。
3. SU菜单`Extensions → SU MCP Bridge → Change port...`设成 **19876**，重启SU，检查`Status`。上游默认9876与常见Blender桥冲突，因此本集成采用19876；两端必须一致。若默认端口已占用，停止的是SU自己的桥，不要关掉Blender服务。
4. 在MCP客户端加入[mcp-config.example.json](mcp-config.example.json)对应条目，将`REPLACE_WITH_REPO_ABSOLUTE_PATH`替换为仓库绝对路径。该JSON是使用`mcpServers`结构的示例；其他客户端按其原生配置格式填同样的command/args/env。客户端调用超时宜高于桥接120秒。
5. `node tools/sketchup-mcp/scripts/probe.mjs`检查离线协议和工具发现。SU启动且端口正确后，`node tools/sketchup-mcp/scripts/probe.mjs --live-readonly`只调用`ping`与`model_info`，核实控制的确实是目标模型。
6. 第一次真实建模用新建的测试副本：创建10×8×3米体块、回读尺寸、截图查看、移动、撤销、另存测试SKP，再导出一个模型和PNG。通过后记录具体SU版本与结果，不用离线测试冒充实机成功。

程序输出协议使用stdout，诊断使用stderr。`scripts/start.mjs`仅启动固定版本，不下载、不安装、不弹确认框。

## 建筑概念阶段怎么用

- 场地底图、体量、楼层、交通与开放空间按命名群组／组件组织，保留可编辑对象。标签用于显示组织，不替代群组隔离几何。
- 工具长度／坐标默认 **毫米**，面积平方米、体积立方米；Ruby API内部长度是英寸。设计输入米要明确换算，不把米值直接传给毫米参数或原生Ruby坐标。
- 主要修改后从实际SU视口截图检查，再对照平面／剖切／轴测；基础建模不提前强制装饰、室内标签体系或工程量统计。
- CAD导入还取决于SU版本、授权及对应导入器；任意格式可用与否必须实测。PDF和图片可以先由资料识读工具提取／校准，再作为参考导入；本连接器不是PDF识图器，不能把截图自动当精确线稿。
- 与Blender/Revit交换时先用已知尺寸核单位、轴向、原点、地面标高，再核对象可编辑程度；不承诺SKP网格自动成为原生BIM。
- 同一SU模型保持一个写入者。普通编辑可撤销，但保存／打开文件不等于可撤销编辑；写入超时先查模型状态，不直接重放。Ruby作为需要时的扩展，不要求每条命令人工审批。
- 桥仅监听本机；`run_ruby`具有SU进程权限，保持loopback，不把此接口直接暴露到局域网／公网。

## 文件

- [选型比较](SELECTION.md)：为何当前优先此实现及备选边界。
- [验证记录](VERIFICATION.md)：明确区分发布包、离线协议／模拟测试与实机。
- `vendor/`：上游原版包、SHA256清单、MIT许可和第三方声明，纳入本仓库版本管理。
- `upstream.json`：固定版本、来源和校验值。
- `scripts/prepare.ps1`、`start.mjs`、`probe.mjs`：准备、启动、只读连接检查。
- `repo/`：本机检查用上游浅克隆；`runtime/`：解开的运行包。二者忽略，不作为嵌套Git仓库提交。迁移只需本目录的已跟踪文件。

没有改造上游源码，也没有强制六Agent或Gate接力；整体流程调整仍等用户反馈汇总。
