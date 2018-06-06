import scrapy
import dateparser

from scrapy.selector import Selector
from urllib.parse import urljoin
from ForumMessages.items import Message


class MessageSpider(scrapy.Spider):
    name = "messages"
    allowed_domains = ["forum.liga.net"]
    start_urls = [
            'http://forum.liga.net/Messages.asp?did=154101&page=1',
            'http://forum.liga.net/Messages.asp?did=111808&page=1'
        ]
    visited_urls=[]

    def parse(self, response):
        post_links = response.xpath('.//b/a/@href').extract()
        for post_link in post_links:
            if post_link.find("&page=") != -1:
                url = urljoin(response.url, post_link)
                yield response.follow(url, callback=self.parse_post)

    def parse_post(self, response):
        if response.url not in self.visited_urls:
            self.visited_urls.append(response.url)
            hxs = Selector(response)
            theme = hxs.xpath('.//h1/text()')[0].root
            messages = hxs.xpath('//tr[@class="bgfinlight" or @class="bgfindark"]')
            for message in messages:
                author = message.xpath('.//td/b[2]/a[1]/text()')
                if len(author):
                    author = message.xpath('.//td/b[2]/a[1]/text()').extract()[0]
                    text = message.xpath('.//div[@class="message"]/text()').extract()[0]
                    date = message.xpath('.//td/text()[1]').extract()[0]
                    date = date.replace("\n", "").replace("\t", "").replace("\r", "").replace("\xa0", " ")
                    date = date[:-2]
                    if len(text) and len(date):
                        item = Message()
                        item['theme'] = theme
                        item['author'] = author.replace("\n", "")
                        item['text'] = text.replace("\n", "")
                        item['date'] = dateparser.parse(date)
                        yield item
