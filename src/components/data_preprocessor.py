"""
This module contains the DataPreprocessor class, which is responsible for
preprocessing data. It reads the configuration files, performs necessary
data transformations, and saves the cleaned dataset.
"""

import json
from os.path import dirname, normpath

import pandas as pd

from src.constants import CONFIGS
from src.exception import CustomException
from src.logger import logger
from src.utils.basic_utils import create_directories, read_yaml


class DataPreprocessor:
    """
    This class is responsible for preprocessing data.
    It has methods to clean the data and preprocess the dataset.
    It also handles exceptions and logs the necessary information.
    """

    def __init__(self):
        # Read the configuration files
        self.configs = read_yaml(CONFIGS).data_preprocessing

        # Inputs
        self.scraped_data_path = normpath(self.configs.scraped_data_path)

        # Output file paths
        self.processed_data_path = normpath(self.configs.processed_data_path)

    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        This method performs data cleaning and transformation
        on the input DataFrame.

        Args:
            df (pd.DataFrame): The input DataFrame to be cleaned.

        Returns:
            pd.DataFrame: The cleaned DataFrame.
        """

        # Filter out the test product
        df = df[df["sku"] != "test-product"]

        # Replacement of unnecessary texts
        df.loc[:, "price"] = df["price"].str.replace("£", "")
        df.loc[:, "in_stocks"] = df["in_stocks"].str.replace(" in stock", "")
        df.loc[:, "category"] = df["category"].str.replace("|", " ")

        # Data type change
        df = df.astype({
            "price": "float32",
            "in_stocks": "float32",
            "scrape_ts": "datetime64[ns]"})

        # Expanding the additional info of product as new columns
        info_list = []
        for _, row in df[["sku", "additional_info"]].iterrows():
            additional_info_dict = json.loads(
                row["additional_info"].replace("'", "\""))
            additional_info_dict["sku"] = row["sku"]
            info_list.append(additional_info_dict)

        info_df = pd.DataFrame(info_list)
        info_df.columns = map(lambda x: x.lower(), info_df.columns)

        # Rearranged column list for final dataframe
        rearranged_col_list = [
            "sku", "title", "price_in_pounds",
            "category", "description", "in_stocks",
            "product_image_link", "size", "color",
            "activity", "gender", "material", "pattern",
            "strap", "style", "product_link", "scrape_ts"
        ]

        # Basic transformation for creating final dataframe
        final_df = (
            pd.merge(df, info_df, on="sku", how="inner")
            .drop(columns="additional_info")
            .rename(columns={"price": "price_in_pounds"})
            .reindex(columns=rearranged_col_list)
            .drop_duplicates(subset=["sku"])
            .reset_index(drop=True)
        )
        return final_df

    def preprocess_dataset(self) -> None:
        """
        This method preprocesses the dataset by performing necessary
        data transformation and saving the cleaned data file.

        Raises:
            CustomException: If an error occurs during the preprocessing.
        """
        try:
            # Read the scraped dataset
            scraped_df = pd.read_csv(self.scraped_data_path)

            # Perform data transformation
            logger.info("performing necessary data transformation")
            clean_df = self.clean_data(scraped_df)
            logger.info("data transformation completed")

            # create save directory if not exists
            create_directories([dirname(self.processed_data_path)])

            # Save the cleaned data file
            clean_df.to_csv(self.processed_data_path,
                            index=False, header=True, encoding="utf-8")

            logger.info("clean dataset saved at: %s", self.processed_data_path)
        except Exception as e:
            logger.error(CustomException(e))
            raise CustomException(e) from e
