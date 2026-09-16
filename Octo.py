import os
import re
import sys
import time
from curl_cffi import requests

def bypass_octolink_sequential(target_url):
    print(f"[1/5] Khởi tạo session từ gate: {target_url}")
    session = requests.Session(impersonate="chrome124")
    
    response = session.get(target_url)
    if response.status_code != 200:
        print(f"[!] Lỗi kết nối ban đầu: {response.status_code}")
        return None

    base_domain = target_url.split('/')[2]
    
    print("[2/5] Vượt chốt kiểm tra thiết bị DeviceShield (/check/device)...")
    device_res = session.get(f"https://{base_domain}/check/device")
    if device_res.status_code == 200:
        print("[v] Vượt qua chốt kiểm tra thiết bị thành công!")

    print("[3/5] Tải và giải mã cấu hình để lấy Token...")
    match = re.search(r"([a-fA-F0-9]{32,})", response.text)
    if not match:
        print("[!] Không tìm thấy Token!")
        return None
    
    token = match.group(1)
    print(f"[v] Trích xuất thành công Token: {token}")

    print("\n[4/5] Thực hiện tuần tự lần lượt các bước (Step 1 ➔ 2 ➔ 3 ➔ 4)...")
    
    steps = [
        (1, 3), # Step 1
        (2, 3), # Step 2
        (3, 3), # Step 3
        (4, 3)  # Step 4
    ]

    final_url = None

    for step_num, delay in steps:
        print(f"-> Đang xử lý Step {step_num}/4 (Đợi mô phỏng đếm ngược {delay}s)...")
        time.sleep(delay)
        
        job_url = f"https://{base_domain}/check/job?step={step_num}&token={token}"
        job_res = session.get(job_url)
        
        if job_res.status_code == 200:
            print(f"    [v] Hoàn thành Step {step_num} thành công!")
            
            # Ở Step cuối cùng (Step 4), server trả về JSON chứa link đích
            if step_num == 4:
                try:
                    data = job_res.json()
                    if "url" in data:
                        final_url = data["url"]
                except Exception:
                    pass
        else:
            print(f"    [!] Lỗi ở Step {step_num}, mã phản hồi: {job_res.status_code}")

    if not final_url:
        final_url = f"https://{base_domain}/finish/{token}"

    print("\n[5/5] Hoàn tất toàn bộ các bước! Đã trích xuất xong link đích.")
    return final_url

if __name__ == "__main__":
    url = os.getenv("OCTO_URL")
    
    if url:
        result = bypass_octolink_sequential(url)
        if result:
            with open("ket_qua.txt", "w", encoding="utf-8") as f:
                f.write(result + "\n")
            print(f"\n[*] Link đích thực sự: {result}")
            print("[*] Đã lưu thành công vào file ket_qua.txt")
    else:
        print("[!] Không tìm thấy biến môi trường OCTO_URL!")
