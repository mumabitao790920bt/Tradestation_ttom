#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密系统主入口文件 - 完全自包含版本
将所有依赖模块解密并加载到同一个命名空间中
"""

import base64
import zlib
import sys
import types
import os
from pathlib import Path

def decrypt_module(module_name):
    """解密指定的模块"""
    encrypted_file = f"encrypted_{module_name}.py"
    
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

def load_all_modules():
    """加载所有必需的模块到全局命名空间"""
    print("正在加载所有模块...")
    
    # 需要加载的模块列表（按依赖顺序）
    modules_to_load = [
        "path_fix",
        "data_processing", 
        "trend_line_processing",
        "huatu_mz",
        "回测示例",
        "interactive_backtest",
        "GUI_QT_Interactive",
        "GUI_QT"
    ]
    
    global_namespace = {}
    
    for module_name in modules_to_load:
        try:
            print(f"  加载模块: {module_name}")
            source_code = decrypt_module(module_name)
            
            # 执行模块代码到全局命名空间
            exec(source_code, global_namespace)
            print(f"  ✓ {module_name} 加载成功")
            
        except Exception as e:
            print(f"  ✗ {module_name} 加载失败: {e}")
            return None
    
    print("所有模块加载完成")
    return global_namespace

def run_gui_qt(global_namespace):
    """运行GUI_QT主程序"""
    print("正在启动双均线回测系统...")
    
    try:
        # 从全局命名空间获取main函数
        if 'main' in global_namespace:
            global_namespace['main']()
        else:
            print("错误：找不到main函数")
            
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()

def run_interactive(global_namespace):
    """运行交互式回测程序"""
    print("正在启动交互式回测系统...")
    
    try:
        # 查找交互式回测相关的函数
        if 'run_backtest_interactive' in global_namespace:
            print("交互式回测模块已加载")
            # 这里可以添加交互式回测的启动逻辑
        else:
            print("错误：找不到交互式回测函数")
            
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("=" * 50)
    print("双均线回测系统 - 加密版本")
    print("=" * 50)
    
    # 加载所有模块
    global_namespace = load_all_modules()
    if not global_namespace:
        print("模块加载失败，程序无法启动")
        return
    
    print("\n请选择要运行的程序：")
    print("1. 主程序界面 (GUI_QT)")
    print("2. 交互式回测 (GUI_QT_Interactive)")
    print("3. 退出")
    
    while True:
        try:
            choice = input("\n请输入选择 (1-3): ").strip()
            
            if choice == '1':
                run_gui_qt(global_namespace)
                break
            elif choice == '2':
                run_interactive(global_namespace)
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
            break

if __name__ == "__main__":
    main()
