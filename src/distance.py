import requests
import json
from loguru import logger
import s3fs
from shapely.geometry import LineString
import pandas as pd
from math import radians, cos, sin, asin, sqrt, atan2, sqrt, degrees, modf
import math

def get_distance_osrm(a, b) -> float:
    '''
    Getting distance with OSRM longitude latitude
    returns distance in km
    '''
    # call the OSMR API
    r = requests.get(
        f"http://router.project-osrm.org/route/v1/car/{a[0]},{a[1]};{b[0]},{b[1]}?steps=false&geometries=geojson&overview=full&annotations=false""")
    # then you load the response using the json libray
    # by default you get only one alternative so you access 0-th element of the `routes`
    routes = json.loads(r.content)
    try:
        route_1 = routes.get("routes")[0]
        return route_1['distance']/1000
    except:
        return None

def get_distance_osrm_lat_lon_meters(a, b) -> float:
    '''
    Getting distance with OSRM laitude longitude
    returns distance in km
    '''
    # call the OSMR API
    r = requests.get(
        f"http://router.project-osrm.org/route/v1/car/{a[1]},{a[0]};{b[1]},{b[0]}?steps=false&geometries=geojson&overview=full&annotations=false""")
    # then you load the response using the json libray
    # by default you get only one alternative so you access 0-th element of the `routes`
    routes = json.loads(r.content)
    try:
        route_1 = routes.get("routes")[0]
        return route_1['distance']
    except:
        return None
    
def get_waypoints_osrm(a) -> float:
    '''
    Getting distance with OSRM longitude latitude in form of list
    '''
    locations = ','.join(str(x) for x in a[0])
    for i in range(1,len(a)):
        x = ','.join(str(x) for x in a[i])
        locations = ';'.join([str(locations),str(x)])
    r = requests.get(
        f"http://router.project-osrm.org/route/v1/car/{locations}?steps=false&geometries=geojson&overview=full&annotations=false""")
    # then you load the response using the json libray
    # by default you get only one alternative so you access 0-th element of the `routes`
    routes = json.loads(r.content)
    try:
        route_1 = routes.get("routes")[0]
        return route_1
    except:
        return None
    
def get_distance_osrm_geopoints(a) -> float:
    '''
    Getting distance with OSRM longitude latitude fo list a with geolocations
    '''
    # call the OSMR API
    locations = ','.join(str(x) for x in a[0])
    for i in range(1,len(a)):
        x = ','.join(str(x) for x in a[i])
        locations = ';'.join([str(locations),str(x)])
    r = requests.get(
        f"http://router.project-osrm.org/route/v1/car/{locations}?steps=false&geometries=geojson&overview=full&annotations=false""")
    # then you load the response using the json libray
    # by default you get only one alternative so you access 0-th element of the `routes`
    routes = json.loads(r.content)
    try:
        route_1 = routes.get("routes")[0]
        return route_1['distance']/1000
    except:
        return None

def get_distance_aws(x, client, shipper_prefix = 'Shipper', receiver_prefix = 'Receiver'):
    '''
    Getting distance with AWS 
    Check first if json file already exists
    '''
    s3 = s3fs.S3FileSystem()
    start = [x[f'{shipper_prefix} longitude'], x[f'{shipper_prefix} latitude']]
    end = [x[f'{receiver_prefix} longitude'], x[f'{receiver_prefix} latitude']]
    try:
        with s3.open(f's3://sfgdata/projects/sustainable-transport/processed/aws/{start}_{end}.json', 'r') as fp:
            aws_file = json.load(fp)
        distance = aws_file['Distance']
        return distance
    except:
        try:
            response = client.calculate_route(
            CalculatorName='sustainable-transport',
            DeparturePosition=start,
            DestinationPosition=end,
            DistanceUnit='Kilometers',
            IncludeLegGeometry=True,
            TravelMode='Truck')
            aws_file = response['Legs'][0]
            with s3.open(f's3://sfgdata/projects/sustainable-transport/processed/aws/{start}_{end}.json', 'w') as outfile:
                json.dump(aws_file, outfile)
            distance = aws_file['Distance']
            return distance
        except:
            logger.info(f'No distance for {start}_{end}')
            return None
        
