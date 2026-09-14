# -*- coding: utf-8 -*-
import os
import time
from playwright.sync_api import sync_playwright

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

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-size=1920,1080"
                ]
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            
            page = context.new_page()
            
            # Lắng nghe sự kiện mở popup hoặc tab mới tự động
            def handle_new_page(new_page):
                new_page.wait_for_load_state()
                tab_url = new_page.url
                print(f"[*] Phát hiện tab/popup mới mở ra: {tab_url}")
                if "octolink." not in tab_url and "linksv." not in tab_url and "google" not in tab_url and tab_url != target_url:
                    nonlocal finish_link
                    finish_link = tab_url

            context.on("page", handle_new_page)
            page.on("framenavigated", lambda frame: captured_urls.append(frame.url) if frame == page.main_frame else None)
            
            print("[*] Đang truy cập trang đích...")
            page.goto(target_url, timeout=60000)
            
            try:
                page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass

            # Vòng lặp tương tác chính để vượt qua các bước chờ
            for step in range(10):
                time.sleep(4)
                current_url = page.url
                print(f"[*] Bước {step+1} - URL hiện tại: {current_url}")
                
                # Nếu trang chính đã tự chuyển hướng đến link đích
                if "octolink." not in current_url and "linksv." not in current_url and "google" not in current_url and current_url != target_url:
                    if "ads" not in current_url and "verify" not in current_url and "checkpoint" not in current_url:
                        finish_link = current_url
                        break

                # Bổ sung lớp quét sâu JavaScript location ẩn (bắt redirect ngầm)
                try:
                    js_redirect = page.evaluate("window.location.href")
                    if js_redirect and "octolink." not in js_redirect and "linksv." not in js_redirect and js_redirect != target_url:
                        if "ads" not in js_redirect and "verify" not in js_redirect:
                            print(f"[*] Phát hiện JavaScript Redirect ẩn: {js_redirect}")
                            finish_link = js_redirect
                            break
                except Exception:
                    pass

                # Thử quét và click các nút Get Link / Continue với chế độ ép buộc (force=True)
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
                            print(f"[*] Đang click bằng lực (force) vào phần tử: {sel}")
                            element.click(force=True, timeout=3000)
                            time.sleep(3)
                            break
                except Exception as click_err:
                    print(f"[-] Bỏ qua lỗi click nhỏ: {click_err}")

                # Quét tất cả các thẻ a trên trang xem có link nào đổi hướng ra ngoài chưa
                try:
                    all_links = page.evaluate("Array.from(document.querySelectorAll('a')).map(a => a.href)")
                    for l in all_links:
                        if l and l.startswith("http") and "octolink." not in l and "linksv." not in l and "google" not in l and "facebook" not in l and l != target_url:
                            print(f"[*] Quét được link đích trong trang: {l}")
                            finish_link = l
                            break
                except Exception:
                    pass

                if finish_link != target_url:
                    break

            # Kiểm tra lại danh sách các tab đang mở
            if finish_link == target_url and len(context.pages) > 1:
                for p_tab in context.pages:
                    tab_url = p_tab.url
                    if "octolink." not in tab_url and "linksv." not in tab_url and tab_url != target_url:
                        finish_link = tab_url
                        break

            browser.close()
    except Exception as e:
        print(f"[-] Lỗi hệ thống automation: {e}")

    # Xử lý fallback cuối cùng nếu vẫn giữ nguyên link cũ
    if not finish_link or "octolink." in finish_link or "linksv." in finish_link:
        finish_link = target_url

    # Ghi kết quả vào file để Termux nhận về
    with open("ket_qua.txt", "w", encoding="utf-8") as f:
        f.write(finish_link)
    
    print(f"[+] Hoàn tất bóc tách! Finish link chính xác: {finish_link}")

if __name__ == "__main__":
    main()
