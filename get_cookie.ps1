# get_cookie.ps1 —— 由「获取cookie.bat」调用（用户不用管这个文件）
# 作用：中文界面 —— 检查 Python、准备环境、输入账号、调用 get_cookie.py 取 cookie，并显示可粘贴文本。
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$ErrorActionPreference = "Continue"
$here = $PSScriptRoot
Set-Location $here

function Pause-Exit($code) {
    Write-Host ""
    Read-Host "按回车键关闭本窗口" | Out-Null
    exit $code
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  GameMale 云端版 · 一键获取登录 cookie" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# ---------- 1) 找 Python ----------
function Test-PyCmd($exe, $pre) {
    try {
        $a = @($pre) + @("--version")
        & $exe @a *> $null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

$pyExe = $null
$pyPre = @()
if (Test-PyCmd "py" @("-3")) { $pyExe = "py"; $pyPre = @("-3") }
elseif (Test-PyCmd "python" @()) { $pyExe = "python"; $pyPre = @() }

if (-not $pyExe) {
    Write-Host ""
    Write-Host "❌ 没有检测到 Python。" -ForegroundColor Red
    Write-Host "   请先安装 Python 3.10 或更高版本： https://www.python.org/downloads/"
    Write-Host "   安装时务必勾选 “Add Python to PATH”，装好后重新运行本工具。"
    Pause-Exit 1
}

# ---------- 2) 准备运行环境 ----------
$venv = Join-Path $here ".venv"
$venvPy = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $venvPy)) {
    Write-Host ""
    Write-Host "首次运行：正在创建运行环境（请稍候）..." -ForegroundColor Yellow
    & $pyExe @pyPre -m venv $venv
    if (-not (Test-Path $venvPy)) {
        Write-Host "❌ 创建运行环境失败。请确认 Python 安装正常。" -ForegroundColor Red
        Pause-Exit 1
    }
}

& $venvPy -c "import ddddocr, playwright" *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "正在安装所需组件（首次较慢，请耐心等待，约 1~3 分钟）..." -ForegroundColor Yellow
    & $venvPy -m pip install --upgrade pip
    & $venvPy -m pip install ddddocr playwright
    & $venvPy -c "import ddddocr, playwright" *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 安装组件失败，请检查网络后重试（可换网络或稍后再试）。" -ForegroundColor Red
        Pause-Exit 1
    }
}

# ---------- 3) 输入账号 ----------
Write-Host ""
Write-Host "请输入你在 GameMale 论坛的账号（就是你在论坛里登录用的用户名，不是 GitHub 账号）" -ForegroundColor Cyan
Write-Host "（该信息只在本机使用，不会上传）" -ForegroundColor DarkGray
Write-Host ""

$user = ""
$tries = 0
while ([string]::IsNullOrWhiteSpace($user)) {
    $v = Read-Host "论坛用户名"
    if ($null -eq $v) {
        Write-Host ""
        Write-Host "❌ 读取不到输入。请【直接双击】“获取cookie.bat”运行本工具（不要在非交互环境里运行）。" -ForegroundColor Red
        Pause-Exit 1
    }
    $user = $v.Trim()
    $tries++
    if ($tries -ge 5 -and [string]::IsNullOrWhiteSpace($user)) {
        Write-Host "❌ 连续输入为空，已退出。" -ForegroundColor Red
        Pause-Exit 1
    }
}

$pw = ""
$tries = 0
while ([string]::IsNullOrWhiteSpace($pw)) {
    $sec = Read-Host "论坛密码（输入时不显示）" -AsSecureString
    if ($null -eq $sec) {
        Write-Host ""
        Write-Host "❌ 读取不到输入。请【直接双击】“获取cookie.bat”运行本工具。" -ForegroundColor Red
        Pause-Exit 1
    }
    try {
        $pw = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
    } catch {
        $pw = ""
    }
    if ($null -eq $pw) { $pw = "" }
    $pw = $pw.Trim()
    $tries++
    if ($tries -ge 5 -and [string]::IsNullOrWhiteSpace($pw)) {
        Write-Host "❌ 连续输入为空，已退出。" -ForegroundColor Red
        Pause-Exit 1
    }
}

# ---------- 4) 取 cookie ----------
Write-Host ""
Write-Host "正在打开浏览器 ..." -ForegroundColor Cyan
Write-Host ">>> 若窗口里出现「请进行人机验证」，请用鼠标点一下验证框，之后会自动登录。" -ForegroundColor Yellow
Write-Host ""

$env:USERNAME = $user
$env:PASSWORD = $pw
& $venvPy (Join-Path $here "get_cookie.py")
$rc = $LASTEXITCODE
$env:PASSWORD = ""

if ($rc -ne 0) {
    Write-Host ""
    Write-Host "❌ 获取失败（原因见上面日志）。" -ForegroundColor Red
    Write-Host "   常见原因：验证没点、账号密码不对、网络波动。请重新运行本工具再试。" -ForegroundColor Yellow
    Pause-Exit 1
}

$txtFile = Join-Path $here "_cookie_text.txt"
if (-not (Test-Path $txtFile)) {
    Write-Host "❌ 未生成结果文件，请重试。" -ForegroundColor Red
    Pause-Exit 1
}
$text = (Get-Content $txtFile -Raw).Trim()

# ---------- 5) 显示结果 ----------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ✅ 获取成功！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "请把下面【整段】文本，粘贴到你的 GitHub 仓库："
Write-Host "  仓库页 → Settings → Secrets and variables → Actions → New repository secret"
Write-Host "  Name   填写：SESSION_COOKIES"
Write-Host "  Secret 粘贴：下面这一整段（很长，注意别漏头尾）"
Write-Host ""
Write-Host $text
Write-Host ""
try {
    Set-Clipboard -Value $text
    Write-Host "（已自动复制到剪贴板，可直接 Ctrl+V 粘贴）" -ForegroundColor Green
} catch {
    Write-Host "（复制到剪贴板失败，请手动选中上面的文本复制）" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "提示：约 30 天后 cookie 会过期，届时重新运行本工具，并把 Secret 更新一次即可。"
Pause-Exit 0
