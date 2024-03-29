# fast-gas
Small project connecting to the French government api allowing to have the real time prices of gasoline displayed interactively on a map. This project allows a follow-up of the evolution of the fuel prices as well as an efficient way to compare different gas stations around you.    

This project is part of the 'Cloud computing' course at ENSAE - IP Paris.    

To run :   
- have python>=3.8 installed    
- create a virtual environment and activate it: `virtualenv env` then `source env/bin/activate`     
- `pip install -r requirements.txt`     
- `python -B app.py`  
- go to 127.0.0.1:8080 with Google Chrome   
- activate/authorize Google Chrome to have your current location  

## Run with Docker
At the root of the project:   
- build the image: `docker build -t fast-gas:latest .`    
- run with logs displayed: `docker run -it -p 8080:8080 fast-gas` / or run in background `docker run -d -p 8080:8080 fast-gas`  
- go to 127.0.0.1:8080 with Google Chrome   
- activate/authorize Google Chrome to have your current location.  
