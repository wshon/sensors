from aht20 import ATH20
from bmp280 import BMP280
from i2c import I2CDeviceMP
from machine import Pin, I2C

i2c_device = I2C(scl=Pin(5), sda=Pin(4), freq=100000)

ath20 = ATH20(I2CDeviceMP(i2c_device, ATH20.address))
ath20.init()
c, t = ath20.read_ct_data()
print(f"{t:0.6f} {c:0.6f}")

bmp280 = BMP280(I2CDeviceMP(i2c_device, BMP280.address))
bmp280.init()
p, t, a = bmp280.get_data()
print(f"{p:0.6f} {t:0.6f} {a:0.6f}")
