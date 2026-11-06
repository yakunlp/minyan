# 部署到云端（电脑关机，手机也能用）

本项目是**本地服务**：网页和 Whisper 模型都跑在运行它的那台电脑上。所以你的电脑一关机，`http://电脑IP:8501` 就打不开了。要让手机在电脑关机时也能用，必须把服务放到一个**不关机**的地方。

**重要结论：在 github.com 上直接“使用”是做不到的。** GitHub 只是代码托管，你点开私人仓库只会看到代码，它**不会运行**你的程序（GitHub Pages 只能托管静态网页，跑不了 Python）。但有两条和 GitHub 配合的免费路子，能实现你的目标。

> ⚠️ 安全与版权：本项目已内置**访问口令门**——只要在部署时设置 secret `password`，别人必须先输对口令才能看到界面。**部署到公网时请务必设置它**，否则任何人都能用，并可能触发 BBC 内容的下载。请自行评估版权与隐私责任。

## 只给自己用（屏蔽其他人）

在 Secrets 里设置 `password` 后，打开网页的人会先看到口令输入框；**没输对口令前，页面不会渲染任何功能**，也无法触发转录或 BBC 下载。

**口令可以很短**（手机上打字方便）。生成一个 6 位、易输入的随机码（在电脑上执行）：
```powershell
& 'D:\myAI\newstranscribe\.venv\Scripts\python.exe' -c "import secrets; a='abcdefghjkmnpqrstuvwxyz23456789'; print(''.join(secrets.choice(a) for _ in range(6)))"
```
把它填进 Secrets（Streamlit Cloud：**Advanced settings → Secrets**；本地：写入 `.streamlit\secrets.toml`）：
```toml
password = "k7m2qp"
```

### 手机上免输入：记住这台设备

首次在手机上输入口令时，勾选 **「记住这台设备（把本页加入书签，下次免输入）」**，页面地址会变成：

```
https://<你的应用>.streamlit.app/?k=<你的口令>
```

把这个**带 `?k=` 的完整链接**加到手机主屏/书签，以后点一下就进，**完全不用再输口令**。别人打开普通网址，仍然只能看到口令框。

> 这个链接相当于“登录凭证”，请勿转发；手机丢了就换一个 `password`，旧链接立即作废。


不同托管方式的“屏蔽能力”对比：

| 方式 | 别人能看到什么 | 说明 |
| --- | --- | --- |
| Streamlit Community Cloud + `password` | 只能看到**登录框**，进不去 | 免费版没有“私有应用”，口令就是本项目提供的办法 |
| Hugging Face **Private** Space | **几乎看不到**（需登录你的 HF 账号） | 最接近“只有我能用”的免部署托管；常开、内存更大 |
| GitHub **Codespaces** | **看不到**（只有你能进） | 端口默认私有（Port visibility = Private）；但不是常开，有免费额度上限 |
| 自己的 VPS + 防火墙 | **看不到** | 完全可控，但要自己维护 |

**结论**：图省事 → Streamlit Cloud + 口令（最省心）；要“别人连页面都看不到” → 用**私有 Hugging Face Space** 或 **Codespaces**。

补充：本机使用时，也可以在项目里创建 `.streamlit\secrets.toml` 写入 `password = "..."`，这样**同一 Wi-Fi 下别人扫到你的地址也要口令**。该文件已在 `.gitignore` 中，不会被推到 GitHub。

## 方案 A：Streamlit Community Cloud（推荐，手机随时可用）

把**你的 GitHub 仓库连接到 Streamlit Community Cloud**，由它替你运行，并给你一个网址。之后手机随时打开 `https://<应用名>.streamlit.app`，**你的电脑可以关机**（应用空闲会休眠，再次访问自动唤醒，第一次稍慢）。

1. 把项目推到 GitHub（公开或**私人仓库**都行）：
   ```powershell
   Set-Location 'D:\myAI\newstranscribe'
   git init
   git add .
   git commit -m "newstranscribe"
   git branch -M main
   git remote add origin https://github.com/<你的用户名>/<仓库名>.git
   git push -u origin main
   ```
   `.gitignore` 已排除 `.venv/`、`.models/`、`.logs/`、`transcripts/`、`bbc_downloads/`、`*.log`、`.streamlit/secrets.toml`，不会把大文件或口令传上去。

2. 打开 <https://share.streamlit.io> → 用 GitHub 登录 → **Create app** → 选择你的仓库：
   - Repository：你的仓库；Branch：`main`；**Main file path：`app.py`**。
   - 私人仓库需要在授权时允许 Streamlit 的 GitHub App 读取该仓库。

3. 打开 **Advanced settings → Secrets**，粘贴（设置访问口令）：
   ```toml
   password = "换成你自己的口令"
   ```

4. 点 **Deploy**。构建完成后会给你 `https://<名字>.streamlit.app`。手机打开它、输入口令即可用；**电脑可以关机**。

5. 依赖说明：`requirements.txt` 会自动安装；`packages.txt` 里的系统包（`libgomp1`）会由 apt 安装。首次转录会联网下载 `base.en` 模型（约 74MB）；云端磁盘是临时的，冷启动后会重新下载。

## 方案 B：GitHub Codespaces（就在 GitHub 网站里运行）

如果你就是想在“GitHub 网站里”跑它：

1. 打开仓库页面 → **Code → Codespaces → Create codespace on main**（手机浏览器也行）。
2. 在打开的终端里执行：
   ```bash
   pip install -r requirements.txt
   streamlit run app.py --server.port 8501
   ```
3. Codespaces 会转发 8501 端口，弹出 “Open in Browser”；把该转发地址设为 **Public** 后也能用手机打开。
4. 缺点：不是常开——每次要先开 Codespace，且有每月免费额度（个人账号约 120 core-hours/月）。

## 方案 C：Hugging Face Spaces（可选）

同样“从 GitHub 部署”：在 <https://huggingface.co/new-space> 新建 Space（SDK 选 **Streamlit**）→ 连接你的仓库或直接上传文件。免费 CPU 常开、内存更大，更适合跑 `base.en`/`small.en`。

## 关于手机访问地址提示

在云端打开时，页面**不会**再显示局域网二维码（那个地址在云端没有意义）。相关判断在 `app.py` 的 `is_local_request()`。
