#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键获取云端所需的 cookie（在你自己的电脑上运行一次即可）
==========================================================
全过程中文提示；不需要任何配置文件，直接输入论坛账号密码即可。

流程：
  1) 自动准备运行环境（首次较慢）；
  2) 打开真实浏览器，弹出窗口时点一下人机验证，自动用你输入的账号登录；
  3) 保存会话 cookie，并输出一段【可粘贴的 Base64 文本】（同时复制到剪贴板）；
  4) 把那段文本粘贴到 GitHub 仓库的 Secret：SESSION_COOKIES。

约 30 天后 cookie 过期，重新运行本工具并更新 Secret 即可。
"""
import base64
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

try:  # 让控制台正确显示中文
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

VENV = os.path.join(HERE, ".venv")
VENV_PY = os.path.join(VENV, "Scripts", "python.exe")     # Windows
DEPS = ("ddddocr", "playwright")


def _in_venv():
    try:
        return os.path.abspath(sys.executable).lower() == os.path.abspath(VENV_PY).lower()
    except Exception:
        return False


def bootstrap():
    """确保 .venv + 依赖已就绪；若需要，切到 venv 的 python 重新运行本脚本。返回 True 表示已切换（本进程应退出）。"""
    if _in_venv():
        return False
    print("=" * 70)
    print("首次运行：正在准备运行环境（需要联网，可能要 1~3 分钟，请稍候）...")
    print("=" * 70)
    if not os.path.exists(VENV_PY):
        rc = subprocess.call([sys.executable, "-m", "venv", VENV])
        if rc != 0 or not os.path.exists(VENV_PY):
            print("[错误] 创建运行环境失败。请确认 Python 3.10+ 已正确安装（安装时需勾选 Add Python to PATH）。")
            return None
    chk = subprocess.run([VENV_PY, "-c", "import ddddocr, playwright"], capture_output=True)
    if chk.returncode != 0:
        print("正在安装所需组件（首次较慢，请稍候）...")
        subprocess.call([VENV_PY, "-m", "pip", "install", "--upgrade", "pip"])
        rc = subprocess.call([VENV_PY, "-m", "pip", "install", *DEPS])
        if rc != 0:
            print("[错误] 安装组件失败，请检查网络后重试（或换个网络/挂梯子再试）。")
            return None
    print("环境就绪，正在启动 ...")
    # 切到 venv 里的 python 重新运行本脚本（子进程带中文提示）
    rc = subprocess.call([VENV_PY, os.path.abspath(__file__)])
    sys.exit(rc)


def ask_accounts():
    user = os.getenv("USERNAME", "").strip()
    pw = os.getenv("PASSWORD", "").strip()
    print("=" * 70)
    print("请输入你的 GameMale 论坛账号（用于登录，只保存在本机、不会上传）")
    print("=" * 70)
    if not user:
        while not user:
            user = input("论坛用户名：").strip()
            if not user:
                print("用户名不能为空，请重新输入。")
    if not pw:
        import getpass
        while not pw:
            try:
                pw = getpass.getpass("论坛密码（输入时不显示）：").strip()
            except Exception:
                pw = input("论坛密码：").strip()
            if not pw:
                print("密码不能为空，请重新输入。")
    return user, pw


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
    user, pw = ask_accounts()

    print()
    print("正在打开浏览器 ...")
    print(">>> 若窗口里出现「请进行人机验证」，请用鼠标点一下验证框；之后会自动登录。")
    import gamemale_v2 as engine     # 本地版引擎（负责过验证 + 登录）

    gm = engine.Gamemale(user, pw, verbose=True)
    gm.force_visible = True          # 取 cookie 时直接弹窗口，跳过静默等待
    try:
        if not gm.ensure_access():
            print()
            print("[失败] 未能通过 Cloudflare 验证。请重新运行本工具再试；若一直失败，换网络或稍后再试。")
            return 1
        if not gm._is_logged_in():
            if not gm.login():
                print()
                print("[失败] 登录失败。请确认账号密码输入正确（注意区分大小写）。")
                return 1
        gm._save_cookies()
    finally:
        try:
            gm._close_browser()
        except Exception:
            pass

    cookie_file = os.path.join(HERE, "_session_cookies.json")
    if not os.path.exists(cookie_file):
        print("[失败] 未能生成 cookie，请重试。")
        return 1

    text, kept, total = build_text(cookie_file)
    print()
    print("=" * 70)
    print(f"[成功] 已获取登录 cookie（从 {total} 个中提取 {kept} 个）。")
    print()
    print("请复制下面【整段】文本，粘贴到你的 GitHub 仓库：")
    print("  仓库页 → Settings → Secrets and variables → Actions → New repository secret")
    print("  Name  填写：SESSION_COOKIES")
    print("  Secret 粘贴：下面这一整段（很长，注意别漏头尾）")
    print("=" * 70)
    print(text)
    print("=" * 70)
    try:
        subprocess.run("clip", input=text.encode("ascii", "ignore"), shell=True, check=False)
        print("（这段文本已自动复制到剪贴板，可直接 Ctrl+V 粘贴）")
    except Exception:
        pass
    print()
    print("提示：约 30 天后 cookie 会过期，届时重新运行本工具，并把 Secret 更新一次即可。")
    return 0


if __name__ == "__main__":
    if bootstrap() is None:
        sys.exit(1)
    sys.exit(main())
