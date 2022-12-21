import requests
import pandas as pd
from dataclasses import dataclass
from typing import List

class GasDriver:
    def __init__(self) -> None:
        self.url = 'https://data.economie.gouv.fr/api/records/1.0/search/?dataset=prix-carburants-fichier-instantane-test-ods-copie'

    def get_data(self, facets: list = [], filters: list = [], distance_from_point: tuple = (None, None, None)) -> list:
        """
        Method to query data to the API
            - facets: list -> list of the features we want to aggregate the results (equivalent og GROUP BY in SQL)
            - filters: list -> list of the filters we want to apply to our query
            - distance_from_point:tuple -> (latitude: string, longitude: string, distance: float) to get data within the 'distance' from point ('latitude', 'longitude') 
        """
        query = self.url + '&q='
        if len(facets)!=0:
            for facet in facets:
                query += '&facet=%s'%facet
        if len(filters)!=0:
            for f in filters :
                query += '&refine.%s'%f
        if all(i is not None for i in distance_from_point):
            query += '&geofilter.distance=' + distance_from_point[0] + '%2C' + distance_from_point[1] +  '%2C' + distance_from_point[2]
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
    Class for keeping track of a gaz
        - The price of gas changes depending on the gas station
        - We decide to diferentiate two of this object with the name and the price
    """
    name: str
    prix: float

@dataclass
class GasStation:
    """Class for keeping track of a gas stations and all the fuels they sell"""
    address: str
    cp: str
    coords: Point
    fuels: List[Gas]

    def __eq__(self, __o: object) -> bool:
        """Method to set two GasStation objects equals only if their coordinates are equal"""
        return self.coords == __o.coords




if __name__ == '__main__' :
    
    # create a driver that connects to the API
    driver = GasDriver()

    #get raw data
    data = driver.get_data(facets=['id', 'geom', 'prix_nom'], filters=['ville=Paris'], distance_from_point=("48.8520930694", "2.34738897685", "10000")) #renvoie la dernière màj du prix de chaque type de carburant pour toutes les stations de Paris et à une distance inférieure à 10km
    
    #put all raw data we need into GasStation object (we want to plot the GasStarion objects on the map so we need to get all needed info)
    gas_stations = []
    for r in data:
        fields = r['fields']
        #some values can be missing
        try:
            prix_nom = fields['prix_nom']
            prix_valeur = fields['prix_valeur']
        except:
            prix_nom = "Nous disposons pas d'information"
            prix_valeur = None
        gas_station = GasStation(fields['adresse'], fields['cp'], Point(float(fields['geom'][0]), float(fields['geom'][1])), fuels=[Gas(prix_nom, prix_valeur)])
        #if the gas station does not exist we create it
        if  gas_station not in gas_stations:
            gas_stations.append(gas_station)
        #else we had a Gas object to the GasStation.fuels variable
        else : 
            id = [i for i,x in enumerate(gas_stations) if x == gas_station][0]
            gas_stations[id].fuels.append(Gas(fields['prix_nom'], fields['prix_valeur']))


    print(gas_stations)