"""Streamlit web interface for controlling the Growling Cat SEO crawler."""

import json
import os
import sqlite3
import threading
import time

import pandas as pd
import streamlit as st

from crawl_runner import run_crawler_subprocess


def inject_custom_css() -> None:
    """Inject custom CSS for Fira Code font and data-dense dashboard styling."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Fira Sans', 'Source Sans Pro', sans-serif;
        }
        code, pre, [data-testid="stMetricValue"] {
            font-family: 'Fira Code', 'Courier New', monospace !important;
        }
        .stApp {
            background-color: #F8FAFC;
        }
        .stButton button {
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.15s ease;
        }
        .stButton button:hover {
            opacity: 0.9;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def fix_url_scheme(url: str) -> str:
    """Ensure the URL has a proper scheme (http:// or https://)."""
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if "localhost" in url or "127.0.0.1" in url:
        url = "http://" + url
    else:
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


def load_and_display_results(
    status_filter: list[str] | None = None,
    search_url: str = "",
) -> pd.DataFrame | None:
    """Load crawl results from the database and display them.

    Args:
        status_filter: List of status code prefixes to filter by (e.g. ["2xx", "4xx"]).
        search_url: Substring to filter URLs by.

    Returns:
        The filtered DataFrame, or None if no DB or error.
    """
    db_file = "growling_cat.db"
    if not os.path.exists(db_file):
        st.error("No results database found. Please run a crawl first.")
        return None

    try:
        conn = sqlite3.connect(db_file)
        df = pd.read_sql_query("SELECT * FROM pages", conn)
        conn.close()
    except sqlite3.Error as e:
        st.error(f"An error occurred while loading results: {e}")
        return None

    if df.empty:
        st.info("The database is empty. The crawl found no pages to analyze.")
        display_dashboard(df)
        st.write("### Crawled Data:")
        st.write("*No data to display.*")
        return None

    if "title" in df.columns:
        df["title_length"] = df["title"].apply(lambda x: len(x) if x != "N/A" else 0)
    if "meta_description" in df.columns:
        df["meta_description_length"] = df["meta_description"].apply(
            lambda x: len(x) if x != "N/A" else 0
        )

    if search_url:
        df = df[df["url"].str.contains(search_url, case=False, na=False)]
    if status_filter and "All" not in status_filter:
        valid_prefixes = {s[0] for s in status_filter if len(s) == 3 and s.endswith("xx")}
        prefix_series = df["status_code"].notna() & df["status_code"].astype(str).str[0].isin(
            valid_prefixes
        )
        df = df[prefix_series]

    if df.empty:
        st.info("No results match the current filters.")
        return None

    display_dashboard(df)

    st.write("### Crawled Data:")
    df["url"] = df["url"].apply(truncate_url)

    required_cols = ["status_code", "title_length", "meta_description_length"]
    display_df = df.drop(columns=["status_prefix"], errors="ignore")
    if all(col in display_df.columns for col in required_cols):
        st.dataframe(style_dataframe(display_df))
    else:
        st.dataframe(display_df)

    return df


def main() -> None:
    """Main function to run the Streamlit web interface."""
    st.set_page_config(page_title="Growling Cat", layout="wide")
    inject_custom_css()
    st.title("Growling Cat")

    if "auto_show" not in st.session_state:
        st.session_state.auto_show = False

    # --- Sidebar: advanced settings + filters + export ---
    with st.sidebar:
        st.markdown("*Adjust crawl behavior below.*")
        with st.expander("Advanced Settings"):
            depth = st.slider("Crawl Depth (DEPTH_LIMIT):", 1, 5, 2)
            delay = st.slider("Download Delay (seconds):", 0.0, 5.0, 0.5, 0.1)
            concurrency = st.slider("Concurrent Requests:", 1, 16, 8)
            js_rendering = st.checkbox("Enable JavaScript Rendering", False)

        st.markdown("---")
        st.markdown("### Filters")
        status_filter = st.multiselect(
            "Status Code:",
            options=["All", "2xx", "3xx", "4xx", "5xx"],
            default=["All"],
            placeholder="Filter by status...",
        )
        search_url = st.text_input("Search URL:", placeholder="Filter by URL...")

        st.markdown("---")
        st.markdown("### Export")
        if st.session_state.get("csv_data") is not None:
            st.download_button(
                label="Download CSV",
                data=st.session_state.csv_data,
                file_name="growling_cat_results.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # --- Main area: URL input + crawl/load buttons ---
    url = st.text_input("Website URL:", "https://quotes.toscrape.com/")

    col1, col2 = st.columns([1, 1])
    with col1:
        start_clicked = st.button("Start Crawling", use_container_width=True)
    with col2:
        load_clicked = st.button("Load Results", use_container_width=True)

    # --- Progress area (placeholder cleared on each rerun) ---
    progress_area = st.empty()

    # --- Crawl handler ---
    if start_clicked:
        cleaned_url = fix_url_scheme(url.strip())
        if cleaned_url:
            st.session_state.auto_show = False

            with progress_area.container():
                bar = st.progress(0)
                status = st.empty()

                crawl_result: dict[str, bool | str] = {"success": False, "message": ""}

                def do_crawl() -> None:
                    s, m = start_crawl_process(
                        cleaned_url, depth, delay, concurrency, js_rendering
                    )
                    crawl_result["success"] = s
                    crawl_result["message"] = m

                thread = threading.Thread(target=do_crawl, daemon=True)
                thread.start()

                while thread.is_alive():
                    if os.path.exists("progress.json"):
                        try:
                            with open("progress.json", encoding="utf-8") as f:
                                data = json.load(f)
                            total = data.get("total", 0)
                            completed = data.get("completed", 0)
                            if total > 0:
                                pct = min(completed / total, 1.0)
                                bar.progress(pct)
                                status.text(f"Crawled {completed} of {total} pages...")
                        except (json.JSONDecodeError, OSError):
                            pass
                    time.sleep(1)

                thread.join()
                bar.progress(1.0)
                status.text("")

            if crawl_result["success"]:
                st.success("Crawl complete!")
                st.session_state.auto_show = True
            else:
                st.error("Crawl failed!")
                msg = str(crawl_result["message"])
                st.text_area("Error Log:", msg, height=300)
        else:
            st.warning("Please enter a valid URL.")

    # --- Load and display results ---
    should_show = load_clicked or st.session_state.pop("auto_show", False)
    if should_show:
        df = load_and_display_results(
            status_filter=status_filter if status_filter else ["All"],
            search_url=search_url if search_url else "",
        )
        if df is not None and not df.empty:
            st.session_state.csv_data = df.to_csv(index=False).encode("utf-8")
        else:
            st.session_state.csv_data = None
            if "csv_data" in st.session_state:
                del st.session_state.csv_data

    display_faq()


if __name__ == "__main__":
    main()
