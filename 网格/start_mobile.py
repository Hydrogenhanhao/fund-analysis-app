#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动端基金分析系统启动脚本
"""

import socket
import subprocess
import sys
import os
from config_mobile import FLASK_HOST, FLASK_PORT

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 创建一个socket连接来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    print("=" * 60)
    print("📱 移动端基金分析系统")
    print("=" * 60)
    
    # 获取本机IP
    local_ip = get_local_ip()
    
    print(f"🚀 正在启动移动端服务器...")
    print(f"📱 手机访问地址: http://{local_ip}:{FLASK_PORT}")
    print(f"💻 电脑访问地址: http://127.0.0.1:{FLASK_PORT}")
    print("=" * 60)
    print("📋 使用说明:")
    print("1. 确保手机和电脑在同一WiFi网络")
    print("2. 在手机浏览器中输入上述手机访问地址")
    print("3. 按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    try:
        # 启动Flask应用
        from APP_mobile import app
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
