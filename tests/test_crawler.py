import pytest
from scrapy.http import HtmlResponse, Request
import sys
import os

# Add the project root to the Python path
# This is necessary for the test runner to find the 'crawler' and 'items' modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crawler import SEOCrawler
from items import PageItem


# Get the absolute path to the directory of the current script
# This is to ensure that the test can find the sample.html file
# regardless of where pytest is run from.
TEST_DIR = os.path.dirname(os.path.abspath(__file__))

@pytest.fixture
def spider():
    """Pytest fixture to initialize the SEOCrawler."""
    return SEOCrawler(start_url="https://example.com")

@pytest.fixture
def sample_html_response():
    """Pytest fixture to create a Scrapy HtmlResponse from the sample HTML file."""
    sample_html_path = os.path.join(TEST_DIR, "sample.html")
    with open(sample_html_path, "r") as f:
        html_content = f.read()
    
    # The URL is important for the spider to resolve relative links
    request = Request(url="https://example.com")
    response = HtmlResponse(
        url="https://example.com",
        body=html_content,
        encoding='utf-8',
        headers={'Content-Type': 'text/html'},
        request=request
    )
    return response

def test_parse_seo_data(spider, sample_html_response):
    """
    Test that the spider correctly parses all the SEO data from the sample HTML.
    """
    # The parse method is a generator, so we consume it and get the first item
    results = list(spider.parse(sample_html_response))
    
    # We expect the first yielded item to be a PageItem
    item = results[0]
    assert isinstance(item, PageItem)

    # Assertions for each field
    assert item['url'] == "https://example.com"
    assert item['status_code'] == 200
    assert item['title'] == "Sample Page Title"
    assert item['meta_description'] == "This is a sample meta description."
    assert item['canonical'] == "https://example.com/canonical-url"
    assert item['h1_tags'] == "Main Heading 1; Another H1"
    assert item['h2_tags'] == "Sub Heading 2"
    assert item['h3_tags'] == "Sub Heading 3"
    assert item['image_alts'] == "Sample Image Alt Text"
    assert 'Sample Site' in item['json_ld']

def test_follow_internal_links(spider, sample_html_response):
    """
    Test that the spider follows internal links and ignores external ones.
    """
    results = list(spider.parse(sample_html_response))
    
    # Filter for yielded Request objects (the links to follow)
    requests = [r for r in results if isinstance(r, Request)]
    
    # There are two internal links in the sample HTML
    assert len(requests) == 2
    
    followed_urls = {req.url for req in requests}
    assert "https://example.com/internal-link" in followed_urls
    assert "https://example.com/another-internal-link" in followed_urls
    
    # Ensure the external link is not followed
    assert "https://external.com/external-link" not in followed_urls

@pytest.fixture
def sample_js_html_response():
    """Pytest fixture to create a Scrapy HtmlResponse from the JS sample HTML file."""
    sample_html_path = os.path.join(TEST_DIR, "sample_js.html")
    with open(sample_html_path, "r") as f:
        html_content = f.read()
    
    request = Request(url="https://example.com/js")
    response = HtmlResponse(
        url="https://example.com/js",
        body=html_content,
        encoding='utf-8',
        headers={'Content-Type': 'text/html'},
        request=request
    )
    return response

def test_parse_js_rendered_content(mocker, sample_js_html_response):
    """
    Test that the spider correctly parses JavaScript-rendered content
    when the js_rendering flag is enabled.
    """
    # Mock the selenium webdriver
    mock_driver = mocker.MagicMock()
    # When the driver gets a URL, have it return the page source *after* JS execution
    final_html = """
    <html><head>
        <meta charset="UTF-8">
        <title>JS Rendered Page</title>
    </head>
    <body>
        <h1>Static Content</h1>
        <div id="dynamic-content"><h2>This H2 was added by JavaScript</h2></div>

        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const container = document.getElementById('dynamic-content');
                const h2 = document.createElement('h2');
                h2.textContent = 'This H2 was added by JavaScript';
                container.appendChild(h2);
            });
        </script>
    
    </body></html>"""
    mock_driver.page_source = final_html
    
    # Mock the webdriver.Chrome class to return our mock_driver instance
    mocker.patch('selenium.webdriver.Chrome', return_value=mock_driver)

    # Initialize the spider with JS rendering enabled
    spider = SEOCrawler(start_url="https://example.com/js", js_rendering="True")
    
    # The parse method is a generator, so we consume it and get the first item
    results = list(spider.parse(sample_js_html_response))
    item = results[0]

    # Assert that the dynamically added H2 tag is found
    assert item['h2_tags'] == 'This H2 was added by JavaScript'
    
    # Ensure the driver was used
    mock_driver.get.assert_called_once_with("https://example.com/js")
