#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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
from bokeh.resources import CDN, INLINE
from datetime import date, timedelta
from bokeh.transform import factor_cmap
from pmdarima import auto_arima
import warnings
from statsmodels.tsa.arima.model import ARIMA
warnings.filterwarnings('ignore')
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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


def plot():
  
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
    df = df.rename(columns={'fields.prix_nom': "Carburant", 'fields.prix_valeur': "Prix",'fields.prix_maj': "Date"})

    # # We remove timestamps to keep only the date, with date format
    for i in range(len(df)):
        df.iloc[i, 2] = str(df.iloc[i, 2])[:10]

    df['Date'] = pd.to_datetime(df['Date'], format = '%Y-%m-%d')
    df = df.sort_values(by = ['Date'])

    # #to keep only the value we want, anc convert Carburant to columns, to make it easier to manipulate afterwards
    df1 = pd.pivot_table(df,
                        values = 'Prix',
                        index = ['Date'],
                     columns = ['Carburant']
                        ,aggfunc=np.mean)

    df2 = df1.reset_index()

    #######################################
    # 2. Predictions over the next 5 days #
    #######################################

#     #We use the pdm library to perform a time series prediction of the average gas price for the next 5 days
#     gas = ['SP95', 'SP98', 'E85','Gazole','GPLc','E10']
#     J = [(date.today() + timedelta(days = i+1)).strftime("%Y-%m-%d") for i in range(5)]


#     # We remove the NAN values for each type of gas (which can be very different)
#     no_nan = [df1[['Date', i]].dropna() for i in gas]

#     # We obtain the ARMA(p,d,q) parameters for each gas
#     parameters = [auto_arima(no_nan[count][value], suppress_warnings = True, seasonal = True, m = 1).get_params().get("order") for count, value in enumerate(gas)]

#     # We fit each ARMA model on the training value (for simplicity, training values macth the historical data for each gas type)
#     models = [ARIMA(endog = no_nan[count][value], order = parameters[count]).fit() for count, value in enumerate(gas)]

#     start, end = len(df), len(df) + 5
#     forecast = [models[i].predict(start = start , end =  end) for i in range(len(models))]
#     predictions = pd.DataFrame(0, index = np.arange(len(J)), columns = ['Date'] + gas)

#     #We store the day+5 predictions into a dataframe, with the corresponding dates
#     for count, value in enumerate(J):
#         predictions['Date'].iloc[-count -1] = J[-count-1]

#     for i in range(len(gas)):
#         for j in range(len(J)):
#             h = pd.DataFrame(forecast[i])
#             predictions.iloc[j, i+1] = h.iloc[-j+5]



#     #We eventually merge the historical data as well as the forecasted ones, which will be used as our database for plotting
#     df1['Category'] = 'Historique'
#     predictions['Category'] = 'Prévision'
#     df2 = pd.concat([df1, predictions])

    #######################################
    #       3. Datavizualization tool     #
    #######################################
    #Reduces vizulization (and prediction base) to the past 8 weeks
    df2 = df2[df2['Date'] > str(date.today() - timedelta(weeks= 8))]
    source = ColumnDataSource(df2)

    plot = figure(width = 600,
               height = 300,
               x_axis_type='datetime',
               title = str('Prix journalier moyen - '+ 'SP95'))

    plot.grid.grid_line_alpha = 0.4
    plot.axis.minor_tick_out = 0
    plot.axis.major_tick_out = 4
    plot.legend.background_fill_alpha = 0.0
    plot.legend.border_line_alpha = 0.0
    plot.toolbar.logo = None
    plot.toolbar_location = None
    plot.title.align = 'center'
    plot.yaxis[0].formatter = PrintfTickFormatter(format = '€ %0.2f')

    # Creates a javascript hovertool that changes the color 
    # when the user hovers on a particular value, and displays the average price as well as the date 

    plot.add_tools(HoverTool(tooltips=[('Date', '@Date{%F}'), 
                                    ('Prix moyen (€)', '$y')],
                           formatters = {'@Date': 'datetime'}))

    gas = ['SP95', 'SP98', 'E85','Gazole','GPLc','E10']

#     index_cmap = factor_cmap('Category', palette = ['#4292c6', '#EE6677'], 
#                            factors = sorted(df1.Category.unique()))

    circle = plot.circle(x = "Date", y = "SP95", 
                     line_color = '#4292c6',
                     fill_color = '#4292c6',
                     source = source,
                         size = 15,
                         fill_alpha=0.4,
                         hover_color='red',
                        legend_label = 'SP95')

    # Creates a dropdown menu to select the desired gas type, and then update the underlying data selection
    dropdown = Dropdown(label="Choisissez votre carburant", menu = gas, button_type = 'primary')

    code = """
      let s = source.data
      s["SP95"] = s[this.item]
      plot.title.text = 'Prix journalier moyen - ' + this.item 
      legend.change.emit()
      legend.label.value = this.item
      plot.change.emit()
      source.change.emit();
    """

    dropdown.js_on_event("menu_item_click", CustomJS(args=dict(source=source, plot = plot, legend = plot.legend.items[0]), code=code))

    # Creates a date-slider that allows the user to select its desired timeframe from vizualization
    startdate, enddate =df2['Date'].iat[0] , df2['Date'].iat[-1]

    date_range_slider = DateRangeSlider(
      title="Date", start=startdate, end=enddate,
      value=(startdate, enddate), step=1, width=300)

    callback = CustomJS(args=dict(plot = plot), code="""
      plot.x_range.start = cb_obj.value[0]
      plot.x_range.end = cb_obj.value[1]
      plot.x_range.change.emit()
      """)
    date_range_slider.js_on_change('value', callback)

    layout = column(children = [plot, dropdown, date_range_slider], sizing_mode = "stretch_width")
#     show(layout)
    script1, div1 = components(layout)
    jss= CDN.js_files[0]
    widget = CDN.js_files[2]
    return render_template('index.html',
                  script1 = script1,
                  div1 = div1,
                  jss = jss,
                  widget = widget)