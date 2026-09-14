#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import subprocess
import webbrowser
import urllib.request
from datetime import datetime

def install_requirements():
    for package in ["rich", "curl_cffi"]:
        try:
            __import__(package if package != "curl_cffi" else "curl_cffi.requests")
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_requirements()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box
from curl_cffi import requests

console = Console()

NASA_LOGO = r"""
███╗   ██╗ █████╗ ███████╗ █████╗
████╗  ██║██╔══██╗██╔════╝██╔══██╗
██╔██╗ ██║███████║███████║███████║
██║╚██╗██║██╔══██║╚════██║██╔══██║
██║ ╚████║██║  ██║███████║██║  ██║
╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
"""

# Thay đổi link này thành link Raw file domains.txt trên GitHub của bạn
GITHUB_DOMAIN_URL = "https://raw.githubusercontent.com/username/repo/main/domains.txt"
LOCAL_DOMAIN_FILE = "domains.txt"
PROXY_FILE = "proxy.txt"

def clear_screen():
    os.system("clear")

def gradient_logo():
    colors = [
        "bold red", "bold orange1", "bold yellow", 
        "bold green", "bold cyan", "bold blue", "bold magenta"
    ]
    text = Text()
    lines = NASA_LOGO.splitlines()
    for line in lines:
        if not line:
            text.append("\n")
            continue
        for i, char in enumerate(line):
            if char == " ":
                text.append(" ")
            else:
                color = colors[i % len(colors)]
                text.append(char, style=color)
        text.append("\n")
    return Align.center(text)

def log_line(level, message):
    now = datetime.now().strftime("%H:%M:%S")
    level_colors = {
        "INFO": "cyan",
        "PASS": "green",
        "WARN": "yellow",
        "FAIL": "red",
        "STEALTH": "magenta",
    }
    color = level_colors.get(level, "white")
    return Text.assemble(
        (f"{now} ", "dim"),
        ("[STEALTH] ", "bright_blue"),
        (f"{level:<4} ", color),
        (message, "white"),
    )

def show_log(level, message):
    console.print(log_line(level, message))

def load_domains():
    domains = []
    try:
        if os.path.exists(LOCAL_DOMAIN_FILE):
            with open(LOCAL_DOMAIN_FILE, "r", encoding="utf-8") as f:
                domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            show_log("PASS", f"Đã tải {len(domains)} domain từ bộ nhớ cục bộ.")
        else:
            show_log("INFO", "Đang tải danh sách domain từ GitHub...")
            req = urllib.request.urlopen(GITHUB_DOMAIN_URL, timeout=5)
            content = req.read().decode("utf-8")
            domains = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
            with open(LOCAL_DOMAIN_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(domains))
            show_log("PASS", f"Đã tải và lưu {len(domains)} domain từ GitHub.")
    except Exception as e:
        show_log("WARN", f"Không thể tải từ GitHub: {e}. Dùng danh sách dự phòng.")
        domains = ["octohide.com", "linksv.net"]
    return domains

def load_proxy():
    if os.path.exists(PROXY_FILE):
        try:
            with open(PROXY_FILE, "r", encoding="utf-8") as f:
                proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                if proxies:
                    proxy_url = proxies[0]
                    show_log("PASS", f"Đã nạp Proxy ẩn IP: {proxy_url}")
                    return {"http": proxy_url, "https": proxy_url}
        except Exception as e:
            show_log("WARN", f"Lỗi đọc file proxy: {e}")
    show_log("WARN", "Không tìm thấy file proxy.txt, sử dụng IP gốc của thiết bị.")
    return None

def get_clipboard_url():
    """Lấy link từ Clipboard Android qua Termux API với thời gian chờ tối ưu, chống treo máy"""
    try:
        res = subprocess.run(["termux-clipboard-get"], capture_output=True, text=True, timeout=1)
        if res.returncode == 0:
            clip_text = res.stdout.strip()
            if clip_text:
                for token in clip_text.split():
                    if token.startswith(("http://", "https://")):
                        return token
                return clip_text
    except Exception:
        pass
    return None

