from geopy.geocoders import Bing
from loguru import logger

def get_lon_lat_bing(x, api_key, prefix: str):
    '''
    Getting longitude and latitude
    prefix_lat_long is either in this case either
    Shipper or Receiver
    '''
    geolocator = Bing(api_key=api_key)
    # Rue Roland Garros, 27930 Guichainville, France
    address = str(x[f'{prefix} address'])+', '+str(x[f'{prefix} zip']) + \
        ' '+str(x[f'{prefix} city'])+', '+str(x[f'{prefix} country'])
    location = geolocator.geocode(address)
    if location is not None:
        if location[0]!=x[f'{prefix} city']:
            return location.latitude, location.longitude
    else:
        address = str(x[f'{prefix} zip'])+' '+str(x[f'{prefix} city']
                                                  )+', '+str(x[f'{prefix} country'])
        location = geolocator.geocode(address)
        if (location is not None):
            logger.info(f'{address}')
            return location.latitude, location.longitude
        else:
            address = str(x[f'{prefix} city'])+', ' + \
                str(x[f'{prefix} country'])
            location = geolocator.geocode(address)
            if location is not None:
                logger.info(f'{address}')
                return location.latitude, location.longitude
            else:
                return None, None

def get_lon_lat_aws_prefix(x, client, prefix: str):
    '''
    Getting longitude and latitude
    prefix_lat_long is either in this case either
    Shipper or Receiver
    '''
    # Rue Roland Garros, 27930 Guichainville, France
    address = str(x[f'{prefix} address'])+', '+str(x[f'{prefix} zip']) + \
        ' '+str(x[f'{prefix} city'])+', '+str(x[f'{prefix} country'])
    response = client.search_place_index_for_text(IndexName='sustainable-transport',Text=address, MaxResults=5)
    if response['Results']!=[]:
        return response['Results'][0]['Place']['Geometry']['Point']
    else:
        address = str(x[f'{prefix} zip'])+' '+str(x[f'{prefix} city']
                                                  )+', '+str(x[f'{prefix} country'])
        response = client.search_place_index_for_text(IndexName='sustainable-transport',Text=address, MaxResults=5)
        if response['Results']!=[]:
            logger.info(f'{address}')
            return response['Results'][0]['Place']['Geometry']['Point']
        else:
            address = str(x[f'{prefix} city'])+', ' + \
                str(x[f'{prefix} country'])
            response = client.search_place_index_for_text(IndexName='sustainable-transport',Text=address, MaxResults=5)
            if response['Results']!=[]:
                logger.info(f'{address}')
                return response['Results'][0]['Place']['Geometry']['Point']
            else:
                return None

def get_lon_lat_aws(x, client):
    '''
    Getting longitude and latitude without a Prefix
    '''
    # Rue Roland Garros, 27930 Guichainville, France
    address = str(x[f'Address'])+', '+str(x[f'Zip']) + \
        ' '+str(x[f'City'])+', '+str(x[f'Country'])
    response = client.search_place_index_for_text(IndexName='sustainable-transport',Text=address, MaxResults=5)
    if response['Results']!=[]:
        return response['Results'][0]['Place']['Geometry']['Point']
    else:
        address = str(x[f'Zip'])+' '+str(x[f'City'])+', '+str(x[f'Country'])
        response = client.search_place_index_for_text(IndexName='sustainable-transport',Text=address, MaxResults=5)
        if response['Results']!=[]:
            logger.info(f'{address}')
            return response['Results'][0]['Place']['Geometry']['Point']
        else:
            address = str(x[f'City'])+', '+str(x[f'Country'])
            response = client.search_place_index_for_text(IndexName='sustainable-transport',Text=address, MaxResults=5)
            if response['Results']!=[]:
                logger.info(f'{address}')
                return response['Results'][0]['Place']['Geometry']['Point']
            else:
                logger.error(f'No result for {address}')
                return None



