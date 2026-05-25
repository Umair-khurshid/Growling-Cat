"""Scrapy item pipelines."""

import logging
import sqlite3

from scrapy import Spider

logger = logging.getLogger(__name__)


class SqlitePipeline:
    """Pipeline that stores scraped items in a SQLite database."""

    def __init__(self) -> None:
        self.connection: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None

    def open_spider(self, _spider: Spider | None = None) -> None:
        """Called when the spider is opened. Creates the database and table."""
        try:
            self.connection = sqlite3.connect("growling_cat.db")
            self.cursor = self.connection.cursor()
            self.cursor.execute(
                """
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
            """
            )
            self.connection.commit()
            logger.info("Successfully connected to SQLite database.")
        except sqlite3.Error as e:
            logger.error("Database error: %s", e)
            raise

    def close_spider(self, _spider: Spider | None = None) -> None:
        """Called when the spider is closed. Closes the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("SQLite database connection closed.")

    def process_item(self, item: dict[str, object], spider: Spider) -> dict[str, object]:  # noqa: ARG002
        """Insert or replace an item into the pages table."""
        if not self.cursor or not self.connection:
            logger.error("No database cursor or connection available.")
            return item
        try:
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO pages (
                    url, status_code, title, meta_description, canonical, h1_tags, h2_tags,
                    h3_tags, image_alts, json_ld, broken_links
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get("url"),
                    item.get("status_code"),
                    item.get("title"),
                    item.get("meta_description"),
                    item.get("canonical"),
                    item.get("h1_tags"),
                    item.get("h2_tags"),
                    item.get("h3_tags"),
                    item.get("image_alts"),
                    item.get("json_ld"),
                    item.get("broken_links", "N/A"),
                ),
            )
            self.connection.commit()
            logger.debug("Item stored in database: %s", item["url"])
        except sqlite3.Error as e:
            logger.error("Failed to insert item %s: %s", item["url"], e)
        return item
