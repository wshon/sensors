try:
    import struct
except ImportError:
    import ustruct as struct


class BMP280Calib():
    _layout = 'HhhHhhhhhhhh'

    def __init__(
        self,
        dig_T1,
        dig_T2,
        dig_T3,
        dig_P1,
        dig_P2,
        dig_P3,
        dig_P4,
        dig_P5,
        dig_P6,
        dig_P7,
        dig_P8,
        dig_P9,
    ) -> None:
        self.dig_T1 = dig_T1
        self.dig_T2 = dig_T2
        self.dig_T3 = dig_T3
        self.dig_P1 = dig_P1
        self.dig_P2 = dig_P2
        self.dig_P3 = dig_P3
        self.dig_P4 = dig_P4
        self.dig_P5 = dig_P5
        self.dig_P6 = dig_P6
        self.dig_P7 = dig_P7
        self.dig_P8 = dig_P8
        self.dig_P9 = dig_P9

    @staticmethod
    def from_bytes(datas):
        vs = struct.unpack(BMP280Calib._layout, datas)
        return BMP280Calib(
            dig_T1=vs[0],
            dig_T2=vs[1],
            dig_T3=vs[2],
            dig_P1=vs[3],
            dig_P2=vs[4],
            dig_P3=vs[5],
            dig_P4=vs[6],
            dig_P5=vs[7],
            dig_P6=vs[8],
            dig_P7=vs[9],
            dig_P8=vs[10],
            dig_P9=vs[11],
        )


class Mode:
    Sleep = 0x00
    Forced = 0x01
    Normal = 0x03


class Oversamp:
    Skipped = 0x00
    Os1x = 0x01
    Os2x = 0x02
    Os4x = 0x03
    Os8x = 0x04
    Os16x = 0x05


class Config:
    pressure_osr = Oversamp.Os8x
    temperature_osr = Oversamp.Os16x
    mode = Mode.Normal

    @staticmethod
    def to_bytes():
        return (Config.temperature_osr << 5 | Config.pressure_osr << 2 | Config.mode).to_bytes(1, 'big')


class BMP280:
    address = 0x77

    _data_frame_size = 6
    _t_fine = 0

    class Address:
        ChipIDRegister = 0xD0
        CtrlMeasureRegister = 0xF4
        ConfigurationRegister = 0xF5
        PressureMSBRegister = 0xF7
        CalibDigT1LSBRegister = 0x88

    def __init__(self, i2c) -> None:
        self._i2c = i2c
        
        self._bmp280_id = self._i2c.readfrom_mem(self.address, self.Address.ChipIDRegister, 1)[0]
        datas = self._i2c.readfrom_mem(self.address, self.Address.CalibDigT1LSBRegister, 24)
        self._bmp280_cal = BMP280Calib.from_bytes(datas)
        self._i2c.writeto_mem(self.address, self.Address.CtrlMeasureRegister, Config.to_bytes())
        self._i2c.writeto_mem(self.address, self.Address.ConfigurationRegister, (5 << 2).to_bytes(1, 'big'))
        self._filter_buf = []

    def get_pressure(self):
        # read data from sensor
        data = self._i2c.readfrom_mem(self.address, self.Address.PressureMSBRegister, self._data_frame_size)
        bmp280RawPressure = (((data[0]) << 12) | ((data[1]) << 4) | (data[2] >> 4))
        bmp280RawTemperature = (((data[3]) << 12) | ((data[4]) << 4) | (data[5] >> 4))
        return bmp280RawPressure, bmp280RawTemperature

    def compensate_t(self, value):
        """
        Returns temperature in DegC, resolution is 0.01 DegC. Output value of "5123" equals 51.23 DegC
        _t_fine carries fine temperature as global value
        """
        var1 = ((((value >> 3) - (self._bmp280_cal.dig_T1 << 1))) * (self._bmp280_cal.dig_T2)) >> 11
        var2 = (((((value >> 4) - (self._bmp280_cal.dig_T1)) * ((value >> 4) - (self._bmp280_cal.dig_T1))) >> 12) * (self._bmp280_cal.dig_T3)) >> 14
        self._t_fine = var1 + var2

        T = (self._t_fine * 5 + 128) >> 8

        return T

    def compensate_p(self, value):
        """
        Returns pressure in Pa as unsigned 32 bit integer in Q24.8 format (24 integer bits and 8 fractional bits).
        Output value of "24674867" represents 24674867/256 = 96386.2 Pa = 963.862 hPa
        """
        var1 = (self._t_fine) - 128000
        var2 = var1 * var1 * self._bmp280_cal.dig_P6
        var2 = var2 + ((var1 * self._bmp280_cal.dig_P5) << 17)
        var2 = var2 + ((self._bmp280_cal.dig_P4) << 35)
        var1 = ((var1 * var1 * self._bmp280_cal.dig_P3) >> 8) + ((var1 * self._bmp280_cal.dig_P2) << 12)
        var1 = ((((1) << 47) + var1)) * (self._bmp280_cal.dig_P1) >> 33
        if var1 == 0:
            return 0
        p = 1048576 - value
        p = (int)((((p << 31) - var2) * 3125) / var1)
        var1 = ((self._bmp280_cal.dig_P9) * (p >> 13) * (p >> 13)) >> 25
        var2 = ((self._bmp280_cal.dig_P8) * p) >> 19
        p = ((p + var1 + var2) >> 8) + ((self._bmp280_cal.dig_P7) << 4)
        return p

    def pressure_to_altitude(self, pressure):
        CONST_PF = 0.1902630958  # (1/5.25588) Pressure factor
        # Fixed Temperature. ASL is a function of pressure and temperature, but as the temperature changes so much (blow a little towards the flie and watch it drop 5 degrees) it corrupts the ASL estimates.
        FIX_TEMP = 25
        if pressure > 0:
            return ((pow((1015.7 / pressure), CONST_PF) - 1.0) * (FIX_TEMP + 273.15)) / 0.0065
        else:
            return 0

    def presssure_filter(self, value):
        if len(self._filter_buf) < 5:
            self._filter_buf.append(value)
        else:
            if abs(value - self._filter_buf[-1]) < 0.1:
                self._filter_buf.append(value)
                self._filter_buf.pop(0)
        return sum(self._filter_buf) / len(self._filter_buf)

    def get_data(self):
        bmp280RawPressure, bmp280RawTemperature = self.get_pressure()
        t = self.compensate_t(bmp280RawTemperature) / 100.0
        p = self.compensate_p(bmp280RawPressure) / 25600.0
        pressure = self.presssure_filter(p)
        temperature = t  # 单位度
        asl = self.pressure_to_altitude(pressure)  # 转换成海拔
        return pressure, temperature, asl


if __name__ == "__main__":
    import smbus
    from i2c import I2CDeviceSmbus

    i2c3 = smbus.SMBus(3)
    bmp280 = BMP280(I2CDeviceSmbus(i2c3, BMP280.address))
    bmp280.init()
    p, t, a = bmp280.get_data()
    print(f"{p:0.6f} {t:0.6f} {a:0.6f}")
