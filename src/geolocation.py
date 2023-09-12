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
    address = str(x[f'{prefix} address']) + ', ' + str(x[f'{prefix} zip']) + \
        ' ' + str(x[f'{prefix} city']) + ', ' + str(x[f'{prefix} country'])
    location = geolocator.geocode(address)
    if location is not None:
        if location[0] != x[f'{prefix} city']:
            return location.latitude, location.longitude
    else:
        address = str(x[f'{prefix} zip']) + ' ' + \
            str(x[f'{prefix} city']) + ', ' + str(x[f'{prefix} country'])
        location = geolocator.geocode(address)
        if (location is not None):
            logger.info(f'{address}')
            return location.latitude, location.longitude
        else:
            address = str(x[f'{prefix} city']) + ', ' + \
                str(x[f'{prefix} country'])
            location = geolocator.geocode(address)
            if location is not None:
                logger.info(f'{address}')
                return location.latitude, location.longitude
            else:
                return None, None