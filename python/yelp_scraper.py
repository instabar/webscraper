import scrapy

class YelpScraper(scrapy.Spider):
    name = 'bartendingspider'

    # Bartending services search in DC
    start_urls = ['https://www.yelp.com/search?find_desc=Bartending+Services&find_loc=Washington%2C+DC']

    def parse(self, response):
        for list_item in response.css('li.lemon--li__373c0__1r9wz'):
            yield {'title': list_item.css('a::text').getall()}

        for next_page in response.css('a.next-posts-link'):
            yield response.follow(next_page, self.parse)
