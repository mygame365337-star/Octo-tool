import os
import sys
import time
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich import box

console = Console()


NASA_LOGO = r"""
███╗   ██╗ █████╗ ███████╗ █████╗
████╗  ██║██╔══██╗██╔════╝██╔══██╗
██╔██╗ ██║███████║███████╗███████║
██║╚██╗██║██╔══██║╚════██║██╔══██║
██║ ╚████║██║  ██║███████║██║  ██║
╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
"""


def clear_screen():
    os.system("clear")


def gradient_logo():
    colors = [
        "bold red",
        "bold orange1",
        "bold yellow",
        "bold green",
        "bold cyan",
        "bold blue",
        "bold magenta",
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
        "STEP": "magenta",
    }

    color = level_colors.get(level, "white")

    return Text.assemble(
        (f"{now} ", "dim"),
        ("[SYS] ", "bright_blue"),
        (f"{level:<4} ", color),
        (message, "white"),
    )


def make_header():
    return Panel(
        gradient_logo(),
        border_style="bright_white",
        padding=(0, 2),
        title="[bold cyan]OCTO LINK ENGINE[/bold cyan]",
        subtitle="[dim]Termux Edition[/dim]",
    )


def show_startup():
    clear_screen()
    console.print(make_header())

    table = Table(
        title="ENGINE STATUS",
        box=box.SIMPLE_HEAVY,
        border_style="green",
        show_header=False,
    )

    table.add_row("Host", "[green]Termux / Android[/green]")
    table.add_row("Browser", "[yellow]Manual browser session[/yellow]")
    table.add_row("Captcha", "[yellow]User confirmation required[/yellow]")
    table.add_row("Mode", "[cyan]Final URL monitor[/cyan]")
    table.add_row(
        "Started",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    console.print(table)
    console.print()


def show_log(level, message):
    console.print(log_line(level, message))


def main():
    show_startup()

    show_log("PASS", "Giao diện NASA đã khởi động")
    show_log("INFO", "Termux đang chờ link Octo...")
    show_log("WARN", "Captcha nếu xuất hiện phải hoàn tất thủ công")

    console.print()
    url = console.input("[bold cyan]>> Dán link Octo: [/bold cyan]").strip()

    if not url.startswith(("http://", "https://")):
        show_log("FAIL", "URL không hợp lệ")
        sys.exit(1)

    show_log("PASS", f"Đã nhận URL: {url}")
    show_log("INFO", "Mở trình duyệt để bạn hoàn tất các bước xác minh")
    show_log("INFO", "Sau khi xong, quay lại nhập link cuối cùng")

    console.print()
    final_url = console.input(
        "[bold green]>> Dán finish link sau khi hoàn tất: [/bold green]"
    ).strip()

    if final_url.startswith(("http://", "https://")):
        show_log("PASS", "Đã nhận finish link")
        console.print(
            Panel(
                final_url,
                title="[bold green]FINISH LINK[/bold green]",
                border_style="green",
            )
        )

        with open("ket_qua.txt", "w", encoding="utf-8") as f:
            f.write(final_url)

        show_log("PASS", "Đã lưu vào ket_qua.txt")
    else:
        show_log("FAIL", "Finish link không hợp lệ")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Đã dừng chương trình.[/yellow]")
