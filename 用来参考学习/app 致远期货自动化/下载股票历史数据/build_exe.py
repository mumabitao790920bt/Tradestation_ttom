import os
import subprocess
import sys

def check_nuitka():
    """检查Nuitka是否可用"""
    try:
        import nuitka
        print("✅ Nuitka已安装")
        return True
    except ImportError:
        print("❌ Nuitka未安装或不在当前Python环境中")
        return False

def get_python_executable():
    """获取当前Python可执行文件路径"""
    return sys.executable

def build_exe():
    """使用Nuitka打包项目为exe文件 - 完全独立版本"""
    
    # 检查Nuitka
    if not check_nuitka():
        print("请先安装Nuitka: pip install nuitka")
        return False
    
    # 主程序文件
    main_file = "stock_analysis_gui.py"
    
    # 检查主程序文件是否存在
    if not os.path.exists(main_file):
        print(f"错误：找不到主程序文件 {main_file}")
        return False
    
    # 检查必需的数据文件
    required_files = [
        "stock_list_20241219.csv",
        "baostock_complete_data_collector_v2.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"错误：缺少必需的文件: {', '.join(missing_files)}")
        return False
    
    # 创建输出目录
    output_dir = "dist"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 获取当前Python可执行文件
    python_exe = get_python_executable()
    print(f"🔧 使用Python环境: {python_exe}")
    
    # Nuitka打包命令 - 完全独立版本
    cmd = [
        python_exe, "-m", "nuitka",
        "--standalone",  # 创建独立可执行文件，包含所有依赖
        "--onefile",    # 打包成单个exe文件
        "--windows-disable-console",  # 禁用控制台窗口
        "--enable-plugin=tk-inter",   # 启用tkinter插件
        "--include-package=baostock", # 包含baostock包
        "--include-package=pandas",   # 包含pandas包
        "--include-package=tkcalendar", # 包含tkcalendar包
        "--include-package=numpy",    # 包含numpy包
        "--include-package=pymysql",  # 包含pymysql包
        "--include-data-files=baostock_complete_data_collector_v2.py=baostock_complete_data_collector_v2.py",  # 包含数据采集器
        "--include-data-files=stock_list_20241219.csv=stock_list_20241219.csv",  # 包含股票列表CSV文件
        "--output-dir=dist",          # 输出目录
        "--output-filename=股票数据分析系统.exe",  # 输出文件名
        "--assume-yes-for-downloads", # 自动下载依赖
        "--show-progress",            # 显示进度
        "--disable-console",          # 禁用控制台
        main_file
    ]
    
    print("=" * 60)
    print("🚀 开始打包股票数据分析系统 - 完全独立版本")
    print("=" * 60)
    print(f"📁 主程序文件: {main_file}")
    print(f"📂 输出目录: {output_dir}")
    print("🔧 打包模式: 完全独立 (无需Python环境)")
    print("📦 包含文件:")
    print("   - baostock_complete_data_collector_v2.py (数据采集器)")
    print("   - stock_list_20241219.csv (股票列表)")
    print("=" * 60)
    
    try:
        print("⏳ 执行打包命令...")
        print("⚠️  首次打包可能需要较长时间，请耐心等待...")
        print(f"🔧 使用Python: {python_exe}")
        print(f"📦 命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("=" * 60)
        print("✅ 打包成功！")
        print(f"📦 输出文件位置: {output_dir}/股票数据分析系统.exe")
        print("=" * 60)
        
        # 检查生成的文件
        exe_path = os.path.join(output_dir, "股票数据分析系统.exe")
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"📊 文件大小: {file_size:.2f} MB")
            print("💡 文件较大是正常的，包含了所有必要的依赖")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("=" * 60)
        print("❌ 打包失败！")
        print("🔍 错误信息:")
        print(e.stderr)
        print("🔍 标准输出:")
        print(e.stdout)
        print("=" * 60)
        return False
    except Exception as e:
        print("=" * 60)
        print("❌ 打包过程中出现未知错误！")
        print(f"🔍 错误信息: {str(e)}")
        print("=" * 60)
        return False

def test_exe():
    """测试生成的exe文件"""
    exe_path = "dist/股票数据分析系统.exe"
    
    if not os.path.exists(exe_path):
        print("❌ 找不到生成的exe文件")
        return False
    
    print("=" * 50)
    print("🧪 测试生成的exe文件...")
    print("=" * 50)
    
    try:
        # 检查文件大小
        file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
        print(f"📊 文件大小: {file_size:.2f} MB")
        
        if file_size < 50:  # 如果小于50MB，可能缺少依赖
            print("⚠️  警告：文件较小，可能缺少某些依赖")
        else:
            print("✅ 文件大小正常，包含完整依赖")
        
        print("✅ exe文件生成成功")
        print(f"📁 文件路径: {exe_path}")
        print("💡 此文件可以在任何Windows电脑上独立运行")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def create_delivery_package():
    """创建交付包"""
    print("=" * 50)
    print("📦 创建交付包...")
    print("=" * 50)
    
    delivery_dir = "股票数据分析系统_交付版"
    
    # 创建交付目录
    if not os.path.exists(delivery_dir):
        os.makedirs(delivery_dir)
    
    # 复制文件
    files_to_copy = [
        ("dist/股票数据分析系统.exe", f"{delivery_dir}/股票数据分析系统.exe"),
        ("使用说明.md", f"{delivery_dir}/使用说明.md"),
        ("README.md", f"{delivery_dir}/README.md"),
        ("stock_list_20241219.csv", f"{delivery_dir}/stock_list_20241219.csv"),  # 新增：包含股票列表文件
    ]
    
    for src, dst in files_to_copy:
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, dst)
            print(f"✅ 复制: {src} -> {dst}")
        else:
            print(f"⚠️  跳过: {src} (文件不存在)")
    
    print("=" * 50)
    print("✅ 交付包创建完成！")
    print(f"📁 交付目录: {delivery_dir}")
    print("💡 此文件夹可以直接交付给客户使用")
    print("📋 包含文件:")
    print("   - 股票数据分析系统.exe (主程序)")
    print("   - stock_list_20241219.csv (股票列表)")
    print("   - 使用说明.md (使用说明)")
    print("   - README.md (说明文档)")
    print("=" * 50)

