import streamlit as st
import pandas as pd
import os
import json
import time
import threading
from main import run_crawler

# Function to ensure URLs have a scheme (http:// or https://)
def fix_url_scheme(url: str) -> str:
    if not url:
        return ""
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    return url

# Function to start the Scrapy crawler in a separate thread
def start_crawl(cleaned_url, depth, delay, concurrency, js_rendering):
    # Remove old progress file
    if os.path.exists("progress.json"):
        os.remove("progress.json")
    
    run_crawler(cleaned_url, depth, delay, concurrency, js_rendering)

# Main Streamlit App
def main():
    st.set_page_config(page_title="Growling Cat", layout="wide")
    st.title("🐈‍⬛ Growling Cat")

    # URL Input
    url = st.text_input("Website URL:", "")

    # Crawl Settings Panel
    with st.expander("⚙️ Advanced Settings"):
        depth = st.slider("Crawl Depth (DEPTH_LIMIT):", 1, 5, 2)
        delay = st.slider("Download Delay (seconds):", 0.0, 5.0, 0.5, 0.1)
        concurrency = st.slider("Concurrent Requests:", 1, 16, 8)
        js_rendering = st.checkbox("Enable JavaScript Rendering", False)

    # Progress Bar UI Elements
    progress_bar = st.empty()
    status_text = st.empty()

    # Start Crawling Button
    if st.button("Start Crawling"):
        cleaned_url = fix_url_scheme(url.strip())

        if cleaned_url:
            st.info(f"**Crawling {cleaned_url}... This may take a while.**")
            progress_bar.progress(0)  # Initialize the progress bar
            status_text.text("Crawling started...")

            # Start Scrapy in a separate thread
            crawl_thread = threading.Thread(
                target=start_crawl, args=(cleaned_url, depth, delay, concurrency, js_rendering)
            )
            crawl_thread.start()

            # Real-time progress tracking
            while True:
                time.sleep(1)  # Check progress every second

                if not crawl_thread.is_alive():
                    break  # Crawl finished

                # Read progress.json for actual progress
                try:
                    if os.path.exists("progress.json") and os.path.getsize("progress.json") > 0:
                        with open("progress.json", "r") as f:
                            data = json.load(f)
                        total = data.get("total", 1)
                        completed = data.get("completed", 0)
                        done = data.get("done", False)

                        progress_percent = int((completed / total) * 100) if total > 0 else 0

                        progress_bar.progress(progress_percent)
                        status_text.text(f"🔄 Crawling in progress... ({progress_percent}%)")

                        if done:
                            break  # Stop loop if Scrapy signals "done"
                    else:
                        status_text.text("⏳ Waiting for progress update...")
                except (json.JSONDecodeError, FileNotFoundError):
                    status_text.text("⚠️ Error reading progress. Retrying...")

            # Ensure the crawl thread finishes completely
            crawl_thread.join()

            # Final UI Updates
            progress_bar.progress(100)
            status_text.text("✅ Crawl complete!")
            st.success("🎉 Crawl complete! Click 'Load Results' to see the data.")

        else:
            st.warning("⚠️ Please enter a valid URL.")

    # Load and display results after crawling
    if st.button("Load Results"):
        if os.path.exists("output.csv"):
            df = pd.read_csv("output.csv")
            st.write("### Crawled Data:")
            st.dataframe(df)
        else:
            st.error("❌ No results found. Try crawling a different website.")

    # FAQ Section
    st.markdown("---")
    st.subheader(" Frequently Asked Questions (FAQ)")
    
    with st.expander("What does Crawl Depth mean?"):
        st.write("""
        **Crawl Depth** determines how deep the crawler goes into the website.  
        - **1** = Only the homepage  
        - **2** = Homepage + first-level links  
        - **3+** = Deeper levels (more pages, but slower)  
        Higher depth = More pages, but takes longer.
        """)

    with st.expander(" What is Download Delay?"):
        st.write("""
        **Download Delay** is the wait time between requests to the same website.  
        - **Lower delay (0-1s) = Faster crawling** but might get blocked.  
        - **Higher delay (2-5s) = Slower but safer** (reduces risk of bans).  
        Recommended: 0.5s (default).
        """)

    with st.expander(" What does Concurrent Requests do?"):
        st.write("""
        This controls how many pages the crawler processes at the same time.  
        - **Higher (8-16)** = Faster crawling, but may overload the site.  
        - **Lower (1-4)** = Slower, but safer.  
        Default: **8** (Balanced speed).
        """)

    with st.expander(" Should I enable JavaScript Rendering?"):
        st.write("""
        Some websites load content using JavaScript (JS).  
        - **Enable this if the site uses JS for important content.**  
        - **Disabling it makes crawling faster** (recommended for most sites).  
        **Downside:** Slower crawling if enabled.
        """)

if __name__ == "__main__":
    main()
