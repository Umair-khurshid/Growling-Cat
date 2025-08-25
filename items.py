import scrapy

class PageItem(scrapy.Item):
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
