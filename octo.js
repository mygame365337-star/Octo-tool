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

    console.log("🚀 Đang khởi động trình duyệt với Proxy trực tiếp...");
    
    const browser = await puppeteer.launch({
        headless: "new",
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--proxy-server=http://p1.bytesflows.com:8001'
        ]
    });

    const page = await browser.newPage();

    // Xác thực tài khoản Proxy trực tiếp tại đây để tránh lỗi biến môi trường
    await page.authenticate({ 
        username: 'u-GrAj9sAQ', 
        password: 'bv04TdCA' 
    });

    // Chặn tài nguyên nặng để tiết kiệm băng thông proxy tối đa
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

    page.on('response', async (response) => {
        const url = response.url();
        if (response.status() === 200 && (url.includes('destination') || url.includes('target') || url.includes('get-link'))) {
            try {
                const data = await response.json();
                if (data && data.url) {
                    finalDestinationUrl = data.url;
                }
            } catch (e) {}
        }
    });

    try {
        console.log(`🌐 Đang mở link: ${targetUrl}`);
        await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 50000 });

        console.log("⏳ Đang xử lý các bước chuyển hướng...");
        for (let stage = 1; stage <= 3; stage++) {
            console.log(`🔄 Chặng ${stage}/3...`);
            await new Promise(resolve => setTimeout(resolve, 6000));
        }

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
        console.log("🔒 Đã đóng trình duyệt.");
    }
})();
