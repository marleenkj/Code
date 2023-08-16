import pandas as pd
from src.geolocation import get_lon_lat_aws
from loguru import logger
import boto3

project_path = 's3://sfgdata/projects/sustainable-transport'
dataset_name = 'oerebro_nshift_2022'

client = boto3.client('location')

if __name__ == '__main__':
    # to save logs in log file add
    logger.add('logfile_long_lat.log')

    # Import new data
    df = pd.read_csv(f'{project_path}/processed/{dataset_name}_routes.csv')
    # Get unique clients
    df = df[['Address', 'City', 'Zip', 'Country', 'Country code']].drop_duplicates().reset_index(drop=True)
    logger.info(f'Unique clients: {df.shape}')

    # get long, lat
    logger.info(f'Retrieving lon/lat started')
    df[['Longitude', 'Latitude']] = df.apply(
        lambda x: get_lon_lat_aws(x, client), axis=1, result_type='expand')

    # save to s3
    df.to_csv(f'{project_path}/processed/{dataset_name}_geolocation.csv', index=False)
    logger.success(f'Getting long lat done')