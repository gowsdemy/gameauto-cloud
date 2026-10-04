#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_cookie.py —— 由「获取cookie.ps1」调用，只负责"干活"：
  用真实浏览器过 Cloudflare 验证 + 登录，保存会话 cookie，并把可粘贴的 Base64 文本写到 _cookie_text.txt。
中文提示由 get_cookie.ps1 负责（本文件只输出诊断日志和结果文件）。
"""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

TEXT_FILE = os.path.join(HERE, "_cookie_text.txt")
COOKIE_FILE = os.path.join(HERE, "_session_cookies.json")


def build_text(cookie_file):
    data = json.load(open(cookie_file, encoding="utf-8"))
    keep = [c for c in data if "gamemale.com" in (c.get("domain") or "")]
    if not keep:
        keep = data
    slim = [{"name": c["name"], "value": c["value"],
             "domain": c.get("domain"), "path": c.get("path") or "/"} for c in keep]
    text = base64.b64encode(json.dumps(slim, ensure_ascii=False).encode("utf-8")).decode()
    return text, len(slim), len(data)


def main():
    user = (os.getenv("USERNAME") or "").strip()
    pw = (os.getenv("PASSWORD") or "").strip()
    if not user or not pw:
        print("[get_cookie] 缺少账号信息（应由 获取cookie.ps1 传入）")
        return 2

    if os.path.exists(TEXT_FILE):
        try:
            os.remove(TEXT_FILE)
        except Exception:
            pass

    import gamemale_v2 as engine   # 本地版引擎（负责过验证 + 登录）

    gm = engine.Gamemale(user, pw, verbose=True)
    gm.force_visible = True        # 直接弹可见窗口，跳过静默等待
    try:
        if not gm.ensure_access():
            print("[get_cookie] 未能通过 Cloudflare 验证")
            return 1
        if not gm._is_logged_in():
            if not gm.login():
                print("[get_cookie] 登录失败（请检查账号密码）")
                return 1
        gm._save_cookies()
    finally:
        try:
            gm._close_browser()
        except Exception:
            pass

    if not os.path.exists(COOKIE_FILE):
        print("[get_cookie] 未生成 cookie 文件")
        return 1

    text, kept, total = build_text(COOKIE_FILE)
    with open(TEXT_FILE, "w", encoding="ascii", errors="ignore") as f:
        f.write(text)
    print(f"[get_cookie] 成功：从 {total} 个 cookie 中提取 {kept} 个，已写入 _cookie_text.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
