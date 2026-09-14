# -*- coding: utf-8 -*-
import os
import time
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

def main():
    target_url = os.environ.get("OCTO_URL", "").strip()
    
    if not target_url:
        print("[!] Không tìm thấy URL mục tiêu.")
        with open("ket_qua.txt", "w", encoding="utf-8") as f:
            f.write("ERROR: Missing URL")
        return

    print(f"[*] Đang xử lý vượt link cho: {target_url}")
    finish_link = target_url
    captured_urls = []

    # Danh sách User-Agent thực tế mới nhất để xoay vòng tránh bị bắt bài
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ]
    chosen_ua = random.choice(user_agents)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--no-first-run",
                    "--no-zygote",
                    "--disable-gpu",
                    "--window-size=1920,1080"
                ]
            )
            
            proxy_url = os.environ.get("PROXY_URL", "").strip()
            proxy_config = {"server": proxy_url} if proxy_url else None

            context = browser.new_context(
                user_agent=chosen_ua,
                viewport={"width": 1920, "height": 1080},
                locale="vi-VN",
                timezone_id="Asia/Ho_Chi_Minh",
                proxy=proxy_config,
                extra_http_headers={
                    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"Windows"'
                }
            )
            
            page = context.new_page()
            stealth_sync(page)
            
            # Tự động đóng các hộp thoại cảnh báo JavaScript (alert/confirm) nếu có
            page.on("dialog", lambda dialog: dialog.dismiss())
            
            # Lắng nghe tab mới
            def handle_new_page(new_page):
                try:
                    new_page.wait_for_load_state(timeout=5000)
                    tab_url = new_page.url
                    print(f"[*] Phát hiện tab/popup mới mở ra: {tab_url}")
                    if "octolink." not in tab_url and "linksv." not in tab_url and "google" not in tab_url and tab_url != target_url:
                        nonlocal finish_link
                        finish_link = tab_url
                except Exception:
                    pass

            context.on("page", handle_new_page)
            page.on("framenavigated", lambda frame: captured_urls.append(frame.url) if frame == page.main_frame else None)
            
            # Cơ chế Retry (Thử lại tối đa 2 lần nếu gặp lỗi kết nối hoặc Cloudflare chặn ngay từ đầu)
            max_retries = 2
            success_loaded = False
            
            for attempt in range(max_retries):
                try:
                    print(f"[*] Đang truy cập trang đích (Lần thử {attempt+1})...")
                    page.goto(target_url, timeout=60000, wait_domcontentloaded=True)
                    
                    # Kiểm tra xem có dính trang lỗi ngay lúc vừa vào không
                    current_url = page.url
                    if "5xx-error-landing" in current_url or "cloudflare.com" in current_url:
                        print(f"[-] Bị Cloudflare chặn ở lần thử {attempt+1}, đang làm mới lại...")
                        time.sleep(5)
                        continue
                    
                    success_loaded = True
                    break
                except Exception as e:
                    print(f"[-] Lỗi tải trang lần {attempt+1}: {e}")
                    time.sleep(3)

            if not success_loaded:
                print("[-] Không thể vượt qua cổng bảo vệ sau các lần thử.")

            # Vòng lặp tương tác chính
            for step in range(12):
                time.sleep(random.uniform(3.5, 5.0)) # Độ trễ ngẫu nhiên giống con người
                current_url = page.url
                print(f"[*] Bước {step+1} - URL hiện tại: {current_url}")
                
                if "5xx-error-landing" in current_url or "cloudflare.com" in current_url:
                    print("[-] Đang kẹt ở trang chặn Cloudflare, thử tải lại trang...")
                    try:
                        page.reload(timeout=30000)
                    except Exception:
                        pass
                    continue

                if "octolink." not in current_url and "linksv." not in current_url and "google" not in current_url and current_url != target_url:
                    if "ads" not in current_url and "verify" not in current_url and "checkpoint" not in current_url:
                        finish_link = current_url
                        break

                try:
                    js_redirect = page.evaluate("window.location.href")
                    if js_redirect and "octolink." not in js_redirect and "linksv." not in js_redirect and js_redirect != target_url:
                        if "ads" not in js_redirect and "verify" not in js_redirect and "cloudflare" not in js_redirect:
                            print(f"[*] Phát hiện JavaScript Redirect ẩn: {js_redirect}")
                            finish_link = js_redirect
                            break
                except Exception:
                    pass

                try:
                    selectors = [
                        "a.btn-success", "#getlink", ".get-link", "a.get-link",
                        "button#btn", "a:has-text('Get Link')", "button:has-text('Get Link')",
                        "a:has-text('Tải xuống')", "a:has-text('Click Here')", "a.btn-primary",
                        "a:has-text('Continue')", "input[type='submit']", "#continuation", ".landing-btn"
                    ]
                    
                    for sel in selectors:
                        element = page.locator(sel).first
                        if element.count() > 0 and element.is_visible():
                            print(f"[*] Đang mô phỏng di chuyển chuột và click vào phần tử: {sel}")
                            box = element.bounding_box()
                            if box:
                                page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2, steps=5)
                                time.sleep(random.uniform(0.8, 1.5))
                            element.click(force=True, timeout=3000)
                            time.sleep(3)
                            break
                except Exception as click_err:
                    print(f"[-] Bỏ qua lỗi click nhỏ: {click_err}")

                try:
                    all_links = page.evaluate("Array.from(document.querySelectorAll('a')).map(a => a.href)")
                    for l in all_links:
                        if l and l.startswith("http") and "octolink." not in l and "linksv." not in l and "google" not in l and "facebook" not in l and "cloudflare" not in l and l != target_url:
                            print(f"[*] Quét được link đích trong trang: {l}")
                            finish_link = l
                            break
                except Exception:
                    pass

                if finish_link != target_url:
                    break

            if finish_link == target_url and len(context.pages) > 1:
                for p_tab in context.pages:
                    tab_url = p_tab.url
                    if "octolink." not in tab_url and "linksv." not in tab_url and "cloudflare" not in tab_url and tab_url != target_url:
                        finish_link = tab_url
                        break

            browser.close()
    except Exception as e:
        print(f"[-] Lỗi hệ thống automation: {e}")

    if not finish_link or "octolink." in finish_link or "linksv." in finish_link or "cloudflare" in finish_link:
        finish_link = target_url

    with open("ket_qua.txt", "w", encoding="utf-8") as f:
        f.write(finish_link)
    
    print(f"[+] Hoàn tất bóc tách! Finish link chính xác: {finish_link}")

if __name__ == "__main__":
    main()
