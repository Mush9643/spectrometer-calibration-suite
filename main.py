import sys
from PyQt6.QtCharts import QChart, QLineSeries, QValueAxis, QChartView, QLogValueAxis
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QDialog, \
    QSplashScreen, QCheckBox  # Добавляем QCheckBox
from PyQt6.QtGui import QPixmap, QIcon, QPainter
from PyQt6.QtCore import Qt, QTimer
from modbus import ModbusClient  # Импортируем ModbusClient из файла modbus.py
from settings_dialog import SettingsDialog  # Импортируем диалоговое окно настроек
import pandas as pd  # Для работы с Excel
import math  # Для логарифмического преобразования


class SpectrumWindow(QMainWindow):
    def __init__(self, modbus):
        super().__init__()
        # Сохраняем ModbusClient для использования
        self.modbus_client = modbus
        # Устанавливаем заголовок окна
        self.setWindowTitle("Спектр импульсов")

        # Устанавливаем иконку окна
        self.setWindowIcon(QIcon("M-Photoroom.png"))  # Замените "icon.png" на путь к вашей иконке

        # Создаем график
        self.chart = QChart()
        self.chart.setTitle("Спектр импульсов (0-1023)")
        # Создаем серию данных для графика
        self.series = QLineSeries()
        self.series.setName("Импульсы")
        # Чтение данных с устройства Modbus
        try:
            self.spectrum_values = self.update_spectrum()
        except Exception as e:
            self.show_error_message(str(e))
            self.spectrum_values = []
        # Добавляем серию на график
        self.chart.addSeries(self.series)
        # Создаем и настраиваем оси
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Точка спектра")
        self.axis_x.setRange(0, 1023)
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Значение импульса")

        # Исправленный способ получения минимального и максимального значения
        points = self.series.points()
        if points:
            y_values = [point.y() for point in points]
            self.axis_y.setRange(min(y_values), max(y_values))
        else:
            self.axis_y.setRange(0, 1)  # Задаём начальный диапазон, если данные отсутствуют

        # Привязываем оси к графику
        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)
        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)

        # Создаем виджет для отображения графика
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Кнопка для сохранения данных
        self.export_button = QPushButton("Экспорт в Excel")
        self.export_button.clicked.connect(self.export_to_excel)

        # Чекбокс для переключения в логарифмический масштаб
        self.log_checkbox = QCheckBox("Логарифмический масштаб")
        self.log_checkbox.stateChanged.connect(self.toggle_log_scale)

        # Размещаем виджеты в вертикальном layout
        layout = QVBoxLayout()
        layout.addWidget(self.chart_view)
        layout.addWidget(self.export_button)
        layout.addWidget(self.log_checkbox)

        # Создаем контейнер для размещения layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_spectrum(self):
        """
        Обновляет данные спектра с устройства Modbus и обновляет график.
        """
        spectrum_values = self.modbus_client.read_spectrum(
            start_register=0x0100,
            num_registers=1024,
            slave_address=1
        )

        # Очищаем предыдущие данные на графике
        self.series.clear()

        # Добавляем новые данные в серию, заменяя первые два значения на 0 для отображения
        for i, value in enumerate(spectrum_values):
            display_value = 0 if i < 2 else value
            self.series.append(i, display_value)

        # Сохраняем оригинальные значения спектра
        self.spectrum_values = spectrum_values
        return spectrum_values

