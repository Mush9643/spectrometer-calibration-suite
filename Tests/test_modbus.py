import pytest
from unittest.mock import Mock, patch
from pymodbus.exceptions import ModbusException
from modbus import ModbusClient

@pytest.fixture
def modbus_client():
    """Фикстура с замоканным клиентом."""
    with patch("modbus.ModbusSerialClient") as MockSerialClient:
        mock_instance = MockSerialClient.return_value
        client = ModbusClient(
            port="COM1",
            baud_rate=9600,
            parity="N",
            stop_bits=1,
            byte_size=8,
            timeout=1
        )
        return client

def test_modbus_client_initialization():
    """Проверяет инициализацию ModbusClient с правильными параметрами."""
    with patch("modbus.ModbusSerialClient") as MockSerialClient:
        modbus_client = ModbusClient(
            port="COM1",
            baud_rate=9600,
            parity="N",
            stop_bits=1,
            byte_size=8,
            timeout=1
        )
        MockSerialClient.assert_called_once_with(
            port="COM1",
            baudrate=9600,
            parity="N",
            stopbits=1,
            bytesize=8,
            timeout=1
        )
        assert modbus_client.client == MockSerialClient.return_value

def test_read_spectrum_success(modbus_client):
    """Проверяет успешное чтение спектра."""
    modbus_client.client.connect.return_value = True
    response1 = Mock(isError=Mock(return_value=False), registers=[1, 2, 3, 4])
    response2 = Mock(isError=Mock(return_value=False), registers=[5, 6, 7])
    modbus_client.client.read_holding_registers.side_effect = [response1, response2]

    result = modbus_client.read_spectrum(100, 7, 1, max_registers_per_request=4)

    assert result == [1, 2, 3, 4, 5, 6, 7]
    modbus_client.client.connect.assert_called_once()
    modbus_client.client.read_holding_registers.assert_any_call(address=100, count=4, slave=1)
    modbus_client.client.read_holding_registers.assert_any_call(address=104, count=3, slave=1)
    modbus_client.client.close.assert_called_once()

def test_read_spectrum_modbus_error(modbus_client):
    """Проверяет ошибку при чтении регистров."""
    modbus_client.client.connect.return_value = True
    response = Mock(isError=Mock(return_value=True))
    modbus_client.client.read_holding_registers.return_value = response
    with pytest.raises(ModbusException, match="Ошибка при чтении регистров"):
        modbus_client.read_spectrum(100, 10, 1)
    modbus_client.client.connect.assert_called_once()
    modbus_client.client.read_holding_registers.assert_called_once_with(address=100, count=10, slave=1)
    modbus_client.client.close.assert_called_once()

def test_read_spectrum_always_closes_connection(modbus_client):
    """Проверяет, что соединение закрывается даже при ошибке."""
    modbus_client.client.connect.return_value = True
    modbus_client.client.read_holding_registers.side_effect = ModbusException("Test error")
    with pytest.raises(ModbusException, match="Test error"):
        modbus_client.read_spectrum(100, 10, 1)
    modbus_client.client.close.assert_called_once()
