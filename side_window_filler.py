from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHeaderView
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import struct

class SideWindow(QWidget):
    def __init__(self, main_geometry, modbus_client, main_window):
        super().__init__()
        self.modbus = modbus_client  # Сохраняем клиент Modbus
        self.main_window = main_window
        self.setWindowTitle("Дополнительное окно")

        # Вычисляем параметры для нового окна
        main_x = main_geometry.x()
        main_y = main_geometry.y()
        main_width = main_geometry.width()
        main_height = main_geometry.height()
        side_width = (main_width // 2) * 0.9
        side_x = main_x + main_width
        side_y = main_y
        side_height = main_height
        self.setGeometry(side_x, side_y, int(side_width), side_height)

        # Применяем улучшенный стиль
        self.setStyleSheet("""
                            QWidget {
                                background-color: #F8FAFC;
                                font-family: 'Montserrat', sans-serif;
                            }
                            QLabel#titleLabel {
                                font-size: 18px;
                                font-weight: 600;
                                color: #4A4A4A;
                                padding: 10px 10px 5px 10px;
                                border-bottom: 1px solid #E2E8F0;
                            }
                            QTableWidget {
                                background-color: #FFFFFF;
                                border: 1px solid #4A4A4A;
                                border-radius: 8px;
                                font-family: 'Montserrat', sans-serif;
                                font-size: 13px;
                                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                            }
                            QHeaderView::section {
                                background-color: #4A4A4A;
                                color: #FFFFFF;
                                padding: 10px;
                                border: none;
                                border-bottom: 1px solid #E2E8F0;
                                font-weight: 600;
                                font-size: 15px;
                                border-top-left-radius: 8px;
                                border-top-right-radius: 8px;
                            }
                            QTableWidget::item {
                                padding: 10px;
                                border-bottom: 1px solid #E2E8F0;
                                color: #1A202C;
                            }
                            QTableWidget::item:alternate {
                                background-color: #F8FAFC;
                            }
                            QTableWidget::item:selected {
                                background-color: #E2E8F0;
                                color: #1A202C;
                            }
                            QPushButton#fillButton, QPushButton#updateButton {
                                background-color: #4A4A4A;
                                color: #FFFFFF;
                                border: none;
                                border-radius: 5px;
                                padding: 8px 16px;
                                font-size: 12px;
                                font-weight: 600;
                                max-width: 150px;
                            }
                            QPushButton#fillButton:hover, QPushButton#updateButton:hover {
                                background-color: #5A5A5A;
                            }
                            QPushButton#fillButton:pressed, QPushButton#updateButton:pressed {
                                background-color: #3A3A3A;
                            }
                        """)

        # Создаем layout для окна
        side_layout = QVBoxLayout()
        side_layout.setContentsMargins(20, 20, 20, 20)
        side_layout.setSpacing(20)

        # Добавляем заголовок (будем обновлять после чтения серийного номера)
        self.title_label = QLabel("Детектор")
        self.title_label.setObjectName("titleLabel")
        side_layout.addWidget(self.title_label)

        # Создаем таблицу
        self.side_table = QTableWidget()
        self.side_table.setColumnCount(2)
        self.side_table.setRowCount(22)
        self.side_table.setHorizontalHeaderLabels(["Параметр", "Значение"])

        # Данные для таблицы
        data = [
            ("a (Alfa)", ""),
            ("b (Alfa)", ""),
            ("НУД α, № канала (2700)", ""),
            ("ВУД ROI 3, № канала (4385.6)", ""),
            ("НУД ROI 2, № канала (5687.5)", ""),
            ("НУД ROI 6, № канала (6192.35)", ""),
            ("НУД ROI 4, № канала (6337.7)", ""),
            ("НУД ROI 5, № канала (8044.6)", ""),
            ("k1p9", ""),
            ("НУД β", ""),
            ("ВУД β", ""),
            ("k1c0", ""),
            ("a (Beta)", ""),
            ("b (Beta)", ""),
            ("Pn (80 кэВ)", ""),
            ("Pn (146 кэВ)", ""),
            ("Pn (400 кэВ)", ""),
            ("Pn (850 кэВ)", ""),
            ("Pn (1500 кэВ)", ""),
            ("Pn (2515 кэВ)", ""),

        ]

        # Заполняем таблицу
        for row, (param, value) in enumerate(data):
            param_item = QTableWidgetItem(param)
            param_item.setFlags(param_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.side_table.setItem(row, 0, param_item)
            value_item = QTableWidgetItem(value)
            self.side_table.setItem(row, 1, value_item)

        # Настраиваем таблицу
        self.side_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.side_table.setAlternatingRowColors(True)
        self.side_table.setShowGrid(False)
        self.side_table.verticalHeader().setVisible(False)

        # Добавляем таблицу в layout
        side_layout.addWidget(self.side_table)

        # Добавляем кнопку "Заполнить значения"
        fill_button = QPushButton("Вывод")
        fill_button.setObjectName("fillButton")
        fill_button.clicked.connect(self.fill_values)

        update_button = QPushButton("Обновить")
        update_button.setObjectName("updateButton")
        update_button.clicked.connect(self.update_from_report)

        # Горизонтальный layout для кнопок
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(fill_button)
        button_layout.addWidget(update_button)
        button_layout.addStretch()

        side_layout.addLayout(button_layout)
        self.setLayout(side_layout)

        # Читаем серийный номер при открытии окна
        self.read_serial_number()

    def read_serial_number(self):
        """Чтение серийного номера (8 символов) из регистров 0x8008-0x800F"""
        try:
            if not self.modbus.client.connect():
                raise ConnectionError("Не удалось подключиться к устройству")

            # Читаем 8 регистров (16 байт)
            registers = self.modbus.read_spectrum(
                start_register=0x8008,
                num_registers=8,
                slave_address=1
            )

            # Проверяем длину полученных данных
            if len(registers) != 8:
                raise ValueError(f"Ожидалось 8 регистров, получено {len(registers)}")

            # Преобразуем регистры в байты
            serial_bytes = bytearray()
            for reg in registers:
                serial_bytes.extend(reg.to_bytes(2, byteorder='big'))

            # Берем первые 8 байт (8 символов)
            serial_bytes = serial_bytes[:8]

            # Проверяем содержимое для отладки
            print(f"Сырые байты: {serial_bytes.hex()}")

            # Пытаемся декодировать как ASCII, заменяя невалидные символы
            try:
                serial_str = serial_bytes.decode('ascii')
            except UnicodeDecodeError:
                serial_str = serial_bytes.decode('latin-1')  # Поддерживает 0-255

            # Удаляем невидимые и управляющие символы (например, NUL)
            serial_str = ''.join(c for c in serial_str if 32 <= ord(c) <= 126)

            # Урезаем до 8 символов, если строка длиннее
            serial_str = serial_str[:8]

            # Проверяем результат для отладки
            print(f"Обработанная строка: {serial_str!r}")

            # Обновляем заголовок окна и метку
            self.setWindowTitle(f"Серийный номер: {serial_str}")
            self.title_label.setText(f"Серийный номер: {serial_str}")

        except Exception as e:
            self.title_label.setText("Ошибка чтения серийного номера")
            print(f"Ошибка при чтении серийного номера: {str(e)}")

    def fill_values(self):
        """Заполняет таблицу значениями, записывая значения из регистров в соответствующие строки."""
        try:
            # Читаем значения из регистров
            if not self.modbus.client.connect():
                raise ConnectionError("Не удалось подключиться к устройству")

            # Читаем все регистры от 0x5000 до 0x5022 (35 регистров)
            registers = self.modbus.read_spectrum(
                start_register=0x5000,
                num_registers=35,  # От 0x5000 до 0x5022 (0x5022 - 0x5000 + 1 = 35)
                slave_address=1
            )
            if len(registers) != 35:
                raise ValueError(f"Ожидалось 35 значений из регистров 0x5000-0x5022, получено {len(registers)}")

            # Преобразуем регистры 0x5000-0x5001 в float (строка 12)
            float_bytes_5000 = struct.pack('>HH', registers[0], registers[1])  # 0x5000, 0x5001
            value_5000_float = struct.unpack('>f', float_bytes_5000)[0]

            # Преобразуем регистры 0x5002-0x5003 в float (строка 13)
            float_bytes_5002 = struct.pack('>HH', registers[2], registers[3])  # 0x5002, 0x5003
            value_5002_float = struct.unpack('>f', float_bytes_5002)[0]

            # Преобразуем регистры 0x5004-0x5005 в float (строка 0)
            float_bytes_5004 = struct.pack('>HH', registers[4], registers[5])  # 0x5004, 0x5005
            value_5004_float = struct.unpack('>f', float_bytes_5004)[0]

            # Преобразуем регистры 0x5006-0x5007 в float (строка 1)
            float_bytes_5006 = struct.pack('>HH', registers[6], registers[7])  # 0x5006, 0x5007
            value_5006_float = struct.unpack('>f', float_bytes_5006)[0]

            # Преобразуем регистры 0x500B-0x500C в float (строка 8)
            float_bytes_500B = struct.pack('>HH', registers[11], registers[12])  # 0x500B, 0x500C
            value_500B_float = struct.unpack('>f', float_bytes_500B)[0]

            # Преобразуем регистры 0x500D-0x500E в float (строка 11)
            float_bytes_500D = struct.pack('>HH', registers[13], registers[14])  # 0x500D, 0x500E
            value_500D_float = struct.unpack('>f', float_bytes_500D)[0]

            # Извлекаем значения (uint16) по индексам
            value_500F = registers[15]  # 0x500F (индекс 15: 0x500F - 0x5000 = 15)
            value_5010 = registers[16]  # 0x5010 (индекс 16: 0x5010 - 0x5000 = 16)
            value_5011 = registers[17]  # 0x5011 (индекс 17: 0x5011 - 0x5000 = 17)
            value_5012 = registers[18]  # 0x5012 (индекс 18: 0x5012 - 0x5000 = 18)
            value_5013 = registers[19]  # 0x5013 (индекс 19: 0x5013 - 0x5000 = 19)
            value_5018 = registers[24]  # 0x5018 (индекс 24: 0x5018 - 0x5000 = 24)
            value_501D = registers[29]  # 0x501D (индекс 29: 0x501D - 0x5000 = 29)
            value_5022 = registers[34]  # 0x5022 (индекс 34: 0x5022 - 0x5000 = 34)

            # Выводим значения для отладки
            print(f"Значение из регистров 0x5000-0x5001 (float): {value_5000_float}")
            print(f"Значение из регистров 0x5002-0x5003 (float): {value_5002_float}")
            print(f"Значение из регистров 0x5004-0x5005 (float): {value_5004_float}")
            print(f"Значение из регистров 0x5006-0x5007 (float): {value_5006_float}")
            print(f"Значение из регистров 0x500B-0x500C (float): {value_500B_float}")
            print(f"Значение из регистров 0x500D-0x500E (float): {value_500D_float}")
            print(f"Значение из регистра 0x500F: {value_500F}")
            print(f"Значение из регистра 0x5010: {value_5010}")
            print(f"Значение из регистра 0x5011: {value_5011}")
            print(f"Значение из регистра 0x5012: {value_5012}")
            print(f"Значение из регистра 0x5013: {value_5013}")
            print(f"Значение из регистра 0x5018: {value_5018}")
            print(f"Значение из регистра 0x501D: {value_501D}")
            print(f"Значение из регистра 0x5022: {value_5022}")

            # Сопоставление строк и значений
            row_values = {
                0: value_5004_float,  # 0x5004-0x5005 (float, строка 0)
                1: value_5006_float,  # 0x5006-0x5007 (float, строка 1)
                2: value_5011,  # 0x5011 (uint16, строка 2)
                3: value_5012,  # 0x5012 (uint16, строка 3)
                4: value_5013,  # 0x5013 (uint16, строка 4)
                5: value_5018,  # 0x5018 (uint16, строка 5)
                6: value_501D,  # 0x501D (uint16, строка 6)
                7: value_5022,  # 0x5022 (uint16, строка 7)
                8: value_500B_float,  # 0x500B-0x500C (float, строка 8)
                9: value_500F,  # 0x500F (uint16, строка 9)
                10: value_5010,  # 0x5010 (uint16, строка 10)
                11: value_500D_float,  # 0x500D-0x500E (float, строка 11)
                12: value_5000_float,  # 0x5000-0x5001 (float, строка 12)
                13: value_5002_float,  # 0x5002-0x5003 (float, строка 13)
            }

            # Заполняем таблицу
            for row in range(self.side_table.rowCount()):
                if row in row_values:
                    # Форматируем float с двумя знаками после запятой
                    if row in (0, 1, 8, 11, 12, 13):  # Для значений float
                        item = QTableWidgetItem(f"{row_values[row]:.2f}")
                    else:
                        item = QTableWidgetItem(str(row_values[row]))
                else:
                    item = QTableWidgetItem(str(row + 1))  # Оставляем числа от 1 до 24 для остальных строк

                self.side_table.setItem(row, 1, item)  # Столбец 'Значение' (индекс 1)

        except Exception as e:
            print(f"Ошибка при чтении регистров: {str(e)}")
            # Если произошла ошибка, заполняем таблицу значениями по умолчанию
            for row in range(self.side_table.rowCount()):
                item = QTableWidgetItem(str(row + 1))
                self.side_table.setItem(row, 1, item)

    def update_from_report(self):
        """Обновляет значения в столбце 'Значения' на основе данных из вкладки Report."""
        try:
            # Получаем таблицу из вкладки Report
            report_table = self.main_window.calibration_table

            # Создаём словарь параметров и значений из вкладки Report
            report_values = {}
            for row in range(report_table.rowCount()):
                param_item = report_table.item(row, 0)
                value_item = report_table.item(row, 1)
                if param_item and value_item:
                    param = param_item.text()
                    value = value_item.text()
                    report_values[param] = value

            # Обновляем значения в таблице side_table
            for row in range(self.side_table.rowCount()):
                param_item = self.side_table.item(row, 0)
                if param_item:
                    param = param_item.text()
                    if param in report_values:
                        # Если параметр найден в таблице Report, обновляем значение
                        new_value = report_values[param]
                        value_item = QTableWidgetItem(new_value)
                        self.side_table.setItem(row, 1, value_item)

        except Exception as e:
            print(f"Ошибка при обновлении значений из вкладки Report: {str(e)}")