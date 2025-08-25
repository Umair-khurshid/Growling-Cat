import os
import sqlite3
import subprocess
import sys

import pandas as pd
import numpy as np
import streamlit as st

def fix_url_scheme(url: str) -> str:
    """
    Ensure the URL has a proper scheme (http:// or https://).
    """
    if not url:
        return ""
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    return url

def start_crawl_process(cleaned_url, depth, delay, concurrency, js_rendering):
    """
    Launches the Scrapy crawler in a separate, isolated process.
    """
    db_file = "growling_cat.db"
    # Delete old database file if it exists to ensure a fresh crawl
    if os.path.exists(db_file):
        os.remove(db_file)
    if os.path.exists(f"{db_file}-journal"):
        os.remove(f"{db_file}-journal")

    # Construct the command to run the dedicated crawl script
    command = [
        sys.executable, # Use the same python interpreter that's running streamlit
        "run_crawl_process.py",
        cleaned_url,
        str(depth),
        str(delay),
        str(concurrency),
        str(js_rendering),
    ]

    # Run the command as a subprocess
    # This blocks until the crawl is complete, solving the reactor and signal issues
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True, ""
    except subprocess.CalledProcessError as e:
        # If the crawl script exits with an error, capture and display it
        error_message = f"Crawler process failed with exit code {e.returncode}.\n"
        error_message += f"Stderr:\n{e.stderr}"
        return False, error_message

def style_dataframe(df):
    """Applies conditional styling to the DataFrame for a heatmap effect."""
    def style_status_code(code):
        if 200 <= code < 300:
            return 'background-color: #8FBC8F; color: black'  # Dark Sea Green
        elif 300 <= code < 400:
            return 'background-color: #F0E68C; color: black'  # Khaki
        elif 400 <= code < 600:
            return 'background-color: #CD5C5C; color: white'  # Indian Red
        return ''

    def style_length(length, optimal_min, optimal_max, warn_range):
        if length == 0:
            return 'background-color: #CD5C5C; color: white' # Red for missing
        if optimal_min <= length <= optimal_max:
            return 'background-color: #8FBC8F; color: black'  # Dark Sea Green
        elif (optimal_min - warn_range <= length < optimal_min) or \
             (optimal_max < length <= optimal_max + warn_range):
            return 'background-color: #F0E68C; color: black'  # Khaki
        return 'background-color: #CD5C5C; color: white' # Indian Red

    # Apply styles
    styler = df.style.map(style_status_code, subset=['status_code']) \
                     .map(lambda x: style_length(x, 50, 60, 10), subset=['title_length']) \
                     .map(lambda x: style_length(x, 120, 158, 20), subset=['meta_description_length'])

    return styler

def truncate_url(url, max_length=50):
    """Truncate URL for display and show full URL on hover."""
    if len(url) > max_length:
        return f'<a href="{url}" title="{url}" target="_blank">{url[:max_length]}...</a>'
    return url


