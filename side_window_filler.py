from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton, \
    QApplication
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
        self.setWindowIcon(QIcon("M-Photoroom.png"))

        # Получаем размеры главного окна
        main_x = main_geometry.x()
        main_y = main_geometry.y()
        main_width = main_geometry.width()
        main_height = main_geometry.height()

        # Получаем размеры экрана
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # Рассчитываем размеры и положение окна
        side_x = main_x + main_width  # Начинаем от правого края главного окна
        side_y = main_y  # Оставляем ту же высоту, что у главного окна
        side_width = screen_width - side_x  # Ширина от правого края главного окна до правой границы экрана
        side_height = main_height  # Высота равна высоте главного окна

        # Устанавливаем геометрию окна
        self.setGeometry(side_x, side_y, side_width, side_height)

        # Применяем улучшенный стиль
        self.setStyleSheet("""
                    /* Общий стиль окна: белый фон */
                    QWidget {
                        background-color: #FFFFFF;  /* Белый фон, как в основном окне */
                        font-family: 'Montserrat', sans-serif;  /* Простой шрифт */
                    }

                    /* Заголовок окна: черный текст, без нижней границы */
                    QLabel#titleLabel {
                        font-size: 16px;
                        font-weight: 600;
                        color: #000000;  /* Черный текст для читаемости */
                        padding: 10px;
                    }

                    /* Центральная панель (таблица), имитирующая дисплей детектора */
                    QTableWidget {
                        background-color: #D3D3D3;  /* Светло-серая заливка, как у LCD */
                        border: 5px solid #C0392B;  /* Красная рамка, как у кнопок основного окна */
                        font-family: 'Montserrat', sans-serif;
                        font-size: 12px;
                        color: #000000;  /* Черный текст */
                    }

                    /* Заголовки таблицы: серый фон с белым текстом */
                    QHeaderView::section {
                        background-color: #4A4A4A;  /* Темно-серый фон */
                        color: #FFFFFF;  /* Белый текст */
                        padding: 8px;
                        border: none;
                        border-bottom: 1px solid #D3D3D3;
                        font-weight: 600;
                        font-size: 13px;
                        border-top-left-radius: 5px;
                        border-top-right-radius: 5px;
                    }

                    /* Элементы таблицы: белый фон и черный текст */
                    QTableWidget::item {
                        padding: 8px;
                        border-bottom: 1px solid #D3D3D3;
                        color: #000000;
                    }
                    QTableWidget::item:alternate {
                        background-color: #F0F0F0;  /* Легкий серый для чередующихся строк */
                    }
                    QTableWidget::item:selected {
                        background-color: #E0E0E0;
                        color: #000000;
                    }

                    /* Кнопки: красный фон, белый текст, как в основном окне */
                    QPushButton#fillButton, QPushButton#updateButton, QPushButton#outputButton {
                        background-color: #4A4A4A;  /* Красный фон, как у кнопок основного окна */
                        color: #FFFFFF;  /* Белый текст */
                        border: none;
                        border-radius: 5px;  /* Скругленные углы */
                        padding: 10px 20px;
                        font-size: 12px;
                        font-weight: 600;
                        min-width: 80px;
                    }
                    QPushButton#fillButton:hover, QPushButton#updateButton:hover, QPushButton#outputButton:hover {
                        background-color: #D35400;  /* Чуть светлее при наведении */
                    }
                    QPushButton#fillButton:pressed, QPushButton#updateButton:pressed, QPushButton#outputButton:pressed {
                        background-color: #A93226;  /* Чуть темнее при нажатии */
                    }
                """)

        # Создаем layout для окна
        side_layout = QVBoxLayout()
        side_layout.setContentsMargins(15, 15, 15, 15)
        side_layout.setSpacing(15)

        # Добавляем заголовок
        self.title_label = QLabel("Детектор")
        self.title_label.setObjectName("titleLabel")
        side_layout.addWidget(self.title_label)

        # Создаем таблицу
        self.side_table = QTableWidget()
        self.side_table.setColumnCount(2)
        self.side_table.setRowCount(20)
        self.side_table.setHorizontalHeaderLabels(["Параметр", "Значение"])

        # Данные для таблицы
        data = [
            ("a (Alfa)", ""),
            ("b (Alfa)", ""),
            ("a (Beta)", ""),
            ("b (Beta)", ""),
            ("k1p9", ""),
            ("k1c0", ""),
            ("НУД β", ""),
            ("ВУД β", ""),
            ("НУД α, № канала (2700)", ""),
            ("ВУД ROI 3, № канала (4385.6)", ""),
            ("НУД ROI 2, № канала (5687.5)", ""),
            ("НУД ROI 6, № канала (6192.35)", ""),
            ("НУД ROI 4, № канала (6337.7)", ""),
            ("НУД ROI 5, № канала (8044.6)", ""),
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
        side_layout.addWidget(self.side_table)

        # Кнопки
        fill_button = QPushButton("Вывод")
        fill_button.setObjectName("fillButton")
        fill_button.clicked.connect(self.fill_values)

        output_button = QPushButton("Ввод")
        output_button.setObjectName("outputButton")
        output_button.clicked.connect(self.write_values)  # Подключаем новый метод

        update_button = QPushButton("Обновить")
        update_button.setObjectName("updateButton")
        update_button.clicked.connect(self.update_from_report)

        # Компоновка кнопок
        top_button_layout = QHBoxLayout()
        top_button_layout.addStretch()
        top_button_layout.addWidget(fill_button)
        top_button_layout.addWidget(output_button)
        top_button_layout.addStretch()

        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.addStretch()
        bottom_button_layout.addWidget(update_button)
        bottom_button_layout.addStretch()

        side_layout.addLayout(top_button_layout)
        side_layout.addLayout(bottom_button_layout)

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

            # Сопоставление строк и значений
            row_values = {
                0: value_5004_float,  # 0x5004-0x5005 a(Alfa)
                1: value_5006_float,  # 0x5006-0x5007 b(Alfa)
                2: value_5000_float,  # 0x5000-0x5001 a(Beta)
                3: value_5002_float,  # 0x5002-0x5003 b(Beta)
                4: value_500B_float,  # 0x500B-0x500C k1p9
                5: value_500D_float,  # 0x500D-0x500E k1c0
                6: value_500F,  # 0x500F "НУД β"
                7: value_5010,  # 0x5010 "ВУД β"
                8: value_5011,  # 0x5011 (uint16, строка 2)
                9: value_5012,  # 0x5012 (uint16, строка 3)
                10: value_5013,  # 0x5013 (uint16, строка 4)
                11: value_5018,  # 0x5018 (uint16, строка 5)
                12: value_501D,  # 0x501D (uint16, строка 6)
                13: value_5022,  # 0x5022 (uint16, строка 7)


            }

            # Заполняем таблицу
            for row in range(self.side_table.rowCount()):
                if row in row_values:
                    # Форматируем float с двумя знаками после запятой
                    if row in (0, 1, 8, 11, 12, 13):  # Для значений float
                        item = QTableWidgetItem(f"{row_values[row]:.2f}")
                    else:
                        item = QTableWidgetItem(str(row_values[row]))



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

    def write_values(self):
        """Записывает числовые значения из столбца 'Значение' в регистры детектора."""
        try:
            if not self.modbus.client.connect():
                raise ConnectionError("Не удалось подключиться к устройству")

            # Сопоставление строк таблицы с адресами регистров
            register_mapping = {
                0: 0x5004,  # a (Alfa), float (2 регистра)
                1: 0x5006,  # b (Alfa), float (2 регистра)
                2: 0x5000,  # a (Beta), float (2 регистра)
                3: 0x5002,  # b (Beta), float (2 регистра)
                4: 0x500B,  # k1p9, float (2 регистра)
                5: 0x500D,  # k1c0, float (2 регистра)
                6: 0x500F,  # НУД β, uint16 (1 регистр)
                7: 0x5010,  # ВУД β, uint16 (1 регистр)
                8: 0x5011,  # НУД α, uint16 (1 регистр)
                9: 0x5012,  # ВУД ROI 3, uint16 (1 регистр)
                10: 0x5013,  # НУД ROI 2, uint16 (1 регистр)
                11: 0x5018,  # НУД ROI 6, uint16 (1 регистр)
                12: 0x501D,  # НУД ROI 4, uint16 (1 регистр)
                13: 0x5022,  # НУД ROI 5, uint16 (1 регистр)
                14: 0x5014,  # Pn (80 кэВ), uint16 (1 регистр)
                15: 0x5015,  # Pn (146 кэВ), uint16 (1 регистр)
                16: 0x5016,  # Pn (400 кэВ), uint16 (1 регистр)
                17: 0x5017,  # Pn (850 кэВ), uint16 (1 регистр)
                18: 0x5019,  # Pn (1500 кэВ), uint16 (1 регистр)
                19: 0x501A,  # Pn (2515 кэВ), uint16 (1 регистр)
            }

            float_rows = {0, 1, 2, 3, 4, 5}  # Строки с float значениями (2 регистра)

            # Собираем данные для записи
            for row in range(self.side_table.rowCount()):
                value_item = self.side_table.item(row, 1)
                if not value_item or not value_item.text().strip():
                    continue  # Пропускаем пустые строки

                value_str = value_item.text().strip()
                try:
                    # Проверяем, является ли значение числом
                    if row in float_rows:
                        # Для float значений
                        value = float(value_str)
                        # Преобразуем float в два uint16 регистра
                        float_bytes = struct.pack('>f', value)
                        reg1, reg2 = struct.unpack('>HH', float_bytes)
                        address = register_mapping[row]
                        # Используем 0x10 для записи двух регистров
                        response = self.modbus.client.write_registers(
                            address=address,
                            values=[reg1, reg2],
                            slave=1
                        )
                        if response.isError():
                            raise ModbusException(f"Ошибка записи в регистры {hex(address)}-{hex(address + 1)}")
                        print(f"Записано в регистр {hex(address)}: {reg1}")
                        print(f"Записано в регистр {hex(address + 1)}: {reg2}")
                    else:
                        # Для uint16 используем write_registers вместо write_register
                        value = int(float(value_str))
                        if not 0 <= value <= 65535:
                            raise ValueError(f"Значение {value} вне диапазона uint16 (0-65535)")
                        address = register_mapping[row]
                        response = self.modbus.client.write_registers(
                            address=address,
                            values=[value],
                            slave=1
                        )
                        if response.isError():
                            raise ModbusException(f"Ошибка записи в регистр {hex(address)}")
                        print(f"Записано в регистр {hex(address)}: {value}")

                except ValueError as e:
                    print(f"Ошибка: Значение '{value_str}' в строке {row} не является числом или вне диапазона: {e}")
                except ModbusException as e:
                    print(f"Ошибка Modbus при записи в строку {row}: {e}")

        except Exception as e:
            print(f"Ошибка при записи данных: {str(e)}")
        finally:
            self.modbus.client.close()