"""Streamlit web interface for controlling the Growling Cat SEO crawler."""

import json
import os
import sqlite3
import threading
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from crawl_runner import run_crawler_subprocess


def inject_custom_css() -> None:
    """Inject custom CSS for Fira Code font, data-dense dashboard and dark mode."""
    dark_css = ""
    if st.session_state.get("dark_mode", False):
        dark_css = """
        .stApp { background-color: #0E1117 !important; }
        .main .block-container { background-color: #0E1117; }
        .stSidebar { background-color: #1E1E1E; }
        .stSidebar .stMarkdown, .stSidebar label { color: #FAFAFA; }
        [data-testid="stMetricValue"] { color: #58A6FF; }
        [data-testid="stMetricLabel"] { color: #8B949E; }
        .st-emotion-cache-1avcm0f { color: #C9D1D9; }
        h1, h2, h3, h4, h5, h6 { color: #F0F6FC; }
        .stTextInput label, .stSlider label, .stCheckbox label { color: #C9D1D9; }
        .stExpander { border-color: #30363D; }
        .st-bb { border-color: #30363D; }
        .stAlert { background-color: #21262D; }
        """
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] {{
            font-family: 'Fira Sans', 'Source Sans Pro', sans-serif;
        }}
        code, pre, [data-testid="stMetricValue"] {{
            font-family: 'Fira Code', 'Courier New', monospace !important;
        }}
        .stApp {{
            background-color: #F8FAFC;
        }}
        .stButton button {{
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.15s ease;
        }}
        .stButton button:hover {{
            opacity: 0.9;
        }}
        [data-testid="stMetricValue"] {{
            font-size: 1.8rem;
        }}
        {dark_css}
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
    if os.path.exists("progress.json"):
        os.remove("progress.json")

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

    def style_broken_links(val: object) -> str:
        if isinstance(val, str) and val != "N/A":
            return "background-color: #FFD700; color: black; font-weight: bold"
        return ""

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
        .map(style_broken_links, subset=["broken_links"])
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

    if pages_with_broken_links > 0:
        st.warning(
            f"⚠️ Found {pages_with_broken_links} page(s) with broken or missing links. "
            "Check the **broken_links** column in the data table for details."
        )


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
        st.dataframe(style_dataframe(display_df), use_container_width=True)
    else:
        st.dataframe(display_df, use_container_width=True)

    return df


def main() -> None:
    """Main function to run the Streamlit web interface."""
    st.set_page_config(page_title="Growling Cat", layout="wide")

    if "crawling" not in st.session_state:
        st.session_state.crawling = False
    if "auto_show" not in st.session_state:
        st.session_state.auto_show = False
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False

    inject_custom_css()
    st.title("Growling Cat")

    # --- Sidebar: advanced settings + filters + dark mode + export ---
    with st.sidebar:
        st.markdown("*Adjust crawl behavior below.*")

        dark_mode = st.toggle("Dark Mode", value=st.session_state.dark_mode)
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()

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
        start_clicked = st.button(
            "Start Crawling", use_container_width=True, disabled=st.session_state.crawling
        )
    with col2:
        load_clicked = st.button("Load Results", use_container_width=True)

    # --- Progress area ---
    progress_place = st.empty()

    # On each render, remove stale crawl_result.json from a prior run
    if not st.session_state.get("crawling", False):
        for stale in ("crawl_result.json", "progress.json"):
            if os.path.exists(stale):
                try:
                    os.remove(stale)
                except OSError:
                    pass

    # --- Crawl handler (non-blocking) ---
    if start_clicked and not st.session_state.crawling:
        cleaned_url = fix_url_scheme(url.strip())
        if cleaned_url:
            st.session_state.crawling = True
            st.session_state.auto_show = False
            st.session_state.crawl_result = None

            db_file = "growling_cat.db"
            for f in (db_file, f"{db_file}-journal", "progress.json"):
                if os.path.exists(f):
                    os.remove(f)

            def do_crawl() -> None:
                s, msg = start_crawl_process(
                    cleaned_url, depth, delay, concurrency, js_rendering
                )
                with open("crawl_result.json", "w", encoding="utf-8") as f:
                    json.dump({"success": s, "message": msg}, f)

            threading.Thread(target=do_crawl, daemon=True).start()
        else:
            st.warning("Please enter a valid URL.")

    # --- Show progress / result ---
    if st.session_state.crawling:
        result_found = None
        items_scraped = 0

        if os.path.exists("progress.json"):
            try:
                data = json.loads(Path("progress.json").read_text())
                items_scraped = data.get("items_scraped", 0)
            except (json.JSONDecodeError, OSError):
                pass

        if os.path.exists("crawl_result.json"):
            try:
                result_found = json.loads(Path("crawl_result.json").read_text())
                os.remove("crawl_result.json")
            except (json.JSONDecodeError, OSError):
                pass

        if result_found is not None:
            st.session_state.crawl_result = result_found
            st.session_state.crawl_items_scraped = items_scraped
            st.session_state.crawling = False
        else:
            with progress_place.container():
                st.text(f"Pages scraped so far: {items_scraped}")
            time.sleep(1)
            st.rerun()

    # Render result (persists after crawling stops)
    result = st.session_state.get("crawl_result")
    if result is not None:
        items_scraped = st.session_state.get("crawl_items_scraped", 0)
        if result.get("success", True):
            st.success(f"Crawl complete! Scraped {items_scraped} page(s).")
            st.session_state.auto_show = True
        else:
            st.error("Crawl failed!")
            st.text_area("Error Log:", result.get("message", ""), height=300)

    # --- Load and display results ---
    should_show = load_clicked or st.session_state.pop("auto_show", False)
    if should_show and not st.session_state.crawling:
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