def get_distance_aws_lon_lat(start, end, client):
    '''
    Getting distance with AWS 
    Check first if json file already exists
    '''
    s3 = s3fs.S3FileSystem()
    try:
        with s3.open(f's3://sfgdata/projects/sustainable-transport/processed/aws/{start}_{end}.json', 'r') as fp:
            aws_file = json.load(fp)
        distance = aws_file['Distance']
        return distance
    except:
        try:
            response = client.calculate_route(
            CalculatorName='sustainable-transport',
            DeparturePosition=start,
            DestinationPosition=end,
            DistanceUnit='Kilometers',
            IncludeLegGeometry=True,
            TravelMode='Truck')
            aws_file = response['Legs'][0]
            with s3.open(f's3://sfgdata/projects/sustainable-transport/processed/aws/{start}_{end}.json', 'w') as outfile:
                json.dump(aws_file, outfile)
            distance = aws_file['Distance']
            return distance
        except:
            logger.info(f'No distance for {start}_{end}')
            return None

def get_haversine_distance(x, shipper_name = 'Shipper', receiver_name = 'Receiver'):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    lon1, lat1 = [x[f'{shipper_name} longitude'], x[f'{shipper_name} latitude']]
    lon2, lat2 = [x[f'{receiver_name} longitude'], x[f'{receiver_name} latitude']]
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r

def get_haversine_distance_lonlat(start, end):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    lon1, lat1 = start[0], start[1]
    lon2, lat2 = end[0], end[1]
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r

def get_haversine_distance_latlon(start, end):
    """
    Calculate the great circle distance in meters between two points 
    on the earth (specified in decimal degrees)
    """
    lon1, lat1 = start[1], start[0]
    lon2, lat2 = end[1], end[0]
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r

def get_segment_boundaries(x, line):
    x = LineString(line).intersection(x['geometry']).boundary
    a = [x.geoms[0].x, x.geoms[0].y]
    b = [x.geoms[1].x, x.geoms[1].y]
    return pd.Series([a, b])

def distance_per_country_osrm_aws(x, europe, shipper_name = 'Shipper', receiver_name = 'Receiver'):
    '''
    Function to get dictionary with distances per country
    '''
    s3 = s3fs.S3FileSystem()
    start = [x[f'{shipper_name} longitude'], x[f'{shipper_name} latitude']]
    end = [x[f'{receiver_name} longitude'], x[f'{receiver_name} latitude']]
    
    try:
        with s3.open(f's3://sfgdata/projects/sustainable-transport/processed/aws/{start}_{end}.json', 'r') as fp:
            aws_file = json.load(fp)
        line_list = aws_file['Geometry']['LineString']
        df_intersections = europe[LineString(line_list).crosses(europe.geometry)]
        if df_intersections.shape[0]>1:
            df_intersections[['start', 'end']] = df_intersections.apply(lambda x: get_segment_boundaries(x, line_list), axis = 1)
            df_intersections['distance'] = df_intersections.apply(lambda x: get_distance_osrm(x['start'], x['end'])/1000, axis = 1)
            dict_countries = df_intersections.groupby('name')['distance'].sum().to_dict()
            logger.info(dict_countries)
            return dict_countries
    except:
        return None
    
def calculate_azimuth(lat1,lng1,lat2,lng2):
    '''
    calculates the azimuth in degrees from start point to end point
    '''
    startLat = math.radians(lat1)
    startLong = math.radians(lng1)
    endLat = math.radians(lat2)
    endLong = math.radians(lng2)
    dLong = endLong - startLong
    dPhi = math.log(math.tan(endLat/2.0+math.pi/4.0)/math.tan(startLat/2.0+math.pi/4.0))
    if abs(dLong) > math.pi:
         if dLong > 0.0:
             dLong = -(2.0 * math.pi - dLong)
         else:
             dLong = (2.0 * math.pi + dLong)
    bearing = (math.degrees(math.atan2(dLong, dPhi)) + 360.0) % 360.0;
    return bearing

