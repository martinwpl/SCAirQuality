################################################################################
#
#  The script takes in a db table name as a command line parameter.
#  It validates that the name is one of two tables:
#    - monitor_data - Data that is retrieved every 5 minutes
#    - nightly_monitor_data - Data that is retrieved once a day
#  The script then creates the database table if it doesn't already
#  exists.  This table uses the purple air json file tags as
#  it column names.  Here is the definition of the column names
#  with unused columns noted:
#    - ID - PurpleAir Sensor ID
#    - ParentID - The PurpleAir Sensor Id of the "parent" entr for the B Channel
#    - Label - The "name" that appears on the map for this sensor
#    - DEVICE_LOCATIONTYPE - <NOT USED>
#    - THINGSPEAK_PRIMARY_ID - Thingspeak Channel ID for Primary Data
#    - THINGSPEAK_PRIMARY_ID_READ_KEY - Thingspeak Read Key for Primary Data
#    - THINGSPEAK_SECONDARY_ID - Thingspeak Channel ID for Secondary Data
#    - THINGSPEAK_SECONDARY_ID_READ_KEY - Thingspeak Read Key for Secondary Data
#    - Lat - Latitude Position Info
#    - Lon - Longitude Position Info
#    - PM2_5Value - Current PM2.5 Value
#    - LastSeen - <NOT USED>
#    - State - <NOT USED>
#    - Type - Sensor Type (PMS5003, PMS1003, BME280, etc.)
#    - Hidden - Hide from public view on map: true/false
#    - Flag - Data flagged for unusally high readings
#    - DEVICE_BRIGHTNESS - <NOT USED>
#    - DEVICE_HARDWAREDISCOVERED - <NOT USED>
#    - DEVICE_FIRMWAREVERSION - <NOT USED>
#    - Version - <NOT USED>
#    - LastUpdateCheck - <NOT USED>
#    - Uptime - <NOT USED>
#    - RSSI - <NOT USED>
#    - isOwner - Currently logged in user is the sensor owner
#    - A_H - True if sensor output is downgraded or marked for hardware issues
#    - temp_f - Current temperature in F
#    - humidity - Current humidity in %
#    - pressure - Current pressure in Millibars
#    - AGE - Sensor data age (when data was last received) in minutes
#    - Stats - Secondary json blob containing the following data:
#      - v - Real time or current PM2.5 value
#      - v1 - Short term (10 minute average)
#      - v2 - 30 minute average
#      - v3 - 1 hour average
#      - v4 - 6 hour average
#      - v5 - 24 hour average
#      - v6 - One week average
#      - pm - Real time or current PM2.5 Value
#      - lastModified - Last modified time stamp for averages
#      - timeSinceModified - Time between last two readings in milliseconds
# The script then populate the database table with data retrieved for a list of
# stations hard-coded into this script.
#
################################################################################

################################################################################
#
# Python imports - Equivalent to includes in c.
#
################################################################################
import sys
import json
import requests
import mysql.connector
from datetime import datetime

################################################################################
#
# Read the command line argument and ensure it is valid.
#  - As a reminder from the description above, this selects which
#    database to store the current purple air data to.
#
################################################################################
TABLE_NAME = ""
if len(sys.argv) != 2:
    print("Invalid number of arguments!")
    print("  USAGE: script.py table_name")
    exit()
else:
    if sys.argv[1] == "monitor_data":
        TABLE_NAME = sys.argv[1]
    elif sys.argv[1] == "nightly_monitor_data":
        TABLE_NAME = sys.argv[1]
    else:
        print("Invalid table name argument: ", sys.argv[1])
        print("  Valid Tables: monitor_data or nightly_monitor_data")
        exit()

################################################################################
#
# Connect to the MYSQL database on this machine, check to see if the selected
# table exists.  If it does not exist, create it.
#
################################################################################
# Connect to the mysql database.
mydb = mysql.connector.connect(
  host="localhost",
  user="airdata",
  passwd="AESl0uis!",
  database="airdata"
)
mycursor = mydb.cursor()

