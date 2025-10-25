import subprocess
import sys

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ {package} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ {package} 安装失败")
        return False

def main():
    """安装项目依赖"""
    print("正在安装项目依赖...")
    
    # 需要安装的包列表
    packages = [
        "baostock",
        "pandas", 
        "matplotlib",
        "tkcalendar",
        "sqlite3"
    ]
    
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n安装完成: {success_count}/{len(packages)} 个包安装成功")
    
    if success_count == len(packages):
        print("所有依赖安装成功！可以开始使用程序了。")
    else:
        print("部分依赖安装失败，请手动安装失败的包。")

if __name__ == "__main__":
    main() 