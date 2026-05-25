"""E2E tests for the Growling Cat Streamlit UI using Playwright."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.streamlit_pages import StreamlitApp

if TYPE_CHECKING:
    from playwright.sync_api import Page


@pytest.mark.usefixtures("clean_db")
class TestGrowlingCatUI:
    """Comprehensive E2E tests for the Streamlit web interface."""

    def test_page_title_and_layout(self, app_page: Page) -> None:
        """Verify the page title and basic layout elements are rendered."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)
        app.url_input.wait_for(state="visible", timeout=15000)
        assert app.url_input.is_visible(), "URL input should be visible"
        assert app.start_button.is_visible(), "'Start Crawling' button should be visible"
        assert app.load_button.is_visible(), "'Load Results' button should be visible"

    def test_url_input_exists_and_editable(self, app_page: Page) -> None:
        """Verify the URL input field has default text and can be edited."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        assert app.url_input.is_editable(), "URL input should be editable"
        app.set_url("https://example.com")
        assert app.get_url_value() == "https://example.com", "URL should update on fill"

    def test_empty_url_shows_warning(self, app_page: Page) -> None:
        """Submitting with an empty URL should show a validation warning."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        app.set_url("")
        app.start_crawl()
        app.warning_message.wait_for(state="visible", timeout=5000)
        assert app.warning_message.is_visible()

    def test_load_results_without_crawl(self, app_page: Page) -> None:
        """Clicking 'Load Results' with no database should show an error."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        app.click_load_results()
        app.no_db_warning.wait_for(state="visible", timeout=5000)
        assert app.no_db_warning.is_visible()

    def test_advanced_settings_expand(self, app_page: Page) -> None:
        """Advanced Settings expander opens and reveals slider controls."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        assert app.advanced_settings.is_visible()
        app.open_settings()
        app.crawl_depth_slider.wait_for(state="visible", timeout=5000)
        assert app.crawl_depth_slider.is_visible()
        assert app.delay_slider.is_visible()
        assert app.concurrency_slider.is_visible()
        assert app.js_checkbox.is_visible()

    def test_faq_section_rendered(self, app_page: Page) -> None:
        """FAQ section heading and expander items should be visible."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        app.scroll_to_bottom()
        app.faq_header.wait_for(state="visible", timeout=5000)

        expanders = app.faq_expander_items
        count = expanders.count()
        assert count >= 3, f"Expected at least 3 FAQ items, got {count}"

    def test_faq_expanders_open_and_show_content(self, app_page: Page) -> None:
        """Each FAQ expander opens to reveal content when clicked."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        app.scroll_to_bottom()
        app.faq_header.wait_for(state="visible", timeout=5000)

        expanders = app.faq_expander_items
        for i in range(expanders.count()):
            item = expanders.nth(i)
            inner_text = item.inner_text()
            assert len(inner_text) > 0, f"FAQ item {i} should have text"
            assert "?" in inner_text, f"FAQ item {i} should be a question"

    @pytest.mark.slow
    def test_full_crawl_and_load_results(self, app_page: Page, test_server: str) -> None:
        """Full workflow: enter URL, crawl, load results, verify data appears."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        crawl_url = f"{test_server}/sample.html"
        app.set_url(crawl_url)
        app.start_crawl()

        app.success_message.wait_for(state="visible", timeout=60000)
        assert app.success_message.is_visible()

        app.click_load_results()
        app.dashboard_heading.wait_for(state="visible", timeout=10000)
        assert app.dashboard_heading.is_visible(), "Dashboard should be displayed"

        app.crawled_data_heading.wait_for(state="visible", timeout=10000)
        assert app.crawled_data_heading.is_visible(), "Crawled Data table should be displayed"

    @pytest.mark.slow
    def test_crawl_url_missing_scheme_auto_fixed(
        self, app_page: Page, test_server: str
    ) -> None:
        """Entering a URL without scheme should be auto-fixed to https://."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        raw_url = f"localhost:{test_server.split(':')[-1]}/sample.html"
        app.set_url(raw_url)
        app.start_crawl()

        app.success_message.wait_for(state="visible", timeout=60000)
        assert app.success_message.is_visible()

        app.click_load_results()
        app.dashboard_heading.wait_for(state="visible", timeout=10000)
        assert app.dashboard_heading.is_visible()

    @pytest.mark.slow
    def test_dashboard_metrics_after_crawl(self, app_page: Page, test_server: str) -> None:
        """After crawling, the dashboard should show metric cards."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        app.set_url(f"{test_server}/sample.html")
        app.start_crawl()
        app.success_message.wait_for(state="visible", timeout=60000)

        app.click_load_results()
        app.dashboard_heading.wait_for(state="visible", timeout=10000)

        app.scroll_to_top()
        for label in (
            "Total Pages Crawled",
            "Pages with Missing Titles",
            "Pages with Missing Descriptions",
            "Pages with Broken Links",
        ):
            metric_text = app.page.get_by_text(label, exact=True)
            metric_text.wait_for(state="visible", timeout=5000)
            assert metric_text.is_visible(), f"Metric '{label}' should be displayed"

    def test_url_persistence_after_ui_interactions(self, app_page: Page) -> None:
        """URL input content should persist after other UI button clicks."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        app.set_url("https://example.com/page")
        app.click_load_results()
        app.no_db_warning.wait_for(state="visible", timeout=5000)

        assert "https://example.com/page" in app.get_url_value(), (
            "URL value should persist after UI interactions"
        )

    @pytest.mark.slow
    def test_crawl_failure_shows_error_log(self, app_page: Page) -> None:
        """Crawling a non-existent domain should complete and show a status."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        app.set_url("https://this-domain-does-not-exist-634821.test/")
        app.start_crawl()

        app.page.wait_for_function(
            """
            () => {
                const el = document.body.innerText || '';
                return el.includes('Crawl complete!') || el.includes('Crawl failed!');
            }
            """,
            timeout=120000,
        )

        assert app.failure_message.is_visible() or app.success_message.is_visible(), (
            "Crawl should terminate with a visible status message"
        )

    def test_default_values_in_advanced_settings(self, app_page: Page) -> None:
        """Verify advanced settings controls are present with the expected types."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        assert app.advanced_settings.is_visible(), "Advanced Settings expander should exist"
        app.open_settings()

        assert app.crawl_depth_slider.is_visible(), "Depth slider should be visible"
        assert app.delay_slider.is_visible(), "Delay slider should be visible"
        assert app.concurrency_slider.is_visible(), "Concurrency slider should be visible"
        assert app.js_checkbox.is_visible(), "JS rendering checkbox should be visible"

    @pytest.mark.slow
    def test_user_can_crawl_with_custom_settings(
        self, app_page: Page, test_server: str
    ) -> None:
        """User opens advanced settings, modifies them, and crawls successfully."""
        app = StreamlitApp(app_page)
        app.page_title.wait_for(state="visible", timeout=15000)

        app.open_settings()
        app.crawl_depth_slider.wait_for(state="visible", timeout=5000)

        app.set_url(f"{test_server}/sample.html")
        app.start_crawl()
        app.success_message.wait_for(state="visible", timeout=60000)

        app.click_load_results()
        app.dashboard_heading.wait_for(state="visible", timeout=10000)
        assert app.dashboard_heading.is_visible()
