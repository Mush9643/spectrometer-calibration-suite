from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException


class ModbusClient:
    def __init__(self, port, baud_rate, parity, stop_bits, byte_size, timeout):
        self.port = port
        self.baud_rate = baud_rate
        self.parity = parity
        self.stop_bits = stop_bits
        self.byte_size = byte_size
        self.timeout = timeout
        self.client = ModbusSerialClient(
            port=self.port,
            baudrate=self.baud_rate,
            parity=self.parity,
            stopbits=self.stop_bits,
            bytesize=self.byte_size,
            timeout=self.timeout
        )



    def read_spectrum(self, start_register, num_registers, slave_address, max_registers_per_request=125):
        spectrum_values = []
        if not self.client.connect():
            raise ConnectionError("Не удалось подключиться к устройству.")

        try:
            for i in range(0, num_registers, max_registers_per_request):
                address = start_register + i
                count = min(max_registers_per_request, num_registers - i)
                response = self.client.read_holding_registers(address=address, count=count, slave=slave_address)
                if response.isError():
                    raise ModbusException(f"Ошибка при чтении регистров: {response}")
                spectrum_values.extend(response.registers)
        except ModbusException as e:
            raise ModbusException(f"Ошибка Modbus: {e}")
        finally:
            self.client.close()
        return spectrum_values