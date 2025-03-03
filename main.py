import subprocess
import sys
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("main.log")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

def run_crawler(url, depth, delay, concurrency, js_rendering):
    """
    Spawns a new Python process to run crawl.py with custom parameters.
    """
    python_executable = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), "crawl.py")
    args = [
        python_executable,
        script_path,
        url,
        str(depth),
        str(delay),
        str(concurrency),
        "True" if js_rendering else "False"
    ]
    try:
        subprocess.run(args, check=True)
        logger.info(f"Crawler executed successfully for URL: {url}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Crawler process failed: {e}")
