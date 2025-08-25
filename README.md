# Growling Cat - SEO Crawler  🐈‍⬛

Growling Cat is a open-source SEO crawler designed as a cross-platform alternative to Screaming Frog. It efficiently scrapes and analyzes web pages, providing valuable insights into SEO elements, internal linking, and broken links.  

## Features  
- **SEO Data Extraction**: Fetches titles, meta descriptions, headings, images, and structured data.  
- **Crawl Depth Control**: Adjust the depth of internal link crawling.  
- **JavaScript Rendering (Optional)**: Uses Selenium for JavaScript-heavy pages.  
- **Broken Link Detection**: Identifies broken internal links.  
- **Customizable Settings**: Control concurrency, download delays, and rendering options.  

## Installation  
**1. Clone the repository**:  
```sh
   git clone git@github.com:Umair-khurshid/Growling-Cat.git
   cd Growling-Cat
   ```
**2. Install dependencies**:
  ```sh
pip install -r requirements.txt
````
**3. Run the Streamlit UI**:
```sh
streamlit run app.py
 ```
*You can also use the demo at: [Growling Cat](https://growlingcat.streamlit.app/)*

## Troubleshooting
Some websites have strong anti-scraping protections. If a crawl fails or returns no results, try the following:
- **Increase Download Delay**: In the "Advanced Settings," increase the download delay to 2-3 seconds to avoid being rate-limited.
- **Reduce Concurrency**: Lower the number of concurrent requests to 1 or 2.
- **Note**: Some sites may still be difficult to crawl even with these adjustments.

