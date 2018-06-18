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
import os

if os.name == 'nt':
    sys.path.append(sys.prefix+"\\lib\\site-packages")
    print(sys.prefix+"\\lib\\site-packages")
else:
    sys.path.append(sys.prefix+'/local/lib/python3.5/dist-packages')
    sys.path.append(sys.prefix+'/local/lib/python3/dist-packages')



import requests
import json
import datetime
from math import cos, asin, sqrt

class AqiStatus:

    def distance(self, lat1, lon1, lat2, lon2):
        Domoticz.Log("Distance")
        p = 0.017453292519943295
        a = 0.5 - cos((float(lat2)-float(lat1))*p)/2 + cos(float(lat1)*p)*cos(float(lat2)*p) * (1-cos((float(lon2)-float(lon1))*p)) / 2
        return 12742 * asin(sqrt(a))

    def closest(self, data, v):
        Domoticz.Log("closest")
        return min(data, key=lambda p: self.distance(v.get('gegrLat'),v.get('gegrLon'),p.get('gegrLat'),p.get('gegrLon')))

    def getApiData(self, url):
        Domoticz.Log("getapidata")
        response = requests.get(url)
        try:
            if response.status_code == 503:
                Domoticz.Log("503")
                response.raise_for_status()
            else:
                Domoticz.Log("getApiData "+response.status_code)
        except requests.exceptions.HTTPError as e: 
            if e.response.status_code == 503:
                Domoticz.Log("Api unavailable")
                return {"error": True}        
            # else:
            #     Domoticz.Log("get apidata: else")
            #     return {
            #         "error": True,
            #         "message": response.status_code
            #     }
        Domoticz.Log("getApiData: " + response.json())
        return response.json()

    def getValue(self, param):
        Domoticz.Log("getvalues")
        values = self.getApiData("http://api.gios.gov.pl/pjp-api/rest/data/getData/"+param).get("values")

        for status in values:
            if status.get("value") != None:
                return status

    def getSensors(self):
        Domoticz.Log("getSensors")
        sensors = self.getApiData("http://api.gios.gov.pl/pjp-api/rest/station/sensors/" + str(self.stationId))
        retSensors = {}
        unit = 0
        for sensor in sensors:
            unit = unit + 10
            retSensors[sensor.get("param").get("paramCode")] = {
                "paramName": sensor.get("param").get("paramName"), 
                "id": sensor.get("id"), 
                "paramCode": sensor.get("param").get("paramCode"),
                "value": self.getValue(str(sensor.get("id"))),
                "unit": unit
            }
        Domoticz.Log("getSensors: "+str(retSensors))
        return retSensors


    def getLocation(self):
        Domoticz.Log('getLocation')
        location = str(Settings.get("Location")).split(";")
        locationDict = {}
        locationDict["gegrLat"] = location[0]
        locationDict["gegrLon"] = location[1]

        Domoticz.Log('before getApiData')
        stations = self.getApiData("http://api.gios.gov.pl/pjp-api/rest/station/findAll")
        if stations.get("error") == True:
            return stations
        else:
            return self.closest(stations, locationDict)

    def __init__(self):
        print('aqi init')
        self.location = self.getLocation()
        if(self.location.get("error") == False):
            self.name = self.location.get("stationName")
            self.address = self.location.get("addressStreet")
            self.stationId = self.location.get("id")
            self.sensors = self.getSensors()



class BasePlugin:   

    def __init__(self):
        print('plugin init')
        self.nextpoll = datetime.datetime.now()
        self.inProgress = False
        # Domoticz.Debug(sys.version)
        # Domoticz.Log(sys.version)
        # self.pollinterval = int(Parameters["Mode3"]) * 60
        # self.aqi = AqiStatus()

        return

    def postponeNextPool(self, seconds=3600):
        self.nextpoll = (datetime.datetime.now() + datetime.timedelta(seconds=seconds))
        return self.nextpoll


    def onStart(self):
        Domoticz.Log(sys.version)
        Domoticz.Log('onStart')
        aqi = self.getAqiStatus()
        Domoticz.Log("aqi.location: "+str(aqi.location))
        if Parameters["Mode6"] == 'Debug':
            self.debug = True
        else:
            self.debug = False
        Domoticz.Debugging(self.debug)

        self.pollinterval = int(Parameters["Mode3"]) * 60

        if len(Devices) == 0 and aqi.location.get("error") == False:
            for key, value in aqi.sensors.items():
                Domoticz.Log(str(key)+": "+str(value))
                Domoticz.Device(Name=aqi.name+" "+aqi.address+" "+str(key), TypeName="Custom", Unit=int(value.get("unit")), Used=0, Image=19).Create()

        self.onHeartbeat(fetch=False)

    def onStop(self):
        Domoticz.Log('onStop')
        Domoticz.Debugging(0)

    def onConnect(self, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Data, Status, Extra):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log(
            "onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(
            Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self, fetch=False):
        Domoticz.Log('onHeartbeat called')
        now = datetime.datetime.now()
        self.pollinterval = int(Parameters["Mode3"]) * 60
        
        if not fetch:
            if self.inProgress or (now < self.nextpoll):
                Domoticz.Log('skip processing')
                return
        
        self.postponeNextPool(seconds=self.pollinterval)

        try:
            Domoticz.Log("onHeartbeat in progress")
            self.inProgress = True

            self.doUpdate()
        except Exception as e:
            Domoticz.Error("Unrecognized error: %s" % str(e))
        finally:
            self.inProgress = False
        
        return True

    def getAqiStatus(self):
        return AqiStatus()

    def doUpdate(self):
        aqi = self.getAqiStatus()
        if aqi.location.get("error") == False:
            Domoticz.Log("doUpdate in progress")
            for key, value in aqi.sensors.items():
                Domoticz.Log(str(key)+": "+str(value.get("value").get("value")))
                Devices[int(value.get("unit"))].Update(
                    sValue=str(round(value.get("value").get("value"))),
                    nValue=round(value.get("value").get("value"))
                )
            Domoticz.Log("doUpdate finished")
        else:
            Domoticz.Log("No update - api unavailable")
        return

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Status, Description):
    global _plugin
    _plugin.onConnect(Status, Description)

def onMessage(Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect():
    global _plugin
    _plugin.onDisconnect()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Log( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Log("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Log("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Log("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Log("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Log("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Log("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Log("Device LastLevel: " + str(Devices[x].LastLevel))
    return