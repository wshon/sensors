import machine, time, network
import BlynkLib
from aht20 import ATH20
from bmp280 import BMP280
from sgp30 import SGP30
from i2c import I2CDeviceMP

WIFI_SSID = 'YourWiFiNetwork'
WIFI_PASS = 'YourWiFiPassword'

BLYNK_AUTH = 'YourAuthToken'

print("Connecting to WiFi...")
wifi = network.WLAN(network.STA_IF)
wifi.connect(WIFI_SSID, WIFI_PASS)
while not wifi.isconnected():
    time.sleep_ms(50)

print('IP:', wifi.ifconfig()[0])

i2c_device = machine.I2C(scl=machine.Pin(5), sda=machine.Pin(4), freq=100000)

print("Initialize ATH20...")
ath20 = ATH20(I2CDeviceMP(i2c_device, ATH20.address))
ath20.init()
print("Initialize BMP280...")
bmp280 = BMP280(I2CDeviceMP(i2c_device, BMP280.address))
bmp280.init()
print("Initialize SGP30...")
sgp30 = SGP30(i2c_device)

print("Connecting to Blynk...")
blynk = BlynkLib.Blynk(BLYNK_AUTH)


@blynk.on("connected")
def blynk_connected(ping):
    print('Blynk ready. Ping:', ping, 'ms')


tmr_start_time = time.time()
while True:
    blynk.run()
    t = time.time()
    if t - tmr_start_time > 1:
        print("1 sec elapsed, sending data to the server...")
        blynk.virtual_write(0, "time:" + str(t))
        c, t = ath20.read_ct_data()
        blynk.virtual_write(1, t)
        blynk.virtual_write(2, c)
        p, t, a = bmp280.get_data()
        blynk.virtual_write(3, p)
        blynk.virtual_write(4, a)
        blynk.virtual_write(5, t)
        co2, tvoc = sgp30.indoor_air_quality
        blynk.virtual_write(6, co2)
        blynk.virtual_write(7, tvoc)
        tmr_start_time += 1
