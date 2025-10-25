"""
Tradestation 自动化交易策略系统主程序
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.core.config import settings
from app.data.storage import DataStorage
from app.ui.main import TradingUI


def initialize_database():
    """初始化数据库"""
    print("正在初始化数据库...")
    storage = DataStorage()
    storage.create_tables()
    print("数据库初始化完成")


def run_ui():
    """运行UI界面"""
    print("启动Tradestation自动化交易策略系统...")
    print(f"应用名称: {settings.app_name}")
    print(f"版本: {settings.app_version}")
    print("=" * 50)
    
    ui = TradingUI()
    ui.run()


def main():
    """主函数"""
    print("🚀 Tradestation 自动化交易策略系统")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            # 初始化数据库
            initialize_database()
        elif command == "ui":
            # 运行UI界面
            run_ui()
        elif command == "test":
            # 运行测试
            print("运行测试...")
            # 这里可以添加测试代码
        else:
            print(f"未知命令: {command}")
            print("可用命令: init, ui, test")
    else:
        # 默认运行UI界面
        run_ui()


if __name__ == "__main__":
    main()
