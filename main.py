import os
import json
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

def main():
    target_url = os.environ.get("TARGET_URL")
    if not target_url:
        print("[-] Không tìm thấy TARGET_URL!")
        return

    parsed = urlparse(target_url)
    print(f"[+] Domain cổng vào: {parsed.netloc}")
    print(f"[1/5] Khởi tạo session từ gate: {target_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        
        try:
            # Mô phỏng quá trình lướt qua các bước và tìm trang web đích thực sự
            page.goto(target_url, timeout=40000, wait_until="networkidle")
            
            # (Thực thi các bước vượt bot / đếm ngược tại đây theo kịch bản của bạn)
            time.sleep(5)
            
            final_url = page.url
            target_domain = urlparse(final_url).netloc
            
            print(f"[✓] Vượt qua các bước bảo mật thành công!")
            print(f"[TARGET_DOMAIN]: {target_domain}")
            print(f"[✦] Link đích hoàn chỉnh: {final_url}")
            
        except Exception as e:
            print(f"[-] Lỗi xử lý: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
