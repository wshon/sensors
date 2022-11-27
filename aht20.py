import time


class ATH20:
    address = 0x38

    class Address:
        INIT = 0xBE
        SoftReset = 0xBA
        StartTest = 0xAC

    def __init__(self, i2c) -> None:
        self._i2c = i2c
        pass

    def init(self) -> bool:
        self._i2c.write_bytes(self.Address.INIT, b'\x08\x00')
        time.sleep(0.5)
        retry_count = 0
        while not self.read_cal_enable():
            self._i2c.write_bytes(self.Address.SoftReset, b'')
            time.sleep(0.2)
            self._i2c.write_bytes(self.Address.INIT, b'\x08\x00')
            retry_count += 1
            if retry_count >= 10:
                return False
            time.sleep(0.5)
        return True

    def read_status(self) -> int:
        return self._i2c.read_bytes(0x00)

    def read_cal_enable(self) -> bool:
        val = self.read_status()
        return (val & 0x68) == 0x08

    def read_ct_data(self):
        self._i2c.write_bytes(self.Address.StartTest, b'\x33\x00')
        time.sleep(0.075)
        retry_count = 0
        while (self.read_status() & 0x80) == 0x80:
            time.sleep(0.001)
            retry_count += 1
            if retry_count >= 100:
                break
        data = self._i2c.read_bytes(0x00, 7)
        c = (data[1] << 12) | (data[2] << 4) | (data[3] >> 4)
        t = ((data[3] & 0x0f) << 16) | (data[4] << 8) | (data[5])
        c10 = c * 100 * 10 / 1024 / 1024
        t10 = t * 200 * 10 / 1024 / 1024 - 500
        return c10 / 10, t10 / 10


if __name__ == "__main__":
    import smbus
    from i2c import I2CDeviceSmbus

    i2c3 = smbus.SMBus(3)
    ath20 = ATH20(I2CDeviceSmbus(i2c3, ATH20.address))
    ath20.init()
    c, t = ath20.read_ct_data()
    print(f"{t:0.6f} {c:0.6f}")
