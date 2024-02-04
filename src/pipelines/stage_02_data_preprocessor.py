"""
This module contains the DataPreprocessingPipeline class
which is responsible for preprocessing the dataset.
"""
from src.components.data_preprocessor import DataPreprocessor
from src.exception import CustomException
from src.logger import logger


class DataPreprocessingPipeline:
    """
    This class represents a pipeline for data preprocessing.
    It uses the DataPreprocessor class to preprocess the dataset.
    """

    def __init__(self):
        pass

    def main(self):
        """
        This method starts the data preprocessing process. It logs the
        start and end of the process, and handles any exceptions that occur.

        Raises:
            CustomException: If an error occurs during the
            data preprocessing process.
        """
        try:
            logger.info("Data Preprocessing started")
            data_preprocessor = DataPreprocessor()
            data_preprocessor.preprocess_dataset()
            logger.info("Data preprocessing completed successfully")
        except Exception as excp:
            logger.error(CustomException(excp))
            raise CustomException(excp) from excp


if __name__ == "__main__":
    STAGE_NAME = "Data Preprocessing Stage"

    try:
        logger.info(">>>>>> %s started <<<<<<", STAGE_NAME)
        obj = DataPreprocessingPipeline()
        obj.main()
        logger.info(">>>>>> %s completed <<<<<<\n\nx==========x", STAGE_NAME)
    except Exception as e:
        logger.error(CustomException(e))
        raise CustomException(e) from e
