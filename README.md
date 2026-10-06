# GameMale 自动签到 · 云端版

> **在 GitHub Actions 上自动签到，你的电脑不用开着。**
>
> 原理：论坛加了 Cloudflare 人机验证，会拦截云服务器——所以云端**不自己过验证**，
> 而是用你**在电脑上登录一次得到的一段会话 cookie**（存进仓库 Secret）。
> 有这段 cookie，云端就**已经是登录状态**，能直接签到、抽奖、互动，并把结果发到你邮箱。

---

## 一、怎么工作

```
你的电脑（只需一次，约 2 分钟）              GitHub 云端（每天自动，电脑不用开）
──────────────────────────────            ─────────────────────────────────
双击「获取cookie.bat」                      每天定时自动运行（北京 00:17 / 14:43）
   ↓ 打开浏览器，你点一下人机验证               ↓ 读取 Secret: SESSION_COOKIES
   ↓ 自动用你的账号登录                         ↓ 用 cookie 直接访问论坛（免验证、已登录）
得到一段可粘贴的文本  ────粘进 Secret──────→   ↓ 完成 签到/抽奖/互动/抓资产
                                            ↓ 把结果发到你邮箱
（约 30 天后重复一次左边 3 步即可）
```

- 平时电脑**完全不用开**；只有 cookie 过期（约 30 天）时才需要在电脑上再点一次。

---

## 二、一次性配置（约 5 分钟）

### 第 1 步：电脑上"取 cookie"
> 需要：Windows + 已装 **Python 3.10+**（[下载](https://www.python.org/downloads/)，安装时勾选 *Add Python to PATH*）+ **Edge 或 Chrome**。

1. 把这个仓库**下载到电脑**（页面右上角 **Code → Download ZIP**，解压到一个文件夹）。
2. 双击 **`获取cookie.bat`**（首次会自动装依赖，较慢，请耐心）：
   - 按窗口提示**输入你的论坛用户名和密码**（只在本机使用，不会上传）；
   - 会弹出**浏览器窗口**；若出现「请进行人机验证」，**用鼠标点一下验证框**；
   - 之后自动登录，窗口里会打印出一段**很长的文本**，并**自动复制到剪贴板**。

### 第 2 步：把仓库放上 GitHub（设为 Private）
点 GitHub 右上角 **+ → Import repository**，地址填：
`https://github.com/gowsdemy/gameauto-cloud`
起个名字，**Privacy 务必勾 Private**（cookie 是登录凭证）。

### 第 3 步：填 Secrets
进入你的仓库 → **Settings → Secrets and variables → Actions → New repository secret**：

| Name | 填什么 | 必填 |
| --- | --- | --- |
| `SESSION_COOKIES` | **第 1 步拿到的那一整段文本** | ✅ 必填 |
| `SMTP_HOST` | 发件邮箱 SMTP，如 `smtp.qq.com` | 选填（想收邮件就填） |
| `MAIL_USER` | 发件邮箱，如 `123456@qq.com` | 选填 |
| `MAIL_PASS` | SMTP 授权码（**不是**邮箱密码） | 选填 |
| `MAIL_TO` | 收件邮箱；留空则发给自己 | 选填 |
| `USERNAME` | 论坛用户名（只用于报告显示） | 选填 |

> 邮箱三项里只要有一项为空，云端就跳过发信，只做签到。

### 第 4 步：启用 Actions 并手动测一次（之后就会自动运行）
1. 进入仓库 **Actions** 页 → 若出现提示，点 **I understand my workflows, go ahead and enable them**。
2. **放开写入权限**（否则没法把金币基准写回仓库，定时也可能被停）：
   **Settings → Actions → General → Workflow permissions** → 选 **Read and write permissions** → 保存。
3. 左侧选 **GameMale Cloud Sign-in** → 右侧 **Run workflow** → 手动跑一次。
   - 成功：几分钟后收到"任务运行报告"邮件；
   - 失败：收到「**【GameMale 签到失败】请刷新 cookie**」邮件 → 回到第 1 步重新取 cookie 并更新 Secret。

**跑通一次之后，它就会自动运行**：每天北京时间 **00:17** 与 **14:43** 各跑一次，电脑无需开机。
（内置「Keepalive」保活工作流，避免 GitHub 因长期无活动而自动停掉定时任务。）

> 若你**还没设** `SESSION_COOKIES` 就手动跑了，日志里会提示「未配置 SESSION_COOKIES，本次跳过」，按第 3 步补上即可。

---

## 三、cookie 过期怎么办（约 30 天一次）

收到「**请刷新 cookie**」的失败邮件时：
1. 电脑上重新双击 **`获取cookie.bat`**（会再次弹窗点验证）；
2. 复制新文本；
3. 仓库 **Settings → Secrets → Actions → `SESSION_COOKIES` → Update**，粘贴保存。

---

## 四、常见问题

**Q：为什么不用像别的项目那样直接填账号密码？**
因为云端是数据中心 IP，论坛的 Cloudflare 人机验证**必须真人点一下**才过。所以只能"本地点一次 → 云端用这段已通过验证的 cookie"。

**Q：cookie 安全吗？**
它是你的登录凭证。**仓库务必 Private**；cookie **只放 Secret**（加密存储，日志里也会打码）。**绝不**把它写进代码或提交到公开仓库。

**Q：一定要 30 天刷新吗？**
按论坛会话设置约 30 天，也可能更早（换网络、论坛清会话等）。收到失败邮件就刷新。

**Q：定时会准时吗？**
GitHub 定时任务高峰期可能延迟几分钟到几十分钟，属正常，不影响签到。

**Q：`获取cookie.bat` 报错找不到 Python？**
装 Python 3.10+ 并勾选 *Add Python to PATH*，重启命令行再试。

---

## 五、文件说明

| 文件 | 作用 |
| --- | --- |
| `获取cookie.bat` → `get_cookie.ps1` | **在你电脑上**取 cookie（本仓库唯一需要本地运行的；中文提示、直接输入账号密码） |
| `get_cookie.py` | 上面那个工具的内部脚本（负责过验证+登录+导出文本），用户不用管 |
| `gamemale_v2.py` | 取 cookie 用的引擎（过验证 + 登录） |
| `gamemale_cloud.py` | 云端主脚本（cookie + curl_cffi 跑签到） |
| `.github/workflows/signin.yml` | 云端工作流（每天定时 + 可手动触发） |
| `requirements.txt` | 依赖清单（`获取cookie.bat` 会自动安装，无需手动） |

---

## 六、致谢

思路源自 [Highboed/GM-All-In-One](https://github.com/Highboed/GM-All-In-One)（原作者）。

> ⚠️ 再次提醒：`SESSION_COOKIES` 等于你的登录状态，**仓库请设为 Private**，切勿外泄。
