import asyncio
import os
import re
import json
from invisible_playwright import InvisiblePlaywright

OCTO_URL = os.environ.get("OCTO_URL", "")

async def main():
    if not OCTO_URL:
        with open("ket_qua.txt", "w") as f:
            f.write("LỖI: Chưa có OCTO_URL")
        return

    with InvisiblePlaywright(seed=42, headless=True) as browser:
        page = browser.new_page()
        
        print("Mở link Octolink...")
        await page.goto(OCTO_URL, timeout=60000)
        await page.wait_for_timeout(5000)

        # ===== BƯỚC 1: VƯỢT DEVICESHIELD =====
        print("Vượt Deviceshield...")
        try:
            device_result = await page.evaluate("""
                async () => {
                    const r = await fetch('/check/device', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            device: 'mobile',
                            ua: navigator.userAgent
                        })
                    });
                    return await r.json();
                }
            """)
            print(f"Device check: {device_result}")
        except Exception as e:
            print(f"Lỗi device: {e}")

        # ===== BƯỚC 2: TẢI VÀ GIẢI MÃ JSCONF.JS =====
        print("Tải jsconf.js...")
        try:
            jsconf = await page.evaluate("""
                async () => {
                    const r = await fetch('/jsconf.js');
                    return await r.text();
                }
            """)
            
            # Tìm Finish Token trong jsconf
            token_match = re.search(r'finish["\']?\s*[:=]\s*["\']([a-f0-9]{32})', jsconf)
            if not token_match:
                token_match = re.search(r'([a-f0-9]{32})', jsconf)
            
            if token_match:
                finish_token = token_match.group(1)
                finish_url = f"https://octolink.vip/finish/{finish_token}"
                print(f"Finish Token: {finish_token}")
                print(f"Finish URL: {finish_url}")
            else:
                print("Không tìm thấy Finish Token")
                finish_url = None
        except Exception as e:
            print(f"Lỗi jsconf: {e}")
            finish_url = None

        # ===== BƯỚC 3: GỌI API 4 BƯỚC =====
        print("Gọi API 4 bước...")
        final_url = finish_url or "Không lấy được URL"
        
        try:
            for step in range(1, 5):
                print(f"--- Step {step}/4 ---")
                
                # Gọi /check/job
                job_result = await page.evaluate(f"""
                    async () => {{
                        const r = await fetch('/check/job', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{step: {step}}})
                        }});
                        return await r.json();
                    }}
                """)
                print(f"Job response: {job_result}")
                
                # Chờ theo wait time
                wait_time = job_result.get('wait', 10) if isinstance(job_result, dict) else 10
                print(f"Chờ {wait_time}s...")
                await page.wait_for_timeout(wait_time * 1000)
                
                # Gọi /check/continue
                continue_result = await page.evaluate(f"""
                    async () => {{
                        const r = await fetch('/check/continue', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{step: {step}}})
                        }});
                        return await r.json();
                    }}
                """)
                print(f"Continue response: {continue_result}")
                
                # Kiểm tra nếu có finish URL
                if isinstance(continue_result, dict):
                    if continue_result.get('status') == 'finish':
                        final_url = continue_result.get('url', final_url)
                        print(f"FINISH URL: {final_url}")
                        break
                
                await page.wait_for_timeout(2000)
        
        except Exception as e:
            print(f"Lỗi API: {e}")

        # ===== LƯU KẾT QUẢ =====
        print(f"URL cuối: {final_url}")
        with open("ket_qua.txt", "w", encoding="utf-8") as f:
            f.write(final_url)

asyncio.run(main())
