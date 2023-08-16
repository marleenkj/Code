import pandas as pd
from src.distance import distance_per_country_osrm_haversine, distance_per_country_osrm_aws
from loguru import logger
import boto3
import geopandas as gpd
from shapely.geometry import LineString

# To change based on dataset
dataset_name = 'sql_poc1'
project_path = 's3://sfgdata/projects/sustainable-transport'

end_ID = ['Address', 'City', 'Country', 'Country code', 'Zip']
start_ID = ['DC code']

client = boto3.client('location')

train_distances = f'{project_path}/processed/{dataset_name}_train_distances_harversine.csv'

if __name__ == '__main__':
    # Import data
    # datasets need to have column Latitude and Longitude
    df = pd.read_csv(train_distances).head()
    # get distance per country
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    europe =  world[world.continent == "Europe"].explode()
    df['DC-T countries'] = df.apply(lambda x: distance_per_country_osrm_aws(x, europe, 'Shipper', 'DC-T terminal'), axis=1)
    df['T-T countries'] = df.apply(lambda x: distance_per_country_osrm_haversine(x, europe, 'DC-T terminal', 'T-C terminal'), axis=1)
    df['T-C countries'] = df.apply(lambda x: distance_per_country_osrm_aws(x, europe, 'T-C terminal', 'Receiver'), axis=1)

    # df.to_csv(f'{project_path}/processed/{dataset_name}_train_per_countries.csv', index=False)
    logger.success(f'Countries done')