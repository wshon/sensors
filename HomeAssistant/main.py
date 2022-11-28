from umqtt.simple import MQTTClient
import machine
import network
import utime

from config import *
from sensor.aht20 import ATH20
from sensor.bmp280 import BMP280
from sensor.sgp30 import SGP30

LED = machine.Pin(2, machine.Pin.OUT, value=1)

print(f"Client id is: {CLIENT_ID}")
CLIENT = None

print("Connecting to WiFi...")
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASS)
while not wifi.isconnected():
    utime.sleep_ms(50)

print('IP:', wifi.ifconfig()[0])

# define i2c device
i2c_device = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4), freq=100000)

print("Initialize ATH20...")
ath20 = ATH20(i2c_device)
print("Initialize BMP280...")
bmp280 = BMP280(i2c_device)
print("Initialize SGP30...")
sgp30 = SGP30(i2c_device)

def publish_device():
    print(AVAILABILITY_TOPIC)
    # Publish as available once connected
    CLIENT.publish(AVAILABILITY_TOPIC, "online")
    CLIENT.publish(ATH20_T_TOPIC, ATH20_T_PAYLOD)
    CLIENT.publish(ATH20_H_TOPIC, ATH20_H_PAYLOD)
    CLIENT.publish(BMP280_P_TOPIC, BMP280_P_PAYLOD)
    CLIENT.publish(BMP280_T_TOPIC, BMP280_T_PAYLOD)
    CLIENT.publish(BMP280_A_TOPIC, BMP280_A_PAYLOD)
    CLIENT.publish(SGP30_C_TOPIC, SGP30_C_PAYLOD)
    CLIENT.publish(SGP30_T_TOPIC, SGP30_T_PAYLOD)

def on_msg(topic, msg):
    print(f"Received {msg} on {topic}")
    publish_device()

print("Connecting to MQTTClient...")
CLIENT = MQTTClient(CLIENT_ID, SERVER, keepalive=60)
CLIENT.set_callback(on_msg)
CLIENT.connect()

CLIENT.subscribe(HA_STATUS_TOPIC)
publish_device()
print("Connected to {}, subscribed to {} topic".format(SERVER, HA_STATUS_TOPIC))

try:
    sgp30_steady = False
    tmr_start_time = utime.time()
    while 1:
        CLIENT.check_msg()
        t = utime.time()
        if t - tmr_start_time > 1:
            print("1 sec elapsed, sending data to the server...")
            datas = {}
            aht20_h, aht20_t = ath20.read_ct_data()
            datas["aht20_temperature"] = aht20_t
            datas["aht20_humidity"] = aht20_h
            bmp280_p, bmp280_t, bmp280_a = bmp280.get_data()
            datas["bmp280_pressure"] = bmp280_p
            datas["bmp280_temperature"] = bmp280_t
            datas["bmp280_altitude"] = bmp280_a
            sgp30_co2, sgp30_tvoc = sgp30.indoor_air_quality
            if sgp30_steady or not (sgp30_co2 == 400 and sgp30_tvoc == 0):
                sgp30_steady = True
                datas["sgp30_co2"] = sgp30_co2
                datas["sgp30_tvoc"] = sgp30_tvoc
            CLIENT.publish(STATE_TOPIC, json.dumps(datas))
            tmr_start_time += 1
except Exception as e:
    print(e)
    raise e
finally:
    CLIENT.publish(AVAILABILITY_TOPIC, "offline")
    CLIENT.disconnect()
