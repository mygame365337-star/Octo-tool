import os
from proxy_relay import create_proxy
from invisible_playwright import InvisiblePlaywright

OCTO_URL = os.environ.get("OCTO_URL", "")
PROXY_SERVER = os.environ.get("PROXY_SERVER", "")
PROXY_USER = os.environ.get("PROXY_USER", "")
PROXY_PASS = os.environ.get("PROXY_PASS", "")

def main():
    if not OCTO_URL:
        with open("ket_qua.txt", "w") as f:
            f.write("LỖI: Chưa có OCTO_URL")
        return

    local_proxy = None
    if PROXY_SERVER and PROXY_USER and PROXY_PASS:
        upstream = PROXY_SERVER.replace("http://", f"http://{PROXY_USER}:{PROXY_PASS}@")
        print(f"Tạo relay cho: {PROXY_SERVER}")
        local_proxy = create_proxy(upstream, local_type="http")
        print(f"Relay: {local_proxy}")

    with InvisiblePlaywright(seed=42, headless=True) as browser:
        if local_proxy:
            page = browser.new_page(proxy={"server": local_proxy})
        else:
            page = browser.new_page()

        final_url = "Không lấy được URL"

        try:
            print("Mở link Octolink...")
            page.goto(OCTO_URL, timeout=60000)
            page.wait_for_timeout(5000)

            print("Chờ 50s...")
            page.wait_for_timeout(50000)

            allowed = ['sg77', 'neca', 'muts', 'vkventure', 'ok365', 'fun88', 'ttbuy', 'pamanslot', 'slot121', 'skeef']
            
            for attempt in range(5):
                print(f"Lần thử {attempt + 1}/5")
                links = page.locator('a').all()
                found = False
                
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        if href and any(d in href.lower() for d in allowed):
                            print(f"Tìm thấy: {href[:70]}")
                            page.goto(href, timeout=60000)
                            page.wait_for_timeout(20000)
                            
                            try:
                                el = page.locator('div[class*="captcha"], canvas, div[class*="circle"]').first
                                if el.count() > 0:
                                    box = el.bounding_box()
                                    if box:
                                        x = box['x'] + box['width']/2
                                        y = box['y'] + box['height']/2
                                        page.mouse.move(x, y)
                                        page.mouse.down()
                                        page.wait_for_timeout(1500)
                                        page.mouse.up()
                                        print("Đã giải captcha!")
                            except:
                                pass
                            
                            page.wait_for_timeout(5000)
                            final_url = page.url
                            found = True
                            break
                    except:
                        continue
                
                if found:
                    break
                
                print("Thử lại...")
                page.reload()
                page.wait_for_timeout(2000)

        except Exception as e:
            final_url = f"LỖI: {str(e)[:80]}"
        finally:
            browser.close()

        print(f"URL cuối: {final_url}")
        with open("ket_qua.txt", "w", encoding="utf-8") as f:
            f.write(final_url)

if __name__ == "__main__":
    main()
