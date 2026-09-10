import asyncio
import os
from playwright.async_api import async_playwright

R = "\033[0m"; B = "\033[1m"; RED = "\033[91m"; GRN = "\033[92m"
YEL = "\033[93m"; BLU = "\033[94m"; MAG = "\033[95m"; CYN = "\033[96m"; WHT = "\033[97m"

OCTO_URL = os.environ.get("OCTO_URL", "")

def load_file(filename, default=None):
    items = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    items.append(line.lower())
    except FileNotFoundError:
        if default is not None:
            items = default
    return items

def load_domains():
    return load_file("domains.txt", ["sg77.my", "neca.tv", "mutsillustrations.nl", "vkventure.co.in"])

def load_blacklist():
    return load_file("blacklist.txt", [])

def is_blacklisted(url, blacklist):
    url_lower = url.lower()
    for bad in blacklist:
        if bad in url_lower:
            return True
    return False

def is_allowed(url, allowed):
    url_lower = url.lower()
    for good in allowed:
        if good in url_lower:
            return True
    return False

def banner():
    print(CYN + B + """
  ██████╗  ██████╗████████╗ ██████╗ 
 ██╔═══██╗██╔════╝╚══██╔══╝██╔═══██╗
 ██║   ██║██║        ██║   ██║   ██║
 ██║   ██║██║        ██║   ██║   ██║
 ╚██████╔╝╚██████╗   ██║   ╚██████╔╝
  ╚═════╝  ╚═════╝   ╚═╝    ╚═════╝ 
    """ + R)
    print(YEL + "  Tool tự động OctoLink - GitHub Actions" + R)
    print(YEL + "  " + "="*50 + R)

def log(level, msg):
    color = {"INFO": CYN, "WAIT": YEL, "PASS": GRN, "WARN": MAG, "ERR": RED}.get(level, WHT)
    print(f"{color}  [{level}]{R} {msg}")

async def main():
    banner()
    if not OCTO_URL:
        log("ERR", "Chưa có OCTO_URL")
        return

    ALLOWED = load_domains()
    BLACKLIST = load_blacklist()
    
    log("INFO", f"Link: {OCTO_URL}")
    log("INFO", f"Được phép: {len(ALLOWED)} domain")
    log("INFO", f"Blacklist: {len(BLACKLIST)} domain")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        max_attempts = 10  # Thử tối đa 10 lần
        task_found = False

        for attempt in range(max_attempts):
            log("INFO", f"--- Lần thử {attempt + 1}/{max_attempts} ---")
            
            log("INFO", "Mở trang Octolink...")
            await page.goto(OCTO_URL, timeout=60000)
            await page.wait_for_timeout(5000)

            log("WAIT", "Chờ 50 giây...")
            for i in range(50, 0, -1):
                print(f"\r  {YEL}[{i}s]{R} Đang chờ...", end="", flush=True)
                await page.wait_for_timeout(1000)
            print()

            log("INFO", "Tìm link nhiệm vụ...")
            links = await page.locator('a').all()
            
            for link in links:
                try:
                    href = await link.get_attribute('href')
                    if not href:
                        continue
                    
                    # Bỏ qua nếu trong blacklist
                    if is_blacklisted(href, BLACKLIST):
                        log("WARN", f"Bỏ qua (blacklist): {href[:60]}...")
                        continue
                    
                    # Chỉ làm nếu trong domains.txt
                    if is_allowed(href, ALLOWED):
                        log("PASS", f"TÌM THẤY NHIỆM VỤ: {href}")
                        await page.goto(href, timeout=60000)
                        await page.wait_for_timeout(5000)
                        task_found = True
                        break
                    else:
                        log("WARN", f"Bỏ qua (không trong list): {href[:60]}...")
                except:
                    continue
            
            if task_found:
                break
            
            # Nếu không tìm thấy, reload trang
            log("WARN", "Không có nhiệm vụ phù hợp, thử lại...")
            await page.reload()
            await page.wait_for_timeout(3000)

        if not task_found:
            log("ERR", "Không tìm thấy nhiệm vụ phù hợp sau 10 lần thử")
            await browser.close()
            return

        log("WAIT", "Chờ 20 giây...")
        for i in range(20, 0, -1):
            print(f"\r  {YEL}[{i}s]{R} Đang chờ...", end="", flush=True)
            await page.wait_for_timeout(1000)
        print()

        log("INFO", "Tìm captcha...")
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
                    log("PASS", "Đã giải captcha!")
        except:
            pass

        await page.wait_for_timeout(5000)
        final_url = page.url
        log("PASS", f"URL cuối: {final_url}")

        with open("ket_qua.txt", "w", encoding="utf-8") as f:
            f.write(f"Link cuối: {final_url}\n")

        await browser.close()

asyncio.run(main())
