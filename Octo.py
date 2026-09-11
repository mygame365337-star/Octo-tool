import asyncio
import os
from playwright.async_api import async_playwright

R = "\033[0m"; B = "\033[1m"; RED = "\033[91m"; GRN = "\033[92m"
YEL = "\033[93m"; BLU = "\033[94m"; MAG = "\033[95m"; CYN = "\033[96m"; WHT = "\033[97m"

OCTO_URL = os.environ.get("OCTO_URL", "")

def extract_domain(line):
    if "|" in line:
        parts = line.split("|", 1)
        domain = parts[1].strip() if len(parts) >= 2 else line.strip()
    else:
        domain = line.strip()
    domain = domain.replace("https://", "").replace("http://", "").replace("www.", "")
    domain = domain.split("/")[0]
    return domain.lower().strip()

def load_domains():
    domains = []
    try:
        with open("domains.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                domain = extract_domain(line)
                if domain:
                    domains.append(domain)
    except FileNotFoundError:
        domains = ["sg77.my", "neca.tv", "mutsillustrations.nl", "vkventure.co.in"]
    return domains

def load_blacklist():
    items = []
    try:
        with open("blacklist.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                for token in line.replace(",", " ").split():
                    token = token.strip()
                    if token:
                        items.append(token.lower())
    except FileNotFoundError:
        pass
    return items

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
        with open("ket_qua.txt", "w") as f:
            f.write("LỖI: Chưa có OCTO_URL")
        return

    ALLOWED = load_domains()
    BLACKLIST = load_blacklist()
    
    log("INFO", f"Link: {OCTO_URL}")
    log("INFO", f"Domain được phép: {len(ALLOWED)}")
    log("INFO", f"Mã camp bị chặn: {len(BLACKLIST)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        max_attempts = 10
        task_found = False

        for attempt in range(max_attempts):
            log("INFO", f"--- Lần thử {attempt + 1}/{max_attempts} ---")
            
            try:
                await page.goto(OCTO_URL, timeout=60000)
                await page.wait_for_timeout(5000)

                log("WAIT", "Chờ 50 giây...")
                for i in range(50, 0, -1):
                    print(f"\r  {YEL}[{i}s]{R} Đang chờ...", end="", flush=True)
                    await page.wait_for_timeout(1000)
                print()

                links = await page.locator('a').all()
                
                for link in links:
                    try:
                        href = await link.get_attribute('href')
                        if not href:
                            continue
                        
                        if is_blacklisted(href, BLACKLIST):
                            log("WARN", f"Bỏ qua (blacklist): {href[:70]}")
                            continue
                        
                        if is_allowed(href, ALLOWED):
                            log("PASS", f"TÌM THẤY: {href}")
                            await page.goto(href, timeout=60000)
                            await page.wait_for_timeout(5000)
                            task_found = True
                            break
                        else:
                            log("WARN", f"Bỏ qua (không trong list): {href[:70]}")
                    except:
                        continue
                
                if task_found:
                    break
                
                log("WARN", "Thử lại...")
                await page.reload()
                await page.wait_for_timeout(3000)
            except Exception as e:
                log("ERR", f"Lỗi: {e}")
                continue

        if task_found:
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

        # Luôn lấy URL cuối và in ra
        try:
            final_url = page.url
        except:
            final_url = "Không lấy được URL"
        
        print("")
        print("=" * 60)
        print("KẾT QUẢ:")
        print(final_url)
        print("=" * 60)
        print("")
        
        with open("ket_qua.txt", "w", encoding="utf-8") as f:
            f.write(final_url)

        await browser.close()

asyncio.run(main())
