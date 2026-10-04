#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键获取云端所需的 cookie（在本机运行一次即可）
================================================
流程：
  1) 用你电脑上的真实浏览器打开论坛；
  2) 弹出窗口时点一下人机验证（若未自动通过）；自动用 config.env 里的账号登录；
  3) 保存会话 cookie，并输出一段【可粘贴的 Base64 文本】（同时复制到剪贴板）；
  4) 把那段文本粘贴到 GitHub 仓库的 Secret：SESSION_COOKIES。

约 30 天后 cookie 会过期，重新运行本工具并更新该 Secret 即可。
"""
import base64
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)

import gamemale_v2 as engine   # 本地版引擎（负责过验证 + 登录）


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
    engine.load_env_file("config.env")
    user = os.getenv("USERNAME", "").strip()
    pw = os.getenv("PASSWORD", "").strip()
    if not user or not pw:
        print("=" * 72)
        print("[错误] 请先把 config.env.example 复制为 config.env，并填好 USERNAME 和 PASSWORD。")
        print("=" * 72)
        return 1

    print("=" * 72)
    print("开始获取 cookie：马上会弹出浏览器窗口。")
    print("若窗口里出现「请进行人机验证」，请用鼠标点一下验证框；之后会自动登录。")
    print("=" * 72)

    gm = engine.Gamemale(user, pw, verbose=True)
    gm.force_visible = True          # 取 cookie 时直接弹窗口，跳过静默等待
    try:
        ok = gm.ensure_access()
        if not ok:
            print("[失败] 未能通过 Cloudflare 验证。请重试；若一直失败，检查网络或稍后再试。")
            return 1
        if not gm._is_logged_in():
            if not gm.login():
                print("[失败] 登录失败。请检查 config.env 里的 USERNAME / PASSWORD 是否正确。")
                return 1
        gm._save_cookies()
    finally:
        try:
            gm._close_browser()
        except Exception:
            pass

    cookie_file = os.path.join(HERE, "_session_cookies.json")
    if not os.path.exists(cookie_file):
        print("[失败] 未生成 cookie 文件，请重试。")
        return 1

    text, kept, total = build_text(cookie_file)
    print()
    print("=" * 72)
    print(f"[成功] 已获取 cookie：从 {total} 个中提取 {kept} 个（论坛相关）。")
    print()
    print("请复制下面【整段】文本，粘贴到你的 GitHub 仓库：")
    print("  Settings -> Secrets and variables -> Actions -> New repository secret")
    print("  Name   : SESSION_COOKIES")
    print("  Secret : 粘贴下面这一整段（很长，注意别漏头尾）")
    print("=" * 72)
    print(text)
    print("=" * 72)
    try:
        subprocess.run("clip", input=text.encode("ascii", "ignore"), shell=True, check=False)
        print("(已尝试复制到剪贴板，可直接 Ctrl+V 粘贴)")
    except Exception:
        pass
    print()
    print("提示：约 30 天后 cookie 过期，届时重新运行本工具，并在 Secret 里 Update 一次即可。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
