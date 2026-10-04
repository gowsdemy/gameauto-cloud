#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GameMale 云端签到（GitHub Actions 版）
======================================
不依赖浏览器：使用本机导出的【会话 cookie】（存在仓库 Secret `SESSION_COOKIES`）
+ curl_cffi（伪装 Chrome TLS）直接访问论坛。因为 cookie 里已带登录态，
Cloudflare 验证门会直接放行，无需点验证、无需输密码。

- 成功：跑完 签到/抽奖/互动/抓资产，并发一封结果邮件（若配了邮箱）。
- 失败（cookie 过期/未登录/被拦截）：发一封【失败提醒】邮件，并让工作流标红。
"""
import base64
import json
import os
import re
import sys
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

from curl_cffi import requests as cffi

HOST = "www.gamemale.com"
BASE = f"https://{HOST}"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")


def log(msg):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {msg}", flush=True)


def load_cookies():
    """从 Secret 读取 cookie（优先 base64(JSON)，也兼容直接给 JSON）。"""
    raw = (os.environ.get("SESSION_COOKIES") or "").strip()
    if not raw:
        return None
    # 去掉可能的空白/换行
    raw = re.sub(r"\s+", "", raw)
    for attempt in ("b64", "json"):
        try:
            data = json.loads(base64.b64decode(raw).decode("utf-8")) if attempt == "b64" else json.loads(raw)
            if isinstance(data, list) and data:
                return data
        except Exception:
            continue
    return None


class CloudSignin:
    def __init__(self):
        self.sign_result = "未执行"
        self.exchange_result = "未执行"
        self.task_result = "未执行"
        self.assets_report = "未抓取"
        self.post_formhash = None
        self.username = os.getenv("USERNAME", "")
        self.session = cffi.Session(impersonate="chrome")
        self.session.headers.update({"User-Agent": UA,
                                     "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})
        cookies = load_cookies()
        self.cookie_count = len(cookies) if cookies else 0
        if cookies:
            for c in cookies:
                try:
                    self.session.cookies.set(c["name"], c["value"],
                                             domain=c.get("domain"), path=c.get("path") or "/")
                except Exception:
                    pass

    # ---------------- 基础请求（带重试） ----------------
    def _req(self, method, url, **kw):
        last = None
        for i in range(4):
            try:
                return self.session.request(method, url, timeout=30, **kw)
            except Exception as e:
                last = e
                time.sleep(2 * (i + 1))
        raise last

    def _get(self, url, **kw):
        return self._req("GET", url, **kw)

    def _post(self, url, **kw):
        return self._req("POST", url, **kw)

    # ---------------- 访问检查 ----------------
    @staticmethod
    def _gated(html):
        if not html:
            return True
        low = html.lower()
        return ("请稍候" in html) or (("challenges.cloudflare.com/turnstile" in low)
                                      and ("检查站点连接是否安全" in html))

    @staticmethod
    def _logged_in(html):
        return ("退出" in html) or ("logout" in html.lower())

    def ensure_access(self):
        """返回 (是否可用, 失败原因)。"""
        if self.cookie_count == 0:
            return False, "未配置 SESSION_COOKIES（或格式不对）"
        try:
            r = self._get(BASE + "/forum.php")
        except Exception as e:
            return False, f"访问论坛失败：{e}"
        html = r.text
        if self._gated(html):
            return False, "被 Cloudflare 拦截（cookie 已失效/过期）"
        if not self._logged_in(html):
            return False, "未处于登录状态（会话已过期）"
        m = re.search(r'<input type="hidden" name="formhash" value="([0-9a-f]+)"', html)
        if m:
            self.post_formhash = m.group(1)
        else:
            # 有些页面用双引号/单引号，兜底再找一次
            m2 = re.search(r'name="formhash"\s+value="([0-9a-f]+)"', html)
            if m2:
                self.post_formhash = m2.group(1)
        if not self.post_formhash:
            return False, "已登录但未取到 formhash"
        return True, ""

    # ---------------- 日常任务 ----------------
    def sign(self):
        log("执行每日签到 ...")
        url = f"{BASE}/k_misign-sign.html?operation=qiandao&format=button&formhash={self.post_formhash}"
        try:
            res = self._get(url).text
            if "签到成功" in res:
                self.sign_result = "签到成功"
            elif "已签" in res:
                self.sign_result = "今日已签到"
            else:
                self.sign_result = "未知响应"
            log(f"签到结果：{self.sign_result}")
        except Exception as e:
            self.sign_result = f"异常：{e}"
            log(f"签到异常：{e}")

    def exchange(self):
        log("执行每日抽奖 ...")
        url = (f"{BASE}/plugin.php?id=it618_award:ajax&ac=getaward"
               f"&formhash={self.post_formhash}&_={int(time.time() * 1000)}")
        headers = {"accept": "application/json, text/javascript, */*; q=0.01",
                   "referer": f"{BASE}/it618_award-award.html",
                   "x-requested-with": "XMLHttpRequest"}
        try:
            j = self._get(url, headers=headers).json()
            if j.get("tipname") == "":
                self.exchange_result = "无奖励（今日或已抽奖）"
            elif j.get("tipname") == "ok":
                self.exchange_result = f"抽奖成功：{j.get('tipvalue')}"
            else:
                self.exchange_result = f"非预期响应：{j.get('tipname')}"
        except Exception as e:
            self.exchange_result = f"异常：{e}"
        log(f"抽奖结果：{self.exchange_result}")

    def visit_spaces(self):
        n = 0
        for uid in (730713, 62445, 61832):
            try:
                self._get(f"{BASE}/space-uid-{uid}.html")
                n += 1
                time.sleep(1)
            except Exception:
                pass
        return n

    def poke_users(self):
        n = 0
        for uid in (730713, 62445, 61832):
            url = f"{BASE}/home.php?mod=spacecp&ac=poke&op=send&uid={uid}&inajax=1"
            data = {"formhash": self.post_formhash, "poke": "1", "iconid": "3", "pokesubmit": "true"}
            try:
                if "succeed" in self._post(url, data=data,
                                           headers={"x-requested-with": "XMLHttpRequest"}).text:
                    n += 1
                time.sleep(1)
            except Exception:
                pass
        return n

    def stance_blogs(self):
        n, page = 0, 1
        while n < 10 and page <= 3:
            try:
                res = self._get(f"{BASE}/home.php?mod=space&do=blog&view=all&catid=14&page={page}").text
                urls = set(re.findall(r'home\.php\?mod=space(?:&amp;|&)uid=\d+(?:&amp;|&)do=blog(?:&amp;|&)id=\d+', res))
                for uri in urls:
                    if n >= 10:
                        break
                    blog = self._get(f"{BASE}/{uri.replace('&amp;', '&')}").text
                    m = re.search(r'(home\.php\?mod=spacecp(?:&amp;|&)ac=click(?:&amp;|&)op=add[^"\']+)', blog)
                    if m:
                        if "成功" in self._get(f"{BASE}/{m.group(1).replace('&amp;', '&')}",
                                               headers={"x-requested-with": "XMLHttpRequest"}).text:
                            n += 1
                    time.sleep(1)
            except Exception:
                break
            page += 1
        return n

    def draw_and_guess(self):
        url = f"{BASE}/plugin.php?id=viewui_draw&mod=api&ac=adddraw"
        img = ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
               "AAAADklEQVR4AWL6////fwAAAAD//w7I1cwAAAAGSURBVAMACgUD/9k79a8AAAAASUVORK5CYII=")
        data = {"title": "水果", "answer": "苹果", "pic": img, "formhash": self.post_formhash}
        headers = {"x-requested-with": "XMLHttpRequest", "origin": f"https://{HOST}",
                   "referer": f"{BASE}/plugin.php?id=viewui_draw"}
        try:
            r = self._post(url, data=data, headers=headers)
            try:
                msg = r.json().get("message", r.text[:30])
            except Exception:
                msg = r.text[:30]
            if "成功" in msg or "succeed" in msg:
                return "出题成功"
            if "今日" in msg or "上限" in msg or "用完" in msg:
                return "额度已满"
            return f"失败：{str(msg)[:12]}"
        except Exception:
            return "提交异常"

    def fetch_assets(self):
        log("抓取资产 ...")
        try:
            res = self._get(f"{BASE}/home.php?mod=spacecp&ac=credit&op=base").text
            clean = re.sub(r'<[^>]+>', '', res)
            d = {}
            for item in ['金币', '血液', '旅程', '追随', '知识', '咒术', '堕落', '灵魂']:
                m = re.search(f'{item}\\s*[:：]?\\s*(\\d+)', clean)
                d[item] = int(m.group(1)) if m else 0
            cur = d['金币']
            last = cur
            if os.path.exists("gold_record.txt"):
                c = open("gold_record.txt").read().strip()
                if c.isdigit():
                    last = int(c)
            growth = cur - last
            g = f"+{growth}" if growth >= 0 else str(growth)
            open("gold_record.txt", "w").write(str(cur))
            self.assets_report = (
                f"💰 金币: {cur} (较昨日 {g})\n"
                f"🩸 血液: {d['血液']} | ✈️ 旅程: {d['旅程']} | 👣 追随: {d['追随']}\n"
                f"📚 知识: {d['知识']} | 🔮 咒术: {d['咒术']} | 🖤 堕落: {d['堕落']}\n"
                f"👻 灵魂: {d['灵魂']}"
            )
        except Exception as e:
            self.assets_report = f"资产抓取异常：{e}"
        log(f"资产看板：\n{self.assets_report}")

    def interactive(self):
        log("执行互动作业 ...")
        s, p, b, dd = self.visit_spaces(), self.poke_users(), self.stance_blogs(), self.draw_and_guess()
        self.task_result = f"空间访问({s}/3) | 打招呼({p}/3) | 日志表态({b}/10) | 你画我猜({dd})"
        log(f"互动作业：{self.task_result}")

    # ---------------- 邮件 ----------------
    def send_mail(self, subject, body_html):
        host = os.getenv("SMTP_HOST")
        user = os.getenv("MAIL_USER")
        pwd = os.getenv("MAIL_PASS")
        to = os.getenv("MAIL_TO") or user
        if not all([host, user, pwd]):
            log("未配置邮箱，跳过发信")
            return False
        msg = MIMEText(body_html, "html", "utf-8")
        msg["From"] = formataddr((Header("GM-Bot", "utf-8").encode(), user))
        msg["To"] = formataddr((Header("Master", "utf-8").encode(), to))
        msg["Subject"] = Header(subject, "utf-8")
        for port, mode in [(25, "starttls"), (465, "ssl"), (587, "starttls")]:
            try:
                if mode == "ssl":
                    s = smtplib.SMTP_SSL(host, port, timeout=20)
                else:
                    s = smtplib.SMTP(host, port, timeout=20)
                    s.starttls()
                s.login(user, pwd)
                s.sendmail(user, [to], msg.as_string())
                s.quit()
                log(f"邮件已发送（{port}/{mode}）")
                return True
            except Exception as e:
                log(f"SMTP {port}/{mode} 失败：{e}")
        return False

    def report_html(self):
        return (
            f"<h3>GameMale 每日自动签到报告</h3>"
            f"<p><b>核心签到：</b>{self.sign_result}</p>"
            f"<p><b>日常抽奖：</b>{self.exchange_result}</p>"
            f"<p><b>互动作业：</b>{self.task_result}</p>"
            f"<h4>📊 当前资产：</h4>"
            f"<pre style='background:#f4f4f4;padding:12px;border-radius:5px;'>{self.assets_report}</pre>"
            f"<small style='color:#888;'>由 GameMale 云端版生成</small>"
        )

    # ---------------- 主流程 ----------------
    def run(self):
        log("=== GameMale 云端签到 启动 ===")
        log(f"账号：{self.username or '(未填)'} | cookie 数：{self.cookie_count}")
        ok, reason = self.ensure_access()
        if not ok:
            log(f"！！无法继续：{reason}")
            self.send_mail("【GameMale 签到失败】请刷新 cookie",
                           f"<p>本次云端签到<b>失败</b>。</p><p><b>原因：</b>{reason}</p>"
                           f"<p>解决：请在你电脑上双击 <b>运行签到.bat</b> 重新登录一次，"
                           f"再用 <b>导出cookie.bat</b> 导出新 cookie，更新仓库 Secret <b>SESSION_COOKIES</b>。</p>")
            return 1
        log("访问正常且已登录，开始执行任务 ...")
        self.sign()
        self.exchange()
        self.interactive()
        self.fetch_assets()
        self.send_mail(f"GameMale 任务运行报告 - {self.sign_result}", self.report_html())
        log("=== 全部完成 ===")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(CloudSignin().run())
    except Exception as e:
        log(f"未捕获异常：{e}")
        sys.exit(1)
