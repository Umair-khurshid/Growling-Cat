"""
This module contains Scrapy item pipelines.
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)

class SqlitePipeline:
    """
    A Scrapy pipeline that stores items in a SQLite database.
    """
    def __init__(self):
        self.connection = None
        self.cursor = None

    def open_spider(self, _spider):
        """This method is called when the spider is opened."""
        try:
            self.connection = sqlite3.connect("growling_cat.db")
            self.cursor = self.connection.cursor()
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    url TEXT PRIMARY KEY,
                    status_code INTEGER,
                    title TEXT,
                    meta_description TEXT,
                    canonical TEXT,
                    h1_tags TEXT,
                    h2_tags TEXT,
                    h3_tags TEXT,
                    image_alts TEXT,
                    json_ld TEXT,
                    broken_links TEXT
                )
            """)
            self.connection.commit()
            logger.info("Successfully connected to SQLite database.")
        except sqlite3.Error as e:
            logger.error("Database error: %s", e)
            raise

    def close_spider(self, _spider):
        """This method is called when the spider is closed."""
        if self.connection:
            self.connection.close()
            logger.info("SQLite database connection closed.")

    def process_item(self, item, _spider):
        """This method is called for every item pipeline component."""
        try:
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO pages (
                    url, status_code, title, meta_description, canonical, h1_tags, h2_tags,
                    h3_tags, image_alts, json_ld, broken_links
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get('url'),
                    item.get('status_code'),
                    item.get('title'),
                    item.get('meta_description'),
                    item.get('canonical'),
                    item.get('h1_tags'),
                    item.get('h2_tags'),
                    item.get('h3_tags'),
                    item.get('image_alts'),
                    item.get('json_ld'),
                    item.get('broken_links', 'N/A') # Default value
                )
            )
            self.connection.commit()
            logger.debug("Item stored in database: %s", item['url'])
        except sqlite3.Error as e:
            logger.error("Failed to insert item %s: %s", item['url'], e)
        return item