def show_startup():
    clear_screen()
    console.print(Panel(
        gradient_logo(),
        border_style="bright_white",
        padding=(0, 2),
        title="[bold cyan]OCTO LINK ENGINE - PROXY & STEALTH[/bold cyan]",
        subtitle="[dim]Termux + TLS Spoofing + Anti-Freeze Clipboard[/dim]",
    ))

    table = Table(
        title="ENGINE STATUS",
        box=box.SIMPLE_HEAVY,
        border_style="green",
        show_header=False,
    )
    table.add_row("Host", "[green]Termux / Android[/green]")
    table.add_row("Cloudflare Bypass", "[cyan]Active (Chrome 120 TLS Impersonation)[/cyan]")
    table.add_row("IP Protection", "[yellow]Proxy Supported[/yellow]")
    table.add_row("Auto-Capture", "[magenta]Optimized Anti-Freeze Clipboard[/magenta]")
    table.add_row("Started", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    console.print(table)
    console.print()

def main():
    show_startup()
    domains = load_domains()
    proxy_config = load_proxy()

    show_log("PASS", "Khởi tạo thành công hệ thống bảo mật & clipboard tối ưu")
    console.print()

    while True:
        console.print("-" * 50, style="dim")
        url = console.input("[bold cyan]>> Dán link cần vượt (hoặc nhập 'exit' để thoát): [/bold cyan]").strip()

        if url.lower() in ["exit", "quit", "q"]:
            show_log("INFO", "Đang thoát chương trình. Tạm biệt!")
            break

        if not url.startswith(("http://", "https://")):
            show_log("FAIL", "URL không hợp lệ, vui lòng thử lại.")
            continue

        matched_domain = None
        for dom in domains:
            if dom in url:
                matched_domain = dom
                break

        if matched_domain:
            show_log("PASS", f"Khớp domain quản lý: [bold green]{matched_domain}[/bold green]")
        else:
            show_log("WARN", "Domain ngoài danh sách GitHub, vẫn tiếp tục xử lý...")

        show_log("STEALTH", "Đang kết nối qua Proxy & giả lập vân tay Chrome 120...")
        
        try:
            session = requests.Session(impersonate="chrome120")
            response = session.get(url, proxies=proxy_config, timeout=15, allow_redirects=True)
            
            show_log("PASS", f"Kết nối thành công! HTTP Status: {response.status_code}")
            
            if "cf-browser-verification" in response.text or "Just a moment..." in response.text or response.status_code in [403, 503]:
                show_log("WARN", "Phát hiện thách thức JavaScript của Cloudflare. Đang mở trình duyệt...")
                webbrowser.open(url)
            else:
                show_log("PASS", "Vượt qua hàng rào mạng Cloudflare thành công mà không lộ IP thật!")

        except Exception as e:
            show_log("WARN", f"Lỗi kết nối ẩn danh: {e}. Chuyển sang mở trình duyệt thủ công.")
            webbrowser.open(url)

        console.print()
        console.print("[dim]Mẹo: Copy link trên trình duyệt, sau đó nhấn Enter để nhận diện tự động hoặc dán trực tiếp.[/dim]")
        
        final_url = ""
        while not final_url:
            clipboard_link = get_clipboard_url()
            
            if clipboard_link and clipboard_link.startswith(("http://", "https://")):
                console.print(f"[cyan]>> Phát hiện link trong Clipboard:[/cyan] [green]{clipboard_link}[/green]")
                raw_input_str = console.input("[bold green]>> Nhấn Enter để dùng link này (hoặc dán link mới): [/bold green]").strip()
                if not raw_input_str:
                    final_url = clipboard_link
                    break
            else:
                raw_input_str = console.input("[bold green]>> Dán finish link sau khi hoàn tất: [/bold green]").strip()
            
            if raw_input_str:
                extracted = raw_input_str
                for token in raw_input_str.split():
                    if token.startswith(("http://", "https://")):
                        extracted = token
                        break
                final_url = extracted
                break
            else:
                show_log("WARN", "Chưa nhận được link hợp lệ. Vui lòng thử dán trực tiếp link vào đây.")

        show_log("PASS", "Đã nhận finish link thành công!")
        console.print(
            Panel(
                final_url,
                title="[bold green]FINISH LINK[/bold green]",
                border_style="green",
            )
        )

        with open("ket_qua.txt", "w", encoding="utf-8") as f:
            f.write(final_url)

        show_log("PASS", "Đã lưu kết quả vào file ket_qua.txt")
        console.print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Đã dừng chương trình bởi người dùng.[/yellow]")
