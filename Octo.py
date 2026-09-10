import asyncio
import os
from playwright.async_api import async_playwright

R = "\033[0m"; B = "\033[1m"; RED = "\033[91m"; GRN = "\033[92m"
YEL = "\033[93m"; BLU = "\033[94m"; MAG = "\033[95m"; CYN = "\033[96m"; WHT = "\033[97m"

OCTO_URL = os.environ.get("OCTO_URL", "")

def load_domains():
    domains = []
    try:
        with open("domains.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    domains.append(line)
    except FileNotFoundError:
        domains = ["sg77.my", "neca.tv", "mutsillustrations.nl", "vkventure.co.in"]
    return domains

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

    ALLOWED_DOMAINS = load_domains()
    log("INFO", f"Link: {OCTO_URL}")
    log("INFO", f"Đã load {len(ALLOWED_DOMAINS)} domain từ domains.txt")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        log("INFO", "Mở trang Octolink...")
        await page.goto(OCTO_URL, timeout=60000)
        await page.wait_for_timeout(5000)
        log("INFO", f"URL hiện tại: {page.url}")

        log("WAIT", "Chờ 50 giây...")
        for i in range(50, 0, -1):
            print(f"\r  {YEL}[{i}s]{R} Đang chờ...", end="", flush=True)
            await page.wait_for_timeout(1000)
        print()

        log("INFO", "Tìm link nhiệm vụ...")
        links = await page.locator('a').all()
        task_url = None
        for link in links:
            try:
                href = await link.get_attribute('href')
                if href:
                    for d in ALLOWED_DOMAINS:
                        if d in href:
                            task_url = href
                            break
            except:
                continue
            if task_url:
                break

        if task_url:
            log("PASS", f"Tìm thấy: {task_url}")
            await page.goto(task_url, timeout=60000)
            await page.wait_for_timeout(5000)
        else:
            log("WARN", "Không tìm thấy link nhiệm vụ")

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
