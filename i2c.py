class I2CDevice():

    def read_bytes(self, address, size=1):
        pass

    def write_bytes(self, address, datas):
        pass


class I2CDeviceSmbus(I2CDevice):

    def __init__(self, device, address):
        self.d = device
        self.a = address

    def read_bytes(self, address, size=1):
        if size == 1:
            return self.d.read_byte_data(self.a, address)
        else:
            return bytes(self.d.read_i2c_block_data(self.a, address, size))

    def write_bytes(self, address, datas):
        if isinstance(datas, int):
            datas = datas.to_bytes(1, byteorder='big')
        if len(datas) == 1:
            self.d.write_byte_data(self.a, address, datas[0])
        else:
            self.d.write_i2c_block_data(self.a, address, list(datas))


class I2CDeviceMP(I2CDevice):

    def __init__(self, device, address):
        self.d = device
        self.a = address

    def read_bytes(self, address, size=1):
        data = self.d.readfrom_mem(self.a, address, size)
        if size == 1:
            return data[0]
        else:
            return data

    def write_bytes(self, address, datas):
        if isinstance(datas, int):
            datas = datas.to_bytes(1, 'big')
        self.d.writeto_mem(self.a, address, datas)
