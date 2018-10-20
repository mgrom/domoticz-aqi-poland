# domoticz-aqi-poland
A Python plugin for Domoticz to create devices with PM2.5 and PM10 based on http://api.gios.gov.pl

## Installation

```
pip3 install -U requests
```

* Make sure your Domoticz instance supports Domoticz Plugin System - see more https://www.domoticz.com/wiki/Using_Python_plugins

* Get plugin data into DOMOTICZ/plugins directory
```
cd YOUR_DOMOTICZ_PATH/plugins
git clone https://github.com/mgrom/domoticz-aqi-poland
```

* check where modules was installed and in file plugin.py find and correct below lines if needed
sys.path.append(sys.prefix+'/local/lib/python3.5/dist-packages')
sys.path.append(sys.prefix+'/local/lib/python3/dist-packages')

Restart Domoticz
* Make sure that you filled Location Latitude and Longitude in Domoticz Settings (plugin will search for nearest station available in Poland using your coordinates)
* Go to Setup > Hardware and create new Hardware with type: AQI.gov.pl


## Update
```
cd YOUR_DOMOTICZ_PATH/plugins/domoticz-aqi-poland
git pull
```
* Restart Domoticz

## Troubleshooting

Sometimes API is unavailable, so then devices are not going to be updated.

In case of issues, mostly plugin not visible on plugin list, check logs if plugin system is working correctly. See Domoticz wiki for resolution of most typical installation issues http://www.domoticz.com/wiki/Linux#Problems_locating_Python
