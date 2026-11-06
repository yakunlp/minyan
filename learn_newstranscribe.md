# 从零学习英语新闻转录工具：这个项目是怎样产生的

> 本文结合本项目实际开发过程和当前代码编写，适合了解 Python 基础、第一次接触语音识别网页的学习者。
>
> 项目位置：`D:\myAI\newstranscribe`。
> `D:\myAI\newstranscribe\README.md` 侧重快速使用，本文侧重“为什么这样做、先后做了什么、怎样读懂代码”。
>
> 更新提示：第一至十五节记录初版开发过程。后续新增的自动说话人区分见第十六节；前文“尚未区分说话人”等描述属于初版状态，不是当前能力上限。

## 一、先弄清楚：我们究竟要做什么

最初的需求是：把 BBC MP3 音频自动转换为英文文本。

随后需求逐渐明确为：

1. 输入不局限于 BBC，也可以是其他有权使用的英文音频。
2. 做成网页版，手机和电脑都能上传音频。
3. 输出英文原文，不是中文翻译。
4. 不使用按分钟收费的语音识别 API。
5. 第一版只要求同一 Wi-Fi 内使用，电脑保持开机。

把这些要求压缩成一句话：

**用自己的电脑运行一个网页服务，让同一 Wi-Fi 中的手机、电脑上传英文音频，在电脑上识别，再把英文文本返回浏览器。**

这里的“免费”是开源软件和本地计算，不等于不消耗电力，也不等于有永久免费、全天在线的云服务器。

### 为什么先限制第一版范围

第一版只实现上传、转录、查看、编辑和 TXT 下载，没有一开始就做：

- 自动抓取 BBC 网站。
- 中文翻译和摘要。
- 注册、登录和历史记录。
- 公网部署和多人任务队列。

这就是最小可用版本的思路：先证明最重要的流程能运行，再逐步扩展。它既减少开发量，也方便排错。

## 二、先理解整体结构，再开始写代码

```text
手机 / 电脑浏览器
       │ 上传英文音频（通过局域网）
       ▼
电脑上的 Streamlit 网页服务
       │ 接收上传内容，校验文件
       ▼
TranscriptionService 转录服务
       │ 加载本地模型、建立临时音频文件
       ▼
faster-whisper
       │ PyAV 解码 → 模型推理 → 产生带时间戳片段
       ▼
Transcript 结果
       │ 英文文本、开始时间、结束时间
       ▼
浏览器查看 / 编辑 / 下载 TXT
```

手机只负责网页操作，并不运行 Python，也不承担模型推理。

### 为什么不用自己训练模型

语音识别的核心能力由预训练的 Whisper 模型提供。本项目做的是使用模型进行推理，而不是收集数据、训练神经网络。

可以把它理解为：模型是已经学会英语听写的“大脑”，Python 项目负责给它递交音频、管理资源、展示结果。

### 为什么选择这些技术

| 技术 | 在本项目中的作用 | 选择原因 |
| --- | --- | --- |
| Python 3.12 | 执行应用和模型调用 | 与本次使用的依赖组合兼容，已经实际运行验证 |
| Streamlit | 生成网页、处理上传和交互 | 不需要先搭建独立的 HTML/JavaScript 前端，适合快速原型 |
| faster-whisper | 调用 Whisper 模型识别英语 | 可用本地 CPU 推理，不需要收费 API |
| PyAV | 读取 MP3、WAV 等音频 | 负责解码，常规安装通常不必额外装系统 FFmpeg |
| unittest | 自动化测试 | Python 标准库自带，不需要额外测试框架 |
| Python 标准库 | 路径、临时目录、锁、下载、哈希校验 | 能完成的工作不再增加第三方库 |

`base.en` 是默认英语模型；`small.en` 是另一个可选英语模型，通常需要更多资源。当前已准备并实际验证的是 `base.en`，不是两个模型都已安装。

## 三、实际开发过程：项目怎样一步步变成现在这样

这是过程回顾，不代表每一步当时都一次成功。

| 阶段 | 做了什么 | 得到了什么 |
| --- | --- | --- |
| 需求讨论 | 从 BBC MP3 转录明确到手机/电脑网页、本地免费、同一 Wi-Fi | 确定部署方式和第一版范围 |
| 环境检查 | 查看目录、Python 解释器 | 起初目录为空；默认 Python 是 3.15，后来确认已安装 3.12.10 |
| 初版实现 | 建立页面、转录模块、配置、启动脚本、说明和测试 | 具备完整代码，但不等于已经可以运行 |
| 依赖安装排错 | 检查日志，发现默认下载速度慢，改为本次使用清华 PyPI 镜像 | 安装 Streamlit、faster-whisper 等依赖 |
| 网页启动 | 启动服务、检查 8501 端口及 HTTP 响应 | 解决“电脑网页打不开” |
| 模型下载排错 | 从异常堆栈发现 Hugging Face 连接超时，镜像返回 403 | 确认问题在模型准备阶段，不是音频 |
| 本地模型支持 | 增加下载脚本、SHA-256 校验和本地模型优先加载 | 成功准备 `base.en` 模型 |
| 真实转录排错 | 实际运行时发现 PyAV 19 的接口不兼容 | 将 PyAV 固定为 16.0.1 |
| 回归验证 | 自动化测试、合成英语语音转录、HTTP 检查 | 13 项测试通过，真实模型推理成功，网页返回 HTTP 200 |

本项目一个很重要的经验是：**代码写完、依赖装好、页面能打开、模型能加载、真实音频能转录，是五个不同的验证阶段。**

## 四、第一步：准备 Python 和独立环境

### 4.1 为什么选 Python 3.12

开发早期电脑默认 Python 为 3.15.2。后来确认 Python 3.12.10 已安装，因此实际项目选择 Python 3.12 创建虚拟环境。

这不表示 Python 3.15 一定不支持，而是语音识别依赖包含多个二进制包，使用已验证组合比直接追新更稳妥。

### 4.2 什么是虚拟环境

虚拟环境是当前项目独立的 Python 包环境。例如本项目的解释器是：

`D:\myAI\newstranscribe\.venv\Scripts\python.exe`

它能避免其他项目升级依赖后影响这个项目，也不必卸载电脑中其他 Python 版本。

如果在一台新电脑上复现，在 PowerShell 执行：

```powershell
Set-Location 'D:\myAI\newstranscribe'
py -3.12 --version
py -3.12 -m venv 'D:\myAI\newstranscribe\.venv'
```

已经有可用虚拟环境时，不需要反复创建。

### 4.3 安装依赖

依赖声明位于 `D:\myAI\newstranscribe\requirements.txt`：

