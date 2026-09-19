const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');

puppeteer.use(StealthPlugin());

(async () => {
    // Sử dụng trực tiếp thông tin proxy tối ưu cho tiết kiệm băng thông
    const proxyServer = "p1.bytesflows.com:8001";
    const proxyUser = "u-GrAj9sAQ";
    const proxyPass = "bv04TdCA";
    const targetUrl = process.env.OCTO_URL;

    if (!targetUrl) {
        console.error("❌ Lỗi: Chưa có URL mục tiêu!");
        process.exit(1);
    }

    console.log("🚀 Đang khởi động trình duyệt tối ưu tiết kiệm Proxy...");
    
    const browser = await puppeteer.launch({
        headless: "new",
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            `--proxy-server=http://${proxyServer}`
        ]
    });

    const page = await browser.newPage();

    // Xác thực Proxy dân cư
    await page.authenticate({ username: proxyUser, password: proxyPass });

    // --- TIẾT KIỆM PROXY: CHẶN TÀI NẢY NẶNG (ẢNH, CSS, FONT) ---
    await page.setRequestInterception(true);
    page.on('request', (request) => {
        const resourceType = request.resourceType();
        // Chỉ cho phép tải tài liệu HTML, Script (JS) và XHR/Fetch để trang web hoạt động
        if (['image', 'stylesheet', 'font', 'media'].includes(resourceType)) {
            request.abort(); // Chặn lại để không tốn data proxy
        } else {
            request.continue();
        }
    });

    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36");
    await page.setViewport({ width: 1366, height: 768 });

    let finalDestinationUrl = null;

    // Bắt link đích qua luồng phản hồi mạng
    page.on('response', async (response) => {
        const url = response.url();
        if (response.status() === 200 && (url.includes('destination') || url.includes('target') || url.includes('out') || url.includes('get-link'))) {
            try {
                const data = await response.json();
                if (data && data.url) {
                    finalDestinationUrl = data.url;
                }
            } catch (e) {}
        }
    });

    try {
        console.log(`🌐 Đang mở link mục tiêu (chế độ siêu tiết kiệm data): ${targetUrl}`);
        await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });

        console.log("⏳ Đang tiến hành xử lý các chặng chờ...");

        // Vòng lặp chờ rút gọn thời gian nhờ đã chặn bớt tài nguyên nặng
        for (let stage = 1; stage <= 4; stage++) {
            console.log(`🔄 [Chặng ${stage}/4] Đang xử lý...`);
            await new Promise(resolve => setTimeout(resolve, 8000)); // Rút ngắn thời gian chờ mỗi chặng
        }

        // Bóc tách link cuối từ DOM nếu chưa bắt được qua mạng
        if (!finalDestinationUrl) {
            finalDestinationUrl = await page.evaluate(() => {
                const linkElement = document.querySelector('#get-link') || 
                                    document.querySelector('.destination-link') || 
                                    document.querySelector('a.btn-success') ||
                                    document.querySelector('a.get-link');
                return linkElement ? linkElement.href : window.location.href;
            });
        }

        console.log(`🎯 Thành công! Link đích: ${finalDestinationUrl}`);
        fs.writeFileSync('result.txt', finalDestinationUrl || "Không tìm thấy link đích");

    } catch (error) {
        console.error("❌ Lỗi thực thi:", error);
        fs.writeFileSync('result.txt', `Lỗi: ${error.message}`);
    } finally {
        await browser.close();
        console.log("🔒 Đã đóng trình duyệt an toàn.");
    }
})();
