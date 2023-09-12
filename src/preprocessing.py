from loguru import logger
import country_converter as coco
import numpy as np
import re


def clean_string(x):
    try:
        x = re.sub(" # ", ' ', x)
        x = re.sub("# ", ' ', x)
        x = re.sub("#", ' ', x)
        x = re.sub(" , ", ' ', x)
        x = re.sub(", ", ' ', x)
        x = re.sub(",", ' ', x)
        x = re.sub("- ", ' ', x)
        x = re.sub("-", ' ', x)
        x = re.sub("-", ' ', x)
        return x
    except BaseException:
        return x


def get_country_name(df):
    '''
    Create country name columns for shipper and receiver without a Prefix
    '''
    dict_country_code = {}
    code_unique = df['Country code'].dropna().unique()
    for i in range(len(code_unique)):
        dict_country_code[code_unique[i]] = coco.convert(
            names=code_unique[i], to='name_short', not_found=None)
    df['Country'] = df['Country code'].replace(dict_country_code)
    return df


def data_preprocessing_bridge(df, dict_names: dict, df_ig_shipper):
    '''
    several cleaning and preprocessing steps for bridge
    '''
    # Rename column names based on given dictionary
    df = df.rename({y: x for x, y in dict_names.items()}, axis=1)
    df = df[dict_names.keys()]

    # delete row that have weight = 0 or no entry for unit
    df = df[(df['Weight unit'].notna()) & (df['Sender weight'] != 0.0)]

    # Cleaning text fields: all Street, City, Country to upper
    for i in ['Address', 'City', 'Country code', 'Client name']:
        df[i] = df[i].str.upper()
        df[i] = df[i].apply(lambda x: clean_string(x))

    # Add IG/OG indication
    shipper_ig = [
        '00' +
        number for number in df_ig_shipper['Vendor'].astype(str).to_list()]
    df['IG'] = np.where(df['Carrier code'].isin(shipper_ig), 1, 0)

    # Correct weight column
    df['Sender weight (kg)'] = np.where(
        df['Weight unit'] == 'LB',
        df['Sender weight'] * 0.45359237,
        df['Sender weight'])
    df['Sender weight (kg)'] = np.where(
        df['Weight unit'] == 'G',
        df['Sender weight'] / 1000,
        df['Sender weight'])
    df = df.drop(columns=['Weight unit', 'Sender weight'])

    # Correct volume column
    df['Volume (m3)'] = np.where(
        df['Volume unit'] == 'CMD',
        df['Volume'] / 1000,
        df['Volume'])
    df = df.drop(columns=['Volume unit', 'Volume'])

    # Add country name
    df = get_country_name(df)
    return df

def data_preprocessing_nshift(df, dict_names: dict):
    '''
    several cleaning and preprocessing steps for nshift data
    '''
    # Renaming columns
    df = df.rename({y: x for x, y in dict_names.items()}, axis=1)

    # Dropping rows for which we have missing values
    df = df.dropna(subset=['Pickup date', 'DC name'])
    df = df[df['Country code'] != '0']

    try:
        # Convert volume to float
        df['Volume (m3)'] = df['Volume (m3)'].astype('float')
    except BaseException:
        pass

    # Limit data to columns
    df = df[dict_names.keys()]

    # Add shipping type
    df['Shipping type'] = 'Road'

    # Add IG/OG
    df['IG'] = 0

    # All to upper letters
    for i in ['Address', 'Zip', 'City']:
        df[i] = df[i].str.upper()

    # Get country names
    df = get_country_name(df)
    return df


def merge_for_app(df, df_shipper, df_receiver, df_distances):
    '''
    Create final dataframe by adding geolocation and distance to raw dataset
    '''
    # Merging df_shipper on full nshift data
    data = df.merge(
        df_shipper,
        how='left',
        on=['DC code'],
        suffixes=(
            None,
            '_shipper'))

    # Merging df_receiver on full nshift data
    data = data.merge(df_receiver, how='inner', on=[
        'Address', 'City', 'Country code', 'Country', 'Zip'], )

    # Merging df_receiver on full nshift data
    data = data.merge(df_distances,
                      how='inner',
                      on=['Receiver longitude',
                          'Receiver latitude',
                          'Shipper longitude',
                          'Shipper latitude',
                          ])

    data = data.rename(columns={
        'Address_shipper': 'DC address',
        'City_shipper': 'DC city',
        'Zip_shipper': 'DC zip',
        'Country_shipper': 'DC country',
        'Country code_shipper': 'DC country code'
    })
    return data
