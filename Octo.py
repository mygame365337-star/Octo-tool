import asyncio
import os
from invisible_playwright import InvisiblePlaywright

OCTO_URL = os.environ.get("OCTO_URL", "")
PROXY_SERVER = os.environ.get("PROXY_SERVER", "")
PROXY_USER = os.environ.get("PROXY_USER", "")
PROXY_PASS = os.environ.get("PROXY_PASS", "")

async def main():
    if not OCTO_URL:
        with open("ket_qua.txt", "w") as f:
            f.write("LỖI: Chưa có OCTO_URL")
        return

    # Cấu hình proxy
    proxy_config = None
    if PROXY_SERVER:
        proxy_config = {
            "server": PROXY_SERVER,
            "username": PROXY_USER,
            "password": PROXY_PASS
        }
        print(f"Dùng proxy: {PROXY_SERVER}")

    # Khởi tạo invisible_playwright
    with InvisiblePlaywright(seed=42, headless=True, proxy=proxy_config) as browser:
        page = browser.new_page()
        
        # Chặn tài nguyên nặng để tiết kiệm data
        await page.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
            else route.continue_())

        final_url = "Không lấy được URL"

        try:
            print("Mở link Octolink...")
            await page.goto(OCTO_URL, timeout=60000)
            await page.wait_for_timeout(5000)

            print("Chờ 50s...")
            await page.wait_for_timeout(50000)

            allowed = ['sg77', 'neca', 'muts', 'vkventure', 'ok365', 'fun88', 'ttbuy', 'pamanslot', 'slot121', 'skeef']
            
            for attempt in range(5):
                print(f"Lần thử {attempt + 1}/5")
                links = await page.locator('a').all()
                found = False
                
                for link in links:
                    try:
                        href = await link.get_attribute('href')
                        if href and any(d in href.lower() for d in allowed):
                            print(f"Tìm thấy: {href[:70]}")
                            await page.goto(href, timeout=60000)
                            await page.wait_for_timeout(20000)
                            
                            try:
                                el = page.locator('div[class*="captcha"], canvas, div[class*="circle"]').first
                                if await el.count() > 0:
                                    box = await el.bounding_box()
                                    if box:
                                        x = box['x'] + box['width']/2
                                        y = box['y'] + box['height']/2
                                        await page.mouse.move(x, y)
                                        await page.mouse.down()
                                        await page.wait_for_timeout(1500)
                                        await page.mouse.up()
                                        print("Đã giải captcha!")
                            except:
                                pass
                            
                            await page.wait_for_timeout(5000)
                            final_url = page.url
                            found = True
                            break
                    except:
                        continue
                
                if found:
                    break
                
                print("Thử lại...")
                await page.reload()
                await page.wait_for_timeout(2000)

        except Exception as e:
            final_url = f"LỖI: {str(e)[:80]}"
        finally:
            await browser.close()

        print(f"URL cuối: {final_url}")
        with open("ket_qua.txt", "w", encoding="utf-8") as f:
            f.write(final_url)

asyncio.run(main())
