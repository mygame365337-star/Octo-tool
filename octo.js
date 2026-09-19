const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');

puppeteer.use(StealthPlugin());

(async () => {
    const targetUrl = process.env.OCTO_URL;

    if (!targetUrl) {
        console.error("❌ Lỗi: Chưa có URL mục tiêu!");
        process.exit(1);
    }

    console.log(`[1/5] Khởi tạo session thông minh từ gate: ${targetUrl}`);

    const browser = await puppeteer.launch({
        headless: "new",
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--window-size=392,800'
        ]
    });

    const page = await browser.newPage();

    // Chặn tài nguyên nặng (ảnh, css, font, media) để tăng tốc độ tải API tối đa
    await page.setRequestInterception(true);
    page.on('request', (request) => {
        const resourceType = request.resourceType();
        if (['image', 'stylesheet', 'font', 'media'].includes(resourceType)) {
            request.abort();
        } else {
            request.continue();
        }
    });

    await page.setUserAgent("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36");
    await page.setViewport({ width: 392, height: 800, isMobile: true });

    let finalDestinationUrl = null;

    // 🧠 BỘ LẮNG NGHE API THÔNG MINH: Tự động bắt mọi JSON trả về chứa link đích hoặc token
    page.on('response', async (response) => {
        const url = response.url();
        try {
            const contentType = response.headers()['content-type'] || '';
            if (contentType.includes('application/json') || url.includes('finish') || url.includes('get-link') || url.includes('redirect')) {
                const data = await response.json();
                // Quét toàn bộ các trường JSON có khả năng chứa link kết quả
                const possibleUrl = data.url || data.link || data.destination || data.data?.url || data.data?.link;
                if (possibleUrl && typeof possibleUrl === 'string' && possibleUrl.startsWith('http')) {
                    finalDestinationUrl = possibleUrl;
                    console.log(`[🎯 API Intercepted] Đã bắt thành công link từ API server: ${finalDestinationUrl}`);
                }
            }
        } catch (e) {
            // Bỏ qua các response không phải JSON hoặc lỗi phân tích
        }
    });

    try {
        console.log("[2/5] Vượt chốt kiểm tra thiết bị & tải cấu hình bảo mật...");
        await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
        console.log("[✔] Khởi chạy thành công trang đích!");

        console.log("[3/5] Đang xử lý các lớp bảo mật JavaScript & Token...");
        await new Promise(resolve => setTimeout(resolve, 3000));

        console.log("[4/5] Tự động hóa các bước chuyển hướng và tương tác máy chủ...");

        // Vòng lặp thông minh: Kiểm tra và click tự động các nút "Tiếp tục", "Get Link", "Verify" nếu có
        for (let step = 1; step <= 4; step++) {
            if (finalDestinationUrl) break; // Nếu đã bắt được link từ API thì thoát vòng lặp sớm

            console.log(`-> Đang xử lý tiến trình bước [${step}/4]...`);
            
            // Tự động tìm và bấm vào các nút điều hướng trên trang nếu xuất hiện
            try {
                await page.evaluate(() => {
                    const buttons = Array.from(document.querySelectorAll('button, a, input[type="submit"]'));
                    const targetBtn = buttons.find(b => {
                        const text = b.innerText?.toLowerCase() || '';
                        return text.includes('tiếp tục') || text.includes('continue') || text.includes('get link') || text.includes('lấy mã') || text.includes('verify');
                    });
                    if (targetBtn) targetBtn.click();
                });
            } catch (err) {}

            await new Promise(resolve => setTimeout(resolve, 4000));
        }

        // Nếu API chưa tự bắt được, tiến hành quét DOM lần cuối để bóc tách link
        if (!finalDestinationUrl) {
            finalDestinationUrl = await page.evaluate(() => {
                const linkElement = document.querySelector('#get-link') || 
                                    document.querySelector('.destination-link') || 
                                    document.querySelector('a.btn-success') ||
                                    document.querySelector('a.get-link') ||
                                    document.querySelector('a[href^="http"]:not([href*="link999"])');
                return linkElement ? linkElement.href : window.location.href;
            });
        }

        console.log(`[*] Link đích hoàn thành: ${finalDestinationUrl}`);
        console.log("[5/5] Hoàn tất toàn bộ tiến trình! Đã sẵn sàng kết quả.");
        fs.writeFileSync('result.txt', finalDestinationUrl || "Không tìm thấy link đích");

    } catch (error) {
        console.error("❌ Lỗi thực thi:", error);
        fs.writeFileSync('result.txt', `Lỗi: ${error.message}`);
    } finally {
        await browser.close();
    }
})();
