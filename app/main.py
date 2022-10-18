from os import sendfile
from flask import Flask, render_template, request,send_from_directory 
from auth import auth
from events import events
from organization import organization
import requests

# What we use to render a template, aka our frontend
app = Flask(__name__,template_folder="./frontend")
app.register_blueprint(organization, url_prefix="/organization")
app.register_blueprint(events, url_prefix="/events")
app.register_blueprint(auth, url_prefix="/auth")

def getGeoLocation(location):
   query = f"https://nominatim.openstreetmap.org/search?q={location}&format=json"
   res = requests.get(query).json()
   return res

@app.get("/location/<string:query_string>")
def getLocation(query_string):
   queryRes= getGeoLocation(query_string) # JSON
   response = []

   for res in queryRes:
      response.append({"lat":res['lat'],"lon":res['lon'], "display_name": res['display_name']})

   return response 

"""
All the below are frontend Routes
"""
@app.route('/', methods=['GET', 'POST'])
def home():
   return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
   return render_template('login.html')

@app.route('/organizationPage', methods=['GET', 'POST'])
def organizationPage():
   return render_template('organizationPage.html')

@app.route('/userPage', methods=['GET', 'POST'])
def userPage():
   return render_template('userPage.html')

@app.route('/eventCreation', methods=['GET', 'POST'])
def eventCreation():
   return render_template('eventCreation.html')

@app.route('/joinEvent/<string:org>', methods=['GET', 'POST'])
def joinEvent(org):
   return render_template('joinEvent.html',org=org)




# Dynamic Routes
@app.route('/checkin/<string:id>', methods=['GET', 'POST'])
def userOrgPage(id):
   print(id)
   return render_template('checkin.html', pageId=id)

@app.route('/eventInfo/<string:id>', methods=['GET', 'POST'])
def eventInfo(id):
   return render_template('eventInfo.html', pageId=id)



# Return images
@app.get('/img/<string:img>')
def returnImage(img):
   return send_from_directory("img",img)

@app.get('/js/<string:file>')
def returnFile(file):
   return send_from_directory("js",file)

@app.get('/css/<string:file>')
def returnCSS(file):
   return send_from_directory("css",file)



