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
      gas = request.form.getlist('gas[]')
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
         for i in range(len(gas)):
            filters.append('prix_nom=%s'%gas[i])

      # create a driver that connects to the API
      driver = GasDriver()
      #get raw data
      data = driver.get_data(facets=['id', 'geom', 'prix_nom'], filters=filters, distance_from_point=(latitude, longitude, distance))
      #put all raw data we need into GasStation object (we want to plot the GasStarion objects on the map so we need to get all needed info)
      gas_stations = generate_gas_stations(data)

      #we create markers for each gas station
      closest_gs = min(gas_stations, key=attrgetter('dist_from_loc')) #reprend ici et copie sans mes lignes avec le fuirtherst pou rla dist
      furthest_gs= 1000 # distance out of range that way for first iteration it is for sure lower
      min_price = 1500
      for gs in gas_stations:
         for fuel in gs.fuels:
            if fuel.prix is not None:
               if fuel.prix<min_price*1.02 and gs.dist_from_loc<furthest_gs*0.95 or fuel.prix<min_price*0.99 and gs.dist_from_loc<furthest_gs*1.1 :
                  min_price = fuel.prix
                  furthest_gs=gs.dist_from_loc
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
   app.run(host='127.0.0.1', port=8080, debug=True)