def get_path_length(lat1,lng1,lat2,lng2):
    '''
    calculates the distance between two lat, long coordinate pairs
    '''
    R = 6371000 # radius of earth in m
    lat1rads = radians(lat1)
    lat2rads = radians(lat2)
    deltaLat = radians((lat2-lat1))
    deltaLng = radians((lng2-lng1))
    a = sin(deltaLat/2) * sin(deltaLat/2) + cos(lat1rads) * cos(lat2rads) * sin(deltaLng/2) * sin(deltaLng/2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    d = R * c

    return d

def get_destination_lat_long(lat,lng,azimuth,distance):
    '''
    returns the lat an long of destination point 
    given the start lat, long, aziuth, and distance
    '''
    R = 6378.1 #Radius of the Earth in km
    brng = radians(azimuth) #Bearing is degrees converted to radians.
    d = distance/1000 #Distance m converted to km

    lat1 = radians(lat) #Current dd lat point converted to radians
    lon1 = radians(lng) #Current dd long point converted to radians

    lat2 = asin( sin(lat1) * cos(d/R) + cos(lat1)* sin(d/R)* cos(brng))

    lon2 = lon1 + atan2(sin(brng) * sin(d/R)* cos(lat1), 
           cos(d/R)- sin(lat1)* sin(lat2))

    #convert back to degrees
    lat2 = degrees(lat2)
    lon2 = degrees(lon2)

    return[lat2, lon2]

def get_line_string(interval,lat1,lng1,lat2,lng2):
    '''
    returns every coordinate pair inbetween two coordinate 
    pairs given the desired interval
    '''
    azimuth = calculate_azimuth(lat1,lng1,lat2,lng2)
    coords = []
    d = get_path_length(lat1,lng1,lat2,lng2)
    remainder, dist = modf((d / interval))
    counter = 1.0
    coords.append([lat1,lng1])
    for distance in range(1,int(dist)):
        c = get_destination_lat_long(lat1,lng1,azimuth,counter)
        counter += 1.0
        coords.append(c)
    counter +=1
    coords.append([lat2,lng2])
    return coords

def distance_per_country_osrm_haversine(x, europe, shipper_name = 'Shipper', receiver_name = 'Receiver'):
    '''
    Function to get dictionary with distances per country
    '''
    #point interval in meters
    interval = 1000
    #start point
    lng1 = x[f'{shipper_name} longitude']
    lat1 = x[f'{shipper_name} latitude']
    #end point
    lng2 = x[f'{receiver_name} longitude']
    lat2 = x[f'{receiver_name} latitude']
    try:
        line_list = get_line_string(interval,lng1,lat1,lng2,lat2)
        df_intersections = europe[LineString(line_list).crosses(europe.geometry)]
        if df_intersections.shape[0]>1:
            df_intersections[['start', 'end']] = df_intersections.apply(lambda x: get_segment_boundaries(x, line_list), axis = 1)
            df_intersections['distance'] = df_intersections.apply(lambda x: get_haversine_distance_lonlat(x['start'], x['end']), axis = 1)
            dict_countries = df_intersections.groupby('name')['distance'].sum().to_dict()
            logger.info(dict_countries)
            return dict_countries
    except:
        return None

def get_waypoints_aws(start, end):
    '''
    Getting distance with AWS 
    Check first if json file already exists
    '''
    s3 = s3fs.S3FileSystem()
    try:
        with s3.open(f's3://sfgdata/projects/sustainable-transport/processed/aws/{start}_{end}.json', 'r') as fp:
            aws_file = json.load(fp)
            
        return aws_file
    except:
        return 'No file'