# Check if the purpleair table has been created.
mycursor.execute("SHOW TABLES")
table_exists = False
for table_name in mycursor:
    if table_name[0] == TABLE_NAME:
        table_exists = True

# Create a string to is the MYSQL command to create the desired table.
# I will do this one table column at a time so that it is easy to
# follow.   In the end the create table command should look something
# like: "CREATE TABLE monitor_data (ID INT, PM2_5 FLOAT, lastModified DATETIME)"
# but with more fields of course.
MYSQL = "CREATE TABLE " + TABLE_NAME + " ("
MYSQL = MYSQL + "ID INT" + ", "
MYSQL = MYSQL + "ParentID VARCHAR(10)" + ", "
MYSQL = MYSQL + "Label VARCHAR(128)" + ", "
#    - DEVICE_LOCATIONTYPE - <NOT USED> - maybe VARCHAR(20)
MYSQL = MYSQL + "THINGSPEAK_PRIMARY_ID INT" + ", "
MYSQL = MYSQL + "THINGSPEAK_PRIMARY_ID_READ_KEY VARCHAR(20)" + ", "
MYSQL = MYSQL + "THINGSPEAK_SECONDARY_ID INT" + ", "
MYSQL = MYSQL + "THINGSPEAK_SECONDARY_ID_READ_KEY VARCHAR(20)" + ", "
MYSQL = MYSQL + "Lat FLOAT" + ", "
MYSQL = MYSQL + "Lon FLOAT" + ", "
MYSQL = MYSQL + "PM2_5Value FLOAT" + ", "
#    - LastSeen - <NOT USED> - maybe BIGINT
#    - State - <NOT USED> - maybe VARCHAR(20)
MYSQL = MYSQL + "Type VARCHAR(64)" + ", "
MYSQL = MYSQL + "Hidden VARCHAR(10)" + ", "
MYSQL = MYSQL + "Flag VARCHAR(10)" + ", "
#    - DEVICE_BRIGHTNESS - <NOT USED> - maybe VARCHAR(20)
#    - DEVICE_HARDWAREDISCOVERED - <NOT USED> - maybe VARCHAR(128)
#    - DEVICE_FIRMWAREVERSION - <NOT USED> - maybe VARCHAR(20)
#    - Version - <NOT USED> - maybe VARCHAR(10)
#    - LastUpdateCheck - <NOT USED> - maybe VARCHAR(20)
#    - Uptime - <NOT USED> - maybe INT
#    - RSSI - <NOT USED> - maybe INT
MYSQL = MYSQL + "isOwner INT" + ", "
MYSQL = MYSQL + "A_H VARCHAR(10)" + ", "
MYSQL = MYSQL + "temp_f FLOAT" + ", "
MYSQL = MYSQL + "humidity FLOAT" + ", "
MYSQL = MYSQL + "pressure FLOAT" + ", "
MYSQL = MYSQL + "AGE INT" + ", "
MYSQL = MYSQL + "v FLOAT" + ", "
MYSQL = MYSQL + "v1 FLOAT" + ", "
MYSQL = MYSQL + "v2 FLOAT" + ", "
MYSQL = MYSQL + "v3 FLOAT" + ", "
MYSQL = MYSQL + "v4 FLOAT" + ", "
MYSQL = MYSQL + "v5 FLOAT" + ", "
MYSQL = MYSQL + "v6 FLOAT" + ", "
MYSQL = MYSQL + "pm FLOAT" + ", "
MYSQL = MYSQL + "lastModified DATETIME" + ", "
MYSQL = MYSQL + "timeSinceModified BIGINT" + ")"

# Create the table in the database using the mysql command from above.
if not table_exists:
    mycursor.execute(MYSQL)
    print("Create Table: ", TABLE_NAME)