```text
streamlit>=1.41,<2
faster-whisper>=1.1,<2
# faster-whisper 1.2.1 passes metadata_errors to av.open; PyAV 19 removed it.
av==16.0.1
```

`>=` 和 `<` 表示允许的版本区间；`==` 表示精确指定版本。

安装命令：

```powershell
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' -m pip install -r 'D:\myAI\newstranscribe\requirements.txt'
```

下载过慢时，可以只对这一条安装命令使用镜像：

```powershell
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' -m pip install -r 'D:\myAI\newstranscribe\requirements.txt' --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

不要同时启动多个进程往同一个虚拟环境安装包。命令开始下载不代表安装成功，需要等待结束并检查结果。

PowerShell 中的 `&` 是调用运算符，用来运行引号中的可执行文件路径；`-m pip` 表示用指定 Python 运行 pip，避免把依赖装到错误的解释器。

注意：当前依赖文件不是完整锁文件。以后重新安装时，Streamlit、faster-whisper 及其间接依赖可能变化，仍需重新测试兼容性。

## 五、第二步：认识当前项目文件

以下是以 `D:\myAI\newstranscribe` 为根目录的结构示意，后文提到的文件都位于此根目录下：

```text
D:\myAI\newstranscribe\
├── app.py                       网页入口
├── transcriber.py               上传验证、模型加载、转录服务、结果结构
├── download_model.py            base.en 模型下载和完整性校验
├── requirements.txt             依赖版本要求
├── start.ps1                    PowerShell 启动入口
├── README.md                    安装和使用说明
├── learn_newstranscribe.md       本学习文档
├── .gitignore                   排除环境、模型、日志等生成内容
├── .streamlit\
│   └── config.toml              监听地址、端口、上传限制等配置
├── tests\
│   ├── test_app.py              页面状态和交互测试
│   ├── test_transcriber.py      转录服务逻辑测试
│   ├── test_download_model.py   下载与校验测试
│   └── test_audio.py            真实音频解码兼容性测试
├── .venv\                      虚拟环境，安装时生成
├── .models\
│   └── base.en\                 下载后的本地模型
└── .logs\                      本次调试所用的测试音频、辅助脚本和日志
```

根目录中另外存在安装、服务和测试日志，它们是本次运行产生的诊断记录，不是应用必须依赖的源代码。

当前版本不需要数据库，也不要求用户创建固定的音频输入、文本输出目录：通过网页上传，结果通过浏览器下载。

## 六、第三步：实现转录服务

主要阅读 `D:\myAI\newstranscribe\transcriber.py`。

### 6.1 先定义结果，不把模型对象直接交给页面

代码定义了两个数据类：

- `TranscriptSegment`：一段文本，以及开始、结束秒数。
- `Transcript`：全部片段和音频总时长。

`Transcript.text` 把各片段用换行连接，供页面显示和 TXT 下载使用。

这使页面不需要了解 faster-whisper 的内部返回对象，模型相关逻辑集中在一个模块里。

`@dataclass(frozen=True)` 的作用是简化数据对象定义，并禁止常规方式重新给字段赋值。结果片段还保存为元组，减少后续意外修改。

### 6.2 校验上传文件

`validate_upload(filename, size)` 检查：

1. 后缀是否属于 MP3、WAV、M4A、FLAC、OGG、AAC。
2. 文件是否为空。
3. 是否超过 `50 * 1024 * 1024` 字节。

页面先校验一次，服务入口再校验一次。前者用于尽快提示用户，后者避免其他调用方绕过页面限制。

**后缀校验不是文件内容真实性校验。** 把损坏文件改名为 MP3 仍然可能通过后缀检查，最终是否能解码需要 PyAV 判断。

### 6.3 加载模型

`create_model(name)` 先检查模型目录，例如：

`D:\myAI\newstranscribe\.models\base.en`

如果检测到 `config.json`、`model.bin`、`tokenizer.json`，就传入本地目录，并启用 `local_files_only=True`。否则传入模型名称，让库尝试从 Hugging Face 下载。

主要推理设置：

```python
device="cpu"
compute_type="int8"
```

- `cpu`：不要求 NVIDIA 显卡。
- `int8`：使用适合 CPU 的量化计算方式，通常能减少资源消耗；不表示所有模型都一样快。

存在文件只是本地准备状态的基本检查，不是每次启动都重新校验模型哈希。文件损坏、内容不匹配仍可能加载失败。

加载异常会转换成 `ModelLoadError`，同时通过 `raise ... from exc` 保留底层异常，方便日志诊断。

### 6.4 复用模型，而不是每个文件都重新加载

`TranscriptionService` 保存当前模型和名称：

- 同一个服务连续使用 `base.en`：复用已加载模型。
- 从 `base.en` 切换到 `small.en`：释放旧引用，再加载新模型。
- 加载失败：不把错误模型标记为已经准备好，下次允许重试。

这是性能优化，也能避免同时在内存中主动保留两套模型。

### 6.5 用锁保护计算资源

服务使用 `threading.Lock`，获取方式是：

```python
self._lock.acquire(blocking=False)
```

没有拿到锁就抛出 `BusyError`，让页面提示稍后重试，而不是把多个重任务同时压给电脑。

这是**单进程内的并发保护**，不是任务队列，也不是跨多台服务器的分布式锁。当前部署只有一个网页服务进程，因此足够用于第一版。

`finally` 中释放锁，确保转录异常后不会一直处于“忙碌”状态。

### 6.6 临时文件为什么不能直接用上传文件名

上传文件名由用户提供，不能直接拿来当服务器保存路径。

当前做法：

1. 用 `TemporaryDirectory` 创建随机工作目录。
2. 使用固定文件名 `audio` 加上已经检查的后缀。
3. 写入上传字节。
4. 在临时目录有效期内完成识别。
5. 离开 `with` 后自动清理目录。

这样，即使文件名包含路径字符，也不会被用来指定服务器磁盘位置。

正常返回和普通异常都会触发清理；强制结束进程或断电时不能保证自动清理。上传内容也可能仍暂存在浏览器、服务会话内存中，不能把它理解为安全擦除。

### 6.7 真正调用识别

核心调用的参数为：

```python
segments, info = self._model.transcribe(
    str(audio_path),
    language="en",
    task="transcribe",
    beam_size=5,
    vad_filter=True,
)
```

| 参数 | 作用 |
| --- | --- |
| `language="en"` | 明确按英语识别，不依赖语言自动检测 |
| `task="transcribe"` | 转录语音，不执行翻译任务 |
| `beam_size=5` | 解码时保留多个候选，有准确率与速度取舍 |
| `vad_filter=True` | 使用语音活动检测过滤部分非语音区域 |

### 6.8 最容易忽略的一点：segments 是惰性迭代器

不能认为执行完 `model.transcribe(...)` 就代表识别已完成。音频解码、特征准备等可能在调用中进行，而片段生成和主要推理会在遍历 `segments` 时继续执行。

因此代码必须在临时目录存在期间完成：

```python
for segment in segments:
    text = segment.text.strip()
