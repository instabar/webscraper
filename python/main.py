import scrapy

class BlogSpider(scrapy.Spider):
    name = 'bartendingspider'
    start_urls = ['https://www.yelp.com/search?find_desc=Bartending+Services&find_loc=Washington%2C+DC']

    def parse(self, response):
        for title in response.css('.post-header>h2'):
            yield {'title': title.css('a ::text').get()}

        for next_page in response.css('a.next-posts-link'):
            yield response.follow(next_page, self.parse)
