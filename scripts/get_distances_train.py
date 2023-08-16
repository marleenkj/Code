import pandas as pd
from src.distance import get_distance_aws
from loguru import logger
import boto3
import itertools

# To change based on dataset
dataset_name = 'sql_poc1'
client = boto3.client('location')

project_path = 's3://sfgdata/projects/sustainable-transport'
start_geolocation_filepath = f'{project_path}/processed/df_shipper_geolocation_aws_modified.csv'
end_geolocation_filepath = f'{project_path}/processed/{dataset_name}_geolocation.csv'
terminals_filepath = f'{project_path}/raw/terminals_europe_V1.xlsx'
routes_filepath = f'{project_path}/processed/{dataset_name}_routes.csv'

if __name__ == '__main__':
    # Import data
    # datasets need to have column Latitude and Longitude
    logger.info('Data Import started')
    df_receiver = pd.read_csv(end_geolocation_filepath, dtype={'Zip': str}).dropna(subset=['Latitude']).rename(
        columns={"Longitude": "Receiver longitude", "Latitude": "Receiver latitude"})
    df_receiver = df_receiver[df_receiver['Country code']== 'FR'] # only for France for now
    df_shipper = pd.read_csv(start_geolocation_filepath, dtype={'Zip': str}).rename(
        columns={"Longitude": "Shipper longitude", "Latitude": "Shipper latitude"})
    df_shipper = df_shipper[df_shipper['Country code']=='FR'] # only for France for now
    df_routes = pd.read_csv(routes_filepath, dtype={'Zip': str})
    df_routes = df_routes[df_routes['Country code']=='FR'] # only for France for now

    # Import terminals
    df_terminal = pd.read_excel(terminals_filepath)
    df_terminal = df_terminal[(df_terminal['country'] == 'France') & (
        df_terminal['modes'] == 'Road, Rail')].reset_index(drop=True).reset_index(names='id')
    logger.success('Data import done')

    # Create key column for cross join
    df_shipper['key'] = 1
    df_terminal['key'] = 1
    df_receiver['key'] = 1

    # DC-T routes:
    # Create all dc-terminal routes and get DC-T distance
    logger.info(f'DC-Terminal routes started')
    df_dc_terminal = pd.merge(df_shipper, df_terminal, on='key').drop("key", 1).rename(
        columns={"latitude": "Receiver latitude", "longitude": "Receiver longitude"})
    df_dc_terminal['Distance DC-T'] = df_dc_terminal.apply(
            lambda x: get_distance_aws(x, client, "Shipper", "Receiver"), axis=1)

    # Get closest DC-T terminals
    df_dct = df_dc_terminal.iloc[df_dc_terminal.groupby(['DC code'])['Distance DC-T'].idxmax().reset_index()['Distance DC-T'].to_list()]
    df_dct = df_dct.rename({'Receiver latitude': 'DC-T terminal latitude',
                            'Receiver longitude': 'DC-T terminal longitude',
                            'id': 'DC-T terminal id'}, axis = 1)
    logger.success(f'Closest DC-T terminals identified')

    # T-C routes:
    # Create all terminal-client routes and get T-C distance
    logger.info(f'Terminal-Client Routes started')
    df_terminal_receiver = pd.merge(df_receiver, df_terminal, on='key').drop("key", 1).rename(
        columns={"latitude": "Shipper latitude", "longitude": "Shipper longitude"})
    df_terminal_receiver['Distance T-C'] = df_terminal_receiver.apply(
            lambda x: get_distance_aws(x, client, "Shipper", "Receiver"), axis=1)

    # Get closest T-C terminals
    df_tc = df_terminal_receiver.iloc[df_terminal_receiver.groupby(['Receiver longitude', 'Receiver latitude'])['Distance T-C'].idxmax().reset_index()['Distance T-C'].to_list()]
    df_tc = df_tc.rename({'Shipper latitude': 'T-C terminal latitude',
            'Shipper longitude': 'T-C terminal longitude',
            'id': 'T-C terminal id'}, axis=1)
    logger.success(f'Closest T-C terminals identified')

    # Merge routes, closest T-C terminals, and closest DC-T terminals
    df = df_routes.merge(df_dct[['DC code', 'Distance DC-T', 'DC-T terminal latitude', 'DC-T terminal longitude', 'DC-T terminal id']], on = ['DC code'], how = 'left')
    df = df.merge(df_tc, on = ['Address','City', 'Zip', 'Country', 'Country code'], how = 'left')
    df = df.dropna(subset = ['T-C terminal latitude'])

    # Get T-T distance
    logger.info(f'Terminal-Terminal routes started')
    logger.info(df.info())
    df['Distance T-T'] = df.apply(
        lambda x: get_distance_aws(x, client, "DC-T terminal", "T-C terminal"), axis=1)
    logger.success(f'T-T distance calculated')
    
    # Get total distance
    df['Distance total'] = df['Distance T-C'] + \
        df['Distance DC-T']+df['Distance T-T']
    
    # Save dataset to s3
    df.to_csv(
        f'{project_path}/processed/{dataset_name}_train_distances.csv', index=False)
    logger.success(f'Perparation done and dataset saved to S3')
    