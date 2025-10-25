import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime

EMBED_PY_URL = "https://www.python.org/ftp/python/3.9.13/python-3.9.13-embed-amd64.zip"

# 最小依赖（可按需扩充）
REQUIREMENTS = [
    "PyQt5==5.15.*",
    "PyQtWebEngine==5.15.*",
    "backtrader",
    "pandas",
    "numpy",
    "matplotlib",
    "Pillow",
]

# 项目必要文件与目录
PROJECT_FILES = [
    "GUI_QT.py",
    "GUI_QT_Interactive.py",
    "interactive_backtest.py",
    "回测示例.py",
    "huatu_mz.py",
    "data_processing.py",
    "trend_line_processing.py",
    os.path.join("下载股票历史数据", "downloader_bridge.py"),
]


def run(cmd, cwd=None, check=True):
    print("$", cmd)
    proc = subprocess.run(cmd, shell=True, cwd=cwd)
    if check and proc.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")
    return proc.returncode


def download(url: str, dst: Path):
    import urllib.request
    print(f"Downloading: {url} -> {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r, open(dst, "wb") as f:
        shutil.copyfileobj(r, f)


def write_text(p: Path, content: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def build_portable(out_root: Path, src_root: Path):
    # 目录结构
    pkg_dir = out_root / "Portable_Package"
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    (pkg_dir / "project").mkdir(parents=True, exist_ok=True)
    (pkg_dir / "wheels").mkdir(parents=True, exist_ok=True)

    # 复制项目文件
    for rel in PROJECT_FILES:
        src = src_root / rel
        dst = pkg_dir / "project" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not src.exists():
            print(f"[WARN] missing: {rel}")
            continue
        shutil.copy2(src, dst)

    # 生成 requirements.txt
    req_txt = "\n".join(REQUIREMENTS) + "\n"
    write_text(pkg_dir / "requirements.txt", req_txt)

    # 下载嵌入式 Python 与 get-pip
    embed_zip = pkg_dir / "python_embed.zip"
    download(EMBED_PY_URL, embed_zip)

    # 预下载离线 wheels（使用当前环境）
    # 预下载离线 wheels（包含 pip 自身，避免在线获取 get-pip）
    run(f"{sys.executable} -m pip download pip -d wheels", cwd=str(pkg_dir))
    run(f"{sys.executable} -m pip download -r requirements.txt -d wheels", cwd=str(pkg_dir))

    # 可选：源码混淆（pyarmor），若可用则使用
    try:
        run(f"{sys.executable} -m pip install -U pyarmor", cwd=str(src_root))
        obf_dir = pkg_dir / "project_obf"
        if obf_dir.exists():
            shutil.rmtree(obf_dir)
        obf_dir.mkdir()
        # 仅对项目 py 文件做混淆，不处理第三方
        # 逐文件混淆，失败则回退原文件
        for rel in PROJECT_FILES:
            if not rel.endswith(".py"):
                continue
            src = pkg_dir / "project" / rel
            if not src.exists():
                continue
            out_file = obf_dir / Path(rel).name
            out_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                run(f"{sys.executable} -m pyarmor.cli obfuscate --platform windows.x86_64 --output '{out_file.parent}' '{src}'")
            except Exception:
                shutil.copy2(src, out_file)
        # 用混淆后文件替换根项目入口（保留原始 project 以备调试）
        # 简化处理：复制 obf 文件到 project 根，同名覆盖
        for f in obf_dir.glob("*.py"):
            shutil.copy2(f, pkg_dir / "project" / f.name)
    except Exception as e:
        print(f"[INFO] 跳过混淆（pyarmor 不可用或失败）：{e}")

    # 生成 install.cmd
    # 写 pip_bootstrap.py
    pip_boot = (
        "import sys, os, glob, zipfile, shutil\n"
        "wheels_dir = sys.argv[1]\n"
        "cands = glob.glob(os.path.join(wheels_dir, 'pip-*.whl'))\n"
        "assert cands, 'pip wheel not found'\n"
        "whl = max(cands, key=os.path.getsize)\n"
        "td = os.path.join(os.path.dirname(__file__), '_pip_boot')\n"
        "shutil.rmtree(td, True); os.makedirs(td, exist_ok=True)\n"
        "with zipfile.ZipFile(whl) as z: z.extractall(td)\n"
        "sys.path.insert(0, td)\n"
        "from pip._internal.cli.main import main as pip_main\n"
        "raise SystemExit(pip_main(['install','--no-index','--find-links', wheels_dir, 'pip']))\n"
    )
    write_text(pkg_dir / "pip_bootstrap.py", pip_boot)

    install_cmd = f"""
@echo off
setlocal
echo == Portable Python 安装开始 ==
set PKG_DIR=%~dp0
set PYDIR=%PKG_DIR%local_python

if not exist "%PYDIR%" mkdir "%PYDIR%"

rem 解压嵌入式 Python（需 PowerShell）
powershell -NoProfile -Command "Expand-Archive -Force '%PKG_DIR%python_embed.zip' '%PYDIR%'"

rem 修改 _pth 以启用 site-packages
for %%f in ("%PYDIR%\python3*.pth") do (
  echo .>"%%f"
  echo Lib\site-packages>>"%%f"
  echo import site>>"%%f"
)

rem 离线安装 pip（从 wheels 中）
"%PYDIR%\python.exe" "%PKG_DIR%pip_bootstrap.py" "%PKG_DIR%wheels"

rem 离线安装依赖
"%PYDIR%\python.exe" -m pip install --no-index --find-links="%PKG_DIR%wheels" -r "%PKG_DIR%requirements.txt"

echo 安装完成。
echo 运行普通回测:  双击 run_gui.cmd
echo 运行交互回测:  双击 run_interactive.cmd
pause
"""
    write_text(pkg_dir / "install.cmd", install_cmd)

    # 生成 run 脚本
    run_gui = r"""
@echo off
setlocal
set PKG_DIR=%~dp0
"%PKG_DIR%local_python\python.exe" "%PKG_DIR%project\GUI_QT.py"
"""
    write_text(pkg_dir / "run_gui.cmd", run_gui)

    run_inter = r"""
@echo off
setlocal
set PKG_DIR=%~dp0
"%PKG_DIR%local_python\python.exe" "%PKG_DIR%project\GUI_QT_Interactive.py"
"""
    write_text(pkg_dir / "run_interactive.cmd", run_inter)

    # 使用说明
    readme = """使用说明（便携版）
1) 双击 install.cmd，一步完成：解压便携 Python、安装 pip、离线安装依赖。
2) 安装后：
   - 运行普通回测：双击 run_gui.cmd
   - 运行交互回测：双击 run_interactive.cmd
3) 无需系统安装 Python，所有文件仅在本文件夹内。若被安全软件拦截，请允许。
"""
    write_text(pkg_dir / "使用说明_便携版.txt", readme)

    print(f"\n✅ 便携交付包已生成: {pkg_dir}")


if __name__ == "__main__":
    out_root = Path(os.environ.get("PKG_WORK", r"D:\pkg_work"))
    src_root = Path(os.environ.get("PKG_SRC", os.path.dirname(os.path.abspath(__file__))))
    out_root.mkdir(parents=True, exist_ok=True)
    build_portable(out_root, src_root)


