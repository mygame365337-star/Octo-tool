# -*- coding: utf-8 -*-
import os
import time
from curl_cffi import requests
from playwright.sync_api import sync_playwright

def main():
    # 1. Lấy URL do Termux gửi sang thông qua biến môi trường OCTO_URL
    target_url = os.environ.get("OCTO_URL", "").strip()
    
    if not target_url:
        print("[!] Lỗi: Không tìm thấy link yêu cầu từ biến OCTO_URL.")
        with open("ket_qua.txt", "w", encoding="utf-8") as f:
            f.write("ERROR: Missing target URL")
        return

    print(f"[*] Bắt đầu xử lý link: {target_url}")
    
    finish_link = ""

    # 2. Tiến hành tự động hóa bằng Playwright (Chạy ẩn danh trên Cloud)
    try:
        with sync_playwright() as p:
            # Khởi động trình duyệt Chromium ẩn danh
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            print("[*] Đang truy cập trang đích...")
            page.goto(target_url, timeout=60000)
            
            # Chờ đợi quá trình vượt link hoặc redirect hoàn tất (tùy thuộc vào logic trang web)
            print("[*] Đang chờ hệ thống xử lý qua lớp bảo mật...")
            time.sleep(10) # Thời gian chờ load script trang đích
            
            # Lấy URL hiện tại sau khi đã vượt qua các bước chuyển hướng (Redirect / Finish link)
            current_url = page.url
            print(f"[*] URL hiện tại: {current_url}")
            
            # Nếu trang web có hiển thị finish link ở một thẻ nào đó, bạn có thể trích xuất ở đây.
            # Hoặc mặc định lấy URL hiện tại khi đã redirect đến trang kết quả:
            finish_link = current_url
            
            browser.close()
    except Exception as e:
        print(f"[-] Lỗi khi dùng Playwright: {e}")
        # Fallback thử dùng curl_cffi nếu playwright gặp sự cố
        try:
            print("[*] Thử nghiệm kết nối bằng curl_cffi...")
            session = requests.Session(impersonate="chrome120")
            res = session.get(target_url, timeout=30, allow_redirects=True)
            finish_link = res.url
        except Exception as ex:
            print(f"[-] Fallback thất bại: {ex}")
            finish_link = target_url # Trả về link gốc nếu lỗi hoàn toàn

    # 3. Ghi kết quả finish link vào file ket_qua.txt để GitHub Actions đóng gói gửi về Termux
    if not finish_link:
        finish_link = target_url

    with open("ket_qua.txt", "w", encoding="utf-8") as f:
        f.write(finish_link)
    
    print(f"[+] Đã ghi thành công Finish Link vào ket_qua.txt: {finish_link}")

if __name__ == "__main__":
    main()
