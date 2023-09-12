import os
import dash
import dash_bootstrap_components as dbc
#import dash_auth
import pandas as pd
import datetime as dt
import numpy as np
from ast import literal_eval
import json

route_preffix = os.environ.get('EXTRAPATH', '') + '/'

app_name = "Decision Support Tool for CRFT"

"""
# Import data
project_path = '../../data'
dataset_name = 'poc3'

df = pd.read_csv(f'{project_path}/processed/{dataset_name}.csv', 
                 low_memory=False,
                 parse_dates=['Pickup date'], 
                 dtype={'DC zip': str, 'Zip': str}).sort_values(by='Pickup date')
df = df.dropna(subset = ['Distance (km)'])
"""

# Import data
project_path = '../../notebooks/results'
dataset_name = 'df_limited'
df_limited = pd.read_csv(f'{project_path}/{dataset_name}.csv', parse_dates=['Delivery date'])
dataset_name = 'df_distance_matrix'
df_distance_matrix = pd.read_csv(f'{project_path}/{dataset_name}.csv', index_col = 0)
df_results_details = pd.read_csv(f'{project_path}/df_results_details.csv', index_col = [0])
dataset_name = 'df_results_direct_ftl_truck_speed_80_80'
results_direct_ftl_truck = pd.read_csv(f'{project_path}/direct/{dataset_name}.csv')
dataset_name = 'df_results_direct_ftl_train_speed_80_80'
results_direct_ftl_train = pd.read_csv(f'{project_path}/direct/{dataset_name}.csv')
dataset_name = '0730_results_base_weekly'
df_ghg = pd.read_csv(f'{project_path}/old/{dataset_name}.csv')
df_ghg_converted = pd.read_csv(
    f'{project_path}/old/{dataset_name}.csv', 
    converters={'routes railroad': literal_eval, 'routes road': literal_eval})

# Import dict terminals
f = open("../../data/external/intermodal_terminals/dict_terminals.json")
dict_terminals = json.load(f)

# Import dict points
f = open("../../data/processed/dict_points.json")
dict_points = json.load(f)

dict_results = {
 'co2 road': 2008.889022706869,
 'distance road': 2477629,
 'routes road': [['DC2', 'C22', 'C13', 'C27', 'C15', 'C28', 'C24', 'DC2']],
 'processing time road': 0.890625,
 'co2 railroad': 1457.7977660290946,
 'distance railroad': 3439485.0,
 'terminal allocation': [[],
  ['C24', 'C28'],
  [],
  ['C13', 'C27'],
  ['C15'],
  [],
  ['C22'],
  [],
  [],
  []],
 'routes railroad': {'T1': [[]],
  'T2': [['T2', 'C28', 'C24', 'T2']],
  'T3': [[]],
  'T4': [['T4', 'C27', 'C13', 'T4']],
  'T5': [['T5', 'C15', 'T5']],
  'T6': [[]],
  'T7': [['T7', 'C22', 'T7']],
  'T8': [[]],
  'T9': [[]],
  'T10': [[]]},
 'processing time railroad': 3.734375}

app = dash.Dash(
    __name__,
    title=app_name,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    routes_pathname_prefix=route_preffix
)

# auth = dash_auth.BasicAuth(
#     app,
#     {'user': 'psswrd'}
# )
