#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新交付文件脚本 - 重新生成加密版本
"""

import os
import shutil
import base64
import zlib
from pathlib import Path

def encrypt_python_file(file_path, output_dir):
    """加密Python文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 压缩并编码源代码
        compressed = zlib.compress(content.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('ascii')
        
        # 创建加密后的Python文件
        encrypted_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密的Python文件 - {os.path.basename(file_path)}
"""

import base64
import zlib
import sys
import types

def decrypt_and_run():
    """解密并执行代码"""
    # 加密的源代码
    encoded_source = """{encoded}"""
    
    try:
        # 解码和解压缩
        compressed = base64.b64decode(encoded_source.encode('ascii'))
        source_code = zlib.decompress(compressed).decode('utf-8')
        
        # 创建模块并执行
        module = types.ModuleType("__main__")
        exec(source_code, module.__dict__)
        
    except Exception as e:
        print(f"执行错误: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    decrypt_and_run()
'''
        
        # 保存加密文件
        output_file = output_dir / f"encrypted_{os.path.basename(file_path)}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(encrypted_content)
        
        return True
    except Exception as e:
        print(f"加密失败 {file_path}: {e}")
        return False

def update_encrypted_delivery():
    """更新加密交付目录"""
    print("正在更新加密交付目录...")
    
    # 路径设置
    delivery_dir = Path("客户交付")
    unencrypted_dir = delivery_dir / "非加密交付"
    encrypted_dir = delivery_dir / "加密交付"
    
    if not unencrypted_dir.exists():
        print("❌ 非加密交付目录不存在")
        return False
    
    # 清空加密目录
    if encrypted_dir.exists():
        shutil.rmtree(encrypted_dir)
    encrypted_dir.mkdir(exist_ok=True)
    
    # 需要加密的Python文件
    python_files = [
        "GUI_QT.py",
        "GUI_QT_Interactive.py",
        "data_processing.py", 
        "trend_line_processing.py",
        "huatu_mz.py",
        "interactive_backtest.py",
        "回测示例.py",
        "path_fix.py"  # 新增的路径修复模块
    ]
    
    # 加密Python文件
    encrypted_count = 0
    for file_name in python_files:
        file_path = unencrypted_dir / file_name
        if file_path.exists():
            if encrypt_python_file(file_path, encrypted_dir):
                encrypted_count += 1
                print(f"✓ 加密: {file_name}")
            else:
                print(f"✗ 加密失败: {file_name}")
    
    # 复制非Python文件到加密目录（不加密）
    for item in unencrypted_dir.iterdir():
        if item.is_file() and not item.suffix == '.py':
            shutil.copy2(item, encrypted_dir)
            print(f"✓ 复制到加密目录: {item.name}")
    
    print(f"✓ 加密更新完成，共加密 {encrypted_count} 个Python文件")
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("更新加密交付文件")
    print("=" * 50)
    
    try:
        if update_encrypted_delivery():
            print("\n" + "=" * 50)
            print("✓ 加密交付文件更新完成！")
            print("=" * 50)
        else:
            print("\n❌ 更新失败")
            
    except Exception as e:
        print(f"❌ 更新过程中出现错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
