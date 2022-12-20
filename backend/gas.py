import requests
import pandas as pd

class GasDriver:
    def __init__(self) -> None:
        self.url = 'https://data.economie.gouv.fr/api/records/1.0/search/?dataset=prix-carburants-fichier-instantane-test-ods-copie'

    def query(self, filters=None):
        query = self.url + '&q=&facet=id&facet=adresse&facet=ville&facet=prix_maj&facet=prix_nom&facet=cp&facet=com_arm_name&facet=epci_name&facet=dep_name&facet=reg_name&facet=services_service&facet=horaires_automate_24_24'
        if filters is not None:
            for f in filters :
                query += '&refine.%s'%f
        r = requests.get(query)
        res = r.json()
        return res['records']

if __name__ == '__main__' :
    driver = GasDriver()
    data = driver.query(filters=['ville=Paris', 'cp=75019']) #renvoie la dernière màj du prix de chaque type de carburant pour toutes les stations du 19ème à Paris
    print(data[0])