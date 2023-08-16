import pandas as pd
from src.preprocessing import data_preprocessing_bridge
from loguru import logger
import boto3
import s3fs
import json

# here for oerebro dataset
project_path = 's3://sfgdata/projects/sustainable-transport'
dict_column_names = 'bridge_names'
dataset_name = 'sql_poc4'

client = boto3.client('location')
s3 = s3fs.S3FileSystem()

if __name__ == '__main__':
    logger.info('Preprocessing has started')
    # Import new data and dictionary
    df = pd.read_csv(f'{project_path}/raw/{dataset_name}.csv', low_memory=False)
    with s3.open(f'{project_path}/external/{dict_column_names}.json', 'r') as fp:
        dict_names = json.load(fp)
    df_ig_shipper = pd.read_csv(f'{project_path}/external/ig_shipper.csv')

    # Data Cleaning
    df = data_preprocessing_bridge(df, dict_names, df_ig_shipper)

    logger.info(df.columns)

    #df.to_csv(f'{project_path}/processed/{dataset_name}_cleaned.csv', index=False)

    # Get routes with AWS and store in S3
    df = df[['DC code', 'Client no', 'Client name','Address', 'City', 'Zip','Country', 'Country code']].drop_duplicates().reset_index(drop=True)
    logger.info(f'Unique Routes: {df.shape}')
    #df.to_csv(f'{project_path}/processed/{dataset_name}_routes.csv', index=False)
    logger.success(f'Preprocessing has finished and routes saved in file under {dataset_name}_routes.csv')
