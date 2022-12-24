from flask import Flask, render_template, request
from backend.gas import GasDriver, generate_gas_stations
from backend.geo import create_gmaps_link, get_coords_from_address
from operator import attrgetter

app=Flask(__name__)

@app.route('/', methods=('GET', 'POST'))
def root():
   #we retrieve the data entered by the user in the form
   markers = []
   filters = []
   if request.method == 'POST':
      gas = request.form['gas']
      location = request.form['location'].split(',')
      latitude, longitude = location[0], location[1]
      cp = request.form['cp']
      address = request.form['address']
      distance = str(float(request.form['distance'])*1000)
      car = request.form['car']

      if address != '':
         address += ', %s'%cp
         location = get_coords_from_address(address)[1]
         latitude, longitude = str(location[0]), str(location[1])
         marker = {
            'lat': location[0],
            'lon': location[1],
            'popup': 'Adresse entrée',
            'color': 'violet'
         }
         markers.append(marker)

      if gas != 'none':
         filters.append('prix_nom=%s'%gas)

      # create a driver that connects to the API
      driver = GasDriver()
      #get raw data
      data = driver.get_data(facets=['id', 'geom', 'prix_nom'], filters=filters, distance_from_point=(latitude, longitude, distance))
      #put all raw data we need into GasStation object (we want to plot the GasStarion objects on the map so we need to get all needed info)
      gas_stations = generate_gas_stations(data)

      #we create markers for each gas station
      closest_gs = min(gas_stations, key=attrgetter('dist_from_loc'))
      min_price = 1500
      for gs in gas_stations:
         for fuel in gs.fuels:
            if fuel.prix is not None:
               if fuel.prix<min_price:
                  min_price = fuel.prix
                  cheaper_gs = gs

      for gs in gas_stations :
         gmaps_link = create_gmaps_link((gs.coords.latitude, gs.coords.longitude))
         print(gmaps_link)
         marker = {
            'lat': gs.coords.latitude,
            'lon': gs.coords.longitude,
            'popup': ', '.join([f.name + ': ' + str(f.prix) + 'euros' for f in gs.fuels]),
            'maps_link': gmaps_link
         }
         if gs == cheaper_gs:
            marker['color'] = 'green'
         elif gs == closest_gs:
            marker['color'] = 'yellow'
         else:
            marker['color'] = 'blue'
         
         markers.append(marker)
      
   # we pass the data to the template (html file)
   return render_template('index.html',markers=markers )

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8080, debug=True)