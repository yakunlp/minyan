# 英语新闻转录工具

免费的本地英语音频转录网页。电脑运行 Python 服务，手机和电脑连接同一可信 Wi-Fi，通过浏览器上传音频、查看/编辑英文文本并下载 TXT。不需要收费 API，不需要手机安装 App。

## 环境和安装

- Windows，推荐 Python 3.12 64 位；无独立显卡也可运行。
- 初次安装依赖和下载模型需要联网。模型下载来自 Hugging Face，连接失败时请检查网络；本项目不包含模型文件。
- 本项目使用 Streamlit、faster-whisper、CPU int8 推理；通常无需另装系统 FFmpeg。
- PyAV 固定为 16.0.1：PyAV 19 的 `av.open` 不再接受 faster-whisper 1.2.1 使用的 `metadata_errors` 参数，请通过项目依赖文件安装，不要单独升级 PyAV。

在 PowerShell 执行：

```powershell
Set-Location 'D:\myAI\newstranscribe'
py -3.12 -m venv 'D:\myAI\newstranscribe\.venv'
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' -m pip install -r 'D:\myAI\newstranscribe\requirements.txt'
```

已有虚拟环境时跳过创建步骤。在 VS Code 中选择解释器 `D:\myAI\newstranscribe\.venv\Scripts\python.exe`。

## 启动

```powershell
Set-Location 'D:\myAI\newstranscribe'
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' -m streamlit run 'D:\myAI\newstranscribe\app.py'
```

也可以在 PowerShell 中执行 `& 'D:\myAI\newstranscribe\start.ps1'`（**会在终端里直接打印手机访问地址和二维码**，无需先在电脑上打开网页）。若执行策略禁止脚本，使用上面的 Python 启动命令即可，无需放宽系统策略。

电脑打开 **http://localhost:8501**。终端必须保持运行；Ctrl+C 停止服务。应先切换到项目目录，确保 Streamlit 加载 `D:\myAI\newstranscribe\.streamlit\config.toml`。只想用手机时，启动后直接**用手机相机扫描终端里的二维码**即可。

### 桌面图标：一键用 Chrome 打开（电脑端）

在电脑上使用时，双击这个图标即可打开网页。运行一次：

```powershell
powershell -ExecutionPolicy Bypass -File 'D:\myAI\newstranscribe\create-open-shortcut.ps1'
```

会在桌面创建 `News Transcriber.lnk` 快捷方式（图标取自 Chrome）。以后**双击该图标**即可：若服务尚未运行，会先自动启动（弹出服务窗口），待页面就绪后用 Google Chrome 打开 `http://localhost:8501`；若未安装 Chrome，则退回默认浏览器打开。服务窗口需保持运行，关闭它即停止服务。服务窗口由 `start.ps1` 启动，所以窗口里也会打印手机二维码。

### 桌面图标：手机优先（扫码打开，不必先开电脑网页）

如果你主要用手机，运行一次：

```powershell
powershell -ExecutionPolicy Bypass -File 'D:\myAI\newstranscribe\create-phone-shortcut.ps1'
```

会在桌面创建 `News Transcriber (Phone).lnk`。双击它只做两件事：**启动服务**，并在窗口里**打印手机地址和二维码**（不打开电脑浏览器）。手机扫码即可使用。

## 手机访问

