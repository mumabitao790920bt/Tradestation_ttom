import os
import sys
import subprocess


def ensure_nuitka():
    try:
        import nuitka  # noqa: F401
    except Exception:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "nuitka", "orderedset", "zstandard"])  # nuitka deps


def build_pyqt_app(script: str, output_name: str, output_dir: str = "dist"):
    python_exe = sys.executable
    # Detect PyQtWebEngine availability and its resource paths
    has_webengine = False
    webengine_data_args = []
    try:
        import PyQt5  # type: ignore
        from PyQt5 import QtWebEngineWidgets  # noqa: F401
        has_webengine = True
        qt_pkg = os.path.dirname(PyQt5.__file__)
        qt5_dir = os.path.join(qt_pkg, 'Qt5')
        res_dir = os.path.join(qt5_dir, 'resources')
        trans_dir = os.path.join(qt5_dir, 'translations')
        bin_dir = os.path.join(qt5_dir, 'bin')
        if os.path.isdir(res_dir):
            webengine_data_args += [f"--include-data-dir={res_dir}=PyQt5/Qt5/resources"]
        if os.path.isdir(trans_dir):
            webengine_data_args += [f"--include-data-dir={trans_dir}=PyQt5/Qt5/translations"]
        qtwe_proc = os.path.join(bin_dir, 'QtWebEngineProcess.exe')
        if os.path.exists(qtwe_proc):
            webengine_data_args += [f"--include-data-files={qtwe_proc}=QtWebEngineProcess.exe"]
    except Exception:
        has_webengine = False
    base = [
        python_exe, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--windows-console-mode=disable",
        "--assume-yes-for-downloads",
        "--enable-plugin=pyqt5",
        # 稳定插件族；WebEngine 资源通过 include-data-dir 注入
        "--include-qt-plugins=sensible,platforms,styles,imageformats,iconengines",
        f"--output-dir={output_dir}",
        f"--output-filename={output_name}",
        "--nofollow-import-to=tests,examples",
        script,
    ]
    base.extend(webengine_data_args)
    # Optional icon
    if os.path.exists("app.ico"):
        base.insert(3, "--windows-icon-from-ico=app.ico")
    # Optional UPX
    upx = os.environ.get("UPX_BIN")
    if upx and os.path.exists(upx):
        base.insert(3, f"--upx-binary={upx}")
        base.insert(3, "--enable-plugin=upx")

    print("\n=== Building (onefile):", script)
    print(" ", " ".join(base))
    try:
        subprocess.check_call(base)
        return True
    except subprocess.CalledProcessError:
        # Fallback to dir mode, more稳定
        dir_cmd = base.copy()
        dir_cmd.remove("--onefile")
        print("Onefile failed, fallback to standalone directory mode...")
        print(" ", " ".join(dir_cmd))
        subprocess.check_call(dir_cmd)
        return True


def main():
    ensure_nuitka()
    ok1 = build_pyqt_app("GUI_QT.py", "GUI_QT.exe")
    ok2 = build_pyqt_app("GUI_QT_Interactive.py", "GUI_QT_Interactive.exe")
    if ok1 and ok2:
        print("\n✅ All done. See 'dist' folder.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()


