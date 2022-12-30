from flask import Flask, render_template, request
from backend.gas import GasDriver, generate_gas_stations, average_price_plot, ReverseGeo
from backend.geo import create_gmaps_link, get_coords_from_address
from operator import attrgetter
import random

import requests
import json
import bokeh
import numpy as np
import pandas as pd
from bokeh.plotting import figure, output_file
from bokeh.models import DatetimeTickFormatter, PrintfTickFormatter, ColumnDataSource, Grid, Line, Dropdown, LinearAxis, Plot, HoverTool, CustomJS, Slider, Select, DateRangeSlider
from bokeh.io import show, curdoc
from bokeh.layouts import gridplot, column
from bokeh.embed import components
from bokeh.resources import CDN
from datetime import date, timedelta
from bokeh.transform import factor_cmap

app=Flask(__name__)

@app.route('/', methods=('GET', 'POST'))
def root():

   ###############################################################
   # 1. Get all the data we need to build our interactive plot   #
   ###############################################################

   # To get the data we need as source to build our interactive plot
   plot_data = average_price_plot()
   plot_source = plot_data.query()
   df = json.loads(plot_source)
   df = pd.json_normalize(df, 'records')

   # We only keep the data required to construct our plot: gas type, the date and the related price
   df = df[['fields.prix_nom','fields.prix_valeur','fields.prix_maj']]
   df = df.rename(columns = {
                  'fields.prix_nom': "Carburant",
                  'fields.prix_valeur': "Prix",
                  'fields.prix_maj': "Date"})

   # # We remove timestamps to keep only the date, with date format
   for i in range(len(df)):
      df.iloc[i, 2] = str(df.iloc[i, 2])[:10]

   df['Date'] = pd.to_datetime(df['Date'], format = '%Y-%m-%d')
   df = df.sort_values(by = ['Date'])

   # #to keep only the value we want, anc convert Carburant to columns, to make it easier to manipulate afterwards
   df1 = pd.pivot_table(df,
                        values = 'Prix',
                        index = ['Date'],
                        columns = ['Carburant'],
                        aggfunc=np.mean)

   df2 = df1.reset_index()

   #######################################
   # 2. Predictions over the next 5 days #
   #######################################

   gas = ['SP95', 'SP98', 'E85','Gazole','GPLc','E10']
   J = [(date.today() + timedelta(days = i+1)).strftime("%Y-%m-%d") for i in range(5)]

   predictions = pd.DataFrame(0, index = np.arange(len(J)), columns = ['Date'] + gas)
   for count, value in enumerate(J):
      predictions['Date'].iloc[-count -1] = J[-count-1]

   df2 = df2[df2['Date'] > str(date.today() - timedelta(weeks= 8))]

   df2['Category'] = 'Historique'
   predictions['Category'] = 'Prévision'
   df3 = pd.concat([df2, predictions])

   for count, value in enumerate(gas):
      if value == 'Date':
         pass
      for j in range(len(J)):
         df3[value].iloc[j-5] = df3[value].iloc[-(j+10):-6].mean(skipna=True)

   #######################################
   #       3. Datavizualization tool     #
   #######################################
   #Reduces vizulization (and prediction base) to the past 8 weeks

   source = ColumnDataSource(df3)

   plot = figure(width = 600,
                  height = 300,
                  x_axis_type='datetime',
                  title = str('Prix journalier moyen (France) - '+ 'SP95'),
                  tools='tap')

   # Creates a javascript hovertool that changes the color 
   # when the user hovers on a particular value, and displays the average price as well as the date 

   plot.add_tools(HoverTool(tooltips =
                           [('Date', '@Date{%F}'), 
                           ('Prix moyen (€)', '$y'),
                           ('Source', '@Category')],
                           formatters =
                           {'@Date': 'datetime'}))

   gas = ['SP95', 'SP98', 'E85','Gazole','GPLc','E10']

   index_cmap = factor_cmap('Category', 
                  palette = ['#4292c6', '#EE6677'], 
                  factors = sorted(df3.Category.unique()))

   circle = plot.circle(x = "Date",
                        y = "SP95", 
                        line_color = index_cmap,
                        fill_color = index_cmap,
                        source = source, size = 17,
                        fill_alpha=0.4,
                        hover_color='limegreen',
                        legend_field= 'Category',
                        selection_color="gold",
                        nonselection_fill_alpha=0.2,
                        nonselection_fill_color="grey",
                        nonselection_line_color="grey",
                        nonselection_line_alpha=1.0)

   # Creates a dropdown menu to select the desired gas type, and then update the underlying data selection
   dropdown = Dropdown(label="Choisissez votre carburant", menu = gas, button_type = 'primary')

   code = """
   let s = source.data
   s["SP95"] = s[this.item]
   plot.title.text = 'Prix journalier moyen (France) - ' + this.item 
   plot.change.emit()
   source.change.emit();
   """
   dropdown.js_on_event("menu_item_click", CustomJS(args=dict(source = source, plot = plot, legend = plot.legend.items[0]), code=code))

   # Creates a date-slider that allows the user to select its desired timeframe from vizualization
   startdate, enddate = df3['Date'].iat[0] , df3['Date'].iat[-1]
   date_range_slider = DateRangeSlider(
   title="Date", start=startdate, end=enddate,
   value=(startdate, enddate), step=1, width=300)

   callback = CustomJS(args=dict(plot = plot), code="""
   plot.x_range.start = cb_obj.value[0]
   plot.x_range.end = cb_obj.value[1]
   plot.x_range.change.emit()
   """)

   date_range_slider.js_on_change('value', callback)
   plot.grid.grid_line_alpha = 0.4
   plot.axis.minor_tick_out = 0
   plot.axis.major_tick_out = 4
   plot.legend.background_fill_alpha = 0.0
   plot.legend.border_line_alpha = 0.0
   plot.toolbar.logo = None
   plot.toolbar_location = None
   plot.title.align = 'center'
   plot.yaxis[0].formatter = PrintfTickFormatter(format = '€ %0.2f')
   plot.xaxis[0].formatter = DatetimeTickFormatter(days = ["%d-%b"], months = ['%d-%b'])
   layout = column(children = [plot, dropdown, date_range_slider], sizing_mode = "stretch_width")
   script1, div1 = components(layout)
   jss= CDN.js_files[0]
   widget = CDN.js_files[2]


   markers = []
   filters = []
   automates = []
   #we retrieve the data entered by the user in the form
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
         marker = {
            'lat': gs.coords.latitude,
            'lon': gs.coords.longitude,
            'popup': ', '.join([f.name + ': ' + str(f.prix) + 'euros ' + '(as of ' + str(f.maj)[:10] + ')' for f in gs.fuels]) + ', Automate 24-24: ' + gs.horaires_automate_24_24,
            'maps_link': gmaps_link
         }
         if gs == cheaper_gs: #if a marker doesn't appear, it is because it has been combined with another one (the order of the if conditions maters!)
            marker['color'] = 'green'
         elif gs == closest_gs:
            marker['color'] = 'yellow'
         elif gs == best_gs:
            marker['color'] = 'orange'
         else:
            marker['color'] = 'blue'
         
         markers.append(marker)
      
   # we pass the data to the template (html file)
   return render_template('index.html',markers=markers,
                  script1 = script1,
                  div1 = div1,
                  jss = jss,
                  widget = widget)

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8080, debug=True)