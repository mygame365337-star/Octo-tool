# -*- coding: utf-8 -*-
import os
import sys
import time
from urllib.parse import urlparse, quote_plus
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
            print(f"[*] Mở trang nhiệm vụ: {target_url}")
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)

            for step in range(1, 6):
                print(f"[*] --- ĐANG XỬ LÝ STEP {step} ---")
                
                # Trích xuất từ khóa nhiệm vụ trên trang
                search_keyword = ""
                try:
                    keyword_element = page.locator("div.search-keyword, span.keyword, .text-danger, b").first
                    if keyword_element.is_visible():
                        search_keyword = keyword_element.inner_text().strip()
                except:
                    pass

                if not search_keyword or len(search_keyword) > 25:
                    path_parts = urlparse(target_url).path.strip("/").split("/")
                    search_keyword = path_parts[-1] if path_parts else "c168"

                print(f"[*] Từ khóa tìm kiếm: {search_keyword}")

                # Sử dụng DuckDuckGo HTML để tìm kiếm (không bị dính Captcha như Google)
                search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_keyword)}"
                print(f"[*] Truy vấn qua DuckDuckGo: {search_url}")
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                domains_list = load_domains_from_file()
                clicked_target = False

                # Quét kết quả trả về từ DuckDuckGo
                results = page.locator("a.result__url").all()
                if not results:
                    results = page.locator("a.result__snippet, .result__body a").all()

                for elem in results:
                    try:
                        href = elem.get_attribute("href") or elem.inner_text()
                        if href:
                            if not href.startswith("http"):
                                href = "https://" + href.strip()
                                
                            parsed_href = urlparse(href)
                            href_netloc = parsed_href.netloc.lower()
                            
                            matched = False
                            for d in domains_list:
                                d_prefix = d.split('.')[0]
                                if d_prefix in href_netloc:
                                    matched = True
                                    break
                            
                            if matched:
                                print(f"[+] Tìm thấy website mục tiêu: {href}")
                                page.goto(href, wait_until="domcontentloaded", timeout=30000)
                                clicked_target = True
                                break
                    except:
                        continue

                if not clicked_target:
                    print("[-] Không tìm thấy domain khớp trực tiếp, thử mở link kết quả đầu tiên...")
                    try:
                        first_res = page.locator("a.result__url").first
                        if first_res.is_visible():
                            first_res.click()
                    except:
                        pass

                # Cuộn xuống đáy trang để hoàn thành yêu cầu thời gian/mã
                print("[*] Đang cuộn trang lấy dữ liệu...")
                for _ in range(4):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)

                # Quay lại trang Octolink chính để qua bước tiếp theo
                print(f"[*] Quay lại trang Octolink...")
                page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                # Bấm nút Continue / Get Link
                for selector in ["a.btn-success", "button#btn", "#getlink", "button:has-text('Continue')", "button:has-text('Get Link')", "a:has-text('Continue')"]:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible():
                            btn.click(timeout=3000)
                            break
                    except:
                        continue
                
                time.sleep(5)

                current_url = page.url
                if "finish" in current_url or (current_url != target_url and "http" in current_url):
                    final_url = current_url
                    if "finish" in current_url:
                        break

            final_url = correct_domain_tld(final_url)

        except PlaywrightTimeoutError:
            print("[-] Hết thời gian chờ.")
        except Exception as e:
            print(f"[-] Lỗi: {e}")
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
    print(f"[+] Kết quả cuối: {result_link}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
