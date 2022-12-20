from flask import Flask, render_template

app=Flask(__name__)

@app.route('/')
def root():
   markers=[
   {
    'lat':48.71108385372915,
    'lon':2.2076466976090274,
    'popup':'ENSAE'
    }
   ]
   return render_template('index.html',markers=markers )

if __name__ == '__main__':
   app.run(host="localhost", port=8080, debug=True)