1. 手机、电脑连接同一 Wi-Fi，电脑网络配置为可信的“专用网络”。
2. 启动服务时，**终端（服务窗口）会直接打印「📱 手机访问地址」和一个二维码**——手机用相机/“扫一扫”扫描它即可打开，**不需要先在电脑上打开网页**（通过 `start.ps1` 或桌面「(Phone)」图标启动都会打印）。
3. 若已经打开了电脑网页，页面**顶部也会显示同样的地址和二维码**，同样可以扫。
4. 若两处都没有显示地址，在电脑 PowerShell 执行 `ipconfig`，找到无线局域网适配器的 IPv4（不要用 VPN、虚拟网卡或 127.0.0.1），再访问 `http://电脑IPv4地址:8501`。
5. 打不开时最常见的原因是防火墙：**以管理员身份运行项目里的 `allow-phone.ps1`**（右键 → 以管理员身份运行），它会创建一条只放行**本局域网**、TCP 8501 的规则并打印可用地址；也可以手动把当前网络改成“专用”。不要关闭防火墙，也不要把 8501 开放到公网。
6. 其它排查：电脑是否休眠、服务窗口是否还开着、地址是否变化、路由器/热点是否开启访客网络或 AP 隔离。手机的 localhost 指手机自身，不能用来访问电脑。

二维码由本机用 `qrcode` 依赖现算（不经第三方服务）。若你之前已经装过依赖，重新执行一次 `& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' -m pip install -r 'D:\myAI\newstranscribe\requirements.txt'` 即可补上该依赖；缺少时页面会自动退回只显示文字地址，不会报错。

无需路由器端口映射，不要将 8501 端口开放到公网。HTTP 不加密，仅限可信家庭局域网，不建议上传敏感音频。

## 电脑关机也能用？（部署到云端）

这台电脑一关机，`http://电脑IP:8501` 就打不开了——因为网页和识别模型都跑在它上面。若希望**电脑关机时手机也能用**：把项目推到 GitHub，再用 **Streamlit Community Cloud** 从仓库部署，就能得到一个手机随时可访问的网址（**注意：不能在 github.com 上直接运行**，GitHub 不运行你的程序）。

部署后请**在 Secrets 里设置 `password`**，这样只有知道口令的人能用（免费版 Streamlit Cloud 没有“私有应用”，访问口令就是屏蔽其他人的办法）。**口令可以很短**——首次登录勾选「记住这台设备」后，把带 `?k=` 的链接存到手机主屏，以后一键进入、无需输入。想要“别人连页面都看不到”，改用私有 Hugging Face Space 或 Codespaces。完整步骤见 **`DEPLOY.md`**。

## 使用

1. 上传 MP3、WAV、M4A、FLAC、OGG 或 AAC，最多 50 MB。
2. 选择 `base.en`（默认，较快）或 `small.en`（通常更准确，但更慢）。
3. 点击“开始转录”，首次使用每个模型会下载到 `D:\myAI\newstranscribe\.models`。
4. 保持页面打开，等待文本生成。进度是已经处理的音频位置，不是剩余时间估算。
5. 校对文本，可全选复制或下载 UTF-8 TXT；可展开原始时间戳。

建议先使用 1～3 分钟音频。上传大小不代表音频时长；长音频在解码时可能占用大量内存。当前版本不适合多人并发或超长录音，整个服务一次只处理一个任务，其他任务会提示稍后重试。

本项目支持可选的本地自动说话人区分，不提供翻译，默认不自动下载 BBC 内容（另有可选的“一键抓取并转录 BBC News”，见下节），请仅处理你有权使用的音频。人名、数字、背景音乐等可能导致识别错误，重要内容需要人工核对。

## 自动区分说话人（免账号）

使用 sherpa-onnx 2.0.1，在 CPU 上运行 sherpa 官方公开发布的 pyannote segmentation 3.0 ONNX 分段模型和 NeMo TitaNet small 声纹模型，不使用 pyannote.audio 的受限整套管线。不需要 Hugging Face 账号或访问令牌，不上传音频到第三方服务。它根据声学特征聚类，不根据文本猜测身份。

先按项目依赖文件安装新增的 sherpa-onnx，再显式下载公开模型：

```powershell
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' -m pip install -r 'D:\myAI\newstranscribe\requirements.txt'
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' 'D:\myAI\newstranscribe\download_speaker_models.py'
```

