import os
import shutil
import subprocess
import sys
from datetime import datetime


def run_cmd(cmd, cwd=None):
    print("$", cmd)
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")


def ensure_dir(path: str):
    if os.path.exists(path):
        return
    os.makedirs(path, exist_ok=True)


def copy_needed_files(src_root: str, pkg_root: str):
    need_files = [
        "GUI_QT.py",
        "GUI_QT_Interactive.py",
        "interactive_backtest.py",
        "回测示例.py",
        "huatu_mz.py",
        "data_processing.py",
        "trend_line_processing.py",
        "build_exe.py",
        os.path.join("下载股票历史数据", "downloader_bridge.py"),
    ]
    for rel in need_files:
        src = os.path.join(src_root, rel)
        dst = os.path.join(pkg_root, rel)
        ensure_dir(os.path.dirname(dst))
        if not os.path.exists(src):
            print(f"[WARN] 缺少文件: {rel}")
            continue
        shutil.copy2(src, dst)


def main():
    # 默认参数
    work_root = os.environ.get("PKG_WORK", r"D:\pkg_work")
    env_name = os.environ.get("PKG_ENV", "pybt_pkg")
    src_root = os.environ.get("PKG_SRC", os.path.dirname(os.path.abspath(__file__)))

    print("=== 一键打包开始 ===")
    print("工作目录:", work_root)
    print("源项目:", src_root)
    print("环境名:", env_name)

    # 1) 准备工作目录
    pkg_root = os.path.join(work_root, "proj")
    if os.path.exists(pkg_root):
        shutil.rmtree(pkg_root, ignore_errors=True)
    ensure_dir(pkg_root)

    # 2) 复制必要文件
    copy_needed_files(src_root, pkg_root)

    # 3) 创建干净 conda 环境 (Python 3.9)
    print("创建 conda 环境", env_name)
    try:
        run_cmd(f"cmd /c conda env remove -n {env_name} -y")
    except Exception:
        print(f"[INFO] 环境 {env_name} 不存在，跳过删除。")
    run_cmd(f"cmd /c conda create -n {env_name} python=3.9 -y")

    # 4) 安装最小依赖（conda）
    conda_pkgs = "pyqt=5.15.* pyqtwebengine=5.15.* pandas numpy matplotlib pillow pip"
    run_cmd(f"cmd /c conda install -n {env_name} -y {conda_pkgs}")

    # 5) 安装 pip 依赖（在该环境）
    run_cmd(f"cmd /c conda run -n {env_name} pip install backtrader nuitka orderedset zstandard")

    # 6) 执行打包
    print("开始打包...")
    run_cmd(f"cmd /c conda run -n {env_name} python build_exe.py", cwd=pkg_root)

    dist_dir = os.path.join(pkg_root, "dist")
    print("\n✅ 完成。可执行文件在:", dist_dir)

    # 7) 生成交付包
    time_tag = datetime.now().strftime("%Y%m%d_%H%M")
    delivery_dir = os.path.join(work_root, f"交付包_{time_tag}")
    if os.path.exists(delivery_dir):
        shutil.rmtree(delivery_dir, ignore_errors=True)
    ensure_dir(delivery_dir)

    # 复制 exe 或 standalone 目录
    if os.path.exists(dist_dir):
        for name in os.listdir(dist_dir):
            s = os.path.join(dist_dir, name)
            d = os.path.join(delivery_dir, name)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

    # 附带文档/资源（如存在）
    for rel in ["stock_list_20241219.csv", "README.md", "使用说明.md"]:
        src = os.path.join(src_root, rel)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(delivery_dir, os.path.basename(src)))

    # 简要说明
    readme = os.path.join(delivery_dir, "使用说明_快速开始.txt")
    if not os.path.exists(os.path.join(delivery_dir, "使用说明.md")):
        with open(readme, "w", encoding="utf-8") as f:
            f.write(
                """交付包快速开始
1) 双击运行 GUI_QT.exe（普通回测）或 GUI_QT_Interactive.exe（交互式回测）。
2) 如未生成单文件，目录中 *.dist 内包含可执行程序，请进入目录运行同名 exe。
3) 若使用交互式回测，出现上方决策条后，可先缩放图表，再选择“按策略执行/跳过”。
4) 如需日线数据源，放置 stock_list_20241219.csv 与程序同目录可用。
注：首次运行可能被安全软件拦截，请允许。
"""
            )

    print("交付包已生成:", delivery_dir)
    print("=== 一键打包结束 ===")


if __name__ == "__main__":
    main()


