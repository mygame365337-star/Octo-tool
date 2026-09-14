# -*- coding: utf-8 -*-
import os
import sys
import time
from urllib.parse import urlparse, quote_plus
from playwright.sync_api import sync_playwright

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
            return target_url.replace(parsed.netloc, d)
            
    return target_url

def run_automation():
    target_url = get_input_url()
    # Mặc định ban đầu nếu lỗi sẽ giữ link cũ, nhưng ta sẽ ưu tiên lấy link trạm trung gian captcha
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
            print(f"[*] Mở trang: {target_url}")
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)

            # Vượt qua 3 bước đầu để tiến tới bước giải captcha / step cuối
            for step in range(1, 4):
                print(f"[*] --- Đang vượt qua bước {step} ---")
                
                search_keyword = ""
                try:
                    kw_elem = page.locator("div.search-keyword, span.keyword, .text-danger, b, code").first
                    if kw_elem.is_visible():
                        search_keyword = kw_elem.inner_text().strip()
                except:
                    pass

                if not search_keyword or len(search_keyword) > 25:
                    path_parts = urlparse(target_url).path.strip("/").split("/")
                    search_keyword = path_parts[-1] if path_parts else "c168"

                # Tìm kiếm qua DuckDuckGo HTML
                search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_keyword)}"
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)

                domains_list = load_domains_from_file()
                clicked_target = False

                for elem in page.locator("a.result__url, .result__body a").all():
                    try:
                        href = elem.get_attribute("href") or elem.inner_text()
                        if href:
                            if not href.startswith("http"):
                                href = "https://" + href.strip()
                            parsed_href = urlparse(href)
                            href_netloc = parsed_href.netloc.lower()
                            
                            for d in domains_list:
                                if d.split('.')[0] in href_netloc:
                                    page.goto(href, wait_until="domcontentloaded", timeout=30000)
                                    clicked_target = True
                                    break
                            if clicked_target:
                                break
                    except:
                        continue

                # Cuộn trang ở trang đích
                for _ in range(2):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)

                # Quay lại trang Octolink để chuyển bước tiếp theo
                page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                # Bấm nút chuyển bước
                page.evaluate("""() => {
                    const selectors = ['a.btn-success', 'button#btn', '#getlink', 'button', 'a.btn'];
                    for (let sel of selectors) {
                        let el = document.querySelector(sel);
                        if (el) { el.click(); break; }
                    }
                }""")
                time.sleep(4)

            # ĐẾN BƯỚC CUỐI (STEP 4 / CAPTCHA): Dừng lại, bắt lấy URL hiện tại của trang đang yêu cầu giải captcha và xuất ra file
            print("[*] Đã đến bước giải Captcha / Xác thực cuối cùng. Đang lấy đường dẫn trang...")
            time.sleep(3)
            
            current_page_url = page.url
            if current_page_url:
                final_url = current_page_url
            else:
                final_url = target_url

            final_url = correct_domain_tld(final_url)

        except Exception as e:
            print(f"[-] Lỗi: {e}")
            final_url = target_url
        finally:
            browser.close()

    return final_url

def main():
    target_url = get_input_url()
    if not target_url:
        write_result("ERROR: Missing OCTO_URL")
        return 1

    print(f"[*] Bắt đầu tiến trình...")
    result_link = run_automation()
    write_result(result_link)
    print(f"[+] Kết quả cuối được ghi vào file: {result_link}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
