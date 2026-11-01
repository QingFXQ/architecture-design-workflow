# macOS / Windows 本地图像超分方案调研

> 调研时间：2026-08-11（Asia/Shanghai）。本报告只陈述本次以浏览器 UA `curl` 成功抓取的 GitHub、Hugging Face API/页面内容；“待验证”不应被当作可直接上线的兼容性承诺。

## 推荐结论

1. **Mac 最小、最稳的可执行链路：`waifu2x-ncnn-vulkan` macOS release → CLI。** 当前 release 明确提供 macOS 包，并明确宣称支持 Apple Silicon Vulkan；无需 Python/CUDA。适合先把生成图稳定放大 2×或 4×，保留 PNG 输出。它的模型和参数侧重“降噪等级 + 倍率”，对写实效果图的主观细节重建能力不能在本次来源中量化；应先以一张代表图做 A/B。
2. **Mac 本地质量优先：`chaiNNer` universal DMG + PyTorch MPS。** 它有当前 macOS universal DMG、集成 Python 和明确的 Apple Silicon MPS 支持；适合作为可视化、可复查的 ESRGAN/超分节点链路。需要在 Dependency Manager 安装 PyTorch，并对选用模型做一次实际加载验证。
3. **Windows（已有 ComfyUI）最终效果图主链路：`4x-UltraSharp` 预放大 + `ComfyUI_UltimateSDUpscale` 分块 diffusion 细化。** 前者快且可复现，后者以 tile 方式在较低硬件压力下重绘细节。它是本报告的高质量备选，而不是 Mac 的最小依赖方案。
4. **Real-ESRGAN ncnn-vulkan 的 macOS build 确实存在，但不作为 Apple Silicon 首选。** 官方 release `v0.2.5.0` 有 `realesrgan-ncnn-vulkan-20220424-macos.zip`，本次 `curl -I -L` 实际拿到 200 / 51,817,124 bytes；但它是 2022 资产，README 写的是 Intel/AMD/Nvidia GPU，未明确承诺 Apple Silicon。把它列为“下载后 smoke test”的备选；失败时优先转 chaiNNer MPS 或 Windows ComfyUI。

## 方案对比

