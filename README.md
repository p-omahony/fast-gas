# fast-gas  
To run :   
- have python>=3.8 installed    
- create a virtual environment and activate it: `virtualenv env` then `source env/bin/activate`     
- `pip install -r requirements.txt`     
- `python -B app.py`  

## Run with Docker
At the root of the project:   
- build the image: `docker build -t fast-gas:latest .`    
- run with logs displayed: `docker run -it -p 8080:8080 fast-gas` / or run in background `docker run -d -p 8080:8080 fast-gas`  