# A Python plugin for Domoticz to create devices with PM2.5 and PM10 based on http://api.gios.gov.pl
#
# Author: mgrom
#
# v 0.1
"""
<plugin key="AQIgovpl" name="AQI.gov.pl" author="mgrom" version="0.1" wikilink="http://api.gios.gov.pl" externallink="https://github.com/mgrom/Aqi.gov.pl">
    <params>
        <param field="Mode3" label="Check every x minutes" width="40px" default="15" required="true" />
		<param field="Mode6" label="Debug" width="75px">
			<options>
				<option label="True" value="Debug"/>
				<option label="False" value="Normal" default="true" />
			</options>
		</param>
    </params>
</plugin>
"""
import Domoticz
import sys
import datetime
from math import cos, asin, sqrt

sys.path.append(sys.prefix+'/local/lib/python3.5/dist-packages')
sys.path.append(sys.prefix+'/local/lib/python3/dist-packages')

import requests
import json

class AqiStatus:

    def distance(self, lat1, lon1, lat2, lon2):
        p = 0.017453292519943295
        a = 0.5 - cos((float(lat2)-float(lat1))*p)/2 + cos(float(lat1)*p)*cos(float(lat2)*p) * (1-cos((float(lon2)-float(lon1))*p)) / 2
        return 12742 * asin(sqrt(a))

    def closest(self, data, v):
        return min(data, key=lambda p: self.distance(v.get('gegrLat'),v.get('gegrLon'),p.get('gegrLat'),p.get('gegrLon')))

    def getApiData(self, url):
        response = requests.get(url)
        return response.json()

    def getValue(self, param):
        values = self.getApiData("http://api.gios.gov.pl/pjp-api/rest/data/getData/"+param).get("values")

        for status in values:
            if status.get("value") != None:
                return status

    def __init__(self):
        self.location = self.getLocation()
        self.name = self.location.stationName
        self.address = self.location.addressStreet
        self.stationId = self.location.id
        self.sensors = self.getSensors()

    def getSensors(self):
        Domoticz.Debug("getSensors")
        sensors = self.getApiData("http://api.gios.gov.pl/pjp-api/rest/station/sensors/" + str(self.stationId))
        retSensors = {}
        for sensor in sensors:
            retSensors[sensor.get("param").get("paramCode")] = {
                "paramName": sensor.get("param").get("paramName"), 
                "id": sensor.get("id"), 
                "paramCode": sensor.get("param").get("paramCode"),
                "value": self.getValue(str(sensor.get("id")))
            }
        Domoticz.Debug("getSensors: "+str(retSensors))
        return retSensors


    def getLocation(self):
        Domoticz.Debug('getLocation')
        location = str(Settings.get("Location")).split(";")
        locationDict = {}
        locationDict["gegrLat"] = location[0]
        locationDict["gegrLon"] = location[1]

        stations = self.getApiData("http://api.gios.gov.pl/pjp-api/rest/station/findAll")
        return self.closest(stations, locationDict)

class BasePlugin:   

    def __init__(self):
        self.nextpoll = datetime.datetime.now()
        self.inProgress = False

        self.aqi = AqiStatus()

        return

    def postponeNextPool(self, seconds=3600):
        self.nextpoll = (datetime.datetime.now() + datetime.timedelta(seconds=seconds))
        return self.nextpoll


    def onStart(self):
        Domoticz.Debug(str(self.aqi.location))
        if Parameters["Mode6"] == 'Debug':
            self.debug = True
        else:
            self.debug = False
        Domoticz.Debugging(self.debug)

        self.pollinterval = int(Parameters["Mode3"]) * 60

        if len(Devices) == 0:
            for key, value in self.aqi.sensors.items():
                Domoticz.Debug(key+": "+value)
                Domoticz.Device(Name=self.aqi.name+" "+self.aqi.address+" "+key, TypeName="Custom", Unit=int(value.get("unit")), Used=0, Image=7).Create()

        self.onHeartbeat(fetch=False)

    def onStop(self):
        Domoticz.Debug('onStop called')
        Domoticz.Debugging(0)

    def onHeartbeat(self, fetch=False):
        now = datetime.datetime.now()

        if not fetch:
            if self.inProgress or (now < self.nextpoll):
                Domoticz.Debug('skip processing')
                return
        
        self.postponeNextPool(seconds=self.pollinterval)

        try:
            Domoticz.Debug("onHeartbeat in progress")
            self.inProgress = True

            self.doUpdate()
        except Exception as e:
            Domoticz.Error("Unrecognized error: %s" % str(e))
        finally:
            self.inProgress = False
        
        return True

    def doUpdate(self):
        for key, value in self.aqi.sensors.items():
            Devices[str(value.get("unit"))].Update(
                sValue=str(value.get("value")),
                nValue=0
            )


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

