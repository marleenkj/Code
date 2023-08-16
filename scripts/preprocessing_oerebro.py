import pandas as pd
from src.preprocessing import data_preprocessing_oerebro
from loguru import logger
import boto3
import s3fs
import json

project_path = 's3://sfgdata/projects/sustainable-transport'
dataset_name = 'oerebro_nshift_2022'
dict_column_names = 'nshift_names'

client = boto3.client('location')
s3 = s3fs.S3FileSystem()

if __name__ == '__main__':
    logger.info('Import started')
    # Import new data and dictionary
    df = pd.read_csv(f'{project_path}/raw/Shipment Report RDC Örebro 2022-01-01 - 2022-12-31.csv', delimiter = ';', decimal = '.')
    with s3.open(f'{project_path}/external/{dict_column_names}.json', 'r') as fp:
        dict_names = json.load(fp)

    # Data Cleaning
    logger.info('Preprocessing has started')
    df = data_preprocessing_oerebro(df, dict_names)

    logger.info(df.columns)

    # Get routes with AWS and store in S3
    df = df[['DC code', 'Client name', 'Address', 'City', 'Zip','Country', 'Country code']].drop_duplicates().reset_index(drop=True)
    logger.info(f'Unique Routes: {df.shape}')
    df.to_csv(f'{project_path}/processed/{dataset_name}_routes.csv', index=False)

    logger.success('Preprocessing has finished and file saved')