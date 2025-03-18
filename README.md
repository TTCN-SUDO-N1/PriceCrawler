# PriceCrawler

## Cài đặt

Để cài đặt Python và Scrapy, hãy làm theo các bước sau:

### Cài đặt Python

1. Tải phiên bản Python mới nhất từ [trang web chính thức](https://www.python.org/downloads/).
2. Làm theo hướng dẫn cài đặt cho hệ điều hành của bạn.

### Cài đặt Scrapy

Sau khi cài đặt Python, bạn có thể cài đặt Scrapy bằng pip(Windows):

```bash
pip install scrapy
```

Xác minh cài đặt bằng cách chạy:

```bash
scrapy version
```

Lệnh này sẽ hiển thị phiên bản Scrapy đã cài đặt.

Cài đặt cho Ubuntu(linux):

```bash
sudo apt install python3-scrapy
```

### Tạo dự án 

1.  Sau khi cài đặt scrapy thì ta chạy lệnh này trên Terminal,Command Prompt hoặc Powershell

```bash
scrapy startproject <tên project>
cd <tên project>
```
2.  Tạo file trong folder spider
```bash
cd spiders
touch <ten file>,py
```

3.  Thêm code vào file
Ví dụ:
```python
import scrapy

class QuotesSpider(scrapy.Spider):
    name = "quotes"
    start_urls = [
        'http://quotes.toscrape.com/page/1/',
    ]

    def parse(self, response):
        # Extract quote data using CSS selectors
        for quote in response.css('div.quote'):
            yield {
                'text': quote.css('span.text::text').get(),
                'author': quote.css('span small::text').get(),
                'tags': quote.css('div.tags a.tag::text').getall(),
            }

        # Follow pagination link to the next page
        next_page = response.css('li.next a::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)
```
4.  Thoát khỏi folder spider và chạy lệnh
```bash
scrapy crawl <tên spider> -o output.json
```
Tên spider trong phần name của file .py mà ta tạo
```python
class QuotesSpider(scrapy.Spider):
    name = "quotes"
    start_urls = [
        'http://quotes.toscrape.com/page/1/',
    ]
```

Ví dụ:
```bash
cd ..
scrapy crawl quotes -o quotes.json
```
5.  Kiểm tra file json vừa tạo 
