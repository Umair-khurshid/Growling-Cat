import logging
import os
import subprocess
import sys

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("main.log")
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def run_crawler(url, depth, delay, concurrency, js_rendering):
    """
    Spawns a new Python process to run crawl.py with custom parameters.
    """
    python_executable = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), "run_crawl_process.py")

    args = [
        python_executable,
        script_path,
        url,
        str(depth),
        str(delay),
        str(concurrency),
        "True" if js_rendering else "False",
    ]

    try:
        subprocess.run(args, check=True)
        logger.info("Crawler executed successfully for URL: %s", url)
    except subprocess.CalledProcessError as error:
        logger.error("Crawler process failed: %s", error)
