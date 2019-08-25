import scrapy
import os

outfile = "output/yelp-output.json"
find = "Bartending+Services"
# New%20York%2C%20NY
# Washington%2C%20DC
# Raleigh%2C%20NC
location = "New%20York%2C%20NY"


class YelpScraper(scrapy.Spider):

    name = 'bartendingspider'

    def __init__(self):
        super()

        if (os.path.exists(outfile)):

            os.remove(outfile)

    # Bartending services search in DC
    start_urls = [
        f"""https://www.yelp.com/search?find_desc={find}&find_loc={location}"""]

    def parse(self, response):
        for list_item in response.css('li.lemon--li__373c0__1r9wz'):

            title = list_item.css(
                'a.link-color--blue-dark__373c0__1mhJo::text').get()
            category = list_item.css(
                'a.link-color--inherit__373c0__15ymx::text').get()

            if (title and category):

                # goto detail page
                detail_page = list_item.css(
                    'a.link-color--blue-dark__373c0__1mhJo::attr(href)').get()

                if detail_page is not None:

                    detail_page = response.urljoin(detail_page)
                    yield scrapy.Request(detail_page, callback=self.parse_detail)

        # next page
        next_page = None
        for link in response.css("div[aria-label='Pagination navigation'] a"):
            if link.css("span::text").re_first(r'Next') is not None:
                next_page = link.attrib['href']
                break

        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parse_detail(self, response):

        title = response.css(
            'h1.biz-page-title::text').get()
        rating = response.css(
            'div.i-stars::attr(title)').get()

        categories = response.css(
            'div.biz-main-info span.category-str-list a::text').getall()

        mapbox = response.css('div.mapbox-text')

        website = mapbox.css('span.biz-website a::text').get()
        phone = mapbox.css('span.biz-phone::text').get()

        yield {'website': website,
               'phone': phone,
               'title': title,
               'rating': rating,
               'categories': categories, }