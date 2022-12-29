import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import json
import pandas as pd
from dataclasses import dataclass
from typing import List

class GasDriver:
    def __init__(self) -> None:
        self.url = 'https://data.economie.gouv.fr/api/records/1.0/search/?dataset=prix-carburants-fichier-instantane-test-ods-copie'

    def get_data(self, facets: list = [], filters: list = [], automates: list = [], distance_from_point: tuple = (None, None, None)) -> list:
        """
        Method to query data to the API
            - facets: list -> list of the features we want to aggregate the results (equivalent og GROUP BY in SQL)
            - filters: list -> list of the filters we want to apply to our query
            - distance_from_point:tuple -> (latitude: string, longitude: string, distance: float) to get data within the 'distance' from point ('latitude', 'longitude')
            - automates -> yes and/or no for presence of automates in the gas station (another set of filters)
        """
        query = self.url + '&q='
        if len(facets)!=0:
            for facet in facets:
                query += '&facet=%s'%facet
        if len(filters)!=0:
            carburants=['prix_nom=SP98','prix_nom=SP95','prix_nom=Gazole','prix_nom=E10','prix_nom=E85','prix_nom=GPLc']
            for f in carburants :
                if f not in filters :
                    query += '&exclude.%s'%f
        if len(automates)!=0:
            for a in automates:
                query += '&refine.%s'%a
        if all(i is not None for i in distance_from_point):
            query += '&geofilter.distance=' + distance_from_point[0] + '%2C' + distance_from_point[1] +  '%2C' + distance_from_point[2]
        query += '&rows=100'
        r = requests.get(query)
        res = r.json()
        return res['records']


@dataclass
class Point:
    """Class for keeping track of the location of a gas station"""
    latitude: float
    longitude: float


@dataclass
class Gas:
    """
    Class for keeping track of gas
        - The price of gas changes depending on the gas station
        - We decide to diferentiate it according to its name, its price and the latter one's last updated date
    """
    name: str
    prix: float
    maj: str

@dataclass
class GasStation:
    """Class for keeping track of a gas station and all the fuels it sells"""
    address: str
    cp: str
    horaires_automate_24_24: str
    coords: Point
    fuels: List[Gas]
    dist_from_loc: float

    def __eq__(self, __o: object) -> bool:
        """Method to set two GasStation objects equals only if their coordinates are equal"""
        return self.coords == __o.coords


def generate_gas_stations(data):
    #put all raw data we need into GasStation object (we want to plot the GasStarion objects on the map so we need to get all needed info)
    gas_stations = []
    for r in data:
        fields = r['fields']
        #some values can be missing
        try:
            prix_nom = fields['prix_nom']
            prix_valeur = fields['prix_valeur']
            prix_maj = fields['prix_maj']
        except:
            prix_nom = "Nous ne disposons pas d'information"
            prix_valeur = None
            prix_maj = None
        gas_station = GasStation(fields['adresse'], fields['cp'], fields['horaires_automate_24_24'], coords=Point(float(fields['geom'][0]), float(fields['geom'][1])), fuels=[Gas(prix_nom, prix_valeur, prix_maj)], dist_from_loc=float(fields['dist']))
        #if the gas station does not exist we create it
        if  gas_station not in gas_stations:
            gas_stations.append(gas_station)
        #else we had a Gas object to the GasStation.fuels variable
        else : 
            id = [i for i,x in enumerate(gas_stations) if x == gas_station][0]
            gas_stations[id].fuels.append(Gas(fields['prix_nom'], fields['prix_valeur'], fields['prix_maj']))
    return gas_stations

class average_price_plot:
    def __init__(self) -> None:
        self.url = 'https://data.economie.gouv.fr/api/records/1.0/search/?dataset=prix-carburants-fichier-instantane-test-ods-copie'
 
    def query(self, filters=None):
        query = self.url + '&q=&rows=10000&facet=prix_maj&facet=prix_nom&facet=prix_valeur'
        if filters is not None:
            for f in filters :
                query += '&refine.%s'%f
        r = requests.get(query)
        res = r.json()
        final = json.dumps(res)
        return final

class ReverseGeo:
    def __init__(self) -> None:
        self.url = 'https://api.bigdatacloud.net/data/reverse-geocode-client?'
        
    def query(self, location=None):
        query = self.url
        if location is not None:
            query += 'latitude=' + str(location[0]) + '&longitude=' + str(location[1]) +'&localityLanguage=fr'  
        
        session = requests.Session()
        retry = Retry(connect=5, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        r = session.get(query)
        final = r.json()
        geoloc = pd.DataFrame.from_dict(final, orient='columns')
        return geoloc['city'].iloc[0]