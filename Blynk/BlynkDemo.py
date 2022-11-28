import BlynkLib
from network import WLAN
import machine, time

WIFI_SSID = 'YourWiFiNetwork'
WIFI_PASS = 'YourWiFiPassword'

BLYNK_AUTH = 'YourAuthToken'

print("Connecting to WiFi...")
wifi = WLAN(mode=WLAN.STA)
wifi.connect(ssid=WIFI_SSID, auth=(WLAN.WPA2, WIFI_PASS))
while not wifi.isconnected():
    time.sleep_ms(50)

print('IP:', wifi.ifconfig()[0])

print("Connecting to Blynk...")
blynk = BlynkLib.Blynk(BLYNK_AUTH)


@blynk.on("connected")
def blynk_connected(ping):
    print('Blynk ready. Ping:', ping, 'ms')


def runLoop():
    while True:
        blynk.run()
        machine.idle()


# Run blynk in the main thread:
runLoop()