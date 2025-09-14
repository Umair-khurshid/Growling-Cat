"""
This module defines the Scrapy items that will be used to store the crawled data.
"""
import scrapy

class PageItem(scrapy.Item):
    # pylint: disable=too-few-public-methods
    """
    A Scrapy item that represents a single webpage and its SEO data.
    """
    url = scrapy.Field()
    title = scrapy.Field()
    meta_description = scrapy.Field()
    canonical = scrapy.Field()
    h1_tags = scrapy.Field()
    h2_tags = scrapy.Field()
    h3_tags = scrapy.Field()
    image_alts = scrapy.Field()
    json_ld = scrapy.Field()
    broken_links = scrapy.Field()
    status_code = scrapy.Field()
