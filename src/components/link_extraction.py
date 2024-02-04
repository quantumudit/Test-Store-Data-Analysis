"""
This module contains the ProductLinkExtraction class, which is responsible
for extracting product links from a website. It uses HTTP requests,
HTML parsing, and file I/O operations to scrape the website and save the
extracted links to a CSV file.
"""
import random
import time
from os.path import dirname, exists, normpath

import httpx
from fake_useragent import UserAgent
from selectolax.parser import HTMLParser

from src.constants import CONFIGS
from src.exception import CustomException
from src.logger import logger
from src.utils.basic_utils import create_directories, read_yaml, write_to_csv


class ProductLinkExtraction:
    """
    This class is responsible for extracting product links from a website.
    It provides methods for retrieving the HTML content of a page, parsing
    the HTML, and extracting the product links. The extracted links are then
    saved to a CSV file.

    Methods
    -------
    - get_item_urls(): Retrieves the HTML content of a page, parses it, and
        extracts the product links. Returns the parsed HTML content.
    - get_all_product_links(): Recursively extracts all product links from the
        website by navigating through the pages. Saves the links to the
        output CSV file.
    - scrape_product_links(): Executes the web scraping process by calling the
        necessary methods. Measures the time taken for scraping and logs
        the result.
    """

    def __init__(self):
        # Read the configuration files
        self.configs = read_yaml(CONFIGS).web_scraping

        # Inputs
        self.root_url = self.configs.root_url
        self.timeout = self.configs.timeout
        self.clear = self.configs.clear_data

        # Output file paths
        self.links_data_path = normpath(self.configs.links_data_path)

        # Clear the files if exists
        if self.clear:
            if exists(self.links_data_path):
                with open(self.links_data_path, "w", encoding="utf-8") as f:
                    f.truncate()
                logger.info("Cleared existing contents from %s",
                            self.links_data_path)

    def get_item_urls(self, pg_url: str, head: dict, pg_no: int) -> HTMLParser:
        """
        Get the URLs of all items on a page.

        Args:
            pg_url (str): The URL of the page.
            head (dict): The headers for the HTTP request.
            pg_no (int): The page number.

        Raises:
            CustomException: If there is an error in the request.

        Returns:
            HTMLParser: The parsed HTML content of the page.
        """
        response = httpx.get(pg_url, headers=head, timeout=self.timeout)
        try:
            logger.info("Request responded with the status code: %s",
                        response.status_code)

            # Parse the HTML content
            parsed_html = HTMLParser(response.text)

            # Get the products
            all_products = parsed_html.css("ul.products li")
            logger.info("Total products in the page: %s", len(all_products))

            for product in all_products:
                product_url = product.css_first("a").attrs["href"]
                data = {
                    "page_number": pg_no,
                    "page_url": pg_url,
                    "product_url": product_url
                }

                write_to_csv(self.links_data_path, data)

            # Return the parsed HTML content
            return parsed_html
        except Exception as e:
            logger.error(CustomException(e))
            raise CustomException(e) from e

    def get_all_product_links(self, page_url: str, page_num: int = 1) -> None:
        """
        Get all the product links on a page.

        Args:
            page_url (str): The URL of the page.
            page_num (int, optional): The page number. Defaults to 1.
        """
        # Generate random headers
        user_agent = UserAgent()
        headers = {
            "User-Agent": user_agent.random,
            "accept-language": "en-US"}

        # Generate random sleep time
        sleep_sec = random.randint(1, 5)

        # Write the product info and get the page HTML in variable
        content = self.get_item_urls(page_url, headers, page_num)
        logger.info("Page-%s product links extracted", page_num)
        time.sleep(sleep_sec)

        # Increase the page number
        page_num += 1

        # recursively call to extract all product links
        next_page_element = content.css_first("ul.page-numbers li a.next")

        if next_page_element is not None:
            next_page_url = next_page_element.attrs["href"]
            self.get_all_product_links(next_page_url, page_num)

    def scrape_product_links(self) -> None:
        """
        Scrape all the product links on the website.
        """
        # create save directory if not exists
        create_directories([dirname(self.links_data_path)])

        start_time = time.time()
        self.get_all_product_links(page_url=self.root_url)
        end_time = time.time()

        time_diff = round(end_time - start_time, 2)

        logger.info("Time taken for scraping: %s seconds",
                    f"{time_diff:.2f}")
        logger.info("All product url scraped")