```

如果过早退出临时目录，再到外面遍历，就可能遇到文件或资源生命周期问题。

每产生片段，服务可调用 `on_progress` 回调，把进度交给页面。这个比例来自片段结束时间 / 音频总时长，最多先显示 99%，最后由页面显示完成；它不是剩余秒数预测，也不会准确反映模型下载进度。

## 七、第四步：把转录能力放到网页上

主要阅读 `D:\myAI\newstranscribe\app.py`。

### 7.1 为什么没有单独的前端项目

Streamlit 用 Python 声明页面组件，负责生成浏览器界面。当前不需要自己维护独立的前端构建系统、REST API 和页面路由。

不过它仍然有浏览器和服务端：页面在手机上显示，Python 代码在电脑上运行，并不是在手机浏览器里直接执行 Python。

### 7.2 页面组件如何对应需求

| 网页需求 | 使用的组件或能力 |
| --- | --- |
| 上传音频 | `st.file_uploader` |
| 选择模型 | `st.selectbox` |
| 预览播放 | `st.audio` |
| 点击开始 | `st.button` |
| 等待和进度 | `st.spinner`、`st.progress` |
| 校对文本 | `st.text_area` |
| 下载 TXT | `st.download_button` |
| 查看时间戳 | `st.expander`、`st.dataframe` |
| 错误或成功提示 | `st.error`、`st.warning`、`st.success` |

当前“复制”方式是从文本框全选复制，没有单独的一键复制按钮。

### 7.3 Streamlit 重跑和会话状态

Streamlit 的一个关键特点是：用户交互通常会让页面脚本从上到下重新执行。

如果只把结果放在普通局部变量中，下一次交互后就可能没有了。因此页面把结果保存到 `st.session_state`：

- `transcript`：原始片段结果。
- `result_name`：建议下载文件名。
- `elapsed`：处理耗时。
- `editable_text`：用户当前校对后的文本。

下载按钮读取的是 `editable_text` 对应文本，所以文本框修改提交并触发重跑后，下载内容会包含修改。时间戳表仍展示原始模型输出，不会随人工修改重新对齐。

更换音频或模型时，回调 `clear_result()` 删除旧结果，避免把上一个音频的文本误认为新结果。

### 7.4 模型资源缓存与会话状态有什么区别

`get_service()` 使用 `@st.cache_resource`：

- 资源缓存用于复用转录服务及其模型，通常可被不同会话共享。
- 会话状态用于保存当前用户的页面结果，不用来共享用户文本。

正因为服务资源共享，内部才需要锁来保护并发调用。

### 7.5 错误提示应该按阶段区分

页面单独处理：

- `BusyError`：其他任务占用服务，稍后重试。
- `ModelLoadError`：模型下载或加载失败，还没开始读取用户音频。
- 其他异常：记录完整堆栈，显示一般转录错误提示。

日志使用 `logger.exception(...)` 保存异常上下文。最初只有统一错误提示，导致用户以为音频坏了；读取日志后才改为单独提示模型问题。

## 八、第五步：让同一 Wi-Fi 的手机也能访问

配置文件：`D:\myAI\newstranscribe\.streamlit\config.toml`。

关键设置：

```toml
[server]
address = "0.0.0.0"
port = 8501
headless = true
maxUploadSize = 50
enableCORS = true
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

### 三个地址概念不要混淆

- `0.0.0.0`：服务监听所有 IPv4 网络接口，不是让用户在浏览器输入的地址。
- `localhost` / `127.0.0.1`：当前设备自身。在电脑上能访问电脑服务，手机输入则指向手机自己。
- 电脑的 Wi-Fi IPv4：手机访问电脑时要用的地址。

比如电脑 IPv4 是 `192.168.1.23`，手机就访问 `http://192.168.1.23:8501`。这是示例地址，实际用 `ipconfig` 查询。

电脑和手机需要连接同一网络，Windows 防火墙只允许可信专用网络通信；路由器访客网络或 AP 隔离也可能阻止设备互访。

保留 CORS 和 XSRF 防护，不通过关闭防火墙来解决问题。它们也不等于用户登录功能。本项目仍然没有身份验证，不应把端口直接开放到公网。

HTTP 不加密，仅限可信局域网。`gatherUsageStats=false` 关闭的是 Streamlit 使用统计，不代表模型下载永远不需要网络。

## 九、第六步：解决实际遇到的三个主要问题

### 问题一：电脑网页打不开

**当时现象：** 浏览器无法连接网页。

**检查结果：** Streamlit、faster-whisper 尚未安装成功，8501 端口没有监听。后台下载仍在进行，速度较慢。

**解决过程：**

1. 查看安装日志，而不是先怀疑浏览器。
2. 检查安装进程，避免重复安装。
3. 测试清华 PyPI 镜像可访问后，只为本次安装使用镜像。
4. 等依赖安装完成，再启动 Streamlit。
5. 请求首页和健康检查接口，确认 HTTP 200。

**学到的知识：** 浏览器页面依赖后端服务正在运行。创建了代码文件，并不等于已经部署了网站。

HTTP 200 只能证明 HTTP 请求成功，还需要网页交互测试和真实转录测试，不能只靠状态码判断全部功能正常。

### 问题二：音频可以播放，却提示转录失败

**日志关键异常：**

```text
ConnectTimeout
LocalEntryNotFoundError
```

**真实原因：** 程序从 Hugging Face 查询或下载模型时连接超时，本地没有可用模型。异常出现在模型构造阶段，尚未读取用户音频。

最初又检查了 Hugging Face 镜像，但返回 403；随后测试 ModelScope 的对应仓库可以访问，才采用显式下载脚本。

**这里要分清两种下载：**

- pip / PyPI：下载 Python 库。
- Hugging Face / 模型镜像：下载模型权重与配置。

解决 pip 下载慢，不会自动解决模型站点不可达。

### 问题三：模型下载好了，真实转录仍报错

**日志关键异常：**

```text
TypeError: open() got an unexpected keyword argument 'metadata_errors'
```

**真实原因：** 当时安装了 PyAV 19.0.2，而 faster-whisper 1.2.1 的解码调用传入 `metadata_errors`，新版本 PyAV 接口不再接受这个参数。

**解决过程：**

1. 停止正在运行的服务，避免加载中的库文件影响替换。
2. 把 PyAV 固定为 16.0.1。
3. 在 `requirements.txt` 记录约束，避免下次重装又出现同样问题。
4. 增加真实 WAV 解码测试，不只用假模型测试。
5. 重新执行实际模型转录，确认成功。
6. 重启网页服务，让新依赖生效。

