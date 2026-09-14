# -*- coding: utf-8 -*-

import os
import sys
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

OUTPUT_FILE = "ket_qua.txt"

# Mở rộng toàn diện các selector thường dùng cho các trang rút gọn
CLICK_SELECTORS = [
    "a.btn-success", "a.btn-primary", "a.get-link", "button#btn",
    "#getlink", "#continuation", ".landing-btn", "input[type='submit']",
    "a:has-text('Get Link')", "button:has-text('Get Link')",
    "a:has-text('Continue')", "button:has-text('Continue')",
    "a:has-text('Click Here')", "button:has-text('Click Here')",
    "a:has-text('Tải xuống')", "button:has-text('Tải xuống')",
    "a:has-text('Verify')", "button:has-text('Verify')",
    "a:has-text('Next')", "button:has-text('Next')",
    "button", ".btn", "a.btn"
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
    """Thực hiện cuộn trang và tìm click các nút chuyển tiếp một cách linh hoạt hơn"""
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    except:
        pass

    for selector in CLICK_SELECTORS:
        try:
            elements = page.locator(selector)
            count = elements.count()
            for i in range(count):
                element = elements.nth(i)
                if element.is_visible():
                    element.scroll_into_view_if_needed(timeout=2000)
                    element.click(timeout=3000)
                    print(f"[+] Đã click thành công vào: {selector}")
                    return True
        except Exception:
            continue
    return False

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
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
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

            # Tăng vòng lặp lên 30 bước để đủ thời gian cho các trang đếm ngược lâu (15-30 giây)
            for step in range(30):
                time.sleep(2)
                current_url = page.url
                print(f"[*] Bước {step + 1}: {current_url}")

                if current_url and current_url != target_url and is_http_url(current_url):
                    parsed_netloc = urlparse(current_url).netloc.lower()
                    if not any(d in parsed_netloc for d in ignored_domains):
                        final_url = current_url

                click_next_button(page)
                time.sleep(3)

                if page.url != target_url:
                    final_url = page.url

                if popup_urls:
                    popup_target = popup_urls[-1]
                    parsed_popup = urlparse(popup_target).netloc.lower()
                    if not any(d in parsed_popup for d in ignored_domains):
                        final_url = popup_target
                        print(f"[+] Lấy được URL từ popup: {final_url}")
                        break

                # Kiểm tra nếu trang đã chuyển hướng hẳn khỏi domain ban đầu
                current_netloc = urlparse(page.url).netloc.lower()
                target_netloc = urlparse(target_url).netloc.lower()
                if current_netloc != target_netloc and not any(d in current_netloc for d in ignored_domains):
                    final_url = page.url
                    break

        except PlaywrightTimeoutError:
            print("[-] Hết thời gian chờ tải trang.")
            try:
                page.screenshot(path="timeout_error.png")
            except:
                pass
        except Exception as error:
            print(f"[-] Lỗi trình duyệt: {error}")
            try:
                page.screenshot(path="browser_error.png")
            except:
                pass
        finally:
            context.close()
            browser.close()

    return final_url

def main():
    target_url = get_input_url()
    if not target_url:
        write_result("ERROR: Missing OCTO_URL")
        return 1
    if not is_http_url(target_url):
        write_result("ERROR: Invalid URL")
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
