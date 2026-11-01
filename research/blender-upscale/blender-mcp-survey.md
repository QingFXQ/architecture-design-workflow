# Blender MCP 服务器调研

> 调研时间：2026-08-11（Asia/Shanghai）。所有星标、更新时间和安装结论均以本次用浏览器 UA `curl` 成功读取的 GitHub API、README 或 Blender 官方文档为准；不是根据搜索摘要推断。`待验证` 表示来源没有给出足够的可复现实证。

## 结论先行

**主选：[`ahujasid/blender-mcp`](https://github.com/ahujasid/blender-mcp)。** 它的社区规模和近期维护显著领先，Python/`uvx` 服务器加 Blender 单文件 addon 的部署最适合“Windows 上运行 Blender、Mac 上运行 Visualization Agent”的现有拓扑。它能通过 `execute_blender_code` 覆盖相机、灯光、场景、渲染及本地导入，且 socket 默认只绑定 `localhost:9876`，可安全地通过 SSH 隧道跨机使用。

**备选：[`dcc-mcp/dcc-mcp-blender`](https://github.com/dcc-mcp/dcc-mcp-blender)。** 若任务需要明确、可审计的 Camera/Light/Render/Import 独立工具（而不希望主要依赖任意 Python），选它。代价是它是 Blender 4.2+ Extension、带 `dcc-mcp-core` 和 200+ 工具的较重体系，远程 transport 为 HTTP/gateway 而不是本方案指定的 9876 socket。

不推荐把 [`VxASI/blender-mcp-vxai`](https://github.com/VxASI/blender-mcp-vxai) 用于新的生产链路：README 功能说明较全，但本次 API 抓到的最后一次提交是 2025-03-21，明显落后于前两者。

## 候选对比

| 候选 | GitHub / 活跃度（本次 API） | 功能覆盖：Camera / Light / Scene / Render / Object / Import / Python | 安装与架构 | 已知限制 |
|---|---|---|---|---|
| **ahujasid/blender-mcp** | [仓库](https://github.com/ahujasid/blender-mcp)，**25,707 stars**、2,449 forks、4 open issues；`updated_at` 2026-08-11，`pushed_at` 2026-08-11；最近提交 2026-08-03（修复 socket 串行化导致的 MCP timeout）。MIT。 | **Camera：P；Light：P；Scene：有 `get_scene_info`，修改为 P；Render：P；Object：有 `get_object_info`，增删改为 P；Import：资产下载/导入及 P；Python：有 `execute_blender_code`。** P = 经任意 `bpy` Python，不是专用工具。源码确认的直接 MCP 工具包括 scene/object 查询、viewport 截图、任意 Python、Poly Haven、Sketchfab 和 Hyper3D/Hunyuan3D 资产流程。 | Blender addon `addon.py` 在 GUI 内开 TCP server；外部 MCP 为 Python 包，入口 `blender-mcp`。README 给出 `uvx blender-mcp`，并给出 `pipx install blender-mcp` 后备方案。 | addon 源码明确拒绝 `blender -b`：后台模式没有 GUI timer 执行命令；`listen(1)`；任意 Python 是高权限执行面；README 仍提示复杂请求可能 timeout，建议拆小。 |
| **dcc-mcp/dcc-mcp-blender** | [仓库](https://github.com/dcc-mcp/dcc-mcp-blender)，**20 stars**、3 forks、1 open issue；`pushed_at` 2026-08-06，最近提交同日，最新 Release **v0.1.43**（2026-08-06，含 macOS/Windows/Linux ZIP）。MIT。 | **Camera：专用 `create_camera` 等；Light：专用；Scene：专用；Render：专用 `render_scene` / settings；Object：专用；Import：专用 FBX/OBJ/USD 等；Python：专用 `execute_python`。** README 枚举 200+ 工具，覆盖最完整。 | Blender 内嵌 Streamable HTTP MCP；推荐下载平台 ZIP，在 Blender 4.2+ 用 *Preferences → Extensions → Install from Disk*；也可 `pip install dcc-mcp-blender` 并从 Blender Python 启动。 | README 明确说 **不能**用 legacy *Add-ons → Install*；默认暴露任意 Python（可用环境变量禁用）；较大工具面和新 gateway 架构增加部署/安全审查量；默认示例 endpoint 为 `http://127.0.0.1:9765/mcp`，不直接兼容本报告的 9876 隧道配置。 |
| **VxASI/blender-mcp-vxai** | [仓库](https://github.com/VxASI/blender-mcp-vxai)，**299 stars**、24 forks、2 open issues；API `updated_at` 2026-08-10 但实际 `pushed_at` 与最后提交均为 **2025-03-21**。MIT。 | README 声称：**Camera、Light、Scene、Render、Object、Import、Python** 均可由自然语言/脚本工作流覆盖（渲染、灯光、相机、导入模型均列出）；**专用 MCP tool 名称和实际 Python 执行接口本次未取到，待验证。** | README：`uvx blender-mcp-vxai==1.0.7`，安装 `blender_mcp_addon.py` 并在 sidebar 启动。 | 长期无代码提交；README 同时说 Windows/Linux 可 `pip install uv`，与主选使用 uv 官方安装器的建议不同；版本 1.0.5/1.0.7 的表述也需实际部署前再核对。 |

## 主选落地：Windows Blender + Mac MCP server

### 1. Windows：安装 addon 并启动本地监听

1. 从主选仓库下载 [`addon.py`](https://raw.githubusercontent.com/ahujasid/blender-mcp/main/addon.py)。在 Blender 中打开 **Edit → Preferences → Add-ons → Install…**，选择该文件，再勾选 **Interface: Blender MCP**。这是项目 README 明示的安装法。
2. 若需要人工检查/保留 addon 文件，Windows 的 Blender 4.3 addons 根目录是：
   ```text
   /path/to/user-home Foundation\Blender\4.3\scripts\addons\
   ```
   以 Blender 的 *Install…* 实际写入位置为准；不要只把单个文件随意改名后复制而跳过启用步骤。
3. 在 3D View 中按 `N`，打开 **BlenderMCP** 标签，保持 host 为 `localhost`、port 为 `9876`，点击 **Connect to Claude**。源码默认值就是 `localhost:9876`，并以 TCP `bind`/`listen(1)` 启动。
4. Windows 上需启用 OpenSSH Server，并让防火墙只允许来自 Mac 的 SSH 入站（通常 TCP/22）；**不要**对局域网开放 9876。因为 addon 本身只监听 loopback，SSH 正是跨机入口。

### 2. Mac：安装 MCP server 并配置客户端

1. 安装 `uv`（README 的 macOS 命令）：
   ```bash
   brew install uv
   ```
   可先验证：`which uvx`。若 GUI MCP 客户端找不到 PATH，应在其配置中使用输出的绝对路径（项目 README 特别指出 Dock 启动的 GUI 不继承 shell PATH）。
2. 启动隧道（此终端保持运行）：
   ```bash
   ssh -N -L 9876:127.0.0.1:9876 仁@YOUR_REVIT_HOST
   ```
   这使 Mac 的 `127.0.0.1:9876` 映射至 Windows 上 addon 的 `127.0.0.1:9876`。登录用户、SSH 服务状态和 Windows 地址本次未在本机验证，属于部署前检查项。
3. 给 Mac 上的 MCP client 配置 server（示例为 Claude/Cursor 类 stdio 配置）：
   ```json
   {
     "mcpServers": {
       "blender": {
         "command": "/opt/homebrew/bin/uvx",
         "args": ["--python", "3.11", "blender-mcp"],
         "env": {
           "UV_PYTHON_PREFERENCE": "only-managed",
           "BLENDER_HOST": "127.0.0.1",
           "BLENDER_PORT": "9876"
         }
       }
     }
   }
   ```
   若 `uvx` 实际不在 `/opt/homebrew/bin/uvx`，替换为 `which uvx` 的结果。`BLENDER_HOST` 和 `BLENDER_PORT` 是项目 README 明确支持的环境变量。
4. `pip` 路径（仅在不能用 uv 时）：项目 README 推荐而非普通全局 pip 的替代是：
   ```bash
   pipx install blender-mcp
   pipx ensurepath
   ```
   然后把 `which blender-mcp` 的绝对路径设为 MCP client 的 `command`。包的 `pyproject.toml` 也确认入口为 `blender-mcp = blender_mcp.server:main`、要求 Python >= 3.10。

### 3. macOS addon 路径（同一主选）

macOS 的 addons 根目录为：

```text
~/Library/Application Support/Blender/<ver>/scripts/addons/
```

同样优先通过 *Preferences → Add-ons → Install…* 安装 `addon.py`；只有需要排障时才在该目录检查安装结果。macOS 和 Windows 不能同时持有同一 socket server；本链路中 addon 固定跑在 Windows，Mac 只跑 MCP server 和 SSH client。

## Headless 渲染核验

- **可行。** Blender 官方命令行文档明确给出 `blender -b file.blend -f 10`，说明 `-b` 为无 UI 后台渲染；也给出 `-o` 输出路径，并强调 `-f`/`-a` 必须是最后一个参数。因此用户给出的 `blender -b -o out -f 0` 参数顺序合法，会以默认启动场景渲染第 0 帧；实际工作应指定 `.blend` 和格式，例如：
  ```bash
  /opt/homebrew/bin/blender -b scene.blend -o //out/frame_##### -F PNG -f 0
  ```
- 本机已实际执行 `/opt/homebrew/bin/blender --version`，返回 **Blender 5.2.0 LTS**，故该 Homebrew 路径存在且可执行。
- 注意：这只验证 Blender CLI 渲染，不代表主选 addon 可在 headless 下服务 MCP；其 addon 源码明确禁止 background 模式。若要让 MCP 也跑在 headless/CI，改用备选 DCC-MCP 的 `blender --background --python .../blender_bootstrap.py` 路径（其 README 明示支持）。

## 已抓取来源

1. GitHub repository search API：<https://api.github.com/search/repositories?q=blender+mcp&sort=stars&order=desc&per_page=15>
2. 主选仓库元数据、提交、README、源码：<https://api.github.com/repos/ahujasid/blender-mcp>；<https://api.github.com/repos/ahujasid/blender-mcp/commits?per_page=1>；<https://github.com/ahujasid/blender-mcp>；<https://raw.githubusercontent.com/ahujasid/blender-mcp/main/addon.py>；<https://raw.githubusercontent.com/ahujasid/blender-mcp/main/src/blender_mcp/server.py>；<https://raw.githubusercontent.com/ahujasid/blender-mcp/main/pyproject.toml>
3. DCC-MCP 元数据、README、release、提交：<https://api.github.com/repos/dcc-mcp/dcc-mcp-blender>；<https://github.com/dcc-mcp/dcc-mcp-blender>；<https://api.github.com/repos/dcc-mcp/dcc-mcp-blender/releases/latest>；<https://api.github.com/repos/dcc-mcp/dcc-mcp-blender/commits?per_page=1>
4. VXAI 元数据、README、提交：<https://api.github.com/repos/VxASI/blender-mcp-vxai>；<https://github.com/VxASI/blender-mcp-vxai>；<https://api.github.com/repos/VxASI/blender-mcp-vxai/commits?per_page=1>
5. Blender 官方命令行渲染文档：<https://docs.blender.org/manual/en/latest/advanced/command_line/render.html>
