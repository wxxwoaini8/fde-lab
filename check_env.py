# -*- coding: utf-8 -*-
"""check_env.py —— FDE 开发环境自检（Windows：Git Bash / CMD / PowerShell 通用）

用法（在工作区根目录）：
    python check_env.py

判定标准：所有项目显示 [OK] 才算准备完成。出现 [FAIL] 时脚本会在结尾汇总。
退出码 0 = 全绿，1 = 有 FAIL（可直接用于脚本串联）。

本机适配说明：
- 数据库容器名为 fde-postgres（不是教材示例的 fde-pg），凭据从 docker/.env 读取
- Ruff 格式化检查依赖编辑器内部状态，脚本无法检测，改由人工对照 5.1 节第 16 项
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

OK, WARN, FAIL = "OK", "WARN", "FAIL"
RESULTS: list[tuple[str, str, str]] = []

ROOT = Path(__file__).resolve().parent
PG_CONTAINER = "fde-postgres"
GIT = r"D:\Git\bin\git.exe"


# --------------------------------------------------------------------------
# 输出与记录
# --------------------------------------------------------------------------
def _disp_width(text: str) -> int:
    """中文按 2 列、ASCII 按 1 列估算显示宽度，用于对齐。"""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _disp_width(text))


def add(status: str, name: str, detail: str = "") -> None:
    RESULTS.append((status, name, detail))
    tag = {OK: "[OK]  ", WARN: "[WARN]", FAIL: "[FAIL]"}[status]
    line = f"  {tag} {pad(name, 26)}"
    if detail:
        limit = 96
        if _disp_width(detail) > limit:
            detail = clip(detail, limit)
        line += detail
    print(line.rstrip())


def clip(text: str, width: int) -> str:
    out, w = [], 0
    for ch in text:
        cw = 2 if unicodedata.east_asian_width(ch) in "WF" else 1
        if w + cw > width - 1:
            break
        out.append(ch)
        w += cw
    return "".join(out) + "…"


def title(name: str) -> None:
    print()
    print(f"—— {name} " + "-" * (52 - _disp_width(name)))


# --------------------------------------------------------------------------
# 工具函数
# --------------------------------------------------------------------------
def run(cmd: list[str], timeout: int = 20) -> tuple[int, str] | None:
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return None


def first_line(text: str) -> str:
    for ln in text.splitlines():
        if ln.strip():
            return ln.strip()
    return ""


def find_exe(name: str) -> str:
    """先查 PATH，再查常见安装目录（uv 常装在 ~/.local/bin 而不在 PATH）。"""
    for ext in (".exe", ".cmd", ""):
        p = shutil.which(name + ext) if ext else shutil.which(name)
        if p:
            return p
    home = Path.home()
    candidates = [
        home / ".local" / "bin",
        Path(r"C:\Program Files\nodejs"),
        Path(r"D:\Node"),
        Path(r"D:\Git\bin"),
        Path(r"D:\Git\cmd"),
        Path(r"C:\Windows\System32\OpenSSH"),
    ]
    for base in candidates:
        for ext in (".exe", ".cmd"):
            p = base / (name + ext)
            if p.exists():
                return str(p)
    return ""


def probe(label: str, cmd: list[str], expect_prefix: str = "") -> str:
    """执行命令并检查首行前缀，返回版本串（失败返回空）。"""
    res = run(cmd)
    if res is None:
        add(FAIL, label, f"无法执行 {cmd[0]}")
        return ""
    code, out = res
    line = first_line(out)
    if expect_prefix and not line.lower().startswith(expect_prefix.lower()):
        if code != 0:
            add(FAIL, label, line or f"{cmd[0]} 执行失败")
            return ""
    add(OK, label, line)
    return line


# --------------------------------------------------------------------------
# 各项检查
# --------------------------------------------------------------------------
def check_interpreter() -> None:
    title("Python 解释器")
    in_venv = sys.prefix != sys.base_prefix
    print(f"       解释器：{sys.executable}")
    print(f"       版本  ：{sys.version.split()[0]}")
    major, minor = sys.version_info[:2]
    add(OK if (major, minor) >= (3, 11) else FAIL, "Python 版本",
        f"{major}.{minor}（要求 3.11 及以上）")
    add(OK if in_venv else WARN, "虚拟环境",
        "解释器位于项目环境内" if in_venv
        else "当前不是虚拟环境；请用 .venv 里的 python 运行本脚本")

    exe = find_exe("python") or find_exe("python3")
    if not exe:
        add(FAIL, "python 命令", "PATH 里找不到 python")
    elif "windowsapps" in exe.lower():
        add(FAIL, "python 命令", "命中了 Microsoft Store 别名，请关闭应用执行别名")
    else:
        add(OK, "python 命令", exe)


def check_cli() -> None:
    title("命令行工具")
    res = run([sys.executable, "-m", "pip", "--version"])
    if res is not None and res[0] == 0 and first_line(res[1]):
        add(OK, "pip", first_line(res[1]))
    else:
        add(WARN, "pip", "当前环境没有 pip；补装：python -m ensurepip --upgrade")

    uv_line = probe("uv", ["uv", "--version"], "uv ")
    uv_path = find_exe("uv")
    if uv_line and uv_path:
        uv_dir = os.path.normpath(os.path.dirname(uv_path)).lower()
        on_path = {os.path.normpath(d).lower()
                   for d in os.environ.get("PATH", "").split(os.pathsep) if d}
        if uv_dir not in on_path:
            add(WARN, "uv 在 PATH 里",
                f"uv 装在 {uv_dir}，该目录不在 PATH；重启终端或加入用户 PATH")

    probe("Git", [GIT if Path(GIT).exists() else "git", "--version"], "git version")

    node_line = probe("Node.js", ["node", "-v"], "v")
    if node_line:
        try:
            n = int(node_line.lstrip("v").split(".")[0])
            add(OK if n % 2 == 0 else WARN, "Node 是否 LTS",
                f"主版本 {n}（{'偶数 → LTS' if n % 2 == 0 else '奇数 → Current，建议换 LTS'}）")
        except ValueError:
            add(WARN, "Node 是否 LTS", f"无法解析版本：{node_line}")

    if shutil.which("npm") or find_exe("npm"):
        probe("npm", ["cmd", "/c", "npm", "-v"])
    else:
        add(FAIL, "npm", "PATH 里找不到 npm")

    probe("Docker CLI", ["docker", "--version"], "Docker version")


def check_git() -> None:
    title("Git 配置与 GitHub")
    git = GIT if Path(GIT).exists() else "git"
    gcfg = lambda key: first_line(run([git, "config", "--global", key])[1]) if run([git, "config", "--global", key]) else ""

    name = gcfg("user.name")
    add(OK if name else FAIL, "user.name", name or "未配置")
    email = gcfg("user.email")
    add(OK if email else FAIL, "user.email", email or "未配置")
    branch = gcfg("init.defaultBranch")
    add(OK if branch == "main" else FAIL, "init.defaultBranch", branch or "未配置（应为 main）")

    ssh = r"C:\Windows\System32\OpenSSH\ssh.exe"
    res = run([ssh if Path(ssh).exists() else "ssh", "-T", "git@github.com",
               "-o", "BatchMode=yes", "-o", "ConnectTimeout=15"], timeout=30)
    out = res[1] if res else ""
    if "successfully authenticated" in out.lower():
        user = ""
        if "hi " in out.lower():
            user = out.lower().split("hi ", 1)[1].split("!")[0].strip()
        add(OK, "SSH 到 GitHub", f"已认证（{user}）" if user else "已认证")
    else:
        add(FAIL, "SSH 到 GitHub",
            first_line(out) or "认证失败；检查公钥是否已加到 GitHub")


def check_docker() -> None:
    title("Docker 与数据库")
    res = run(["docker", "ps", "--format", "{{.Names}}"], timeout=30)
    if res is None or res[0] != 0:
        add(FAIL, "Docker 引擎", "未运行或未启动 Docker Desktop")
        add(FAIL, "PostgreSQL 容器", "引擎不可用，无法检查")
        return
    add(OK, "Docker 引擎", "运行中")

    names = [x.strip() for x in res[1].splitlines() if x.strip()]
    add(OK if PG_CONTAINER in names else FAIL, "PostgreSQL 容器",
        f"{PG_CONTAINER} 运行中" if PG_CONTAINER in names
        else f"未运行（现有：{', '.join(names) or '无'}）")

    if PG_CONTAINER not in names:
        return

    user, dbname = "fde", "fde_learn"
    env_file = ROOT / "docker" / ".env"
    if env_file.exists():
        for ln in env_file.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln.startswith("POSTGRES_USER="):
                user = ln.split("=", 1)[1].strip()
            elif ln.startswith("POSTGRES_DB="):
                dbname = ln.split("=", 1)[1].strip()

    res = run(["docker", "exec", PG_CONTAINER, "psql", "-U", user, "-d", dbname,
               "-tAc", "select 1;"], timeout=30)
    if res and res[0] == 0 and "1" in res[1]:
        add(OK, "连接数据库", f"{dbname} / {user} 查询正常")
    else:
        add(FAIL, "连接数据库", first_line(res[1]) if res else "无法执行 psql")

    res = run(["docker", "exec", PG_CONTAINER, "psql", "-U", user, "-d", dbname,
               "-tAc", "select extversion from pg_extension where extname='vector';"],
              timeout=30)
    if res and res[0] == 0 and res[1].strip():
        add(OK, "pgvector 扩展", f"已启用 {res[1].strip()}")
    else:
        add(WARN, "pgvector 扩展", "未启用；第 14 周前执行 CREATE EXTENSION vector 即可")


def check_workspace() -> None:
    title("工作区与磁盘")
    git = GIT if Path(GIT).exists() else "git"
    if not (ROOT / ".git").exists():
        add(FAIL, "Git 仓库", f"{ROOT} 不是仓库")
    else:
        res = run([git, "log", "--oneline", "-1"], timeout=20)
        add(OK if res and res[0] == 0 else FAIL, "Git 仓库",
            first_line(res[1]) if res and res[0] == 0 else "没有任何提交")
        res = run([git, "remote", "get-url", "origin"], timeout=20)
        add(OK if res and res[0] == 0 else WARN, "远端 origin",
            first_line(res[1]) if res and res[0] == 0 else "未配置远端")

    venv = ROOT / ".venv" / "Scripts" / "python.exe"
    add(OK if venv.exists() else FAIL, "项目虚拟环境",
        str(venv) if venv.exists() else "未找到 .venv/Scripts/python.exe")

    total_gb = shutil.disk_usage(ROOT).free / (1024 ** 3)
    add(OK if total_gb >= 10 else WARN, "磁盘余量",
        f"{ROOT.drive} 剩余 {total_gb:.1f} GB（建议 ≥10 GB）")

    shell = os.environ.get("SHELL", "")
    add(OK if "bash" in shell.lower() else WARN, "终端类型",
        shell or "未识别（Git Bash 下会显示 /usr/bin/bash）")


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------
def main() -> int:
    print("=" * 56)
    print(" FDE 开发环境自检")
    print("=" * 56)
    check_interpreter()
    check_cli()
    check_git()
    check_docker()
    check_workspace()

    n_ok = sum(1 for s, _, _ in RESULTS if s == OK)
    n_warn = sum(1 for s, _, _ in RESULTS if s == WARN)
    fails = [(n, d) for s, n, d in RESULTS if s == FAIL]

    print()
    print("=" * 56)
    print(f" 通过 {n_ok} 项，需注意 {n_warn} 项，未通过 {len(fails)} 项")
    print("=" * 56)
    if fails:
        for name, detail in fails:
            print(f"  [FAIL] {name}：{detail}")
        print()
        print(" 处理完上面几项后重跑本脚本。")
        return 1
    print(" 环境全部就绪，可以进入第 1 册。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
