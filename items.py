"""Scrapy items used to store crawled data."""

import scrapy


class PageItem(scrapy.Item):
    """A Scrapy item representing a single webpage and its SEO data."""

    url: scrapy.Field = scrapy.Field()
    title: scrapy.Field = scrapy.Field()
    meta_description: scrapy.Field = scrapy.Field()
    canonical: scrapy.Field = scrapy.Field()
    h1_tags: scrapy.Field = scrapy.Field()
    h2_tags: scrapy.Field = scrapy.Field()
    h3_tags: scrapy.Field = scrapy.Field()
    image_alts: scrapy.Field = scrapy.Field()
    json_ld: scrapy.Field = scrapy.Field()
    broken_links: scrapy.Field = scrapy.Field()
    status_code: scrapy.Field = scrapy.Field()
