from __future__ import annotations

import json
import os

from duckduckgo_search import ddg

from selenium import webdriver
from processing.html import extract_hyperlinks, format_hyperlinks
import processing.text as summary
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.common import exceptions
import logging
from pathlib import Path

def google(query: str):
    if os.getenv("GOOGLE_API_KEY"):
        return(google_official_search(query))
    else: 
        return(google_search(query))

def google_search(query: str, num_results: int = 8) -> str:
    """Return the results of a google search

    Args:
        query (str): The search query.
        num_results (int): The number of results to return.

    Returns:
        str: The results of the search.
    """
    search_results = []
    if not query:
        return json.dumps(search_results)

    results = ddg(query, max_results=num_results)
    if not results:
        return json.dumps(search_results)

    for j in results:
        search_results.append(j)

    return json.dumps(search_results, ensure_ascii=False, indent=4)


def google_official_search(query: str, num_results: int = 8) -> str | list[str]:
    """Return the results of a google search using the official Google API

    Args:
        query (str): The search query.
        num_results (int): The number of results to return.

    Returns:
        str: The results of the search.
    """

    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    try:
        # Get the Google API key and Custom Search Engine ID from the config file
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
        CUSTOM_SEARCH_ENGINE_ID = os.getenv("CUSTOM_SEARCH_ENGINE_ID", "")

        # Initialize the Custom Search API service
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)

        # Send the search query and retrieve the results
        result = (
            service.cse()
            .list(q=query, cx=CUSTOM_SEARCH_ENGINE_ID, num=num_results)
            .execute()
        )

        # Extract the search result items from the response
        search_results = result.get("items", [])

        # Create a list of only the URLs from the search results
        search_results_links = [item["link"] for item in search_results]

    except HttpError as e:
        # Handle errors in the API call
        error_details = json.loads(e.content.decode())

        # Check if the error is related to an invalid or missing API key
        if error_details.get("error", {}).get(
            "code"
        ) == 403 and "invalid API key" in error_details.get("error", {}).get(
            "message", ""
        ):
            return "Error: The provided Google API key is invalid or missing."
        else:
            return f"Error: {e}"

    # Return the list of search result URLs
    return search_results_links

FILE_DIR = Path(__file__).parent.parent

browser = None

def get_browser_instance() -> WebDriver:
    """Create or retrieve the browser instance."""
    global browser
    if not browser:
        logging.getLogger("selenium").setLevel(logging.CRITICAL)

        options_available = {'chrome': ChromeOptions, 'safari': SafariOptions, 'firefox': FirefoxOptions}
        options = options_available[os.getenv("SELENIUM_WEB_BROWSER", "")]()
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
        )
        
        if os.getenv("HIDE_BROWSER", "False") == "True":
            options.add_argument("--headless")  # Add headless argument to hide the browser

        if os.getenv("SELENIUM_WEB_BROWSER", "") == "firefox":
            browser = webdriver.Firefox(
                executable_path=GeckoDriverManager().install(), options=options
            )
        elif os.getenv("SELENIUM_WEB_BROWSER", "") == "safari":
            browser = webdriver.Safari(options=options)
        else:
            browser = webdriver.Chrome(
                executable_path=ChromeDriverManager().install(), options=options
            )

    return browser


def browse_website(url: str, question: str = "") -> tuple[str, WebDriver]:
    """Browse a website and return the answer and links to the user

    Args:
        url (str): The url of the website to browse
        question (str): The question asked by the user

    Returns:
        Tuple[str, WebDriver]: The answer and links to the user and the webdriver
    """
    try:
        driver, text = scrape_text_with_selenium(url)
    except(exceptions.InvalidArgumentException):
        return("COMMAND_ERROR: Invalid URL")
    add_header(driver)
    summary_text = summary.summarize_text(url, text, question, driver)
    # links = scrape_links_with_selenium(driver, url)

    # # Limit links to 5
    # if len(links) > 5:
    #     links = links[:5]

    if os.getenv("HIDE_BROWSER", "False") == "False":
        close_browser(driver)

    # return f"Answer gathered from website: {summary_text} \n \n Links: {links}", driver
    return f"Answer gathered from website: {summary_text}"

def scrape_text_with_selenium(url: str) -> tuple[WebDriver, str]:
    """Scrape text from a website using selenium

    Args:
        url (str): The url of the website to scrape

    Returns:
        Tuple[WebDriver, str]: The webdriver and the text scraped from the website
    """
    driver = get_browser_instance()
    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Get the HTML content directly from the browser's DOM
    page_source = driver.execute_script("return document.body.outerHTML;")
    soup = BeautifulSoup(page_source, "html.parser")

    for script in soup(["script", "style"]):
        script.extract()

    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)
    return driver, text


def scrape_links_with_selenium(driver: WebDriver, url: str) -> list[str]:
    """Scrape links from a website using selenium

    Args:
        driver (WebDriver): The webdriver to use to scrape the links

    Returns:
        List[str]: The links scraped from the website
    """
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    for script in soup(["script", "style"]):
        script.extract()

    hyperlinks = extract_hyperlinks(soup, url)

    return format_hyperlinks(hyperlinks)


def add_header(driver: WebDriver) -> None:
    """Add a header to the website

    Args:
        driver (WebDriver): The webdriver to use to add the header

    Returns:
        None
    """
    driver.execute_script(open(f"{FILE_DIR}/js/overlay.js", "r").read())


def close_browser(driver: WebDriver) -> None:
    """Close the browser

    Args:
        driver (WebDriver): The webdriver to close

    Returns:
        None
    """
    global browser
    if browser:
        browser.quit()
        browser = None