#############################################################
    def toggle_log_scale(self, state):
        """
        Переключает график между линейным и логарифмическим масштабом.
        """
        if state == Qt.CheckState.Checked.value:
            self.apply_log_scale()
        else:
            self.apply_linear_scale()

    def apply_log_scale(self):
        """
        Применяет логарифмический масштаб к оси Y, заменяя первые два значения на 1 только для логарифмического представления.
        """
        if not hasattr(self, "original_series"):  # Сохраняем оригинальную серию только один раз
            self.original_series = self.series

        # Создаем логарифмическую ось
        log_axis_y = QLogValueAxis()
        log_axis_y.setTitleText("Значение импульса (логарифмический масштаб)")

        # Получаем копию точек данных
        points = self.original_series.points()
        if not points:
            log_axis_y.setRange(1, 10)  # Устанавливаем стандартный диапазон
            return

        y_values = [point.y() for point in points]

        # Создаём изменённую версию данных для логарифмического отображения
        log_y_values = y_values.copy()
        if len(log_y_values) >= 2:
            log_y_values[0] = max(log_y_values[0], 1)
            log_y_values[1] = max(log_y_values[1], 1)

        # Исключаем нулевые значения (логарифм не определён для 0)
        log_y_values = [y for y in log_y_values if y > 0]

        if log_y_values:
            log_axis_y.setRange(min(log_y_values), max(log_y_values))
        else:
            log_axis_y.setRange(1, 10)

        # Создаём новый временный `QLineSeries` для логарифмического отображения
        log_series = QLineSeries()
        for i, y in enumerate(log_y_values):
            log_series.append(i, y)

        # Удаляем старую ось Y и добавляем новую
        self.chart.removeAxis(self.axis_y)
        self.chart.addAxis(log_axis_y, Qt.AlignmentFlag.AlignLeft)

        # Отключаем старую серию и добавляем логарифмическую временную серию
        self.chart.removeSeries(self.series)
        self.chart.addSeries(log_series)
        log_series.attachAxis(log_axis_y)

        # Обновляем текущую серию для логарифмического отображения
        self.series = log_series
        self.axis_y = log_axis_y

        print("Обновлённые данные для логарифмического масштаба:", log_y_values)

    def apply_linear_scale(self):
        """
        Восстанавливает оригинальный линейный масштаб без изменений.
        """
        if not hasattr(self, "original_series"):
            return  # Если оригинальная серия не была сохранена, ничего не делаем

        # Создаем линейную ось
        linear_axis_y = QValueAxis()
        linear_axis_y.setTitleText("Значение импульса")

        # Получаем исходные данные
        points = self.original_series.points()
        if points:
            y_values = [point.y() for point in points]
            linear_axis_y.setRange(min(y_values), max(y_values))
        else:
            linear_axis_y.setRange(0, 1)  # Задаём начальный диапазон, если данные отсутствуют

        # Удаляем старую ось Y и добавляем новую
        self.chart.removeAxis(self.axis_y)
        self.chart.addAxis(linear_axis_y, Qt.AlignmentFlag.AlignLeft)

        # Удаляем временную серию логарифмического масштаба и возвращаем оригинальную
        self.chart.removeSeries(self.series)
        self.chart.addSeries(self.original_series)
        self.original_series.attachAxis(linear_axis_y)

        # Восстанавливаем исходную серию
        self.series = self.original_series
        self.axis_y = linear_axis_y

    #############################################################

    def export_to_excel(self):
        """
        Экспорт данных спектра в Excel.
        """
        try:
            if not hasattr(self, 'spectrum_values') or not self.spectrum_values:
                self.show_warning_message("Нет данных для экспорта.")
                return

            data = {
                "Точка спектра": list(range(len(self.spectrum_values))),
                "Значение": self.spectrum_values
            }
            df = pd.DataFrame(data)

            file_name = "spectrum_data.xlsx"
            df.to_excel(file_name, index=False)
            self.show_info_message(f"Данные успешно экспортированы в {file_name}")
        except Exception as e:
            self.show_error_message(f"Ошибка при экспорте данных: {str(e)}")

    def show_info_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Информация")
        msg_box.setText(message)
        msg_box.exec()

    def show_warning_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Предупреждение")
        msg_box.setText(message)
        msg_box.exec()

    def show_error_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Ошибка")
        msg_box.setText(message)
        msg_box.exec()


# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Устанавливаем иконку приложения
    app.setWindowIcon(QIcon("app_icon.png"))  # Замените "app_icon.png" на путь к вашей иконке

    # Показываем диалог настроек
    dialog = SettingsDialog()
    if dialog.exec() == QDialog.DialogCode.Rejected:
        sys.exit(0)  # Выходим, если пользователь нажал Cancel

    # Получаем параметры подключения
    settings = dialog.get_settings()

    # Создаем загрузочный экран
    splash = QSplashScreen(QPixmap("Micasensor.png"))  # Замените "splash_image.png" на путь к вашему изображению
    splash.showMessage("Загрузка...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                       Qt.GlobalColor.white)
    splash.show()

    # Имитируем процесс загрузки (например, подключение к устройству)
    app.processEvents()  # Обеспечиваем отображение загрузочного экрана
    modbus = ModbusClient(
        port=settings["port"],
        baud_rate=settings["baud_rate"],
        parity=settings["parity"],
        stop_bits=settings["stop_bits"],
        byte_size=settings["byte_size"],
        timeout=settings["timeout"]
    )

    # Закрываем загрузочный экран через таймер или после завершения загрузки
    QTimer.singleShot(2000, splash.close)  # Закрываем через 2 секунды

    # Создаем и показываем главное окно
    window = SpectrumWindow(modbus)
    window.resize(800, 600)

    # Ждём закрытия загрузочного экрана, прежде чем показывать главное окно
    QTimer.singleShot(2000, window.show)

    # Запуск цикла событий
    sys.exit(app.exec())