# -*- coding: utf-8 -*-
import os
import sys
import time
from urllib.parse import urlparse
from curl_cffi import requests

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

def correct_domain_tld(target_domain):
    """Rà soát và sửa lỗi TLD bị che (ví dụ cố tình đổi .cm thành .cn hoặc ngược lại)"""
    known_domains = load_domains_from_file()
    clean_domain = target_domain.lower()
    
    # Nếu domain trong danh sách chuẩn khớp với các ký tự đầu nhưng khác phần đuôi (.cn / .cm)
    for d in known_domains:
        base_name = d.rsplit('.', 1)[0]
        if clean_domain.startswith(base_name):
            return d  # Trả về domain chuẩn đã được fix đuôi từ file
            
    # Xử lý thay thế thông minh .cn -> .cm nếu trang cố tình che giấu
    if clean_domain.endswith(".cn"):
        alternative = clean_domain[:-3] + ".cm"
        for d in known_domains:
            if d == alternative:
                return alternative
        return alternative
        
    return clean_domain

def run_octolink_task(target_url):
    parsed = urlparse(target_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    path_parts = parsed.path.strip("/").split("/")
    code = path_parts[-1] if path_parts else ""

    session = requests.Session(impersonate="chrome120")
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": target_url,
        "X-Requested-With": "XMLHttpRequest"
    })

    session.get(target_url)

    final_url = target_url
    step = 1
    max_steps = 5

    while step <= max_steps:
        print(f"[*] --- Đang xử lý STEP {step} ---")
        
        job_url = f"{domain}/check/job"
        try:
            res = session.post(job_url, data={"code": code, "step": step}, timeout=15)
            data = res.json()
            print(f"[*] Phản hồi Job Step {step}: {data}")
            
            if data.get("status") != "success":
                break
                
            # Lấy thời gian chờ thực tế từ server trả về (không cố định 50s)
            wait_time = int(data.get("wait", 15))
        except Exception as e:
            print(f"[-] Lỗi kết nối job step {step}: {e}")
            wait_time = 15

        print(f"[*] Chờ đếm ngược theo đúng thời gian server yêu cầu: {wait_time} giây...")
        for remaining in range(wait_time, 0, -1):
            if remaining % 5 == 0 or remaining <= 5:
                print(f"[*] Thời gian còn lại: {remaining}s")
            time.sleep(1)

        try:
            session.post(f"{domain}/check/countdown", data={"code": code, "step": step}, timeout=15)
        except:
            pass

        continue_url = f"{domain}/check/continue"
        try:
            res = session.post(continue_url, data={"code": code, "step": step}, timeout=15)
            data = res.json()
            print(f"[*] Phản hồi Continue: {data}")
            
            if data.get("status") == "finish":
                raw_finish = data.get("url", target_url)
                # Kiểm tra và chuẩn hóa domain đích (fix lỗi che đuôi .cn/.cm)
                parsed_finish = urlparse(raw_finish)
                fixed_netloc = correct_domain_tld(parsed_finish.netloc)
                final_url = raw_finish.replace(parsed_finish.netloc, fixed_netloc)
                
                print(f"[+] Hoàn thành! Link đích chuẩn: {final_url}")
                break
            elif data.get("status") == "success":
                step = int(data.get("step", step + 1))
            else:
                step += 1
        except Exception as e:
            print(f"[-] Lỗi ở bước tiếp theo: {e}")
            step += 1

        time.sleep(2)

    return final_url

def main():
    target_url = get_input_url()
    if not target_url:
        write_result("ERROR: Missing OCTO_URL")
        return 1

    print(f"[*] Bắt đầu tiến trình tự động cho: {target_url}")
    try:
        finish_link = run_octolink_task(target_url)
    except Exception as error:
        finish_link = f"ERROR: {error}"

    write_result(finish_link)
    print(f"[+] Kết quả cuối cùng: {finish_link}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