def main():
    """
    Streamlit web interface for controlling the Growling Cat SEO crawler.
    """
    st.set_page_config(page_title="Growling Cat", layout="wide")
    st.title("🐈‍⬛ Growling Cat")

    url = st.text_input("Website URL:", "https://quotes.toscrape.com/") # Default example

    with st.expander("⚙️ Advanced Settings"):
        depth = st.slider("Crawl Depth (DEPTH_LIMIT):", 1, 5, 2)
        delay = st.slider("Download Delay (seconds):", 0.0, 5.0, 0.5, 0.1)
        concurrency = st.slider("Concurrent Requests:", 1, 16, 8)
        js_rendering = st.checkbox("Enable JavaScript Rendering", False)

    if st.button("Start Crawling"):
        cleaned_url = fix_url_scheme(url.strip())

        if cleaned_url:
            with st.spinner(f"**Crawling {cleaned_url}... This may take a while.**"):
                success, message = start_crawl_process(
                    cleaned_url, depth, delay, concurrency, js_rendering
                )

            if success:
                st.success("🎉 Crawl complete! Click 'Load Results' to see the data.")
            else:
                st.error("🔥 Crawl failed!")
                st.text_area("Error Log:", message, height=300)
        else:
            st.warning("⚠️ Please enter a valid URL.")

    if st.button("Load Results"):
        db_file = "growling_cat.db"
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                df = pd.read_sql_query("SELECT * FROM pages", conn)
                conn.close()

                # --- Add Length Analysis ---
                if 'title' in df.columns:
                    df['title_length'] = df['title'].apply(lambda x: len(x) if x != 'N/A' else 0)
                if 'meta_description' in df.columns:
                    df['meta_description_length'] = df['meta_description'].apply(lambda x: len(x) if x != 'N/A' else 0)
                # -------------------------

                st.write("### 📊 Dashboard")
                total_pages = len(df)
                missing_titles = len(df[df['title'] == 'N/A'])
                missing_descriptions = len(df[df['meta_description'] == 'N/A'])
                pages_with_broken_links = len(df[df['broken_links'] != 'N/A'])

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Pages Crawled", total_pages)
                col2.metric("Pages with Missing Titles", missing_titles)
                col3.metric("Pages with Missing Descriptions", missing_descriptions)
                col4.metric("Pages with Broken Links", pages_with_broken_links)

                st.write("### Crawled Data:")

                # Apply URL truncation for better display
                df['url'] = df['url'].apply(truncate_url)

                # Display styled dataframe if all columns are present
                if all(col in df.columns for col in ['status_code', 'title_length', 'meta_description_length']):
                    st.dataframe(style_dataframe(df))
                else:
                    st.dataframe(df)

            except Exception as e:
                st.error(f"❌ An error occurred while loading results: {e}")
        else:
            st.error("❌ No results database found. Please run a crawl first.")

    st.markdown("---")
    st.subheader(" Frequently Asked Questions (FAQ)")

    with st.expander("What does Crawl Depth mean?"):
        st.write(
            """
            **Crawl Depth** determines how deep the crawler goes into the website.
            - **1** = Only the homepage
            - **2** = Homepage + first-level links
            - **3+** = Deeper levels (more pages, but slower)
            Higher depth = More pages, but takes longer.
            """
        )

    with st.expander(" What is Download Delay?"):
        st.write(
            """
            **Download Delay** is the wait time between requests to the same website.
            - **Lower delay (0-1s) = Faster crawling** but might get blocked.
            - **Higher delay (2-5s) = Slower but safer** (reduces risk of bans).
            Recommended: 0.5s (default).
            """
        )

    with st.expander(" What does Concurrent Requests do?"):
        st.write(
            """
            This controls how many pages the crawler processes at the same time.
            - **Higher (8-16)** = Faster crawling, but may overload the site.
            - **Lower (1-4)** = Slower, but safer.
            Default: **8** (Balanced speed).
            """
        )

    with st.expander(" Should I enable JavaScript Rendering?"):
        st.write(
            """
            Some websites load content using JavaScript (JS).
            - **Enable this if the site uses JS for important content.**
            - **Disabling it makes crawling faster** (recommended for most sites).
            **Downside:** Slower crawling if enabled.
            """
        )

    with st.expander("Why did my crawl fail or return no results?"):
        st.write(
            """
            Websites can employ anti-scraping measures. If a crawl fails or returns zero pages, it's likely due to one of the following:
            - **Rate Limiting:** The site is blocking the crawler for making too many requests too quickly. **Try increasing the "Download Delay"** in the advanced settings to be more respectful of the site's limits.
            - **Sophisticated Anti-Bot Protection:** Some sites use advanced services (like Cloudflare or Akamai) that can detect and block automated crawlers. These are very difficult to bypass.
            """
        )


if __name__ == "__main__":
    main()
