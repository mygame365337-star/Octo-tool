# -*- coding: utf-8 -*-
import os
import sys
import time
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

def run_api_bypass(target_url):
    session = requests.Session(impersonate="chrome120")
    print(f"[*] Đang xử lý qua API: {target_url}")
    
    # Tại đây thực hiện các bước gửi request API bóc tách token/link như logic trong hình ảnh của bạn
    # Ví dụ giả lập vòng lặp nhận diện JSON trả về từ endpoint của trang rút gọn:
    
    finish_url = target_url
    # Code gọi API tùy thuộc vào cấu trúc của trang (octolink, v.v.)
    
    return finish_url

def main():
    target_url = get_input_url()
    if not target_url:
        write_result("ERROR: Missing OCTO_URL")
        return 1

    try:
        finish_link = run_api_bypass(target_url)
    except Exception as error:
        finish_link = f"ERROR: {error}"

    write_result(finish_link)
    print(f"[+] Finish link: {finish_link}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
