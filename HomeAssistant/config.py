WIFI_SSID = 'YourWiFiNetwork'
WIFI_PASS = 'YourWiFiPassword'
SERVER = "192.168.1.2"

HA_STATUS_TOPIC = "homeassistant/status"

import ubinascii, machine
CLIENT_ID = ubinascii.hexlify(machine.unique_id())
SENSOR_ID = f"air_quality_{CLIENT_ID.decode()}"
STATE_TOPIC = f"homeassistant/sensor/{SENSOR_ID}/state"
AVAILABILITY_TOPIC = f"homeassistant/sensor/{SENSOR_ID}/availability"

import json
def config(key, name, cls, unit):
    return f"homeassistant/sensor/{SENSOR_ID}_{key}/config", json.dumps({
        "device_class": cls,
        "name": f"Air Quality {name}",
        "object_id": f"{SENSOR_ID}_{key}",
        "state_topic": STATE_TOPIC,
        "availability_topic": AVAILABILITY_TOPIC,
        "unit_of_measurement": unit,
        "value_template": f"{{{{ value_json.{key} }}}}"
    })


ATH20_T_TOPIC, ATH20_T_PAYLOD = config("aht20_temperature", "Temperature", "temperature", "C")
ATH20_H_TOPIC, ATH20_H_PAYLOD = config("aht20_humidity", "Humidity", "humidity", "%")
BMP280_P_TOPIC, BMP280_P_PAYLOD = config("bmp280_pressure", "Pressure", "pressure", "hPa")
BMP280_T_TOPIC, BMP280_T_PAYLOD = config("bmp280_temperature", "Temperature", "temperature", "C")
BMP280_A_TOPIC, BMP280_A_PAYLOD = config("bmp280_altitude", "Altitude", None, "m")
SGP30_C_TOPIC, SGP30_C_PAYLOD = config("sgp30_co2", "CO2", "carbon_dioxide", "ppm")
SGP30_T_TOPIC, SGP30_T_PAYLOD = config("sgp30_tvoc", "TVOC", "volatile_organic_compounds", "ppb")
