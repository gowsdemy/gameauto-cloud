# GameMale 自动签到 · 云端版

> 这是 [GameMale 自动签到（本地版）](https://github.com/gowsdemy/gameauto-dsh3) 的**云端版**：
> 在 **GitHub Actions 上自动签到**，**你的电脑不用开着**。
>
> 原理：论坛加了 Cloudflare 人机验证，会拦截云服务器——所以云端**不自己过验证**，
> 而是用你**在电脑上登录一次得到的那段会话 cookie**（存进仓库 Secret）。
> 有这段 cookie，云端就**已经是登录状态**，能直接签到。

---

## 一、它怎么工作

```
你电脑（偶尔用一次）                     GitHub 云端（每天自动）
─────────────────────                  ─────────────────────────
运行本地版「运行签到.bat」                每天定时自动运行
   ↓ 过一次 Cloudflare + 登录              ↓ 读取 Secret: SESSION_COOKIES
得到 _session_cookies.json                  ↓ 用 cookie 直接访问论坛（免验证、已登录）
   ↓ 双击「导出cookie.bat」                 ↓ 完成 签到/抽奖/互动/抓资产/发邮件
得到一段 Base64 文本  ────粘贴到 Secret───→
```

- 平时**不用开电脑**；**约 30 天** cookie 过期后，重做一次上面的"你电脑"三步即可。

---

## 二、一次性配置（约 3 分钟）

### 1. 导入本仓库（建议设为 Private）
点右上角 **+ → Import repository**，地址填 `https://github.com/gowsdemy/gameauto-cloud`，
起个名字，**Privacy 勾 Private**（cookie 是登录凭证，务必私有）。

### 2. 填 Secrets
进入你的仓库 → **Settings → Secrets and variables → Actions → New repository secret**，添加：

| Name | 填什么 | 必填 |
| --- | --- | --- |
| `SESSION_COOKIES` | **本地导出的那一整段 Base64 文本**（怎么来见第 3 步） | ✅ 必填 |
| `SMTP_HOST` | 发件邮箱的 SMTP 服务器，如 `smtp.qq.com` | 选填（要邮件就填） |
| `MAIL_USER` | 发件邮箱，如 `123456@qq.com` | 选填 |
| `MAIL_PASS` | SMTP 授权码（不是邮箱密码） | 选填 |
| `MAIL_TO` | 收件邮箱；留空则发给自己 | 选填 |
| `USERNAME` | 你的论坛用户名（只用于报告里显示） | 选填 |

### 3. 拿到 `SESSION_COOKIES`（在你的电脑上做）
1. 先在你电脑上运行**本地版**的 `运行签到.bat` 一次（它会过一次 Cloudflare 并登录，
   在本地版目录生成 `_session_cookies.json`）。
2. 把 `_session_cookies.json` 复制到**本仓库文件夹**里（和 `导出cookie.bat` 放一起）。
3. 双击 **`导出cookie.bat`** → 它会打印一段很长的文本并**自动复制到剪贴板**。
4. 把这段文本，粘贴进上面第 2 步的 **`SESSION_COOKIES`** Secret 里，保存。

### 4. 打开 Actions 并测试
进入仓库 **Actions** 页 → 若提示就点 **I understand my workflows, go ahead and enable them** →
左侧选 **GameMale Cloud Sign-in** → 右侧 **Run workflow** 手动跑一次。
- 成功：几分钟后你会收到"任务运行报告"邮件；
- 失败：会收到"**请刷新 cookie**"的提醒邮件，重做第 3 步即可。

之后**每天会自动跑两次**（北京时间 00:17 与 14:43），电脑无需开机。

---

## 三、cookie 过期了怎么办（约 30 天一次）

收到「**【GameMale 签到失败】请刷新 cookie**」邮件时：
1. 电脑上重新运行本地版 `运行签到.bat`；
2. 双击 `导出cookie.bat` 拿到新文本；
3. 到仓库 **Settings → Secrets → Actions**，点 `SESSION_COOKIES` → **Update**，粘贴新文本。

---

## 四、常见问题

**Q：为什么不能像本地版那样直接填账号密码？**
因为云端是数据中心 IP，论坛的 Cloudflare 人机验证**必须真人点一下**才过；只有用"已通过验证的 cookie"才能免验证。所以要么本地点一次、要么云端过不了。

**Q：cookie 安全吗？**
它是你的登录凭证。**仓库务必 Private**，cookie **只放 Secret**（Secret 是加密的，日志里也会打码）。千万别把它写进代码或提交到公开仓库。

**Q：一定 30 天过期吗？**
按论坛会话设置约 30 天，可能更短（换网络、论坛清会话等都会提前失效）。收到失败邮件就刷新一次。

**Q：定时不准？**
GitHub 的定时任务在高峰期可能延迟几分钟到几十分钟，属正常；不影响签到。

---

## 五、文件说明

| 文件 | 作用 |
| --- | --- |
| `gamemale_cloud.py` | 云端主脚本（cookie + curl_cffi 跑签到） |
| `.github/workflows/signin.yml` | 云端工作流（定时 + 手动触发） |
| `导出cookie.bat` / `export_cookie.py` | 本地：把 cookie 转成可粘贴的文本 |
| `gold_record.txt` | 金币对比基准（工作流自动更新） |

---

## 六、致谢

思路源自 [Highboed/GM-All-In-One](https://github.com/Highboed/GM-All-In-One)（原作者）。
本云端版由社区改动而来：**本地过一次验证 → 云端免验证自动签到**。

> ⚠️ 再次提醒：`SESSION_COOKIES` 等于你的登录状态，**仓库请设为 Private**，切勿外泄。
