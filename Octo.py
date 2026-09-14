# -*- coding: utf-8 -*-

import os
import sys
import time
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


OUTPUT_FILE = "ket_qua.txt"

CLICK_SELECTORS = [
    "a.btn-success",
    "#getlink",
    ".get-link",
    "a.get-link",
    "button#btn",
    "a.btn-primary",
    "#continuation",
    ".landing-btn",
    "input[type='submit']",

    "a:has-text('Get Link')",
    "button:has-text('Get Link')",
    "a:has-text('Continue')",
    "button:has-text('Continue')",
    "a:has-text('Click Here')",
    "button:has-text('Click Here')",
    "a:has-text('Tải xuống')",
    "button:has-text('Tải xuống')",
]


def write_result(value):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write(str(value))


def get_input_url():
    url = os.environ.get("OCTO_URL", "").strip()
    if not url and len(sys.argv) > 1:
        url = sys.argv[1].strip()
    return url


def is_http_url(url):
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def get_proxy_config():
    """
    Hỗ trợ đọc đồng bộ từ GitHub Actions (PROXY_SERVER, PROXY_USER, PROXY_PASS)
    """
    proxy_url = os.environ.get("PROXY_URL", "").strip()
    if proxy_url:
        return {"server": proxy_url}

    proxy_server = os.environ.get("PROXY_SERVER", "").strip()
    proxy_user = os.environ.get("PROXY_USER", "").strip()
    proxy_pass = os.environ.get("PROXY_PASS", "").strip()

    if not proxy_server:
        return None

    if proxy_server.startswith(("http://", "https://", "socks")):
        return {"server": proxy_server}
    
    if proxy_user and proxy_pass:
        return {"server": f"http://{proxy_user}:{proxy_pass}@{proxy_server}"}
    
    return {"server": f"http://{proxy_server}"}


def load_ignored_domains():
    ignored = set()
    if os.path.exists("domains.txt"):
        try:
            with open("domains.txt", "r", encoding="utf-8") as f:
                for line in f:
                    domain = line.strip().lower()
                    if domain:
                        ignored.add(domain)
        except Exception:
            pass
    return ignored


def click_next_button(page):
    for selector in CLICK_SELECTORS:
        try:
            element = page.locator(selector).first
            if element.count() == 0 or not element.is_visible():
                continue
            element.scroll_into_view_if_needed(timeout=3000)
            element.click(timeout=5000)
            print(f"[+] Đã click phần tử: {selector}")
            return True
        except Exception as error:
            print(f"[-] Không click được {selector}: {error}")
    return False


def get_visible_links(page):
    try:
        links = page.eval_on_selector_all(
            "a[href]",
            """
            elements => elements
                .map(element => element.href)
                .filter(href => href)
            """,
        )
    except Exception:
        return []
    return [link for link in links if is_http_url(link)]


def run(target_url):
    final_url = target_url
    popup_urls = []
    proxy = get_proxy_config()
    ignored_domains = load_ignored_domains()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context = browser.new_context(
            locale="vi-VN",
            timezone_id="Asia/Ho_Chi_Minh",
            viewport={"width": 1365, "height": 768},
            proxy=proxy,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        page = context.new_page()

        def handle_popup(popup):
            try:
                popup.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                pass
            popup_url = popup.url
            if is_http_url(popup_url) and popup_url != target_url:
                popup_urls.append(popup_url)
                print(f"[*] Phát hiện popup: {popup_url}")

        context.on("page", handle_popup)

        try:
            print(f"[*] Đang mở: {target_url}")
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

            for step in range(20):
                time.sleep(3)
                current_url = page.url
                print(f"[*] Bước {step + 1}: {current_url}")

                if current_url and current_url != target_url and is_http_url(current_url):
                    parsed_netloc = urlparse(current_url).netloc.lower()
                    is_ignored = any(d in parsed_netloc for d in ignored_domains)

                    if not is_ignored:
                        final_url = current_url
                        try:
                            page.wait_for_load_state("domcontentloaded", timeout=10000)
                        except PlaywrightTimeoutError:
                            pass
                        if page.url != target_url:
                            final_url = page.url

                click_next_button(page)
                time.sleep(2)

                if page.url != target_url:
                    final_url = page.url

                if popup_urls:
                    popup_target = popup_urls[-1]
                    parsed_popup = urlparse(popup_target).netloc.lower()
                    if not any(d in parsed_popup for d in ignored_domains):
                        final_url = popup_target
                        print(f"[+] URL popup: {final_url}")
                        break

                current_netloc = urlparse(page.url).netloc.lower()
                target_netloc = urlparse(target_url).netloc.lower()
                if current_netloc != target_netloc and not any(d in current_netloc for d in ignored_domains):
                    final_url = page.url
                    time.sleep(3)
                    final_url = page.url
                    break

        except PlaywrightTimeoutError:
            print("[-] Hết thời gian chờ khi tải trang.")
            page.screenshot(path="timeout_error.png")
        except Exception as error:
            print(f"[-] Lỗi trình duyệt: {error}")
            page.screenshot(path="browser_error.png")
        finally:
            context.close()
            browser.close()

    return final_url


def main():
    target_url = get_input_url()

    if not target_url:
        message = "ERROR: Missing OCTO_URL"
        print(f"[-] {message}")
        write_result(message)
        return 1

    if target_url.lower() == "exit":
        print("[*] Đã thoát.")
        write_result("EXIT")
        return 0

    if not is_http_url(target_url):
        message = "ERROR: Invalid URL"
        print(f"[-] {message}: {target_url}")
        write_result(message)
        return 1

    print(f"[*] Bắt đầu xử lý: {target_url}")

    try:
        finish_link = run(target_url)
    except Exception as error:
        finish_link = f"ERROR: {error}"

    write_result(finish_link)
    print(f"[+] Finish link: {finish_link}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
