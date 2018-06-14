# A Python plugin for Domoticz to create devices with PM2.5 and PM10 based on http://api.gios.gov.pl
#
# Author: mgrom
#
# v 0.1
"""
<plugin key="AQIgovpl" name="AQI.gov.pl" author="mgrom" version="0.1" wikilink="http://api.gios.gov.pl" externallink="https://github.com/mgrom/Aqi.gov.pl">
    <params>
		<param field="pm25" label="PM2.5 Sensor" width="200px" required="true" default="0"/>
		<param field="pm10" label="PM10 Sensor" default="0" width="200px" required="true"  />
        <param field="checkFreq" label="Check every x minutes" width="40px" default="15" required="true" />
		<param field="debug" label="Debug" width="75px">
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

    def getValue(param):
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

    def onStart(self):
        if Parameters["debug"] == 'Debug':
            self.debug = True
        else:
            self.debug = False
        Domoticz.Debugging(self.debug)

        self.pollinterval = int(Parameters["checkFreq"]) * 60

        if len(Devices) == 0:
            Domoticz.Device(Name="External PM 2.5", unit=self.PM25, TypeName="Air Quality", Used=1).Create()
            Domoticz.Device(Name="External PM 10",  unit=self.PM10, TypeName="Air Quality", Used=1).Create()

    def onStop(self):
        Domoticz.Debug('onStop called')
        Domoticz.Debugging(0)

    def onHeartbeat(self, fetch=False):
        now = datetime.datetime.now()

        if not fetch:
            if self.inProgress or (now > self.nextpoll):
                return
        
        self.nextpoll = (datetime.datetime.now() + datetime.timedelta(seconds=self.pollinterval))

        try:
            self.inProgress = True

            self.doUpdate()
        except Exception as e:
            Domoticz.Error("Unrecognized error: %s" % str(e))
        finally:
            self.inProgress = False
        
        return True

    def doUpdate(self):
        aqi = AqiStatus(Parameters["pm25"], Parameters["pm10"])

        Devices[self.PM10].Update(nValue=aqi.pm10)
        Devices[self.PM25].Update(nValue=aqi.pm25)

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