**学到的知识：** 满足依赖的版本范围，不保证运行时所有接口一定兼容。没有真实调用的测试，可能发现不了这种问题。

## 十、第七步：理解模型下载脚本

文件：`D:\myAI\newstranscribe\download_model.py`。

该脚本是针对这次网络问题添加的，不是使用网页的每一次都要运行。

执行方式：

```powershell
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' 'D:\myAI\newstranscribe\download_model.py'
```

它只下载 `base.en`，操作步骤是：

1. 从 ModelScope 社区镜像查询仓库文件元数据。
2. 确认包含配置、权重、分词器和词表。
3. 为每个文件取得版本、大小及 SHA-256。
4. 已存在且哈希相同的文件直接跳过。
5. 新文件先写入 `.part` 临时文件。
6. 校验字节数和 SHA-256。
7. 校验通过才替换最终文件，失败则清理临时文件。

四个下载文件的作用：

| 文件 | 作用 |
| --- | --- |
| `config.json` | 模型结构和配置 |
| `model.bin` | 模型权重，主要占用空间 |
| `tokenizer.json` | 分词器配置，让模型 token 与文本对应 |
| `vocabulary.txt` | 词表 |

模型目录是 `D:\myAI\newstranscribe\.models\base.en`，其中权重文件约 138.5 MiB。

SHA-256 能检查内容是否与镜像公布的信息一致，但元数据也来自同一镜像，所以它不是上游真实性的独立证明。脚本只下载固定文件，不执行仓库里的 Python 代码，也不会把用户音频上传给模型站点。

脚本目前没有断点续传：已经校验的完整文件会跳过，下载中断的单个大文件需要重新开始。也不要同时运行多个下载进程写同一个模型目录。

## 十一、第八步：怎样证明代码真的能用

### 11.1 第一层：模块逻辑测试

`D:\myAI\newstranscribe\tests\test_transcriber.py` 使用假模型，验证：

- 后缀、大小、空文件检查。
- 转录片段、空文本过滤和进度。
- 模型复用、切换和失败重试。
- 临时目录在成功和异常时都会清理。
- 非阻塞锁能拒绝重叠任务。
- 本地模型路径启用仅本地加载。
- 模型加载错误转换为明确异常。

假模型不执行真正的语音识别，速度快，适合测试我们自己写的管理逻辑。

通过 `model_factory` 参数注入假模型，是依赖注入的一个简单例子：把昂贵的真实组件替换成可控对象，测试不同结果与异常。

### 11.2 第二层：页面测试

`D:\myAI\newstranscribe\tests\test_app.py` 使用 Streamlit 的 `AppTest`，检查：

- 未上传文件时开始按钮不可用。
- 默认模型和模型选择。
- 结果文本能够显示、编辑。
- 切换模型后旧结果清除。

最初页面首次运行超出了测试工具默认 3 秒等待，因此将 `default_timeout` 调整为 20 秒。延长测试超时不是优化识别速度，而是避免正常页面初始化造成测试误报。

这些测试不等于真实手机浏览器端到端测试，也没有自动覆盖完整的用户上传流程。

### 11.3 第三层：下载和解码测试

- `D:\myAI\newstranscribe\tests\test_download_model.py`：用模拟响应检查下载、文件校验、跳过已验证文件、拒绝损坏内容；不访问真实模型网站。
- `D:\myAI\newstranscribe\tests\test_audio.py`：生成一个 WAV，真正调用 faster-whisper 的解码函数，检查已安装 PyAV 是否兼容；不下载模型。

### 11.4 运行全部自动化测试

```powershell
Set-Location 'D:\myAI\newstranscribe'
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' -m unittest discover -s 'D:\myAI\newstranscribe\tests' -v
```

修复后的开发记录中，结果为 `Ran 13 tests` 和 `OK`。测试数量随以后增加功能可能变化。

另外检查依赖声明是否冲突：

```powershell
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' -m pip check
```

`pip check` 不能代替运行时测试：本次 PyAV 接口问题就是需要真正解码才能发现的。

### 11.5 第四层：真实模型推理

排错时使用 Windows 语音合成生成一段英语测试音频，再用真实模型进行转录，得到：

```text
This is the English News. Today we are testing the audio transcription tool.
```

一次性辅助文件保存在 `D:\myAI\newstranscribe\.logs`，包括测试 WAV 和 `verify_transcription.py`；它们不是网页启动必需文件，也不属于正式单元测试集合。

这证明本地模型加载、音频解码、VAD 和推理这条链路至少在该测试样本上跑通，但不能证明所有音频格式、BBC 节目、口音或手机网络都已验证。

## 十二、第九步：现在怎样运行和使用

### 12.1 启动网页

```powershell
Set-Location 'D:\myAI\newstranscribe'
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' -m streamlit run 'D:\myAI\newstranscribe\app.py'
```

不要直接用 `python app.py` 当作常规启动方式，Streamlit 页面需要由 Streamlit 服务运行。

先切换项目目录，是为了加载 `D:\myAI\newstranscribe\.streamlit\config.toml`。

也可以执行：

```powershell
& 'D:\myAI\newstranscribe\start.ps1'
```

启动脚本会检查虚拟环境和关键库能否导入，再启动服务。它不会自动下载模型，也不等于完整的兼容性检查。若 PowerShell 禁止脚本，使用前面的 Python 命令，不必放宽整个系统的执行策略。

### 12.2 访问和转录

1. 电脑打开 `http://localhost:8501` 或 `http://127.0.0.1:8501`。
2. 手机访问电脑当前 Wi-Fi IPv4 对应的地址，端口为 8501。
3. 上传 1～3 分钟清晰英语音频，先选“快速模式 · base.en”。
4. 点击开始，保持页面打开和电脑运行。
5. 完成后校对文本，并下载 TXT。

当前 `base.en` 已准备好；不要把“页面里列出了 small.en”理解为 small.en 也已下载并测试。

前台运行服务时保持终端打开，按 Ctrl+C 停止。开发过程中也用过后台进程，因此有时关闭当前终端并不代表服务已停止；遇到端口占用应先核对进程，避免反复启动。

### 12.3 从启动到一次识别完成的调用顺序

```text
Streamlit 运行 app.py
  → 绘制上传组件和模型选择框
  → 用户上传，页面校验并提供音频预览
  → 用户点击开始
  → get_service() 取得缓存中的 TranscriptionService
  → transcribe() 校验文件、获取锁
  → create_model() 按需加载本地或下载模型
  → 创建临时文件
  → 模型转录，遍历片段并更新页面进度
  → 返回 Transcript，临时目录清理，锁释放
  → 页面保存会话结果
  → 显示文本、下载按钮、原始时间戳
```