模型来自 sherpa-onnx 官方 GitHub Releases，保存在 `D:\myAI\newstranscribe\.models\speakers`，使用 `segmentation-3.0.onnx` 和 `nemo_en_titanet_small.onnx`。下载脚本通过 HTTPS 获取文件并检查公布的字节数；这些历史发布文件未公布 SHA-256，不能宣称已验证密码学完整性。保留下载包内 LICENSE；再分发、商业使用请核对 pyannote、NeMo 及模型原始数据的许可，不要把“公开下载”等同于无限制使用。候选 Reverb v1 因非生产许可限制未被选用，遗留的 Reverb 下载包不是运行所需模型。

刷新网页，勾选“自动区分说话人”，选择“自动估计”或指定已知人数（1～10），然后重新转录。**该选项默认关闭**（按普通方式转录）；只有需要标注发言人时才勾选，它会额外耗时并需要已下载的说话人模型。旧结果不会自动补标签。已知人数通常有助于减少错误聚类；不要把人数强设为实际不存在的数量。

输出和 TXT 均包含 `[Speaker 1]`、`[Speaker 2]`，时间戳表也显示说话人。标签按该录音中首次出现排序，只在当前录音内有意义，不推断姓名、性别、主持人或记者身份，不可用于身份认证。没有匹配时间段或重叠分数相同的词显示 `[Speaker unknown]`。

实现先生成说话人时间段，再开启 Whisper 词级时间戳，按时间交集分配每个词并合并相邻同说话人文本。多人重叠、短回应、音乐和噪声仍可能误分，无法保证完整保留同时讲话的多路内容。分离和词级转录会增加 CPU 耗时。前 35% 是分离阶段、后 65% 是转录阶段，并非音频位置或剩余耗时估计。

模型未下载或下载失败时可取消该选项，继续原有普通转录。检查 `D:\myAI\newstranscribe\.logs\speaker-download.stderr.log` 仅适用于开发时将错误输出重定向到该文件的启动方式；前台运行下载脚本直接查看终端。

参考：
- https://k2-fsa.github.io/sherpa/onnx/speaker-diarization/models.html
- https://k2-fsa.github.io/sherpa/onnx/speaker-diarization/python.html

## 一键抓取并转录 BBC News（可选，需自行承担版权责任）

除手动上传音频外，还可以一键抓取 BBC World Service 的 5 分钟新闻简报「BBC News」最新一期并直接转录。节目页：`https://www.bbc.co.uk/programmes/p002vsmz/episodes/player`。

**网页方式**：打开网页，在「📡 一键抓取 BBC News」区域点击「📡 抓取并转录最新 BBC News」。程序会：

1. 自动获取最新一期，并**在开始下载时立刻显示是哪一期**（标题、播出时间如 `06/11/2026 16:01 GMT`、节目编号），无需等转录完成；
2. **把这一期的音频和英文文本保存到电脑**的 `D:\myAI\newstranscribe\bbc_downloads` 目录，文件名同时包含播出日期时间和节目编号；
3. 在页面用**本网页提供的音频**播放这一期，并提供 **「⬇️ 下载这一期 MP3」按钮**：可以边听边校对转录文本，或把 MP3 直接下载到手机/电脑；因为音频由本机服务提供，所以手机打开网页就能播放和下载，不需要手机能访问 BBC；
4. 显示处理进度（进度是已处理的音频位置，不是剩余时间估算）；
5. 本地转录，结果与普通转录一样可编辑、下载 TXT、查看时间戳。

**命令行方式（可选，不占用桌面图标）**：桌面只保留一个「打开网页」的图标。如需要无界面脚本，可自行运行：

```powershell
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' 'D:\myAI\newstranscribe\bbc_transcribe.py'
```

可用参数：`--model small.en`、`--speakers`（区分说话人）、`--num-speakers 2`、`--out 目录`、`--no-open`。

