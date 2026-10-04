#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把本地导出的 _session_cookies.json 转成一段 Base64 文本，
供你粘贴到 GitHub 仓库的 Secret：SESSION_COOKIES

用法：
  1) 先在本机运行本地版「运行签到.bat」跑一次（会生成 _session_cookies.json）；
  2) 把该文件复制到本文件夹（或直接拖到本程序/本 bat 上），然后双击「导出cookie.bat」。
"""
import base64
import json
import os
import subprocess
import sys

KEY = "gamemale.com"        # 只保留与本论坛相关的 cookie（丢掉微软/Edge 等无关项）


def find_cookie_file():
    if len(sys.argv) > 1:
        p = sys.argv[1].strip('"')
        if p and os.path.exists(p):
            return p
    p = os.environ.get("COOKIE_FILE", "")
    if p and os.path.exists(p):
        return p
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("_session_cookies.json", "session_cookies.json"):
        fp = os.path.join(here, name)
        if os.path.exists(fp):
            return fp
    return None


def main():
    fp = find_cookie_file()
    if not fp:
        print("[错误] 未找到 _session_cookies.json")
        print("  请先在本机运行一次本地版「运行签到.bat」（会生成 _session_cookies.json），")
        print("  然后把该文件复制到本文件夹，或把它拖到「导出cookie.bat」上再运行。")
        return 1

    try:
        data = json.load(open(fp, encoding="utf-8"))
    except Exception as e:
        print(f"[错误] 读取 {fp} 失败：{e}")
        return 1
    if not isinstance(data, list) or not data:
        print("[错误] cookie 文件内容不是预期的列表格式")
        return 1

    keep = [c for c in data if KEY in (c.get("domain") or "")]
    if not keep:
        keep = data
    slim = [{"name": c["name"], "value": c["value"],
             "domain": c.get("domain"), "path": c.get("path") or "/"} for c in keep]
    text = base64.b64encode(json.dumps(slim, ensure_ascii=False).encode("utf-8")).decode()

    print("=" * 72)
    print(f"已从 {os.path.basename(fp)} 提取 {len(slim)} 个 cookie（原文件 {len(data)} 个）。")
    print("")
    print("请复制下面【整段】文本，粘贴到你的 GitHub 仓库：")
    print("  Settings -> Secrets and variables -> Actions -> New repository secret")
    print("  Name   : SESSION_COOKIES")
    print("  Secret : 粘贴下面这一整段")
    print("=" * 72)
    print(text)
    print("=" * 72)

    try:
        subprocess.run("clip", input=text.encode("ascii", "ignore"), check=False, shell=True)
        print("(上面这段文本已尝试复制到剪贴板，可直接 Ctrl+V 粘贴)")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
