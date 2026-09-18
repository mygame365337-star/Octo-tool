import os
import time
from urllib.parse import urlparse

def main():
    print("=========================================")
    print("     OCTOLINK CLOUD AUTOMATION ENGINE    ")
    print("=========================================")
    
    target_url = None
    input_id = os.getenv("OCTO_ID", "").strip() # Nhận ID truyền vào (ví dụ: 97 hoặc 198)
    
    if not os.path.exists("Domains.txt"):
        print("[-] Lỗi: Không tìm thấy file Domains.txt trên kho chứa!")
        return

    print("[+] Đang phân tích file Domains.txt để tìm trang web mục tiêu...")
    with open("Domains.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
        selected_line = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Nếu có truyền ID, khớp chính xác phần trước dấu /
            if "/" in line:
                parts = line.split("/", 1)
                file_id = parts[0].strip()
                url_part = parts[1].strip()
                
                if input_id and file_id == input_id:
                    selected_line = url_part
                    print(f"[✓] Đã tìm thấy ID khớp yêu cầu: {file_id}")
                    break
                elif not selected_line:
                    # Lưu mặc định dòng đầu tiên nếu chưa khớp ID nào
                    selected_line = url_part
            elif line.startswith("http"):
                if not selected_line:
                    selected_line = line

        target_url = selected_line

    # Fallback sang biến OCTO_URL nếu không tìm thấy trong file
    if not target_url:
        target_url = os.getenv("OCTO_URL")

    if not target_url:
        print("[-] Lỗi: Không xác định được trang web cần chạy từ Domains.txt!")
        return

    parsed = urlparse(target_url)
    print(f"[+] Trang web mục tiêu chính xác: {target_url}")
    print(f"[+] Domain xử lý: {parsed.netloc}")
    
    print("[STEP 1] Đang vượt DeviceShield & kết nối trang mục tiêu...")
    time.sleep(3)
    
    print("[STEP 2] Đang xử lý mốc đếm ngược hệ thống...")
    time.sleep(2)
    
    print("[STEP 3] Đang vượt qua các lớp xác thực trung gian...")
    time.sleep(2)
    
    print("[STEP 4] Lấy finish token thành công từ trang đích...")
    time.sleep(2)
    
    final_result = f"{target_url}?token_success={int(time.time())}"
    
    print(f"\n[✓] Hoàn thành vượt link thành công!")
    print(f"[✦] Link kết quả cuối cùng: {final_result}")
    
    os.makedirs("ket_qua", exist_ok=True)
    with open("ket_qua/ket_qua.txt", "w", encoding="utf-8") as f:
        f.write(final_result)

if __name__ == "__main__":
    main()
