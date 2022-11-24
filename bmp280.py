from ctypes import *

class BMP280Calib(Structure):
    _pack_ = 1
    _fields_ = [
        #(字段名, c类型 )
        ('dig_T1', c_uint16),
        ('dig_T2', c_int16),
        ('dig_T3', c_int16),
        ('dig_P1', c_uint16),
        ('dig_P2', c_int16),
        ('dig_P3', c_int16),
        ('dig_P4', c_int16),
        ('dig_P5', c_int16),
        ('dig_P6', c_int16),
        ('dig_P7', c_int16),
        ('dig_P8', c_int16),
        ('dig_P9', c_int16),
    ]


BMP280_SLAVE_ADDRESS  = 0x77

# calibration parameters
BMP280_DIG_T1_LSB_REG = 0x88
BMP280_DIG_T1_MSB_REG = 0x89
BMP280_DIG_T2_LSB_REG = 0x8A
BMP280_DIG_T2_MSB_REG = 0x8B
BMP280_DIG_T3_LSB_REG = 0x8C
BMP280_DIG_T3_MSB_REG = 0x8D
BMP280_DIG_P1_LSB_REG = 0x8E
BMP280_DIG_P1_MSB_REG = 0x8F
BMP280_DIG_P2_LSB_REG = 0x90
BMP280_DIG_P2_MSB_REG = 0x91
BMP280_DIG_P3_LSB_REG = 0x92
BMP280_DIG_P3_MSB_REG = 0x93
BMP280_DIG_P4_LSB_REG = 0x94
BMP280_DIG_P4_MSB_REG = 0x95
BMP280_DIG_P5_LSB_REG = 0x96
BMP280_DIG_P5_MSB_REG = 0x97
BMP280_DIG_P6_LSB_REG = 0x98
BMP280_DIG_P6_MSB_REG = 0x99
BMP280_DIG_P7_LSB_REG = 0x9A
BMP280_DIG_P7_MSB_REG = 0x9B
BMP280_DIG_P8_LSB_REG = 0x9C
BMP280_DIG_P8_MSB_REG = 0x9D
BMP280_DIG_P9_LSB_REG = 0x9E
BMP280_DIG_P9_MSB_REG = 0x9F

BMP280_CHIPID_REG           = 0xD0 # Chip ID Register
BMP280_RESET_REG            = 0xE0 # Softreset Register
BMP280_STATUS_REG           = 0xF3 # Status Register
BMP280_CTRLMEAS_REG         = 0xF4 # Ctrl Measure Register
BMP280_CONFIG_REG           = 0xF5 # Configuration Register
BMP280_PRESSURE_MSB_REG     = 0xF7 # Pressure MSB Register
BMP280_PRESSURE_LSB_REG     = 0xF8 # Pressure LSB Register
BMP280_PRESSURE_XLSB_REG    = 0xF9 # Pressure XLSB Register
BMP280_TEMPERATURE_MSB_REG  = 0xFA # Temperature MSB Reg
BMP280_TEMPERATURE_LSB_REG  = 0xFB # Temperature LSB Reg
BMP280_TEMPERATURE_XLSB_REG = 0xFC # Temperature XLSB Reg

BMP280_SLEEP_MODE  = 0x00
BMP280_FORCED_MODE = 0x01
BMP280_NORMAL_MODE = 0x03

BMP280_TEMPERATURE_CALIB_DIG_T1_LSB_REG       = 0x88
BMP280_PRESSURE_TEMPERATURE_CALIB_DATA_LENGTH = 24
BMP280_DATA_FRAME_SIZE                        = 6

BMP280_OVERSAMP_SKIPPED = 0x00
BMP280_OVERSAMP_1X      = 0x01
BMP280_OVERSAMP_2X      = 0x02
BMP280_OVERSAMP_4X      = 0x03
BMP280_OVERSAMP_8X      = 0x04
BMP280_OVERSAMP_16X     = 0x05

BMP280_PRESSURE_OSR    = BMP280_OVERSAMP_8X
BMP280_TEMPERATURE_OSR = BMP280_OVERSAMP_16X
BMP280_MODE            = BMP280_PRESSURE_OSR << 2 | BMP280_TEMPERATURE_OSR << 5 | BMP280_NORMAL_MODE

class Bmp280:
    _i2c = None
    _address = 0x77
    _bmp280_id = None
    _bmp280_cal = None
    _filter_buf = []
    t_fine = 0

    def __init__(self, i2c):
        self._i2c = i2c
    
    def init(self):
        self._bmp280_id = self._i2c.read_byte_data(BMP280_SLAVE_ADDRESS, BMP280_CHIPID_REG)
        datas = self._i2c.read_i2c_block_data(BMP280_SLAVE_ADDRESS, BMP280_DIG_T1_LSB_REG, 24)
        self._bmp280_cal = BMP280Calib.from_buffer_copy(bytes(datas))
        self._i2c.write_byte_data(BMP280_SLAVE_ADDRESS, BMP280_CTRLMEAS_REG, BMP280_MODE)
        self._i2c.write_byte_data(BMP280_SLAVE_ADDRESS, BMP280_CONFIG_REG, 5<<2)
        self._filter_buf = []

    def get_pressure(self):
        # read data from sensor
        data = self._i2c.read_i2c_block_data(BMP280_SLAVE_ADDRESS, BMP280_PRESSURE_MSB_REG, BMP280_DATA_FRAME_SIZE)
        bmp280RawPressure = (((data[0]) << 12) | ((data[1]) << 4) | (data[2] >> 4))
        bmp280RawTemperature = (((data[3]) << 12) | ((data[4]) << 4) | (data[5] >> 4))
        return bmp280RawPressure, bmp280RawTemperature


    def compensate_t(self, value):
        """
        Returns temperature in DegC, resolution is 0.01 DegC. Output value of "5123" equals 51.23 DegC
        t_fine carries fine temperature as global value
        """
        var1 = ((((value >> 3) - (self._bmp280_cal.dig_T1 << 1))) * (self._bmp280_cal.dig_T2)) >> 11
        var2  = (((((value >> 4) - (self._bmp280_cal.dig_T1)) * ((value >> 4) - (self._bmp280_cal.dig_T1))) >> 12) * (self._bmp280_cal.dig_T3)) >> 14
        self.t_fine = var1 + var2

        T = (self.t_fine * 5 + 128) >> 8

        return T

    def compensate_p(self, value):
        """
        Returns pressure in Pa as unsigned 32 bit integer in Q24.8 format (24 integer bits and 8 fractional bits).
        Output value of "24674867" represents 24674867/256 = 96386.2 Pa = 963.862 hPa
        """
        var1 = (self.t_fine) - 128000
        var2 = var1 * var1 * self._bmp280_cal.dig_P6
        var2 = var2 + ((var1*self._bmp280_cal.dig_P5) << 17)
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
        CONST_PF = 0.1902630958 # (1/5.25588) Pressure factor
        FIX_TEMP = 25           # Fixed Temperature. ASL is a function of pressure and temperature, but as the temperature changes so much (blow a little towards the flie and watch it drop 5 degrees) it corrupts the ASL estimates.
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
        temperature = t; # 单位度
        asl = self.pressure_to_altitude(pressure) # 转换成海拔
        return pressure, temperature, asl


if __name__ == "__main__":
    import smbus
    i2c3 = smbus.SMBus(3)
    bmp280 = Bmp280(i2c3)
    bmp280.init()
    bmp280.get_data()


