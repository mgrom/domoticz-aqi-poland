import sys
import datetime
from math import cos, asin, sqrt

sys.path.append(sys.prefix+'/local/lib/python3.5/dist-packages')
sys.path.append(sys.prefix+'/local/lib/python3/dist-packages')
sys.path.append(sys.prefix+'/lib/site-packages')

import requests
import json
import pprint


def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((float(lat2)-float(lat1))*p)/2 + cos(float(lat1)*p)*cos(float(lat2)*p) * (1-cos((float(lon2)-float(lon1))*p)) / 2
    return 12742 * asin(sqrt(a))

def closest(data, v):
    return min(data, key=lambda p: distance(v.get('gegrLat'),v.get('gegrLon'),p.get('gegrLat'),p.get('gegrLon')))


class AqiStatus:

    def getApiData(self, url):
        response = requests.get(url)
        return response.json()

    def getValue(self, param):
        # url = "http://api.gios.gov.pl/pjp-api/rest/data/getData/" + param
        # response = requests.get(url)

        values = self.getApiData("http://api.gios.gov.pl/pjp-api/rest/data/getData/"+param).get("values")

        for status in values:
            if status.get("value") != None:
                return status

    def __init__(self):
        self.location = self.getLocation()
        self.name = self.location.get("stationName")
        self.address = self.location.get("addressStreet")
        self.stationId = self.location.get("id")
        self.sensors = self.getSensors()

    
    def getSensors(self):
        sensors = self.getApiData("http://api.gios.gov.pl/pjp-api/rest/station/sensors/" + str(self.stationId))
        retSensors = {}
        unit = 0
        for sensor in sensors:
            unit=unit+10
            retSensors[sensor.get("param").get("paramCode")] = {
                "paramName": sensor.get("param").get("paramName"), 
                "id": sensor.get("id"), 
                "paramCode": sensor.get("param").get("paramCode"),
                "value": self.getValue(str(sensor.get("id"))),
                "unit": unit
            }
        return retSensors


    def getLocation(self):
        # location = str(Settings.get("Location")).split(";")
        locationDict = {}
        locationDict["gegrLat"] = '52.294653'
        locationDict["gegrLon"] = '21.036188'

        stations = self.getApiData("http://api.gios.gov.pl/pjp-api/rest/station/findAll")
        #lati 49-55
        #long 14-24
        return closest(stations, locationDict)


global aqi
aqi = AqiStatus()

pprint.PrettyPrinter(indent=4).pprint(aqi.location)
print(str(aqi.location))
for key, value in aqi.sensors.items():
    print(str(value.get("unit")))
    print(value.get("value"))
    print(aqi.location.get("stationName")+" "+key)

