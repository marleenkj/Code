import pandas as pd
from loguru import logger
import numpy as np

project_path = 's3://sfgdata/projects/sustainable-transport'
dataset_name_1 = 'oerebro_poc3'
dataset_name_2 = 'sql_poc3'
dataset_name = 'poc3'

if __name__ == '__main__':
    logger.info('Import started')
    
    # Data import
    df1 = pd.read_csv(f'{project_path}/processed/{dataset_name_1}.csv', dtype={'DC zip': str, 'Zip': str}, parse_dates=['Pickup date'])
    df2 = pd.read_csv(f'{project_path}/processed/{dataset_name_2}.csv', dtype={'DC zip': str, 'Zip': str}, parse_dates=['Pickup date'])
    
    # Dict for column names
    df = pd.concat([df1, df2], axis = 0).sort_values(by='Pickup date')
    df = df[(df['Pickup date']>='2022-01-01')&(df['Pickup date']<='2022-12-31')]

    df['DC name'] = np.where(df['DC name'] == 'HU08-TPP RDC Cent.', 'DC Ceelog', df['DC name'])

    emission_factor = 83
    df['Co2 diesel'] = emission_factor*df['Distance (km)']*(df['Sender weight (kg)']/1000)
    bev_france = 8
    bev_hungary = 37
    bev_sweden = 1.86
    df['Co2 BEV'] = 0
    df['Co2 BEV'] = np.where(df['DC country']=='France', bev_france*df['Distance (km)']*(df['Sender weight (kg)']/1000), df['Co2 BEV'])
    df['Co2 BEV'] = np.where(df['DC country']=='Sweden', bev_sweden*df['Distance (km)']*(df['Sender weight (kg)']/1000), df['Co2 BEV'])
    df['Co2 BEV'] = np.where(df['DC country']=='Hungary', bev_hungary*df['Distance (km)']*(df['Sender weight (kg)']/1000), df['Co2 BEV'])
    
    # Save to s3
    df.to_csv(f'{project_path}/processed/{dataset_name}.csv', index=False)

    logger.info('Dataset for PoC2 generated and stored')