## 十三、以后遇到问题，按什么顺序检查

| 现象 | 优先检查 | 不要立即做的事 |
| --- | --- | --- |
| 电脑打不开页面 | 服务是否运行、依赖是否安装、8501 是否监听 | 不要先重装 Python 或关闭防火墙 |
| 电脑能打开，手机不能 | 同一 Wi-Fi、电脑 IPv4、防火墙专用网络、AP 隔离 | 不要把 localhost 直接复制到手机 |
| 提示模型加载失败 | 模型是否完整、模型网站连接、底层日志 | 不要先反复转换音频 |
| `metadata_errors` 参数错误 | PyAV 版本是否为项目固定版本 | 不要只靠升级全部依赖碰运气 |
| 音频能播放但不能解码 | 实际编码、格式支持、完整异常 | 不要认为后缀相同就等于编码相同 |
| 模型一直处理 | 音频长度、模型大小、CPU/内存、模型是否仍在下载 | 不要同时连续提交多个重任务 |
| 文本有误 | 背景音乐、口音、数字、人名、模型大小 | 不要把模型输出当成百分之百准确 |

如果是前台运行，异常在终端中查看；如果是本次开发使用的后台日志重定向方式，查看 `D:\myAI\newstranscribe\server.stderr.log`。

日志文件名是启动命令决定的，不是 Streamlit 无论如何都会自动生成该文件。

## 十四、当前边界和下一步学习方向

### 已经实现与已经验证不是同一个概念

- 已实现：上传、英语识别、页面校对、TXT 下载、时间戳查看、临时文件清理和并发保护。
- 开发时已验证：13 项自动化测试、合成英语音频的真实模型推理、电脑 HTTP 请求。
- 仍需要人工验证：用户实际 BBC 音频效果、不同手机浏览器上传与下载、当前路由器中的手机访问。

### 当前限制

- 单服务一次只接受一个计算任务，没有排队和持久化。
- 不保存历史；刷新、断线可能丢失结果，也不保证立即取消后台处理。
- 50 MB 是上传大小限制，不是时长限制。长音频解码仍可能占用大量内存。
- 无登录、HTTPS 和公网安全防护，不应直接暴露公网。
- 不区分说话人、不输出 SRT、不做翻译，也不自动下载 BBC 内容。
- 音频与结果存在会话暂存，不承诺立即安全擦除。
- 模型和本地日志可能占用磁盘，应按需要管理，不能误删仍在使用的文件。

### 推荐的后续练习（尚未实现）

1. 根据片段开始、结束时间新增 SRT 导出，并为时间格式写测试。
2. 细分音频解码失败、内存不足等错误提示。
3. 增加音频时长上限和更清晰的资源提示。
4. 增加模型准备状态展示，避免选择尚未下载的模型后长时间等待。
5. 为真实手机上传和下载补充手动验收清单。
6. 如果以后需要外网使用，先设计身份验证、HTTPS、限流、任务队列和隐私策略，而不是只打开端口。

练习时一次只改一个目标，先补测试，再修改实现，最后重新跑已有测试。

## 十五、建议的阅读和动手顺序

1. 阅读本文第一至第五节：先理解需求、结构和运行环境。
2. 阅读 `D:\myAI\newstranscribe\transcriber.py`：沿着 `validate_upload` → `create_model` → `TranscriptionService.transcribe` 学习。
3. 阅读 `D:\myAI\newstranscribe\app.py`：观察页面组件、会话状态、模型资源缓存怎样配合。
4. 阅读 `D:\myAI\newstranscribe\tests` 中的测试：先看正常路径，再看失败重试与清理。
5. 阅读 `D:\myAI\newstranscribe\download_model.py`：学习流式下载、哈希校验和临时文件替换。
6. 自己运行一次短音频，观察终端或日志，再修改一个纯页面文字，理解 Streamlit 重跑机制。

最后尝试不用看代码回答这五个问题：

- 手机上传之后，模型是在手机还是电脑上运行？
- 为什么模型加载失败时不应该先转换音频格式？
- 为什么临时目录必须覆盖 segments 的整个遍历过程？
- 为什么结果用 session_state 保存，模型服务却用 cache_resource？
- 为什么“13 项测试通过”仍然不能代替用户真实音频和手机浏览器测试？

如果能够解释清楚，就已经掌握了这个项目的核心思路：**把预训练模型包成可靠的服务，再用网页把能力交给用户，并通过日志、分层测试和真实样本逐步证明它能工作。**

## 十六、后续迭代：免账号的自动说话人区分

新增需求：转录文本要区分不同说话人，同时继续免费、本地运行，不要求注册账号或配置令牌。

选型采用 sherpa-onnx + 公开发布的 pyannote segmentation 3.0 ONNX + NeMo TitaNet small。相比需要额外 PyTorch 和受限整套管线访问的方案，这个组合有 Windows CPU 包和无需令牌的公开下载文件。不根据句号、停顿或内容猜说话人，也不推断真实姓名。最初候选 Reverb v1 在检查下载包 LICENSE 后发现有非生产使用限制，因此没有用于最终实现；公开可下载不等于适合目标用途。

新增文件：

- `D:\myAI\newstranscribe\diarization.py`：本地声学分段、声纹聚类和词时间戳对齐。
- `D:\myAI\newstranscribe\download_speaker_models.py`：公开模型下载、大小校验和只复制指定归档文件的安全解包。
- `D:\myAI\newstranscribe\tests\test_diarization.py`：时间重叠匹配、未知标签、服务整合及兼容性测试。

流程变为：音频解码为 16 kHz 单声道 → 声学模型生成说话人时间段 → Whisper 开启 `word_timestamps=True` → 为每个词计算与说话人时间段的交集 → 合并相邻同说话人文字 → 页面和 TXT 显示标签。

为什么按词对齐？一个 Whisper 片段可能同时包含两个人的发言，整段只贴一个标签会丢失其中的说话人变化。当前按最大时间交集分配，没交集或最大交集并列则标记 `Speaker unknown`，不把缺失证据强行归给某个人。

`TranscriptSegment` 新增可选 `speaker` 字段，默认 `None`，保持普通转录兼容；`Transcript.text` 在有标签时输出 `[Speaker 1] ...`。前端加入开关、人数选择，变更配置会清除旧结果；下载仍然取当前编辑文本，因此保留说话人标签。

服务仍用同一把锁保护重任务，缓存已加载分离器；模型缺失时给出单独提示，可关闭区分功能回到普通转录。人数自动估计可能不准确，可以指定已知人数，但标签只在当前录音内有效，并不跨文件识别人。

