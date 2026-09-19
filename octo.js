const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

(async () => {
    // Lấy thông tin từ GitHub Secrets đã thiết lập
    const proxyServer = process.env.PROXY_SERVER; 
    const proxyUser = process.env.PROXY_USER;
    const proxyPass = process.env.PROXY_PASS;
    const targetUrl = process.env.OCTO_URL;

    console.log("🚀 Đang khởi động trình duyệt ẩn danh...");
    
    const browser = await puppeteer.launch({
        headless: "new",
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            `--proxy-server=${proxyServer}`
        ]
    });

    const page = await browser.newPage();

    // Xác thực Proxy dân cư nếu có
    if (proxyUser && proxyPass) {
        await page.authenticate({ username: proxyUser, password: proxyPass });
    }

    // Giả lập giao diện Windows Desktop (Tránh DEVICE_MISMATCH)
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36");
    await page.setViewport({ width: 1366, height: 768 });

    console.log(`🌐 Đang mở link: ${targetUrl}`);
    await page.goto(targetUrl, { waitUntil: 'networkidle2', timeout: 60000 });

    // --- VIẾT LOGIC VƯỢT LINK 4 BƯỚC Ở ĐÂY ---
    console.log("⏳ Đang xử lý các bước đếm ngược...");
    // Ví dụ chờ element hoặc click nút tiếp tục...

    await browser.close();
    console.log("✅ Hoàn tất tiến trình!");
})();
