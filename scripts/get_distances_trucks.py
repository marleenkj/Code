import pandas as pd
from src.distance import get_distance_aws
from loguru import logger
import boto3

# To change based on dataset
dataset_name = 'oerebro_nshift_2022'
project_path = 's3://sfgdata/projects/sustainable-transport'

end_ID = ['Address', 'City', 'Country', 'Country code', 'Zip']
start_ID = ['DC code']

client = boto3.client('location')

start_geolocation_filepath = f'{project_path}/processed/df_shipper_geolocation_aws_modified.csv'
end_geolocation_filepath = f'{project_path}/processed/{dataset_name}_geolocation.csv'
routes_filepath = f'{project_path}/processed/{dataset_name}_routes.csv'

if __name__ == '__main__':
    # Import data
    # datasets need to have column Latitude and Longitude
    df_receiver = pd.read_csv(end_geolocation_filepath, dtype={'Zip': str}).dropna(subset=['Latitude']).rename(
        columns={"Longitude": "Receiver longitude", "Latitude": "Receiver latitude"})
    df_shipper = pd.read_csv(start_geolocation_filepath, dtype={'Zip': str}).rename(
        columns={"Longitude": "Shipper longitude", "Latitude": "Shipper latitude"})
    df_routes = pd.read_csv(routes_filepath, dtype={'Zip': str})

    # Get Lon/Lat for each Client/DC for each route
    df = df_routes.merge(
        df_shipper[start_ID+['Shipper longitude', 'Shipper latitude']], how='left', on=start_ID)
    df = df.merge(
        df_receiver[end_ID+['Receiver longitude', 'Receiver latitude']], how='inner', on=end_ID)

    # Creating unique routes
    df = df[[
        "Receiver longitude", "Receiver latitude",
        "Shipper longitude", "Shipper latitude"
    ]].drop_duplicates().dropna().reset_index(drop=True)
    logger.info(f'Number of combinations: {df.shape[0]}')

    # Get distances with AWS, save in Distance column
    logger.info(f'Routes started')
    df['Distance'] = df.apply(lambda x: get_distance_aws(x, client), axis=1)

    # Save distances
    df.to_csv(
        f'{project_path}/processed/{dataset_name}_distances.csv', index=False)
    logger.success(f'Routes done')
