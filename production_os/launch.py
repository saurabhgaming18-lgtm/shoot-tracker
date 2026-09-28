"""
Unified Launcher for Production Manager OS & Mobile Shoot Tracker
Runs high-performance server accessible by desktop and phones on the network.
"""

import sys
import os
import socket
import argparse
import webbrowser
import threading
import time
import uvicorn

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from production_os.core.production_engine import ProductionEngine

def get_lan_ip() -> str:
    """Discovers local network IP for phone access."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    """Checks if a network port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False

def find_available_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    """Finds the first available port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        if is_port_available(p):
            return p
    return start_port

def open_browser_delayed(url: str, delay: float = 1.2):
    """Opens browser after server starts."""
    def _open():
        time.sleep(delay)
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()

def main():
    parser = argparse.ArgumentParser(description="Saurabh Patil • Production Manager OS & Mobile Tracker")
    parser.add_argument("--web", action="store_true", help="Launch Web Command Dashboard")
    parser.add_argument("--mobile", action="store_true", help="Launch Mobile Phone Shoot Tracker directly")
    parser.add_argument("--cli", action="store_true", help="Launch Interactive Terminal Assistant")
    parser.add_argument("--sync", action="store_true", help="Regenerate Master Excel Sheet")
    parser.add_argument("--port", type=int, default=8000, help="Web Server Port (Default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Listen Host (Default: 0.0.0.0 for phone access)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    
    args = parser.parse_args()

    if not (args.cli or args.sync or args.mobile):
        args.web = True

    if args.sync:
        print("🔄 Synchronizing Master Excel Sheet...")
        engine = ProductionEngine()
        engine.save()
        print(f"✅ Excel sheet updated: {engine.excel_path}")
        print(f"✅ Root Excel sheet updated: {engine.root_excel_path}")

    elif args.cli:
        from production_os.cli_agent import run_cli
        run_cli()

    else:
        port = args.port
        lan_ip = get_lan_ip()

        if not is_port_available(port, host=args.host):
            # Check if Production OS is already running on this port
            try:
                import urllib.request
                res = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/dashboard", timeout=1.5)
                if res.getcode() == 200:
                    url = f"http://localhost:{port}/mobile" if args.mobile else f"http://localhost:{port}"
                    mobile_url = f"http://{lan_ip}:{port}/mobile"
                    print("=" * 68)
                    print("🎬 SAURABH PATIL • PRODUCTION MANAGER OS & MOBILE TRACKER")
                    print(f"🌐 Server is already active at: {url}")
                    print(f"📱 Phone App (Wi-Fi/LAN):       {mobile_url}")
                    print("🚀 Opening in browser...")
                    print("=" * 68)
                    webbrowser.open(url)
                    return
            except Exception:
                pass

            new_port = find_available_port(start_port=port)
            print(f"⚠️ Port {port} is busy. Automatically switching to available port {new_port}...")
            port = new_port

        local_url = f"http://localhost:{port}/mobile" if args.mobile else f"http://localhost:{port}"
        mobile_url = f"http://{lan_ip}:{port}/mobile"
        
        print("=" * 68)
        print("🎬 SAURABH PATIL • PRODUCTION MANAGER OS & MOBILE SHOOT TRACKER")
        print(f"💻 Desktop Dashboard:          http://localhost:{port}")
        print(f"📱 Mobile Phone Shoot Tracker:  {mobile_url}")
        print(f"📶 Connect any phone on same Wi-Fi/Hotspot to: {mobile_url}")
        print("📊 Master Excel sync active:    Production_Master_Tracker_2026.xlsx")
        print("=" * 68)
        
        if not args.no_browser:
            open_browser_delayed(local_url)

        uvicorn.run("production_os.web.server:app", host=args.host, port=port, reload=False)

if __name__ == "__main__":
    main()
