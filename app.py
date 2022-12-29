from flask import Flask, render_template, request
from backend.gas import GasDriver, generate_gas_stations
from backend.geo import create_gmaps_link, get_coords_from_address
from operator import attrgetter
import random

app=Flask(__name__)

@app.route('/', methods=('GET', 'POST'))
def root():
   #we retrieve the data entered by the user in the form
   markers = []
   filters = []
   automates = []
   if request.method == 'POST':
      gas = request.form.getlist('gas[]')
      location = request.form['location'].split(',')
      latitude, longitude = location[0], location[1]
      cp = request.form['cp']
      address = request.form['address']
      distance = str(float(request.form['distance'])*1000)
      horaires_automate_24_24 = request.form['automate']

      if address != '':
         address += ', %s'%cp
         location = get_coords_from_address(address)[1]
         latitude, longitude = str(location[0]), str(location[1])
         marker = {
            'lat': location[0],
            'lon': location[1],
            'popup': 'Adresse renseignée',
            'color': 'violet'
         }
         markers.append(marker)

      if gas != 'none':
         for i in range(len(gas)):
            filters.append('prix_nom=%s'%gas[i])
      
      if horaires_automate_24_24 != 'none':
         automates.append('horaires_automate_24_24=%s'%horaires_automate_24_24)

      # create a driver that connects to the API
      driver = GasDriver()
      #get raw data
      data = driver.get_data(facets=['id', 'geom', 'prix_nom'], filters=filters, automates=automates, distance_from_point=(latitude, longitude, distance))
      #put all raw data we need into GasStation object (we want to plot the GasStarion objects on the map so we need to get all needed info)
      gas_stations = generate_gas_stations(data)

      #we create markers for each gas station
      closest_gs = min(gas_stations, key=attrgetter('dist_from_loc'))
      while True:
         best_gs = random.choice(gas_stations)
         if best_gs.fuels[0].prix is not None:
            break
      #best_ratio = best_gs.fuels[0].prix/best_gs.dist_from_loc*100
      min_loss = best_gs.dist_from_loc/1000 + 50*best_gs.fuels[0].prix #we set aribitrarily that we are ready to go 5km further to get -10cts on the fuel price
      min_price = 1500
      for gs in gas_stations:
         for fuel in gs.fuels:
            if fuel.prix is not None:
               if fuel.prix<min_price: #find the cheapest gas station
                  min_price = fuel.prix
                  cheaper_gs = gs
               if gs.dist_from_loc/1000 + 50*fuel.prix < min_loss:
                  min_loss = gs.dist_from_loc/1000 + 50*fuel.prix
                  best_gs = gs
               #if gs.dist_from_loc/fuel.prix < best_ratio: #best gas station considering the distance/price trade-off
                  #best_ratio = gs.dist_from_loc/fuel.prix
                  #best_gs = gs
               
      for gs in gas_stations :
         gmaps_link = create_gmaps_link((latitude, longitude),(gs.coords.latitude, gs.coords.longitude))
         print(gmaps_link)
         marker = {
            'lat': gs.coords.latitude,
            'lon': gs.coords.longitude,
            'popup': ', '.join([f.name + ': ' + str(f.prix) + 'euros' for f in gs.fuels]),
            'maps_link': gmaps_link
         }
         if gs == cheaper_gs: #if a marker doesn't appear, it is because it is combined with another one (the order of the if conditions maters!)
            marker['color'] = 'green'
         elif gs == closest_gs:
            marker['color'] = 'yellow'
         elif gs == best_gs:
            marker['color'] = 'orange'
         else:
            marker['color'] = 'blue'
         
         markers.append(marker)
      
   # we pass the data to the template (html file)
   return render_template('index.html',markers=markers )

if __name__ == '__main__':
   app.run(host='127.0.0.1', port=8080, debug=True)