| 方案 | 安装/接入与输入输出 | 质量档位 / 操作控制 | GPU 与 macOS 可用性 | 接入“出图 → 本地超分 → 高清效果图” |
|---|---|---|---|---|
| **waifu2x-ncnn-vulkan** | 从 [Releases](https://github.com/nihui/waifu2x-ncnn-vulkan/releases) 解压 macOS 包；自带 binary 和模型，不需要 CUDA/Caffe。CLI 输入为单个文件或目录，支持 JPG/PNG/WebP，输出同样支持这些格式。 | `-s` 可取 1/2/4/8/16/32；`-n` 为 -1/0/1/2/3，值越大降噪越强；`-t` 较小可降低显存占用。建议效果图先 `-n -1 -s 2`（尽量保真）或 `-n 0/1 -s 4`，并与原图 100% 对比。 | README 明确为 Intel/AMD/NVIDIA/**Apple Silicon** + Vulkan，最新 release **20250915** 含 `...-macos.zip`；`-g -1` 可强制 CPU。 | **Mac 最小链路。** 生成模型把 PNG 写入目录后，直接执行下方命令，输出 PNG 交给 Blender 贴图、排版或交付。 |
| **chaiNNer** | 下载 [v0.25.1 macOS universal DMG](https://github.com/chaiNNer-org/chaiNNer/releases/tag/v0.25.1)。首次启动会提供隔离 Python；在 Dependency Manager 安装 PyTorch/NCNN/ONNX 等后，以节点图导入图像、加载模型、超分、保存。 | 质量由所载模型和节点参数决定，不存在一个可跨模型比较的统一“档位”。可先做两个 workflow：2×保守版、4×细节版；同图比对边缘、文字和重复纹理。chaiNNer 的模型兼容范围并非无限：README 明说 PyTorch 只支持“select model architectures”。 | README 明确跨 Windows/macOS/Linux，macOS 10.x 以下不支持；Apple Silicon M1/M2/M3 支持 **PyTorch MPS**，CPU 也可 fallback。NCNN 在部分配置可能不工作或输出黑图。 | **Mac 质量优先链路。** 将生成图拖入工作区；Dependency Manager 选 PyTorch；在节点选择面板添加图像输入、与已验证 SR 模型相匹配的加载/超分节点、保存节点并按类型端口相连。使用 `4x-UltraSharp.pth` 前先在一张图实际加载；该模型文件存在已核验，但本次 chaiNNer 来源没有逐个承诺其兼容性，故为**待验证**。 |
| **Real-ESRGAN（Python）** | [官方仓库](https://github.com/xinntao/Real-ESRGAN) 提供 `inference_realesrgan.py`；输入单文件或目录，默认结果目录为 `results`，支持 `--outscale`、`--tile`、alpha/灰度/16-bit，且可选 GFPGAN 人脸增强。 | `RealESRGAN_x4plus` 为通用 4×；`--outscale 3.5` 等会在模型输出后用 Lanczos4 再缩放；`--tile` 0 为不切块。 | 仓库近期代码推送为 2024-08，最新 release 为 2022。Python inference 源码本次只确认把 `gpu_id` 交给 `RealESRGANer`，没有发现 MPS 分支；Mac MPS 实测兼容性为**待验证**，不应假定加速可用。 | 可用于已有 Python 环境的批量处理；对 Apple Silicon 优先级低于 chaiNNer。命令见下文。 |
| **Real-ESRGAN ncnn-vulkan** | 官方 release `v0.2.5.0` 包含 macOS/Windows/Linux portable zip；不需 CUDA/PyTorch。CLI 支持单个图或目录、JPG/PNG/WebP，`-i/-o/-n/-s/-t/-g`。 | `realesrgan-x4plus` 通用；`realesrgan-x4plus-anime` 动画；`realesrnet-x4plus`；`realesr-animevideov3`。倍率 2/3/4。README 警告 tiled 处理可能有块间不一致，并与 PyTorch 输出略不同。 | macOS 资产**存在且已通过 HEAD 跟随重定向验证**；但项目文字只说 Intel/AMD/Nvidia GPU，未明确 Apple Silicon，也没有 macOS/Metal 支持说明。安装后先运行 `-h` 和单图 smoke test；失败即不要继续排障，转 chaiNNer/waifu2x。 | 可作 Mac 的无 Python 备选或 Windows 的快速批量预放大；不是本报告主选。 |
| **Windows ComfyUI + Ultimate SD Upscale** | 现有 ComfyUI 的 `custom_nodes` 下 clone 插件，重启；把 ESRGAN 权重放入 `models/upscale_models`。插件在 `image/upscaling` 菜单，且自带 template/example workflow。 | 基础 SR（`4x-UltraSharp`）负责确定性放大；Ultimate 节点对大图做 tile 化 image-to-image diffusion，以较小 tile 保持训练分辨率并补细节。质量最高但会改变像素/纹理，需保留基础 SR 输出用于回退。 | Windows 的现有 ComfyUI 最适合；官方 README 明示 Windows portable NVIDIA 包支持 20 系及以上，并有 AMD/Intel 包。Mac 的 ComfyUI 本体可在 Apple Silicon 安装，但本次未验证 Ultimate 节点的 MPS 实际运行，故不把它列为 Mac 首选。 | **Windows 高质量链路。** 输入生成图 → 基础 SR → Ultimate tiled diffusion → Save Image；保留 workflow JSON、seed 和原图以便复现。 |

## 可执行操作

### A. Mac 最小方案：waifu2x-ncnn-vulkan

1. 在 [release 页面](https://github.com/nihui/waifu2x-ncnn-vulkan/releases/tag/20250915) 下载 `waifu2x-ncnn-vulkan-20250915-macos.zip` 并解压。
2. 生成模型先输出无损 PNG，例如 `/path/to/generated.png`。
3. 在解压目录执行（macOS binary 名不带 `.exe`）：

```bash
./waifu2x-ncnn-vulkan \
  -i /path/to/generated.png \
  -o /path/to/generated-4x.png \
  -n 0 -s 4 -t 256
```

4. 若遇显存/驱动问题，先降低 tile，如 `-t 128`；若需要纯保真放大，把 `-n` 改为 `-1`。先运行 `./waifu2x-ncnn-vulkan -h` 确认 macOS release 已正确解压。

### B. Mac 质量优先：chaiNNer MPS

1. 安装 [macOS universal DMG](https://github.com/chaiNNer-org/chaiNNer/releases/tag/v0.25.1)，启动应用；它会使用隔离 Python，不要求先安装系统 Python。
2. 在 Dependency Manager 安装 **PyTorch**。Apple Silicon 下由 README 声明走 MPS；不建议优先选 NCNN，因为项目也警告 macOS NCNN 在部分配置可能异常。
3. 将生成图导入节点图，加载一次经过验证的 SR 模型，连接“图像输入 → 超分 → 保存”。产出使用 PNG；创建 2× 和 4×两个 preset，以便按项目尺寸选择。
4. 可候选下载 [`lokCX/4x-Ultrasharp` 的 `4x-UltraSharp.pth`](https://huggingface.co/lokCX/4x-Ultrasharp)。Hugging Face API 已确认该文件存在；**先试载入再批量跑**，因为 chaiNNer README 未逐模型列出兼容保证。

### C. Windows：已有 ComfyUI 的高质量方案

1. 在 PowerShell / CMD 中进入已有实例的 custom nodes 目录并安装插件：

```powershell
cd C:\path\to\ComfyUI\custom_nodes
git clone https://github.com/ssitu/ComfyUI_UltimateSDUpscale
```

   重启 ComfyUI。替代途径是 ComfyUI Manager 搜索 `UltimateSDUpscale`，或执行 README 给出的 `comfy node install comfyui_ultimatesdupscale`。
2. 下载 [4x-UltraSharp 权重](https://huggingface.co/lokCX/4x-Ultrasharp) 中的 `4x-UltraSharp.pth`，放到：

```text
C:\path\to\ComfyUI\models\upscale_models\4x-UltraSharp.pth
```

   ComfyUI 源码已确认 `upscale_models` 映射到 `models/upscale_models`，内置 `UpscaleModelLoader` 从该目录枚举权重。
3. 在 UI 用插件 Templates 的 Extensions 区加载该插件提供的示例 workflow（或手工以“Load Image → Upscale Model Loader / Image Upscale With Model → Ultimate SD Upscale → Save Image”搭建）。Ultimate 节点还需要可用的 diffusion checkpoint、VAE、正/负提示词；保留生成时的提示词来约束细节重绘。
4. 先只跑基础 `4x-UltraSharp` 并保存 `*-sr.png`；确认构图/文字无误后再用 Ultimate tiled workflow 产出 `*-final.png`。大图显存不足时调低 tile/批量，具体参数从该插件提供的 example workflow 开始，避免无根据地套固定值。

### D. Real-ESRGAN：何时用与命令

**NCNN macOS release 存在性：已确认。** `v0.2.5.0`（2022-04-24）的 assets 包含 `realesrgan-ncnn-vulkan-20220424-macos.zip`；下载 URL 的最终响应为 `200 application/octet-stream`。若要试跑：

```bash
./realesrgan-ncnn-vulkan \
  -i /path/to/generated.png \
  -o /path/to/generated-realesrgan.png \
  -n realesrgan-x4plus -s 4 -t 256
```

**Python 参考命令：**

```bash
python inference_realesrgan.py \
  -n RealESRGAN_x4plus \
  -i /path/to/generated.png \
  -o /path/to/results \
  --outscale 4 --tile 256
```

`--tile` 应按实际内存调小；`--outscale` 可为非整数。Python 路径的依赖安装、权重下载、以及 Mac MPS 行为在此报告范围内未做本机执行，故不能替代 A/B 的主推荐。

## 质量与交付准则

- 生成模型输出先保存原始 PNG；任何超分都写到新文件，不覆盖原图。
- 2×适合版式/网页不足时的保守交付；4×适合最终静帧，但应检查窗格、栏杆、文字、重复材质和人脸等容易出现伪细节的位置。
- 需要“严格不改图”时只用基础 SR（waifu2x 或 4x-UltraSharp）；需要“观感更丰富”时再用 Ultimate diffusion，并将它标注为生成式细化而非纯像素放大。
- 输出优先 PNG；若最终要交付 JPEG，最后一步才压缩，并保留 PNG 母版。

## 已抓取来源

1. Real-ESRGAN：<https://api.github.com/repos/xinntao/Real-ESRGAN>；<https://github.com/xinntao/Real-ESRGAN>；<https://api.github.com/repos/xinntao/Real-ESRGAN/releases/tags/v0.2.5.0>；<https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-macos.zip>；<https://raw.githubusercontent.com/xinntao/Real-ESRGAN/master/inference_realesrgan.py>
2. chaiNNer：<https://api.github.com/repos/chaiNNer-org/chaiNNer>；<https://github.com/chaiNNer-org/chaiNNer>；<https://api.github.com/repos/chaiNNer-org/chaiNNer/releases/latest>
3. waifu2x-ncnn-vulkan：<https://api.github.com/repos/nihui/waifu2x-ncnn-vulkan>；<https://github.com/nihui/waifu2x-ncnn-vulkan>；<https://api.github.com/repos/nihui/waifu2x-ncnn-vulkan/releases/latest>
4. ComfyUI / Ultimate：<https://api.github.com/repos/Comfy-Org/ComfyUI>；<https://github.com/Comfy-Org/ComfyUI>；<https://raw.githubusercontent.com/Comfy-Org/ComfyUI/master/folder_paths.py>；<https://raw.githubusercontent.com/Comfy-Org/ComfyUI/master/comfy_extras/nodes_upscale_model.py>；<https://api.github.com/repos/ssitu/ComfyUI_UltimateSDUpscale>；<https://github.com/ssitu/ComfyUI_UltimateSDUpscale>
5. 4x-UltraSharp 文件清单：<https://huggingface.co/api/models/lokCX/4x-Ultrasharp>；<https://huggingface.co/lokCX/4x-Ultrasharp>