本次新增下载与此前 ModelScope 脚本不同：GitHub 历史资产未提供 SHA-256，只能检查 HTTPS 下载和公开文件大小，不能宣称通过哈希校验。模型许可、网络可达性和实际分离效果需要分别核对。多路同时讲话仍可能误分或无法完整转录，标签需人工校对。

安装和使用命令见 `D:\myAI\newstranscribe\README.md` 的“自动区分说话人”章节。

## 十七、后续迭代：一键抓取并转录 BBC News

新增需求：不想每次手动下载音频再上传，希望“点一个图标/按钮”就自动抓取 BBC 最新新闻并转录。

先调研真实数据来源。目标节目 `p002vsmz` 是 BBC World Service 的 5 分钟新闻简报「BBC News」。节目列表页 `/programmes/p002vsmz/episodes/player` 的剧集由前端渲染，页面上没有可直接读取的链接；但每个剧集块都带 `data-pid="<剧集 id>"` 属性，按由新到旧排列，因此用正则 `data-pid="([bpw][0-9a-z]{7,})"` 取第一个即最新一期。

拿到剧集 id 后分两步换到音频：先访问 `/programmes/{id}.json` 得到 version id，再请求公开媒体选择器 `open.live.bbc.co.uk/mediaselector/.../vpid/{version}/format/json`。它只返回 HLS（`.m3u8`）/DASH 流，没有直链 MP3。关键验证：写探针让项目自带 PyAV 直接 `av.open` 该 `.m3u8`，可以正常打开并解码 AAC（5 分钟音频全量解码约 7 秒），因此**无需自己实现 HLS 分段下载**，把地址直接交给 faster-whisper 即可。

新增/改动文件：

- `bbc.py`：抓取与解析。纯函数 `parse_episode_pids`、`select_audio_href` 便于测试；`latest_episode()` 串起三步网络请求，失败统一抛 `BBCError`。
- `transcriber.py`：把原 `transcribe` 拆成 `transcribe`（写临时文件后调用）与 `_run`（锁、模型、分离、推理），新增 `transcribe_source(source, ...)`，`source` 可为本地路径或 http(s) 媒体地址；这样网页上传与 BBC 流共用同一套逻辑和同一把锁。
- `app.py`：新增「📡 一键抓取 BBC News」区域与按钮，点击后抓取最新一期并转录，结果与普通转录共用展示/编辑/下载，并显示来源。
- `bbc_transcribe.py`：无界面一键脚本，抓取、转录、保存 TXT 到 `transcripts/`（可选自动打开）。
- `run-bbc.bat` + `create-shortcut.ps1`：在桌面生成 `BBC News Auto Transcript.lnk` 快捷方式，双击即运行上面脚本。
- `tests/test_bbc.py`：解析顺序与去重、媒体选择与回退、`latest_episode` 正常/空/网络失败、`transcribe_source` 传参等，均用假数据，不联网。

为什么“抓取”和“转录”要在同一把锁内：两者都吃 CPU 和内存，且模型只有一份。`transcribe_source` 复用 `_run` 的锁，避免网页按钮与上传任务同时跑。

版权与边界：这是**自动下载 BBC 内容**，与初版“不自动下载”的定位不同，属于用户自行承担的选装功能。README 已显著标注仅限个人、有权使用的场景。音频地址有时效，每次重新获取；网络受限会失败并提示。标签、准确度仍以人工核对为准。

## 十八、后续迭代：一键用 Chrome 打开网页

需求：希望桌面有个图标，双击就能用 Chrome 打开转录网页。

新增文件：

- `open-app.ps1`：先用 `Invoke-WebRequest` 探测 `http://localhost:8501` 是否可达；不可达则用 `Start-Process` 启动服务并轮询等待（最多 60 秒）；就绪后按 `Program Files` → `Program Files (x86)` → `LocalAppData` 顺序找到 `chrome.exe`，用 Chrome 打开该地址，找不到 Chrome 时退回默认浏览器。
- `open-app.bat`：双击入口，转调上面的 PowerShell 脚本。
- `create-open-shortcut.ps1`：在桌面生成 `News Transcriber.lnk` 快捷方式，目标是 `open-app.bat`，图标直接取 `chrome.exe,0`，让用户一眼看出“用 Chrome 打开”。

为什么先探测再启动：图标要“一点就开”。如果服务没运行就直接打开浏览器，只会看到连接失败页；先确保可达再打开，体验更稳。已运行的服务不会被重复启动（避免端口冲突）。

一个学到的经验：**改了 `.py` 代码必须重启服务**。Streamlit 会自动重载主脚本 `app.py`，但已导入的库模块（如 `transcriber`）保留在内存，不会热更新；否则会出现“界面是新的、底层是旧的”而导致 `AttributeError` 之类的问题。无界面脚本（`bbc_transcribe.py`、`run-bbc.bat`）每次都是全新进程，不受影响。

## 十九、迭代：只留一个桌面图标 + BBC 抓取后播放与期号信息

需求：桌面只需要一个图标（打开网页）就够；网页在自动抓取后要能播放音频、显示进度，并显示抓到的具体是哪一期。

改动：

- 桌面图标：移除 `run-bbc.bat` 与 `create-shortcut.ps1`（不再创建 `BBC News Auto Transcript.lnk`），只保留 `open-app.*` + `create-open-shortcut.ps1`（生成 `News Transcriber.lnk`）。`bbc_transcribe.py` 仍可作为可选命令行工具，但不再占用桌面图标。
- `bbc.py`：修正取音频的方式。原先直接用 `programme["versions"][0]["pid"]` 换音频，但一集可能有多个 version，只有带音频的那个可用（第一个常常 404），因此改为逐个 version 尝试，直到拿到音频流。新增 `DOWNLOAD_URL`：同一选择器的 `redir` 路由返回**可直接播放的 MP3**（`Content-Type: audio/mp3`，约 5 分钟 / 4.8 MB），供网页播放；HLS 仍交给 PyAV 解码用于转录。`BBCEpisode` 增加 `download_url` 字段。
- `app.py`：抓取成功后把这一期存入 `session_state["bbc_episode"]`，在按钮下方持久显示**抓到的具体一期**（标题、播出时间、节目编号）并给出 `st.audio` 播放器；进度条照旧显示。上传文件或切换模型时用 `clear_result()` 一并清除该期信息。

体验点：`<audio>` 跨域播放 MP3 不需要 CORS 头，所以浏览器可以直接播 BBC 的 `redir` 链接；播放设备需要能访问 BBC，但不要求与运行服务的电脑是同一台。


## 二十、迭代：把最新一期 BBC 音频和文本保存到本地

