#!/usr/bin/env python
# coding: utf-8

# In[5]:


import requests
import json
import bokeh
import numpy as np
import pandas as pd
from bokeh.plotting import figure,output_file, save
from bokeh.models import ColumnDataSource, Grid, Line, Dropdown, LinearAxis, Plot, HoverTool, CustomJS, Slider, Select, DateRangeSlider
from bokeh.plotting import figure, output_file, save
from bokeh.io import show, curdoc
from bokeh.models import ColumnDataSource, Select
from bokeh.models import Slider
from bokeh.layouts import gridplot,row,column
from bokeh.plotting import figure
from datetime import date

class GasDriver:
    def __init__(self) -> None:
        self.url = 'https://data.economie.gouv.fr/api/records/1.0/search/?dataset=prix-carburants-fichier-instantane-test-ods-copie'

    def query(self, filters=None):
        query = self.url + '&q=&rows=10000&facet=id&facet=adresse&facet=ville&facet=prix_maj&facet=prix_nom&facet=cp&facet=com_arm_name&facet=epci_name&facet=dep_name&facet=reg_name&facet=services_service&facet=horaires_automate_24_24'
        if filters is not None:
            for f in filters :
                query += '&refine.%s'%f
        r = requests.get(query)
        res = r.json()
        final = json.dumps(res)
        return final

if __name__ == '__main__' :
    driver = GasDriver()
    data = driver.query(filters=['prix_maj=2022'])

#convert APIs to json file then to pd dataframe   
x = json.loads(data)
df = pd.json_normalize(x, 'records')
df1 = df[['fields.prix_nom','fields.prix_valeur','fields.prix_maj']]
df1 = df1.rename(columns={'fields.prix_nom': "Carburant", 'fields.prix_valeur': "Prix",'fields.prix_maj': "Date"})


#remove timestamps to keep only the date, with date format
for i in range(len(df1)):
    df1.iloc[i, 2] = str(df1.iloc[i, 2])[:10]
    
df1['Date'] = pd.to_datetime(df1['Date'], format = '%Y-%m-%d')
df1 = df1.sort_values(by=['Date'])

#to keep only the value we want, anc convert Carburant to columns, to make it easier to manipulate afterwards
df2 = pd.pivot_table(df1,
                     values = 'Prix',
                     index = ['Date'],
                    columns = ['Carburant']
                     ,aggfunc=np.mean)
df2= df2.reset_index()


#Section for data visualization
source = ColumnDataSource(df2)

# figure
fig = figure(plot_width = 1000,
             plot_height = 600,
             tools="pan, wheel_zoom, box_zoom, reset",
             x_axis_type='datetime',
            x_axis_label="Day",
           y_axis_label="Daily average price")

#create a JS hovertool that changes the color when on a particular value
# displays the average price as well as the date 
fig.add_tools(HoverTool(tooltips=[('Date', '@Date{%F}'), 
                                  ('Prix moyen', '$y')],
                        formatters = {'@Date': 'datetime'}))

gas = ['SP95', 'SP98', 'E85','Gazole','GPLc','E10']

circle = fig.circle(x = "Date", y = "SP95" , source = source, size = 20, fill_alpha=0.4, hover_color="red")

# dropdown menu to select the desired carburant, and then ubpdate the underlying data selection
dropdown = Dropdown(label="Choisissez votre carburant", menu = gas, button_type = 'primary')

code = """
    let s = source.data
    s["SP95"] = s[this.item]
    source.change.emit();
"""

dropdown.js_on_event("menu_item_click", CustomJS(args={"source": source}, code=code))

# date-slider that let the user select its desired timeframe
startdate=df2['Date'].iat[0]
enddate=df2['Date'].iat[-1]

date_range_slider = DateRangeSlider(
    title="Date", start=startdate, end=enddate,
    value=(startdate, enddate), step=1, width=300)

callback = CustomJS(args=dict(fig = fig), code="""
    fig.x_range.start = cb_obj.value[0]
    fig.x_range.end = cb_obj.value[1]
    fig.x_range.change.emit()
    """)
date_range_slider.js_on_change('value', callback)

output_file('average_price_viewer.html')
show(column(children=[fig, dropdown, date_range_slider]))


# In[ ]:




