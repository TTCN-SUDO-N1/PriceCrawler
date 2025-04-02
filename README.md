# PriceCrawler
## Mô tả

PriceCrawler là một ứng dụng Python được xây dựng để thu thập dữ liệu giá từ các trang web thương mại điện tử như Tiki, Shopee và Lazada. Ứng dụng này sử dụng thư viện selenium để tự động hóa việc duyệt web và thu thập tất cả thông tin của trang web rồi chuyển dữ liệu sang một LLM(Large Language Model) để phân tích và xử lý dữ liệu. Ứng dụng này có thể được sử dụng để thu thập dữ liệu giá cho các sản phẩm khác nhau và lưu trữ chúng vào một cơ sở dữ liệu hoặc tệp tin để phân tích sau này.

## Cài đặt
### Cài đặt môi trường

1. #### Cài đặt và kích hoạt môi trường ảo
- Chạy trong thư mục dự án của bạn
```bash
python3 -m venv Crawler
```
```bash
source Crawler/bin/activate
```
2. #### Cài đặt thư viện 
- Cài đặt các thư viện cần thiết bằng cách sử dụng pip:
```bash
pip3 install -r requirements.txt
```

### Cài đặt Driver cho Selenium

- Để sử dụng Selenium, bạn cần cài đặt trình điều khiển (driver) cho trình duyệt mà bạn muốn tự động hóa. Dưới đây là hướng dẫn cài đặt cho ChromeDriver và GeckoDriver (Firefox).

#### Cài đặt ChromeDriver
- Tải xuống ChromeDriver từ trang web chính thức: https://googlechromelabs.github.io/chrome-for-testing/
- Giải nén tệp tải xuống và di chuyển file `chromedriver` vào thư mục hiện tại của bạn

#### Cài đặt GeckoDriver(firefox)
- Tải xuống GekoDriver từ trang web chính thức: https://github.com/mozilla/geckodriver/releases
- Giải nén tệp tải xuống và di chuyển file `gekodriver` vào thư mục hiên tại của bạn
#### Thư mục hiện tại

```bash
PriceCrawler
├── clean.py
├── Crawler
├── `chromedriver/gekodriver` <-- File ở đây 
├── main.py
├── __pycache__
├── README.md
├── requirements.txt
└── web.py
```
## Cài đặt AI

### SOON™

## Sử dụng
### Chạy ứng dụng
- Chạy ứng dụng bằng cách sử dụng lệnh sau:
```bash
streamlit run web.py 
```
- Ứng dụng sẽ mở trong trình duyệt web của bạn và bạn có thể nhập URL của sản phẩm mà bạn muốn thu thập dữ liệu giá.