################################################################################
#
# Get raw json data from Purple Air website.
#
################################################################################
PURPLE_AIR_WEBSITE = 'http://www.purpleair.com/json'
response = requests.get(PURPLE_AIR_WEBSITE)
raw_data = response.text

################################################################################
#
# Convert the raw data into a python dictionary, parse the data for the listed
# air monitors, and convert the raw sub-data into this array.
#
################################################################################
# A hard-coded list of all the air quality monitors we care about.
# At a later time we can load this list from a file.

monitor_list = open("monitor_list.json", "r")
region_list = json.loads(monitor_list.read())
ID_list = region_list["Regions"]
sunshine_coast = ID_list[0]
north = ID_list[1]
prince_george = ID_list[2]
interior = ID_list[3]
island = ID_list[4]

MONITOR_IDS = sunshine_coast["Stations"]
print(sunshine_coast["Stations"])

# Convert the data containing all purple air monitors into json.
json_data = json.loads(raw_data)

# Parse the json file to create an array of the sunshine coast data.
local_array = []
monitor_array = json_data["results"]
for item in monitor_array:
    monitor_id = item["ID"]
    if monitor_id in MONITOR_IDS:
        local_array.append(item)

# Go through the local_array and add the stats the the array item
# instead of being a sub-array.
for item in local_array:
    # convert stats text in python dictionary
    stats = json.loads(item["Stats"])

    # Remove the stats item from the dictionary
    del item["Stats"]

    # Insert stats dictionary into back into rest of data.
    item.update(stats)


################################################################################
#
# Insert data from each monitor into the SQL database.
#
################################################################################
for monitor in local_array:
    # Get the timestamp from the monitor data and convert to SQL date format.
    dt = datetime.fromtimestamp(monitor["lastModified"]/1000)

    # Create SQL string to insert a row into the database table.
    sql = "INSERT INTO " + TABLE_NAME + " (ID, ParentID, Label, THINGSPEAK_PRIMARY_ID, THINGSPEAK_PRIMARY_ID_READ_KEY, THINGSPEAK_SECONDARY_ID, THINGSPEAK_SECONDARY_ID_READ_KEY, Lat, Lon, PM2_5Value, Type, Hidden, Flag, isOwner, A_H, temp_f, humidity, pressure, AGE, v, v1, v2, v3, v4, v5, v6, pm, lastModified, timeSinceModified) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )"

    # Create a list of the data we are going to insert into the table.
    val = (str(monitor.get("ID", 0)), str(monitor.get("ParentID", "null")), monitor.get("Label", "null"), str(monitor.get("THINGSPEAK_PRIMARY_ID", 0)), monitor.get("THINGSPEAK_PRIMARY_ID_READ_KEY", "null"), str(monitor.get("THINGSPEAK_SECONDARY_ID", 0)), monitor.get("THINGSPEAK_SECONDARY_ID_READ_KEY", "null"), str(monitor.get("Lat", 0)), str(monitor.get("Lon", 0)), str(monitor.get("PM2_5Value", 0)), monitor.get("Type", "null"), monitor.get("Hidden", "null"), str(monitor.get("Flag", "null")), str(monitor.get("isOwner", 0)), str(monitor.get("A_H", "null")), str(monitor.get("temp_f", 0)), str(monitor.get("humidity", 0)), str(monitor.get("pressure", 0)), str(monitor.get("AGE", 0)), str(monitor.get("v", 0)), str(monitor.get("v1", 0)), str(monitor.get("v2", 0)), str(monitor.get("v3", 0)), str(monitor.get("v4", 0)), str(monitor.get("v5", 0)), str(monitor.get("v6", 0)), str(monitor.get("pm", 0)), dt, str(monitor.get("timeSinceModified", "null")))

    # Insert the data into the table.
    print("**********************INSERTING DATA**********************\n", sql, val)
    mycursor.execute(sql, val)
    mydb.commit()
