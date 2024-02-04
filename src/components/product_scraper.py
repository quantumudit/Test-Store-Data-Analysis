"""
This module contains the ProductInfoScraper class, which is used for scraping
product information from websites. It uses HTTP requests to retrieve the
HTML content of product pages, and then uses the selectolax library to
parse the HTML and extract the desired information. The scraped data is then
stored in a CSV file.
"""
import random
import time
from dataclasses import asdict
from datetime import datetime
from os.path import exists, normpath

import httpx
from fake_useragent import UserAgent
from selectolax.parser import HTMLParser

from src.constants import CONFIGS, ProductInfo
from src.exception import CustomException
from src.logger import logger
from src.utils.basic_utils import read_csv, read_yaml, write_to_csv


class ProductInfoScraper:
    """
    The ProductInfoScraper class is responsible for scraping product
    information from websites. It provides methods for retrieving product
    details from a given URL, as well as for scraping multiple products
    from a list of URLs. The class uses various libraries and modules, such
    as httpx, fake_useragent, and selectolax, to perform the scraping tasks.
    The scraped data is stored in a CSV file.
    """

    def __init__(self):
        # Read the configuration files
        self.configs = read_yaml(CONFIGS).web_scraping

        # Inputs
        self.timeout = self.configs.timeout
        self.clear = self.configs.clear_data
        self.links_data_path = normpath(self.configs.links_data_path)

        # Output file paths
        self.scraped_data_path = normpath(self.configs.scraped_data_path)

        # Clear the files if exists
        if self.clear:
            if exists(self.scraped_data_path):
                with open(self.scraped_data_path, "w", encoding="utf-8") as f:
                    f.truncate()
                logger.info("Cleared existing contents from %s",
                            self.scraped_data_path)

    def get_product_details(self, product_url: str, headers: str) -> None:
        """
        Fetches and parses the product details from a given product URL.

        Args:
            product_url (str): The URL of the product to be scraped.
            headers (str): The headers to be used in the HTTP request.

        Raises:
            CustomException: If there is an error during the HTTP request
            or parsing the response.

        Returns:
            None: Writes the scraped product details to a CSV file.
        """
        response = httpx.get(
            product_url, headers=headers, timeout=self.timeout)
        try:
            logger.info("Request responded with the status code: %s",
                        response.status_code)

            # Parse the HTML content
            html = HTMLParser(response.text)

            # Create lambda function for simplification
            def fetch(css_selector, fetch_type="first"):
                if fetch_type == "first":
                    if html.css_first(css_selector) is not None:
                        result = html.css_first(css_selector).text(strip=True)
                    else:
                        result = ""
                elif fetch_type == "link":
                    if html.css_first(css_selector) is not None:
                        result = html.css_first(css_selector).attrs["href"]
                    else:
                        result = ""
                elif fetch_type == "all":
                    result = html.css(css_selector)
                elif fetch_type == "f_obj":
                    result = html.css_first(css_selector)
                else:
                    result = None
                return result

            # Get additional details of the product
            more_info = fetch("div#tab-additional_information tr", "all")

            if more_info is not None:
                additional_details = {
                    info.css_first("th").text(strip=True) if info.css_first(
                        "th") is not None else "-":
                    info.css_first("td p").text(strip=True) if info.css_first(
                        "td p") is not None else ""
                    for info in more_info
                }

            # Get the product details in data class
            product_details = ProductInfo(
                title=fetch("h1.product_title"),
                price=fetch("p.price bdi", "all")[-1].text(strip=True),
                in_stocks=fetch("p.stock") if fetch(
                    "p.stock", "f_obj") is not None else "",
                sku=fetch("span.sku"),
                category=fetch("a[rel='tag']"),
                description="\n".join(
                    [
                        ele.text(strip=True) for ele in
                        fetch("div#tab-description p", "all")
                    ]
                ),
                product_image_link=fetch(
                    "div.woocommerce-product-gallery__wrapper a", "link"),
                additional_info=additional_details,
                product_link=product_url,
                scrape_ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            # Write scraped info into CSV file
            write_to_csv(self.scraped_data_path, asdict(product_details))

        except Exception as e:
            logger.error(CustomException(e))
            raise CustomException(e) from e

    def scrape_products(self) -> None:
        """
        Reads a CSV file with product URLs and scrapes each product's details.

        The function generates random headers and sleep times between requests
        to avoid being blocked by the server. The scraped product details are
        written to a CSV file. The function logs the start and end time of the
        scraping process, as well as the total time taken.

        Returns:
            None
        """
        # Read the CSV file with product links
        product_links = read_csv(self.links_data_path)

        # Create user agent object
        user_agent = UserAgent()

        # Scraping start time
        start_time = time.time()

        # Start scraping product in loop
        logger.info("Product scraping started")
        for idx, link in enumerate(product_links):
            product_url = link["product_url"]

            # Generate random headers
            headers = {
                "User-Agent": user_agent.random,
                "accept-language": "en-US"}

            # Generate random sleep time
            sleep_sec = random.randint(1, 3)

            # write product data to csv file
            self.get_product_details(product_url, headers)
            logger.info("%s products scraped", idx+1)
            time.sleep(sleep_sec)

        # Scraping end time
        end_time = time.time()

        # Scraping time interval
        time_diff = round(end_time - start_time)

        # Log time taken for scraping
        logger.info("Time taken for scraping: %s seconds",
                    f"{time_diff:.2f}")
        logger.info("All product url scraped")
