# -*- coding: utf-8 -*-
import os
import sys
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

OUTPUT_FILE = "ket_qua.txt"

def write_result(value):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write(str(value))

def get_input_url():
    url = os.environ.get("OCTO_URL", "").strip()
    if not url and len(sys.argv) > 1:
        url = sys.argv[1].strip()
    return url

def load_domains_from_file():
    domains = []
    if os.path.exists("domains.txt"):
        try:
            with open("domains.txt", "r", encoding="utf-8") as f:
                for line in f:
                    d = line.strip().lower()
                    if d:
                        domains.append(d)
        except:
            pass
    return domains

def correct_domain_tld(target_url):
    """Đối chiếu phần tên chính (trước dấu chấm) với domains.txt và chuẩn hóa lại đuôi TLD"""
    known_domains = load_domains_from_file()
    parsed = urlparse(target_url)
    clean_netloc = parsed.netloc.lower()
    
    parts = clean_netloc.split('.')
    if not parts:
        return target_url
        
    prefix = parts[0]
    for d in known_domains:
        d_prefix = d.split('.')[0]
        if prefix == d_prefix:
            # Thay thế domain cũ bằng domain chuẩn đúng đuôi trong file domains.txt
            return target_url.replace(parsed.netloc, d)
            
    return target_url

def run_automation():
    target_url = get_input_url()
    final_url = target_url
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = browser.new_context(
            locale="vi-VN",
            timezone_id="Asia/Ho_Chi_Minh",
            viewport={"width": 1365, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print(f"[*] Mở trang nhiệm vụ chính: {target_url}")
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)

            # Vòng lặp qua các bước (Step 1 đến Step 4/5)
            for step in range(1, 6):
                print(f"[*] --- BẮT ĐẦU XỬ LÝ STEP {step} ---")
                
                # 1. Quét từ khóa nhiệm vụ hoặc ô tìm kiếm hiển thị trên trang octo
                search_keyword = ""
                try:
                    # Thử lấy text từ khung gợi ý tìm kiếm trên giao diện
                    keyword_element = page.locator("div.search-keyword, span.keyword, .text-danger, b").first
                    if keyword_element.is_visible():
                        search_keyword = keyword_element.inner_text().strip()
                except:
                    pass

                # Nếu không bắt được từ khóa cụ thể, trích xuất mã code từ URL để làm từ khóa tìm kiếm phòng hờ
                if not search_keyword or len(search_keyword) > 20:
                    path_parts = urlparse(target_url).path.strip("/").split("/")
                    search_keyword = path_parts[-1] if path_parts else "c168"

                print(f"[*] Từ khóa nhiệm vụ xác định: {search_keyword}")

                # 2. Mở Google để thực hiện tìm kiếm theo yêu cầu nhiệm vụ
                print(f"[*] Đang tiến hành tìm kiếm trên Google với từ khóa: {search_keyword}")
                page.goto(f"https://www.google.com/search?q={search_keyword}", wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                # 3. Rà soát kết quả tìm kiếm Google để tìm website khớp với domains.txt
                domains_list = load_domains_from_file()
                clicked_target = False

                for i in range(1, 3): # Quét trang 1 và trang 2 Google
                    print(f"[*] Đang quét kết quả tìm kiếm Google (Trang {i})...")
                    search_results = page.locator("a h3").all()
                    
                    for elem in search_results:
                        try:
                            parent_a = elem.locator("xpath=ancestor::a").first
                            href = parent_a.get_attribute("href")
                            if href and href.startswith("http"):
                                parsed_href = urlparse(href)
                                href_netloc = parsed_href.netloc.lower()
                                
                                # Kiểm tra xem domain trên Google có khớp với prefix trong domains.txt không
                                matched = False
                                for d in domains_list:
                                    d_prefix = d.split('.')[0]
                                    if d_prefix in href_netloc:
                                        matched = True
                                        break
                                
                                if matched:
                                    print(f"[+] Tìm thấy website mục tiêu trên Google: {href}")
                                    parent_a.click(timeout=5000)
                                    clicked_target = True
                                    break
                        except:
                            continue
                    
                    if clicked_target:
                        break
                    
                    # Nếu trang 1 không có, bấm nút chuyển sang trang 2 của Google
                    try:
                        next_btn = page.locator("#pnnext, a:has-text('Tiếp')").first
                        if next_btn.is_visible():
                            next_btn.click()
                            time.sleep(3)
                    except:
                        break

                if not clicked_target:
                    print("[-] Không tìm thấy website đích trên Google, quay lại trang chính thử lại...")
                
                # 4. Cuộn xuống đáy trang đích (theo yêu cầu nhiệm vụ lấy mã)
                print("[*] Đang cuộn xuống đáy trang để hoàn thành đếm ngược và lấy mã...")
                for _ in range(5):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)

                # 5. Quay lại trang octo chính để bấm nút Continue / Next sang Step tiếp theo
                print(f"[*] Quay lại trang Octolink để chuyển bước...")
                page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                # Click các nút tiếp tục/get link
                for selector in ["a.btn-success", "button#btn", "#getlink", "button:has-text('Continue')", "button:has-text('Get Link')", "a:has-text('Continue')"]:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible():
                            btn.click(timeout=3000)
                            print(f"[+] Đã bấm nút chuyển bước qua selector: {selector}")
                            break
                    except:
                        continue
                
                time.sleep(5)

                # Kiểm tra nếu trang đã trả về link finish
                current_url = page.url
                if "finish" in current_url or "http" in current_url and current_url != target_url:
                    final_url = current_url
                    if "finish" in current_url:
                        break

            # Chuẩn hóa lại domain lần cuối trước khi xuất kết quả
            final_url = correct_domain_tld(final_url)

        except PlaywrightTimeoutError:
            print("[-] Hết thời gian chờ trình duyệt xử lý.")
        except Exception as e:
            print(f"[-] Lỗi phát sinh trong quá trình chạy: {e}")
        finally:
            browser.close()

    return final_url

def main():
    target_url = get_input_url()
    if not target_url:
        write_result("ERROR: Missing OCTO_URL")
        return 1

    print(f"[*] Bắt đầu tiến trình tự động hóa toàn bộ nhiệm vụ...")
    result_link = run_automation()
    write_result(result_link)
    print(f"[+] Kết quả cuối cùng: {result_link}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
