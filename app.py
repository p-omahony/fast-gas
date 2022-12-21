from flask import Flask, render_template, request

app=Flask(__name__)

@app.route('/', methods=('GET', 'POST'))
def root():
   #we retrieve the data entered by the user in the form
   if request.method == 'POST':
      gas = request.form['gas']
      location = request.form['location']
      cp = request.form['cp']
      distance = request.form['distance']
      car = request.form['car']
   markers=[
   {
    'lat':48.71108385372915,
    'lon':2.2076466976090274,
    'popup':'ENSAE'
    }
   ]
   # we pass the data to the template (html file)
   return render_template('index.html',markers=markers )

if __name__ == '__main__':
   app.run(host="localhost", port=8080, debug=True)