"""
This module contains various constants that can be used in python scripts.
It contains the following:

Constants:
- CONFIGS: The path to the configuration file.

Dataclass:
- ProductInfo: A dataclass for storing product information.
"""

from dataclasses import dataclass
from os.path import normpath

# Configuration file paths
CONFIGS = normpath("conf/configs.yaml")


@dataclass(frozen=True)
class ProductInfo:
    """
    A dataclass for storing product information.
    Attributes:
        title (str): The title of the product.
        price (str): The price of the product.
        in_stocks (str): The availability of the product.
        sku (str): The SKU (stock keeping unit) of the product.
        category (str): The category of the product.
        description (str): The description of the product.
        additional_info (dict): Additional information about the product.
    """
    title: str
    price: str
    in_stocks: str
    sku: str
    category: str
    description: str
    product_image_link: str
    additional_info: dict
    product_link: str
    scrape_ts: str
