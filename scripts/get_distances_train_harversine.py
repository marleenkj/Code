import pandas as pd
from src.distance import get_haversine_distance, get_distance_aws
from loguru import logger
import boto3
import itertools

# To change based on dataset
dataset_name = 'sql_poc1'
client = boto3.client('location')

project_path = 's3://sfgdata/projects/sustainable-transport'
start_geolocation_filepath = f'{project_path}/processed/df_shipper_geolocation_aws_modified.csv' #Unique shipper
end_geolocation_filepath = f'{project_path}/processed/{dataset_name}_geolocation.csv' #Unique clients
terminals_filepath = f'{project_path}/raw/Terminals_France.xlsx' #Unique terminals
routes_filepath = f'{project_path}/processed/{dataset_name}_routes.csv' #Unique routes

if __name__ == '__main__':
    # Import data
    # datasets need to have column Latitude and Longitude
    logger.info('Data Import started')
    df_receiver = pd.read_csv(end_geolocation_filepath, dtype={'Zip': str}).dropna(subset=['Latitude']).rename(
        columns={"Longitude": "Receiver longitude", "Latitude": "Receiver latitude"})
    df_shipper = pd.read_csv(start_geolocation_filepath, dtype={'Zip': str}).rename(
        columns={"Longitude": "Shipper longitude", "Latitude": "Shipper latitude"})
    df_routes = pd.read_csv(routes_filepath, dtype={'Zip': str})
    df_routes = df_routes[df_routes['Country code']== 'FR']
    df_shipper = df_shipper[df_shipper['Country code']== 'FR']
    df_receiver = df_receiver[df_receiver['Country code'] == 'FR']

    # Import terminals
    df_terminal = pd.read_excel(terminals_filepath)
    df_terminal = df_terminal[(df_terminal['country'] == 'France')].reset_index(drop=True).reset_index(names='id')
    logger.success('Data import done')

    # test
    df_receiver = df_receiver.head(100)

    # Create key column for cross join
    df_terminal['key'] = 1

    # DC-T routes:
    # Create all dc-terminal routes and get DC-T distance
    logger.info(f'DC-Terminal routes started')
    df_shipper['key'] = 1
    df_dc_terminal = pd.merge(df_shipper, df_terminal, on='key').drop("key", 1).rename(
        columns={"latitude": "Receiver latitude", "longitude": "Receiver longitude"})
    df_dc_terminal['Distance DC-T'] = df_dc_terminal.apply(
        lambda x: get_haversine_distance(x, "Shipper", "Receiver"), axis=1)

    # Get closest DC-T terminals
    df_dct = df_dc_terminal.iloc[df_dc_terminal.groupby(
        ['DC code'])['Distance DC-T'].idxmin().reset_index()['Distance DC-T'].to_list()]
    df_dct = df_dct.rename({
        'Receiver latitude': 'DC-T terminal latitude',
        'Receiver longitude': 'DC-T terminal longitude',
        'id': 'DC-T terminal id'}, axis=1)
    df_dct['Distance DC-T harversine'] = df_dct['Distance DC-T']
    df_dct['Distance DC-T'] = df_dct.apply(
            lambda x: get_distance_aws(x, client, "Shipper", "DC-T terminal"), axis=1)
    df_dct = df_dct.rename({'Address': 'Shipper address', 'City': 'Shipper city', 'Zip': 'Shipper zip', 'Country': 'Shipper country', 'Country code': 'Shipper country code'}, axis = 1)

    logger.success(f'Distances for clostest DC-T terminals calculated')

    # T-C routes:
    # Create all terminal-client routes and get T-C distance
    logger.info(f'Terminal-Client Routes started')
    df_receiver['key'] = 1
    df_terminal_receiver = pd.merge(df_receiver, df_terminal, on='key').drop("key", 1).rename(
        columns={"latitude": "Shipper latitude", "longitude": "Shipper longitude"})
    df_terminal_receiver['Distance T-C'] = df_terminal_receiver.apply(
        lambda x: get_haversine_distance(x, "Shipper", "Receiver"), axis=1)

    # Get closest T-C terminals
    df_tc = df_terminal_receiver.iloc[df_terminal_receiver.groupby(['Receiver longitude', 'Receiver latitude'])[
        'Distance T-C'].idxmin().reset_index()['Distance T-C'].to_list()]
    df_tc = df_tc.rename({
        'Shipper latitude': 'T-C terminal latitude',
        'Shipper longitude': 'T-C terminal longitude',
        'id': 'T-C terminal id'}, axis=1)
    df_tc['Distance T-C harversine'] = df_tc['Distance T-C']
    logger.success(f'Closest T-C terminals identified')
    df_tc['Distance T-C'] = df_tc.apply(lambda x: get_distance_aws(x, client, "T-C terminal", "Receiver"), axis=1)
    logger.success(f'Distances for clostest DC-T terminals calculated')

    # Merge routes, closest T-C terminals, and closest DC-T terminals
    df = df_routes.merge(df_dct, on = ['DC code'], how = 'left')
    df = df.merge(df_tc, on = ['Address','City', 'Zip', 'Country', 'Country code'], how = 'left')
    df = df.dropna(subset = ['T-C terminal latitude'])

    # Get T-T distance
    logger.info(f'Terminal-Terminal routes started')
    df['Distance T-T'] = df.apply(
        lambda x: get_haversine_distance(x, "DC-T terminal", "T-C terminal"), axis=1)
    logger.success(f'Harversine T-T distance calculated')
    
    # Get total distance
    df['Distance total'] = df['Distance T-C'] + \
        df['Distance DC-T']+df['Distance T-T']
    
    df['Distance direct'] = df.apply(
        lambda x:get_distance_aws(x, client, "Shipper", "Receiver"), axis=1)
    
    '''
    df = df.rename({'Address': 'Receiver address', 
                    'City': 'Receiver city', 
                    'Zip': 'Receiver zip', 
                    'Country': 'Receiver country', 
                    'Country code': 'Receiver country code',
                    'name_x': 'DC-T name',
                    'street_x': 'DC-T street', 
                    'city_x': 'DC-T city', 
                    'country_x': 'DC-T country',
                    'name_y': 'T-C name',
                    'street_y': 'T-C street', 
                    'city_y': 'T-C city', 
                    'country_y': 'T-C country'
                    }, axis = 1)
    '''

    # Save dataset to s3
    df.to_csv(
        f'{project_path}/processed/{dataset_name}_train_distances_harversine.csv', index=False)
    logger.success(f'Perparation done and dataset saved to S3')

