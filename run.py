#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import webbrowser
import time


def main():
    # 改变到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("\n" + "=" * 60)
    print("  企业考勤管理系统 - 移动端优化版 v2.0")
    print("=" * 60 + "\n")

    # 1. 检查Python
    print("[1] 检查Python...", end=" ")
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        print(f"✓ {result.stdout.strip()}\n")
    except:
        print("✗ 失败\n")
        return 1

    # 2. 检查文件
    print("[2] 检查文件...", end=" ")
    app_file = os.path.join(script_dir, 'app_mobile_optimized.py')
    if os.path.exists(app_file):
        print(f"✓ 找到 app_mobile_optimized.py\n")
    else:
        print("✗ 找不到\n")
        print(f"当前目录: {script_dir}\n")
        print("目录内容:")
        for f in os.listdir(script_dir):
            if f.endswith('.py'):
                print(f"  - {f}")
        return 1

    # 3. 安装依赖（添加 pytz）
    print("[3] 安装依赖...", end=" ")
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-q',
            'streamlit==1.54.0', 'pandas==2.3.3', 'sqlalchemy==2.0.47',
            'openpyxl==3.1.5', 'streamlit-option-menu==0.4.0',
            'altair==6.0.0', 'python-dateutil==2.9.0', 'pytz==2024.2'
        ], capture_output=True, timeout=60)
        print("✓ 完成\n")
    except Exception as e:
        print(f"✗ 失败: {e}\n")
        return 1

    # 4. 获取IP
    print("[4] 获取网络地址...", end=" ")
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"✓ {local_ip}\n")
    except:
        local_ip = None
        print("⚠ 无法获取\n")

    # 5. 打印访问地址
    print("=" * 60)
    print("          启动完成 - 访问地址：")
    print("=" * 60)
    print("  本地访问: http://localhost:8501")
    if local_ip:
        print(f"  手机访问: http://{local_ip}:8501")
    print("=" * 60 + "\n")

    # 6. 打开浏览器
    print("[5] 打开浏览器...", end=" ")
    try:
        webbrowser.open('http://localhost:8501')
        print("✓\n")
    except:
        print("✗\n")

    # 7. 启动Streamlit
    print("[6] 启动应用...\n")
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run',
            'app_mobile_optimized.py',
            '--server.port', '8501',
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false',
            '--client.showErrorDetails', 'false'
        ])
        return 0
    except KeyboardInterrupt:
        print("\n\n应用已关闭")
        return 0
    except Exception as e:
        print(f"\n启动失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())