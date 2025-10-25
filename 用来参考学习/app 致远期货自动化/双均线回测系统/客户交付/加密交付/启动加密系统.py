#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双均线回测系统 - 加密启动器
保持原始代码结构，只对源代码进行加密
"""

import base64
import zlib
import sys
import os
from pathlib import Path

def decrypt_source(encrypted_file):
    """解密指定的加密文件"""
    if not os.path.exists(encrypted_file):
        raise FileNotFoundError(f"加密文件不存在: {encrypted_file}")
    
    with open(encrypted_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取加密的源代码
    start_marker = 'encoded_source = """'
    end_marker = '"""'
    
    start_pos = content.find(start_marker) + len(start_marker)
    end_pos = content.find(end_marker, start_pos)
    
    if start_pos == -1 or end_pos == -1:
        raise ValueError("无法找到加密的源代码")
    
    encoded_source = content[start_pos:end_pos]
    
    # 解码和解压缩
    compressed = base64.b64decode(encoded_source.encode('ascii'))
    source_code = zlib.decompress(compressed).decode('utf-8')
    
    return source_code

def create_temp_modules():
    """创建临时模块文件，保持原始导入结构"""
    print("正在创建临时模块...")
    
    # 需要解密的模块列表
    modules_to_decrypt = [
        ("encrypted_path_fix.py", "path_fix.py"),
        ("encrypted_data_processing.py", "data_processing.py"),
        ("encrypted_trend_line_processing.py", "trend_line_processing.py"),
        ("encrypted_huatu_mz.py", "huatu_mz.py"),
        ("encrypted_回测示例.py", "回测示例.py"),
        ("encrypted_interactive_backtest.py", "interactive_backtest.py"),
        ("encrypted_GUI_QT_Interactive.py", "GUI_QT_Interactive.py"),
        ("encrypted_GUI_QT.py", "GUI_QT.py")
    ]
    
    temp_dir = Path("temp_modules")
    temp_dir.mkdir(exist_ok=True)
    
    # 将当前目录添加到Python路径
    sys.path.insert(0, str(temp_dir))
    
    for encrypted_file, module_name in modules_to_decrypt:
        try:
            print(f"  解密模块: {module_name}")
            source_code = decrypt_source(encrypted_file)
            
            # 写入临时文件
            temp_file = temp_dir / module_name
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(source_code)
            
            print(f"  ✓ {module_name} 解密成功")
            
        except Exception as e:
            print(f"  ✗ {module_name} 解密失败: {e}")
            return False
    
    print("所有模块解密完成")
    return True

def cleanup_temp_modules():
    """清理临时模块文件"""
    import shutil
    temp_dir = Path("temp_modules")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        print("临时模块已清理")

def main():
    """主函数"""
    print("=" * 50)
    print("双均线回测系统 - 加密版本")
    print("=" * 50)
    
    try:
        # 创建临时模块
        if not create_temp_modules():
            print("模块创建失败，程序无法启动")
            return
        
        print("\n请选择要运行的程序：")
        print("1. 主程序界面 (GUI_QT)")
        print("2. 交互式回测 (GUI_QT_Interactive)")
        print("3. 退出")
        
        while True:
            try:
                choice = input("\n请输入选择 (1-3): ").strip()
                
                if choice == '1':
                    print("正在启动主程序界面...")
                    # 导入并运行GUI_QT
                    from GUI_QT import main as gui_main
                    gui_main()
                    break
                    
                elif choice == '2':
                    print("正在启动交互式回测...")
                    # 导入并运行GUI_QT_Interactive
                    from GUI_QT_Interactive import main as interactive_main
                    interactive_main()
                    break
                    
                elif choice == '3':
                    print("退出程序")
                    break
                    
                else:
                    print("无效选择，请输入 1、2 或 3")
                    
            except KeyboardInterrupt:
                print("\n\n程序被用户中断")
                break
            except Exception as e:
                print(f"发生错误: {e}")
                import traceback
                traceback.print_exc()
                break
                
    finally:
        # 清理临时文件
        cleanup_temp_modules()

if __name__ == "__main__":
    main()

