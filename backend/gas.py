import requests
import pandas as pd
from dataclasses import dataclass
from typing import List

class GasDriver:
    def __init__(self) -> None:
        self.url = 'https://data.economie.gouv.fr/api/records/1.0/search/?dataset=prix-carburants-fichier-instantane-test-ods-copie'

    def get_data(self, facets=None, filters=None, distance_from_point=(None, None, None)):
        query = self.url + '&q='
        if facets is not None:
            for facet in facets:
                query += '&facet=%s'%facet
        if filters is not None:
            for f in filters :
                query += '&refine.%s'%f
        if all(i is not None for i in distance_from_point):
            query += '&geofilter.distance=' + distance_from_point[0] + '%2C' + distance_from_point[1] +  '%2C' + distance_from_point[2]
        r = requests.get(query)
        res = r.json()
        return res['records']

@dataclass
class Point:
    latitude: float
    longitude: float


@dataclass
class Gas:
    name: str
    prix: float

@dataclass
class GasStation:
    address: str
    cp: str
    coords: Point
    fuels: List[Gas]

    def __eq__(self, __o: object) -> bool:
        return self.coords == __o.coords




if __name__ == '__main__' :
    driver = GasDriver()
    # distance_from_point=("48.8520930694", "2.34738897685", "1000")
    data = driver.get_data(facets=['id', 'geom', 'prix_nom'], filters=['ville=Paris'], distance_from_point=("48.8520930694", "2.34738897685", "10000")) #renvoie la dernière màj du prix de chaque type de carburant pour toutes les stations du 19ème à Paris
    gas_stations = []
    for r in data:
        fields = r['fields']
        try:
            prix_nom = fields['prix_nom']
            prix_valeur = fields['prix_valeur']
        except:
            prix_nom = "Nous disposons pas d'information"
            prix_valeur = None
        gas_station = GasStation(fields['adresse'], fields['cp'], Point(float(fields['geom'][0]), float(fields['geom'][1])), fuels=[Gas(prix_nom, prix_valeur)])
        if  gas_station not in gas_stations:
            gas_stations.append(gas_station)
        else : 
            id = [i for i,x in enumerate(gas_stations) if x == gas_station][0]
            gas_stations[id].fuels.append(Gas(fields['prix_nom'], fields['prix_valeur']))


    print(gas_stations)