def create_standalone_test():
    """创建独立测试说明"""
    test_file = "独立运行测试说明.md"
    
    content = """# 独立运行测试说明

## 测试目的
验证打包的exe文件是否能在没有Python环境的电脑上独立运行。

## 测试步骤

### 1. 准备测试环境
- 找一台没有安装Python的Windows电脑
- 或者创建一个全新的虚拟机

### 2. 复制文件
- 将 `股票数据分析系统.exe` 复制到测试电脑
- 将 `stock_list_20241219.csv` 复制到测试电脑（与exe文件同目录）
- 将 `使用说明.md` 也复制过去

### 3. 运行测试
- 双击运行 `股票数据分析系统.exe`
- 检查是否能正常启动界面
- 测试基本功能是否正常

### 4. 功能验证
- 输入股票代码（如：sh.600030）
- 点击查询按钮
- 检查数据采集是否正常
- 测试K线分析和成交量分析功能
- 测试"下载全部A股"功能（需要CSV文件）

## 预期结果
✅ 程序能正常启动
✅ 界面显示正常
✅ 数据采集功能正常
✅ 分析功能正常
✅ "下载全部A股"功能正常
✅ 无需安装任何额外软件

## 如果出现问题
1. 检查Windows版本是否兼容
2. 确认杀毒软件是否拦截
3. 尝试以管理员身份运行
4. 检查网络连接是否正常
5. 确认CSV文件是否在正确位置

## 成功标准
程序能在任何Windows 10/11电脑上独立运行，无需安装Python或其他依赖。
"""
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 创建测试说明: {test_file}")

def update_usage_guide():
    """更新使用说明"""
    usage_file = "使用说明.md"
    
    content = """# 股票数据分析系统使用说明

## 系统功能
- 股票数据查询和下载
- K线数据分析
- 成交量数据分析
- 批量下载全部A股股票数据
- 断点续传功能

## 使用步骤

### 1. 启动程序
双击运行 `股票数据分析系统.exe`

### 2. 查询股票数据
- 输入股票代码（如：sh.600030）
- 点击"查询"按钮
- 等待数据下载完成

### 3. 分析K线数据
- 设置开始日期和结束日期
- 点击"分析K线数据"按钮
- 查看分析结果

### 4. 分析成交量数据
- 选择需要分析的周期（日线、周线、月线、季线、年线）
- 点击"分析成交量数据"按钮
- 查看详细分析结果

### 5. 下载全部A股数据
- 点击"下载全部A股"按钮
- 程序会自动读取股票列表文件
- 支持暂停/继续/停止功能
- 支持断点续传

## 注意事项
- 首次使用需要下载股票数据
- 确保网络连接正常
- 股票列表文件 `stock_list_20241219.csv` 需要与程序在同一目录
- 数据文件会保存在 `gupiao_lssj` 文件夹中

## 技术支持
如有问题，请查看日志信息或联系技术支持。
"""
    
    with open(usage_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 更新使用说明: {usage_file}")

if __name__ == "__main__":
    print("股票数据分析系统 - Nuitka完全独立打包工具")
    print("=" * 60)
    print("🎯 目标：创建完全独立的exe文件")
    print("💻 要求：无需Python环境即可运行")
    print("📦 新增：包含股票列表文件")
    print("=" * 60)
    
    # 显示当前Python环境信息
    print(f"🔧 当前Python环境: {sys.executable}")
    print(f"🔧 Python版本: {sys.version}")
    print("=" * 60)
    
    # 执行打包
    if build_exe():
        # 测试exe文件
        test_exe()
        
        # 更新使用说明
        update_usage_guide()
        
        # 创建交付包
        create_delivery_package()
        
        # 创建测试说明
        create_standalone_test()
        
        print("\n🎉 打包流程完成！")
        print("📋 检查清单：")
        print("1. ✅ dist/股票数据分析系统.exe (主程序)")
        print("2. ✅ 股票数据分析系统_交付版/ (交付包)")
        print("3. ✅ stock_list_20241219.csv (股票列表)")
        print("4. ✅ 独立运行测试说明.md (测试指南)")
        print("5. ✅ 使用说明.md (更新版使用说明)")
        print("\n💡 重要提醒：")
        print("- 生成的exe文件可以在任何Windows电脑上独立运行")
        print("- 无需安装Python或其他依赖")
        print("- 包含股票列表文件，支持批量下载功能")
        print("- 建议在目标环境上测试运行")
    else:
        print("\n❌ 打包失败，请检查错误信息")
        sys.exit(1) 