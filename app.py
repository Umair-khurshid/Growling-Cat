"""Streamlit web interface for controlling the Growling Cat SEO crawler."""

import os
import sqlite3

import pandas as pd
import streamlit as st

from crawl_runner import run_crawler_subprocess


def fix_url_scheme(url: str) -> str:
    """Ensure the URL has a proper scheme (http:// or https://)."""
    if not url:
        return ""
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    return url


def start_crawl_process(
    cleaned_url: str, depth: int, delay: float, concurrency: int, js_rendering: bool
) -> tuple[bool, str]:
    """Launch the crawler in a separate, isolated subprocess.

    Args:
        cleaned_url: The URL to crawl with a valid scheme.
        depth: Maximum crawl depth.
        delay: Delay between requests in seconds.
        concurrency: Number of concurrent requests.
        js_rendering: Whether to enable JavaScript rendering.

    Returns:
        A tuple of (success: bool, message: str).
    """
    db_file = "growling_cat.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    if os.path.exists(f"{db_file}-journal"):
        os.remove(f"{db_file}-journal")

    return run_crawler_subprocess(cleaned_url, depth, delay, concurrency, js_rendering)


def style_dataframe(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    """Apply conditional styling to the DataFrame for a heatmap effect."""
    optimal_title_min = 50
    optimal_title_max = 60
    title_warn_range = 10
    optimal_desc_min = 120
    optimal_desc_max = 158
    desc_warn_range = 20

    def style_status_code(code: object) -> str:
        if isinstance(code, int) and 200 <= code < 300:
            return "background-color: #8FBC8F; color: black"
        if isinstance(code, int) and 300 <= code < 400:
            return "background-color: #F0E68C; color: black"
        if isinstance(code, int) and 400 <= code < 600:
            return "background-color: #CD5C5C; color: white"
        return ""

    def style_length(length: object, optimal_min: int, optimal_max: int, warn_range: int) -> str:
        if not isinstance(length, int):
            return ""
        if length == 0:
            return "background-color: #CD5C5C; color: white"
        if optimal_min <= length <= optimal_max:
            return "background-color: #8FBC8F; color: black"
        if (optimal_min - warn_range <= length < optimal_min) or (
            optimal_max < length <= optimal_max + warn_range
        ):
            return "background-color: #F0E68C; color: black"
        return "background-color: #CD5C5C; color: white"

    styler = (
        df.style.map(style_status_code, subset=["status_code"])
        .map(
            lambda x: style_length(x, optimal_title_min, optimal_title_max, title_warn_range),
            subset=["title_length"],
        )
        .map(
            lambda x: style_length(x, optimal_desc_min, optimal_desc_max, desc_warn_range),
            subset=["meta_description_length"],
        )
    )
    return styler


def truncate_url(url: str, max_length: int = 50) -> str:
    """Truncate URL for display with full URL on hover."""
    if len(url) > max_length:
        return f'<a href="{url}" title="{url}" target="_blank">{url[:max_length]}...</a>'
    return url


def display_dashboard(df: pd.DataFrame) -> None:
    """Display the dashboard with SEO metrics."""
    st.write("### Dashboard")
    total_pages = len(df)
    missing_titles = len(df[df["title"] == "N/A"])
    missing_descriptions = len(df[df["meta_description"] == "N/A"])
    pages_with_broken_links = len(df[df["broken_links"] != "N/A"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Pages Crawled", total_pages)
    col2.metric("Pages with Missing Titles", missing_titles)
    col3.metric("Pages with Missing Descriptions", missing_descriptions)
    col4.metric("Pages with Broken Links", pages_with_broken_links)


def display_faq() -> None:
    """Display the FAQ section."""
    st.markdown("---")
    st.subheader("Frequently Asked Questions (FAQ)")

    faqs: list[tuple[str, str]] = [
        (
            "What does Crawl Depth mean?",
            (
                "**Crawl Depth** determines how deep the crawler goes into the website.\n"
                "- **1** = Only the homepage\n"
                "- **2** = Homepage + first-level links\n"
                "- **3+** = Deeper levels (more pages, but slower)\n"
                "Higher depth = More pages, but takes longer."
            ),
        ),
        (
            "What is Download Delay?",
            (
                "**Download Delay** is the wait time between requests to the same website.\n"
                "- **Lower delay (0-1s) = Faster crawling** but might get blocked.\n"
                "- **Higher delay (2-5s) = Slower but safer** (reduces risk of bans).\n"
                "Recommended: 0.5s (default)."
            ),
        ),
        (
            "What does Concurrent Requests do?",
            (
                "This controls how many pages the crawler processes at the same time.\n"
                "- **Higher (8-16)** = Faster crawling, but may overload the site.\n"
                "- **Lower (1-4)** = Slower, but safer.\n"
                "Default: **8** (Balanced speed)."
            ),
        ),
        (
            "Should I enable JavaScript Rendering?",
            (
                "Some websites load content using JavaScript (JS).\n"
                "- **Enable this if the site uses JS for important content.**\n"
                "- **Disabling it makes crawling faster** (recommended for most sites).\n"
                "**Downside:** Slower crawling if enabled."
            ),
        ),
        (
            "Why did my crawl fail or return no results?",
            (
                "Websites can employ anti-scraping measures. If a crawl fails or "
                "returns zero pages,"
                " it's likely due to one of the following:\n"
                "- **Rate Limiting:** The site is blocking the crawler for making too many requests"
                " too quickly. **Try increasing the 'Download Delay'** in the advanced settings"
                " to be more respectful of the site's limits.\n"
                "- **Sophisticated Anti-Bot Protection:** Some sites use advanced services"
                " (like Cloudflare or Akamai) that can detect and block automated crawlers."
                " These are very difficult to bypass."
            ),
        ),
    ]

    for question, answer in faqs:
        with st.expander(question):
            st.write(answer)


def load_and_display_results() -> None:
    """Load crawl results from the database and display them."""
    db_file = "growling_cat.db"
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            df = pd.read_sql_query("SELECT * FROM pages", conn)
            conn.close()

            if "title" in df.columns:
                df["title_length"] = df["title"].apply(
                    lambda x: len(x) if x != "N/A" else 0
                )
            if "meta_description" in df.columns:
                df["meta_description_length"] = df["meta_description"].apply(
                    lambda x: len(x) if x != "N/A" else 0
                )

            display_dashboard(df)

            st.write("### Crawled Data:")
            df["url"] = df["url"].apply(truncate_url)

            required_cols = ["status_code", "title_length", "meta_description_length"]
            if all(col in df.columns for col in required_cols):
                st.dataframe(style_dataframe(df))
            else:
                st.dataframe(df)

        except sqlite3.Error as e:
            st.error(f"An error occurred while loading results: {e}")
    else:
        st.error("No results database found. Please run a crawl first.")


def main() -> None:
    """Main function to run the Streamlit web interface."""
    st.set_page_config(page_title="Growling Cat", layout="wide")
    st.title("Growling Cat")

    url = st.text_input("Website URL:", "https://quotes.toscrape.com/")

    with st.expander("Advanced Settings"):
        depth = st.slider("Crawl Depth (DEPTH_LIMIT):", 1, 5, 2)
        delay = st.slider("Download Delay (seconds):", 0.0, 5.0, 0.5, 0.1)
        concurrency = st.slider("Concurrent Requests:", 1, 16, 8)
        js_rendering = st.checkbox("Enable JavaScript Rendering", False)

    if st.button("Start Crawling"):
        cleaned_url = fix_url_scheme(url.strip())
        if cleaned_url:
            with st.spinner(f"Crawling {cleaned_url}... This may take a while."):
                success, message = start_crawl_process(
                    cleaned_url, depth, delay, concurrency, js_rendering
                )
            if success:
                st.success("Crawl complete! Click 'Load Results' to see the data.")
            else:
                st.error("Crawl failed!")
                st.text_area("Error Log:", message, height=300)
        else:
            st.warning("Please enter a valid URL.")

    if st.button("Load Results"):
        load_and_display_results()

    display_faq()


if __name__ == "__main__":
    main()
