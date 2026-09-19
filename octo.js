const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');

// Kích hoạt tính năng ẩn danh né anti-bot
puppeteer.use(StealthPlugin());

(async () => {
    // 1. Lấy thông tin cấu hình từ GitHub Secrets và biến môi trường
    const proxyServer = process.env.PROXY_SERVER; 
    const proxyUser = process.env.PROXY_USER;
    const proxyPass = process.env.PROXY_PASS;
    const targetUrl = process.env.OCTO_URL;

    if (!targetUrl) {
        console.error("❌ Lỗi: Chưa có URL mục tiêu (OCTO_URL trống)!");
        process.exit(1);
    }

    console.log("🚀 Đang khởi động trình duyệt ẩn danh trên mây...");
    
    // 2. Khởi chạy trình duyệt với các thông số bắt buộc cho môi trường Linux/GitHub Actions
    const browser = await puppeteer.launch({
        headless: "new",
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            `--proxy-server=${proxyServer}`
        ]
    });

    const page = await browser.newPage();

    // 3. Xác thực Proxy dân cư (Sticky Session)
    if (proxyUser && proxyPass) {
        await page.authenticate({ username: proxyUser, password: proxyPass });
        console.log("🔒 Đã xác thực Proxy dân cư thành công.");
    }

    // 4. Giả lập thông số thiết bị Windows Desktop tránh lỗi DEVICE_MISMATCH
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36");
    await page.setViewport({ width: 1366, height: 768 });

    // Biến lưu trữ link đích cuối cùng khi bắt được từ luồng mạng
    let finalDestinationUrl = null;

    // Lắng nghe các gói tin phản hồi mạng để "chộp" lấy link đích một cách chính xác nhất
    page.on('response', async (response) => {
        const url = response.url();
        // Bạn có thể tinh chỉnh điều kiện lọc domain đích ở đây nếu cần
        if (response.status() === 200 && (url.includes('destination') || url.includes('target') || url.includes('out'))) {
            try {
                const data = await response.json();
                if (data && data.url) {
                    finalDestinationUrl = data.url;
                }
            } catch (e) {
                // Bỏ qua nếu không phải định dạng JSON
            }
        }
    });

    try {
        console.log(`🌐 Đang mở link mục tiêu: ${targetUrl}`);
        await page.goto(targetUrl, { waitUntil: 'networkidle2', timeout: 60000 });

        console.log("⏳ Bắt đầu tiến trình vượt qua các chặng bảo vệ...");

        // Vòng lặp mô phỏng chờ đợi qua 4 chặng (có thể điều chỉnh thời gian chờ cho phù hợp)
        for (let stage = 1; stage <= 4; stage++) {
            console.log(`🔄 [Chặng ${stage}/4] Đang xử lý và chờ đếm ngược...`);
            
            // Chờ một khoảng thời gian mô phỏng mỗi chặng (ví dụ 12-15 giây)
            await new Promise(resolve => setTimeout(resolve, 15000));

            // Thử tìm và click vào các nút tiếp tục (nếu có trên giao diện trang)
            try {
                await page.evaluate(() => {
                    const buttons = Array.from(querySelectorAll('a, button'));
                    const nextBtn = buttons.find(el => el.innerText.toLowerCase().includes('tiếp tục') || el.innerText.toLowerCase().includes('get link') || el.innerText.toLowerCase().includes('chờ'));
                    if (nextBtn) nextBtn.click();
                });
            } catch (err) {
                // Bỏ qua nếu không tìm thấy nút bấm thủ công và dựa vào thời gian/chuyển hướng tự động
            }
        }

        // Kiểm tra lại nếu chưa bắt được qua mạng thì bóc tách trực tiếp từ DOM của trang
        if (!finalDestinationUrl) {
            finalDestinationUrl = await page.evaluate(() => {
                // Quét các selector phổ biến chứa link kết quả cuối cùng
                const linkElement = document.querySelector('#get-link') || 
                                    document.querySelector('.destination-link') || 
                                    document.querySelector('a.btn-success');
                return linkElement ? linkElement.href : window.location.href;
            });
        }

        console.log(`🎯 Link đích thành công: ${finalDestinationUrl}`);

        // Ghi kết quả vào file result.txt để GitHub Actions đẩy artifact về
        fs.writeFileSync('result.txt', finalDestinationUrl || "Không tìm thấy link đích");

    } catch (error) {
        console.error("❌ Xảy ra lỗi trong quá trình thực thi Puppeteer:", error);
        fs.writeFileSync('result.txt', `Lỗi: ${error.message}`);
    } finally {
        await browser.close();
        console.log("🔒 Đã đóng trình duyệt an toàn.");
    }
})();
