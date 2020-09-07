import urllib.request, urllib.parse, urllib.error
import sqlite3
import json
import codecs
import ssl

#Google Maps Geocoding API URL and Key
api_serviceurl = "https://maps.googleapis.com/maps/api/geocode/json?"        
api_key = "AIzaSyCueqPY9MNML6sdXn-ZPOdkdMKoxvqqNQg"                                                 

#Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

#Open a sqlite database
conn = sqlite3.connect('geodata_index.sqlite')
cur = conn.cursor()

#Delete any existing table with name 'Locations'
cur.execute('''DROP TABLE IF EXISTS Locations''')

#Create a new table with name 'Locations'
cur.execute('''CREATE TABLE Locations (address TEXT, geodata TEXT)''')


#----------Function to take input values----------
def input_values():
    #Take the no. and name of locations as input
    try:
        no_of_locations = int(input("Enter the no. of places to locate on map: "))
    except:
        print("ERROR, You didn't enter an integer.")
        no_of_locations = 0

    list_of_locations = []

    if no_of_locations==1:
        print("Now, Enter the name of the place:")
    elif no_of_locations>1:
        print("Now, Enter the name of the places:")

    for _ in range(no_of_locations):
        location_name = input()
        list_of_locations.append(location_name)

    print('')
    
    return list_of_locations
#-----------------------------------------------------------------------------------------------

    
#----------Function to retrieve the geodata----------
def retrieve_data(location_name):
    address = location_name.strip()

    parameters = dict()
    parameters["address"] = address
    parameters['key'] = api_key

    #Generate the url using urlencode
    url = api_serviceurl + urllib.parse.urlencode(parameters)

    #Check for Internet connection and retrieve the geodata
    try:
        fhand = urllib.request.urlopen(url, context=ctx)
    except:
        print("Device not connected to Internet.\n")
        return ['break',0]

    print('Retrieving', url)
    
    #Read and decode the geodata
    fhand = fhand.read()
    geodata = fhand.decode()

    print('Retrieved', len(geodata), 'characters')

    #Check for Unicode errors
    try:
        js = json.loads(geodata)

        #Check for correct response from the api_serviceurl
        if 'status' not in js or (js['status'] != 'OK' and js['status'] != 'ZERO_RESULTS') :
            print('======= Failed To Retrieve The Geodata =======')
            print(geodata)
            return ['break',0]

        print(geodata)

    except:
        print(geodata)
        return ['continue',0]

    print('')

    #Return the geodata with 'OK' status to the main function
    if ('status' in js and js['status'] == 'OK'):
        return [address,geodata]
    else:
        return ['continue',0]
#-----------------------------------------------------------------------------------------------
   

#----------Function to insert the geodata into the table----------
def insert_data(address,geodata):
    cur.execute('''INSERT INTO Locations (address, geodata)
            VALUES ( ?, ? )''', (memoryview(address.encode()), memoryview(geodata.encode()) ) )
    conn.commit()
#-----------------------------------------------------------------------------------------------


#----------Function to create the javascript file----------
def write_on_js():
    #Query the geodata from the table
    cur.execute('SELECT * FROM Locations')

    #Open the Javascript file
    fhand = codecs.open('geodata_locate.js', 'w', "utf-8")
    
    fhand.write("myData = [\n")

    count = 0

    #Write the geodata to the Javascript file
    for row in cur :
        location_name = row[0].decode() + ','
        data = str(row[1].decode())

        #Check for Unicode errors
        try:
            js = json.loads(str(data))
        except:
            continue

        latitude = js["results"][0]["geometry"]["location"]["lat"]
        longitude = js["results"][0]["geometry"]["location"]["lng"]

        if latitude == 0 or longitude == 0 :
            continue

        location = js['results'][0]['formatted_address']
        location = location.replace("'", "")
        try :
            print(location_name, location, latitude, longitude)
            print('')
            count = count + 1
            if count > 1 : fhand.write(",\n")
            output = "["+str(latitude)+","+str(longitude)+", '"+location_name+" "+location+"']"
            fhand.write(output)
        except:
            continue
    fhand.write("\n];\n")

    #Close the Javascript file
    fhand.close()

    return count
#-----------------------------------------------------------------------------------------------


#----------Main Function----------
#Call the 'input_values()' function to take input
list_of_locations=input_values()

#Retrieve the geodata for each location in the list and insert into the table
for location_name in list_of_locations:
    address,geodata = retrieve_data(location_name)
    if address=='break':
        break
    elif address=='continue':
        continue
    else:
        insert_data(address,geodata)

#Call the 'write_on_js()' function
count=write_on_js()
 
#Close the sqlite database
cur.close()

if count==1:
    print(count, "place located on Geodata map.")
elif count>1:
    print(count, "places located on Geodata map.")
else:
    print("No place located on Geodata map.")

if count>0:
    print("Open geodata_map.html to view the Geodata map.")

#=======================End of Program========================