需求：网页抓取最新一期 BBC News 后，希望把**这一期的音频和文本保存到电脑本地**，页面上继续写明**具体是哪一期**，并且**手机也能回放**。

改动：

- `bbc.py`：新增 `DOWNLOAD_DIR`（`bbc_downloads`）与三个函数。`episode_slug` 用播出时间（`2026-11-04T14:00:00Z` → `2026-11-04_1400`）生成文件名标记，缺失时退回清洗后的标题；`download_audio` 把该期 MP3 流式下载到 `*.mp3.part` 再原子替换（沿用 `download_model.py`、`download_speaker_models.py` 的写法），空文件视为失败；`save_transcript` 把英文文本写到音频旁的 `.txt`，文件开头写明来源、期号、播出时间和节目编号。
- `app.py`：抓取成功后先 `download_audio` 保存音频，再用**保存到本地的文件**（`transcribe_source` 支持本地路径）转录，替代原来的 HLS 地址；转录文本用 `save_transcript` 落盘。`show_episode` 改为播放**本地保存的音频**（传 bytes，由 Streamlit 服务器分发），因此手机通过本网页即可回放，且不受 BBC 临时链接过期影响；保存失败时退回 BBC 的临时 MP3 链接，不再中断转录。会话状态新增 `bbc_audio_path`、`bbc_text_path`，并在 `clear_result` 中一并清除。写文件失败只记录日志、不影响转录结果显示。
- `.gitignore`：新增 `bbc_downloads/`，避免把受版权保护的 BBC 音频和文本提交进版本库。
- `README.md`：更新「一键抓取并转录 BBC News」章节，说明音频/文本保存位置与手机回放方式。
- `tests/test_bbc.py`：新增 `episode_slug`（广播时间与标题回退）、`download_audio`（成功命名与空文件拒绝）、`save_transcript`（写明期号）的测试；`tests/test_app.py` 新增本地保存路径的展示测试。

为什么改用保存到本地的文件转录：原来直接把 BBC 的 HLS 地址交给 PyAV。现在既然要保存音频，就让下载与转录共用同一份本地文件——只请求一次，转录结果与保存的音频严格对应；同时页面播放改为由本网页提供本地文件，播放设备（尤其是手机）不再需要能访问 BBC。保存失败时保留原来的在线流路径作为兜底，行为不回退。

一个容易忽略的点：`st.audio` 传**字符串**时会被当成 URL，手机就会去请求 `http://手机/xxx.mp3` 这种相对地址而播放失败；传 **bytes**（或文件对象）才会由 Streamlit 服务端把音频分发给任意设备。手机能访问网页本身依赖 `.streamlit/config.toml` 里的 `address = "0.0.0.0"` 和同一局域网，这一点与上一节一致。

## 二十一、迭代：网页顶部显示手机访问地址 + 提供 MP3 下载

需求：手机不想每次都去 `ipconfig` 找地址，希望在网页顶部直接看到；并且希望手机打开网页时能把抓到的 MP3 直接下载下来。

改动：

- `app.py`：新增 `local_network_ip()`（用 UDP socket 连一次 `8.8.8.8:80`，只为查出发包网卡，不真正发数据，失败返回 `None`）与 `phone_url()`（拼成 `http://<ip>:<port>`，端口用 `st.get_option("server.port")` 读取，读取失败退回 8501）。页面标题下方按结果显示一行「📱 手机访问」链接或提示。
- `app.py`：`show_episode` 在本地音频存在时，除 `st.audio` 播放外再加一个 `st.download_button`（`mime="audio/mpeg"`，文件名与保存的 `.mp3` 一致，带固定 `key`）。数据传 bytes，由 Streamlit 服务端分发，所以手机点按钮就能把 MP3 存到手机。
- `tests/test_app.py`：初始页断言出现「手机访问」提示；已保存音频的页面断言恰好一个下载按钮。

为什么用 `st.get_option` 取端口：写死 8501 在改端口后会误导，从配置读取能跟随 `.streamlit/config.toml`。为什么下载用 `st.download_button` 而不是 `<a download>` 链接：跨域链接的 `download` 属性常被浏览器忽略、手机多不认，把字节交给服务端既稳定又能保证拿到的就是保存的同一个文件。`DownloadButton` 在 `AppTest` 里只暴露 `click/run/set_value/value`，没有 `label`，因此测试只断言数量。

## 二十二、迭代：默认不区分说话人 + 抓取时立即显示期号

需求：一是把“自动区分说话人”改成默认关闭（普通转录）；二是抓到 BBC 最新一期后，**在下载/转录之前**就把是哪一期（如 `06/11/2026 ...`）显示出来，而不是等转录完成。

改动：

- `app.py`：说话人勾选框默认值由 `speaker_models_ready()` 改为 `False`，并加 `help` 说明默认关闭、需要时再开（`speaker_models_ready()` 仍用于未装模型时的提示）。
- `app.py`：新增 `show_episode_info()`，只显示标题/播出时间/节目编号。BBC 区把按钮结果先存进变量 `start_button`，紧跟一个 `st.empty()` 占位槽 `episode_slot`；抓到节目后**立即**用 `show_episode_info` 写入占位槽，再去下载和转录；页面末尾的完整 `show_episode`（含播放器与下载按钮）写入**同一个占位槽**，因此会在转录完成后**原地刷新**，不会重复出一条。
- `tests/test_app.py`：新增“说话人默认关闭”的断言。

为什么用 `st.empty()` 占位槽：同一位置重复写入只会替换内容，不会叠两条；既能“提前显示”，又能在保存完成后原地补上播放器/下载按钮。AppTest 会遍历容器内的元素，所以先前“已抓取一期”的断言仍然有效。

## 二十三、迭代：扫码直接打开 + 一键放行防火墙

需求：不想在手机上手动输入 IP，希望**手机直接打开并使用**。

改动：

- 新增 `phoneqr.py`：`qr_png(text)` 用 `qrcode` 生成 PNG；未安装或失败时返回 `None`，页面退回只显示文字，不报错。`qrcode` 作为新增依赖写进 `requirements.txt`（PNG 依赖 Streamlit 已带的 Pillow，故不必额外加）。
- `app.py`：顶部「📱 手机访问」下面用 `st.image` 显示该二维码（宽 170），手机相机/“扫一扫”即可打开本页；`qrcode` 不可用时自动跳过。
- 新增 `allow-phone.ps1`：需管理员运行，创建一条只放行**本局域网**（`-RemoteAddress LocalSubnet`）、TCP 8501、Private+Public 的防火墙规则，并打印可用地址；解决“网络被标为公用导致手机连不上”的常见问题。重复运行会先删旧规则，保持幂等。
- `tests/test_phoneqr.py`：断言 `qr_png` 返回 PNG 字节。
- `README.md`：手机访问章节改为“扫码即开”，并加入 `allow-phone.ps1` 说明。

