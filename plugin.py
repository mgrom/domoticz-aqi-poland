# A Python plugin for Domoticz to create devices with PM2.5 and PM10 based on http://api.gios.gov.pl
#
# Author: mgrom
#
# v 0.1
"""
<plugin key="AQIgovpl" name="AQI.gov.pl" author="mgrom" version="0.1" wikilink="http://api.gios.gov.pl" externallink="https://github.com/mgrom/Aqi.gov.pl">
    <params>
		<param field="Mode1" label="PM2.5 Sensor" width="200px" required="true" default="0"/>
		<param field="Mode2" label="PM10 Sensor" default="0" width="200px" required="true"  />
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

sys.path.append(sys.prefix+'/local/lib/python3.5/dist-packages')
sys.path.append(sys.prefix+'/local/lib/python3/dist-packages')

import requests
import json


class AqiStatus:

    def getValue(self, param):
        url = "http://api.gios.gov.pl/pjp-api/rest/data/getData/" + param
        response = requests.get(url)

        values = response.json().get("values")

        for status in values:
            if status.get("value") != None:
                return status

    def __init__(self, pm25Sensor, pm10Sensor):
        self.pm25 = self.getValue(pm25Sensor)
        self.pm10 = self.getValue(pm10Sensor)


class BasePlugin:

    def __init__(self):
        self.nextpoll = datetime.datetime.now()
        self.inProgress = False

        self.PM25 = 10
        self.PM10 = 20

        return

    def postponeNextPool(self, seconds=3600):
        self.nextpoll = (datetime.datetime.now() + datetime.timedelta(seconds=seconds))
        return self.nextpoll


    def onStart(self):
        Domoticz.Debug()
        if Parameters["Mode6"] == 'Debug':
            self.debug = True
        else:
            self.debug = False
        Domoticz.Debugging(self.debug)

        self.pollinterval = int(Parameters["Mode3"]) * 60

        if len(Devices) == 0:
            Domoticz.Device(Name="External PM 2.5", Unit=self.PM25, TypeName="PM 2.5", Used=1).Create()
            Domoticz.Device(Name="External PM 10", Unit=self.PM10, TypeName="PM 10", Used=1).Create()

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
        aqi = AqiStatus(Parameters["Mode1"], Parameters["Mode2"])
        Domoticz.Debug("PM 2.5: " + str(round(aqi.pm10.get("value"))))

        Devices[self.PM10].Update(
            sValue=str(aqi.pm10.get("date")),
            nValue=int(round(aqi.pm10.get("value")))
        )
        Devices[self.PM25].Update(
            sValue=str(aqi.pm25.get("date"))
            nValue=int(round(aqi.pm25.get("value")))
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

