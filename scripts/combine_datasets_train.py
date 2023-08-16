import pandas as pd
from loguru import logger
import json
from src.preprocessing import data_preprocessing_bridge, merge_for_app
import s3fs

project_path = 's3://sfgdata/projects/sustainable-transport'
dataset_name = 'sql_poc2'

if __name__ == '__main__':
    logger.info('Import started')
    
    # Data import
    start_geolocation_filepath = f'{project_path}/processed/df_shipper_geolocation_aws_modified.csv'
    end_geolocation_filepath = f'{project_path}/processed/{dataset_name}_geolocation.csv'
    routes_filepath = f'{project_path}/processed/{dataset_name}_routes.csv'
    dict_column_names = 'bridge_names'

    df_train = pd.read_csv(f'{project_path}/processed/{dataset_name}_distances.csv')
    df_raw = pd.read_csv(f'{project_path}/raw/{dataset_name}.csv')
    
    # Dict for column names
    s3 = s3fs.S3FileSystem()
    with s3.open(f'{project_path}/external/{dict_column_names}.json', 'r') as fp:
        dict_names = json.load(fp)
    dict_names['Shipment id'] = 'TKNUM'

    logger.info('Import done')

    # Cleaning df_raw
    df_raw = data_preprocessing_bridge(df_raw, dict_names)

    # Merging datasets to have all information in one
    data = merge_for_app(df_raw, df_shipper, df_receiver, df_distances)

    data = data.rename(columns = {'Distance': 'Distance (km)'})

    # Add co2 emissions
    emission_factor = 100 #g/tkm conventional truck average
    data['Co2 emissions'] = emission_factor*data['Distance (km)']*(data['Sender weight (kg)']/1000)
    
    # Save to s3
    data.to_csv(f'{project_path}/processed/sql_poc3.csv', index=False)

    logger.info('New dataset generated and stored')