为什么用二维码：手机最自然的“直接打开”就是扫码，比手输 IP 可靠，也不依赖第三方二维码服务（本地用 Pillow+qrcode 现算）。为什么防火墙脚本单独放行 `LocalSubnet`：既能连上手机，又不把端口暴露到公网。脚本只主动修改系统安全设置中的这一条规则，仍需要用户自己以管理员身份运行。

## 二十四、迭代：终端直接打印二维码（不必先开电脑网页）

需求：之前二维码只显示在网页上，而要看它就得先在本机打开网页——这不是用户想要的“手机直接打开”。希望**不打开电脑网页也能用手机打开**。

改动：

- `phoneqr.py`：把原本在 `app.py` 里的 `local_ip()`、`phone_url()` 移进来（并加 `DEFAULT_PORT`、`qr_ascii()`），网页与命令行共用。
- `app.py`：改为 `from phoneqr import ...`，新增 `current_phone_url()`（先用 `st.get_option("server.port")` 取端口，再调用 `phone_url(port)`），删除本地重复实现。
- 新增 `phone_address.py`：命令行打印「📱 手机访问地址」，并把 `qr_ascii()` 生成的方块二维码画在终端；`sys.stdout.reconfigure(encoding="utf-8")` 保证方块字符正确输出。这样**只要服务在跑，看一眼终端就能扫码**。
- `start.ps1`：启动前调用 `phone_address.py`，并设置 `[Console]::OutputEncoding = UTF8`，让二维码方块正常显示。
- `open-app.ps1`：改为通过 `start.ps1` 启动服务，于是电脑端图标的服务窗口里也会出现二维码。
- 新增 `create-phone-shortcut.ps1`：在桌面创建 `News Transcriber (Phone).lnk`，双击仅**启动服务并打印二维码**，不打开电脑浏览器——真正做到“手机优先”。
- `tests/test_phoneqr.py`：新增 `qr_ascii` 含方块字符、`phone_url` 返回合法地址或 `None` 的断言。

为什么用终端 ASCII 二维码：手机最自然的入口是扫码；把二维码放进**启动窗口**，就完全摆脱了“先开电脑网页”的依赖。Windows 终端（Windows Terminal）能渲染 `▀/▄/█` 方块，扫码即可；万一字体不支持，同一段还会打印纯文本地址作为兜底。

## 二十五、迭代：为“电脑关机也能用”做云端部署准备

需求：希望手机在**电脑关机**时也能使用。核对后确认：本机 `http://电脑IP:8501` 依赖那台电脑一直开机；要电脑关机也能用，必须把服务放到一个常开的地方。用户提出的“上传到 GitHub 私人仓库后在 GitHub 网站使用”——**直接做不到**，因为 GitHub 不运行你的程序（Pages 只能托管静态页）。可行的是把仓库接到一个会运行程序的平台。

改动（让项目可直接部署，且本地行为不变）：

- `app.py`：新增可选的**访问口令门** `password_guard()`，只有当 secrets 里配置了 `password` 才启用（用 `hmac.compare_digest` 比较）。本地没有 secrets 时行为完全不变。
- `app.py`：新增 `is_local_request()`，用 `st.context.headers` 的 Host 判断是否为本机/局域网地址；在云端（公共域名）**隐藏**局域网二维码与地址，因为那个地址在云端没有意义。
- `packages.txt`：`libgomp1`，供 Streamlit Cloud 用 apt 安装（`libgomp.so.1` 是 onnxruntime / CTranslate2 的常见系统依赖）。
- `.streamlit/secrets.toml.example`：口令配置模板（`secrets.toml` 本身仍在 `.gitignore` 中）。
- `DEPLOY.md`：Streamlit Community Cloud（推荐）、GitHub Codespaces（在 GitHub 网站里跑）、Hugging Face Spaces 三种部署步骤。
- `app.py` 的隐私说明改为“公网部署务必设置访问口令”。

为什么这样设计：把“口令”和“二维码隐藏”做成**按环境自动开关**，同一份代码既能本地零配置使用，又能公网安全部署，不必维护两个分支。顺带确认 `diarization.py` 是**惰性导入** `sherpa_onnx`，所以不启用说话人区分时，云端不需要加载那套模型，内存占用可控。

## 二十六、迭代：只给自己用——访问口令门

需求：云端或局域网都要**只有自己能用**，屏蔽其他人。

改动：

- `app.py`：强化 `password_guard()`——失败次数记入 `st.session_state.login_failures`，连续输错时 `time.sleep(min(5, failures-2))` 递增限速（只阻塞当前会话，不影响其他会话），成功后清零。新增 `logout_control()`，当口令门启用且已登录时，在侧边栏提供“退出登录”。
- `DEPLOY.md`：新增「只给自己用（屏蔽其他人）」章节：强口令生成命令、Secrets 填写方法，以及四种托管方式的“可见性”对比（Streamlit Cloud + 口令 / 私有 HF Space / Codespaces / 自建 VPS）。
- `README.md`：云端章节补充“部署后设置 `password`”。

为什么这样做：免费版 Streamlit Community Cloud 没有“私有应用”，访问口令是最落地的屏蔽手段；而“别人连页面都看不到”的需求应改用私有 HF Space 或 Codespaces。口令门默认关闭（没有 secret 就不生效），本机使用零影响。

## 二十七、迭代：口令可短 + 手机“记住这台设备”免输入

需求：上一步生成的口令太长，手机上输入不方便。

改动：

- `app.py`：`password_guard()` 支持**短口令**，并新增**书签免输入**——若网址带 `?k=<口令>`，直接判定为已登录（用 `hmac.compare_digest` 比较）。登录表单加一个 **「记住这台设备」** 勾选框，勾上后用 `st.query_params["k"] = 口令` 把它写进当前网址，用户存成手机书签/主屏图标即可一键进入、不再打字。
- `.streamlit/secrets.toml.example`：改为示例短口令 `k7m2qp`，并给出“6 位、避开 0/O/1/l/i 的随机码”生成命令。
- `DEPLOY.md`：把“只给自己用”章节改为短口令 + 「记住这台设备」链接的说明。
- `README.md`：云端章节同步说明。

为什么可行：口令只用于“首次登录”和“在别的设备上登录”，日常手机使用走 `?k=` 链接；把“打字次数”降到接近 0，就不必为了好输而牺牲太多强度——再配合前面的连续输错限速，短口令的风险可接受。`st.query_params` 的读写都包了 `try/except`，在不支持 query params 的环境（如 AppTest）里也不会报错。







