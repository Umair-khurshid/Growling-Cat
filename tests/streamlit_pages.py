"""Page Object Model for the Growling Cat Streamlit web interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page


class StreamlitApp:
    """Page object wrapping the main Streamlit interface for Growling Cat."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.url_input: Locator = page.get_by_label("Website URL:")
        self.start_button: Locator = page.get_by_role("button", name="Start Crawling")
        self.load_button: Locator = page.get_by_role("button", name="Load Results")
        self.advanced_settings: Locator = page.get_by_text("Advanced Settings", exact=True)
        self.crawl_depth_slider: Locator = page.get_by_text(
            "Crawl Depth (DEPTH_LIMIT):", exact=True
        )
        self.delay_slider: Locator = page.get_by_text(
            "Download Delay (seconds):", exact=True
        )
        self.concurrency_slider: Locator = page.get_by_text(
            "Concurrent Requests:", exact=True
        )
        self.js_checkbox: Locator = page.get_by_text(
            "Enable JavaScript Rendering", exact=True
        )
        self.faq_header: Locator = page.get_by_text("Frequently Asked Questions")
        self.page_title: Locator = page.get_by_text("Growling Cat")

    def goto(self) -> None:
        """Navigate to the Streamlit app."""
        self.page.goto("/")
        self.page.wait_for_load_state("domcontentloaded")

    def open_settings(self) -> None:
        """Expand the Advanced Settings panel if not already open."""
        if self.advanced_settings.is_visible():
            self.advanced_settings.click()
            self.page.wait_for_timeout(300)

    def get_settings_expand_state(self) -> bool:
        """Return True if the Advanced Settings expander is open."""
        return self.crawl_depth_slider.is_visible(timeout=1000)

    def set_url(self, url: str) -> None:
        """Fill the website URL input field."""
        self.url_input.fill(url)

    def get_url_value(self) -> str:
        """Return the current URL input value."""
        return self.url_input.input_value() or ""

    def start_crawl(self) -> None:
        """Click the Start Crawling button."""
        self.start_button.click()

    def click_load_results(self) -> None:
        """Click the Load Results button."""
        self.load_button.click()

    def wait_for_crawl_complete(self, timeout_ms: int = 60000) -> None:
        """Wait for the crawl success or failure message to appear."""
        self.page.wait_for_function(
            """
            () => {
                const el = document.body.innerText || '';
                return el.includes('Crawl complete!') || el.includes('Crawl failed!');
            }
            """,
            timeout=timeout_ms,
        )

    def wait_for_crawl_success(self, timeout_ms: int = 60000) -> None:
        """Wait until the crawl success message is visible."""
        self.page.get_by_text("Crawl complete!").wait_for(state="visible", timeout=timeout_ms)

    @property
    def success_message(self) -> Locator:
        """Locator for the crawl success message."""
        return self.page.get_by_text("Crawl complete!")

    @property
    def failure_message(self) -> Locator:
        """Locator for the crawl failure message."""
        return self.page.get_by_text("Crawl failed!")

    @property
    def warning_message(self) -> Locator:
        """Locator for the validation warning."""
        return self.page.get_by_text("Please enter a valid URL.")

    @property
    def error_message(self) -> Locator:
        """Locator for the error text area shown on crawl failure."""
        return self.page.get_by_text("Error Log:")

    @property
    def no_db_warning(self) -> Locator:
        """Locator for the 'no results database' error."""
        return self.page.get_by_text("No results database found")

    @property
    def dashboard_heading(self) -> Locator:
        """Locator for the Dashboard section heading."""
        return self.page.get_by_text("Dashboard")

    @property
    def crawled_data_heading(self) -> Locator:
        """Locator for the Crawled Data section heading."""
        return self.page.get_by_text("Crawled Data:")

    @property
    def faq_expander_items(self) -> Locator:
        """Locator for FAQ question expanders — all <details> containing '?' in their summary."""
        return self.page.locator("details").filter(has_text="?")

    def get_metric_value(self, label: str) -> str:
        """Get the value of a dashboard metric by its label."""
        metric = self.page.get_by_text(label, exact=True)
        parent = metric.locator("..")
        value_el = parent.locator("[data-testid='stMetricValue']")
        return value_el.inner_text()

    def has_data_table(self) -> bool:
        """Check if a dataframe/table is rendered on the page."""
        return self.page.locator("[data-testid='stTable']").first.is_visible(timeout=5000)

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the page."""
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    def scroll_to_top(self) -> None:
        """Scroll to the top of the page."""
        self.page.evaluate("window.scrollTo(0, 0)")