**实现原理**：从节目列表页解析最新一期的剧集 id（HTML 中每个剧集块的 `data-pid`，按由新到旧排序），再查询该剧集得到音频地址。一集可能包含多个版本，只有带音频的版本可播放，程序会逐个尝试；随后向 BBC 公开媒体选择器换取两个时间受限的地址：MP3 地址会先**下载保存到 `bbc_downloads`**（先写 `*.part` 再原子替换），再由 PyAV 直接解码这份本地文件进行转录，既只请求一次，又让保存的音频与转录文本逐一对应；HLS 地址作为保存失败时的备用来源。音频地址有有效期，因此每次都重新获取，同一期的旧文件会被更新覆盖。

**注意**：

- BBC 音频受版权保护。此功能会**自动下载 BBC 内容**，默认仅用于你有权使用的个人学习场景，请不要再分发，并自行确认符合 BBC 使用条款。
- 下载的音频和文本保存在 `D:\myAI\newstranscribe\bbc_downloads`，便于回放和离线查看；该目录已在 `.gitignore` 中忽略，不要提交或再分发。
- 需要联网访问 `bbc.co.uk` 与 BBC 音频 CDN（`*.akamaized.net` 等）；网络受限时可能失败并给出提示。
- 页面上的播放器改为播放**已保存到电脑的音频**，由本机网页服务提供，因此手机不需要能访问 BBC；若保存失败，会退回 BBC 的临时 MP3 链接，此时播放设备才需要能访问 BBC。
- 每次只抓取最新一期，且与上传转录共用同一把锁，一次只处理一个任务。
- 转录仍需本地模型；模型缺失或下载失败的处理与普通转录一致。

## 隐私与资源

- 音频不发送到云端识别 API，仅上传到运行服务的电脑。
- 不保存转录历史。工作临时目录使用随机名称，不使用用户文件名作为磁盘路径；正常结束或异常退出函数时自动清理。
- 上传音频和文本会在浏览器/Streamlit 会话内存中暂存，不承诺关闭标签后立即安全擦除。
- 电脑强制关机或进程被强制结束时，系统临时目录可能残留 `english-transcribe-*` 文件夹。确认服务停止后可手动清理这些目录。
- 模型长期缓存在磁盘，本机识别仍消耗电力和计算资源。“免费”不代表云服务器或全天公网服务免费。
- 未实现登录、任务持久化或公网安全防护。刷新/断线可能丢失结果，任务也不会因此保证立即取消。

## 模型下载失败

如果日志包含 `ConnectTimeout` 和 `LocalEntryNotFoundError`，表示模型下载连接失败，不代表音频损坏。安装 Python 依赖的 PyPI 镜像不会解决 Hugging Face 模型下载问题。

默认尝试从 Hugging Face 下载。无法访问时，可显式运行下面命令，从 ModelScope 社区镜像下载 `base.en`，脚本按镜像仓库提供的 SHA-256 校验文件完整性（这不是上游真实性的独立证明）。只下载模型文件，不上传音频、不执行仓库代码。

```powershell
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' 'D:\myAI\newstranscribe\download_model.py'
```

看到 `Download complete` 后，刷新网页并选择“快速模式 · base.en”重新转录。模型保存在 `D:\myAI\newstranscribe\.models\base.en`，此目录模型完整时只从本地加载，不访问 Hugging Face。中断后可重新执行命令，已校验的文件会跳过；未完成的大文件需重新下载。

精细模式 `small.en` 需要单独下载模型；上述脚本只安装快速模式。也可将可信来源的 CTranslate2 模型文件放入 `D:\myAI\newstranscribe\.models\small.en`，至少包含 `config.json`、`model.bin`、`tokenizer.json`，并保留模型附带的词表及预处理配置。

## 自动化测试

```powershell
Set-Location 'D:\myAI\newstranscribe'
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' -m unittest discover -s 'D:\myAI\newstranscribe\tests' -v
```

单元测试使用假模型检查验证、临时文件清理、模型复用及并发保护；网页测试检查初始界面、结果编辑和状态重置，不下载模型。这些测试不能代替真实音频转录和手机浏览器测试。