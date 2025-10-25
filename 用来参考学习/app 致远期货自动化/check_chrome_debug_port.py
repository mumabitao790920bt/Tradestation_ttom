#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome调试端口检测器
用于检测当前Chrome浏览器的调试端口，方便复用已登录的浏览器实例
"""

import requests
import json
import time
import subprocess
import os
import psutil
from datetime import datetime

def check_chrome_debug_ports():
    """检测Chrome调试端口"""
    print("🔍 正在检测Chrome调试端口...")
    
    # 常见的调试端口
    common_ports = [9222, 9223, 9224, 9225, 9226, 9227, 9228, 9229, 9230]
    
    active_ports = []
    
    for port in common_ports:
        try:
            url = f"http://127.0.0.1:{port}/json"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                tabs = response.json()
                active_ports.append({
                    'port': port,
                    'tabs': tabs,
                    'count': len(tabs)
                })
                print(f"✅ 发现调试端口 {port}，有 {len(tabs)} 个标签页")
        except:
            continue
    
    return active_ports

def find_target_tab(active_ports, target_domain="fk.crkpk.com"):
    """查找目标域名的标签页"""
    print(f"\n🎯 查找包含 {target_domain} 的标签页...")
    
    target_tabs = []
    
    for port_info in active_ports:
        port = port_info['port']
        tabs = port_info['tabs']
        
        for tab in tabs:
            url = tab.get('url', '')
            title = tab.get('title', '')
            
            if target_domain in url:
                target_tabs.append({
                    'port': port,
                    'tab_id': tab.get('id'),
                    'url': url,
                    'title': title,
                    'type': tab.get('type', 'page')
                })
                print(f"✅ 找到目标标签页:")
                print(f"   端口: {port}")
                print(f"   标题: {title}")
                print(f"   URL: {url}")
                print(f"   标签ID: {tab.get('id')}")
    
    return target_tabs

def create_browser_config(debug_port):
    """创建浏览器配置文件"""
    config = {
        "debugger_address": f"127.0.0.1:{debug_port}",
        "chrome_binary": None,
        "user_data_dir": None,
        "profile_directory": None
    }
    
    # 尝试自动检测Chrome路径
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            config["chrome_binary"] = path
            break
    
    # 尝试检测用户数据目录
    user_data_path = r"C:\Users\{}\AppData\Local\Google\Chrome\User Data".format(os.getenv('USERNAME', ''))
    if os.path.exists(user_data_path):
        config["user_data_dir"] = user_data_path
        config["profile_directory"] = "Default"
    
    return config

def main():
    """主函数"""
    print("=" * 60)
    print("Chrome调试端口检测器")
    print("=" * 60)
    
    # 1. 检测调试端口
    active_ports = check_chrome_debug_ports()
    
    if not active_ports:
        print("\n❌ 未发现任何Chrome调试端口")
        print("\n💡 解决方案:")
        print("1. 关闭所有Chrome浏览器")
        print("2. 用以下命令启动Chrome:")
        print("   chrome.exe --remote-debugging-port=9222 --user-data-dir=\"C:\\ChromeUserData\"")
        print("3. 手动打开 https://fk.crkpk.com/trade/MHI 并登录")
        print("4. 重新运行此脚本检测")
        return
    
    # 2. 查找目标标签页
    target_tabs = find_target_tab(active_ports)
    
    if not target_tabs:
        print(f"\n⚠️ 未找到包含 fk.crkpk.com 的标签页")
        print("\n💡 解决方案:")
        print("1. 在已打开的Chrome中手动打开 https://fk.crkpk.com/trade/MHI")
        print("2. 确保已登录账户")
        print("3. 重新运行此脚本检测")
        return
    
    # 3. 选择最佳端口
    best_port = target_tabs[0]['port']
    print(f"\n🎯 推荐使用调试端口: {best_port}")
    
    # 4. 创建配置文件
    config = create_browser_config(best_port)
    
    config_file = "weex_browser_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已创建配置文件: {config_file}")
    print("配置内容:")
    print(json.dumps(config, ensure_ascii=False, indent=2))
    
    print(f"\n🚀 现在可以运行元素检测器:")
    print(f"   python 通过点击获取网页元素.py")
    print(f"   点击'启动浏览器'即可复用已登录的页面")

if __name__ == "__main__":
    main()
