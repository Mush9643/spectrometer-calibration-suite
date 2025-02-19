################################# 1. Импорт необходимых библиотек #################################

import sys
from PyQt6.QtCharts import QChart, QLineSeries, QValueAxis, QChartView, QLogValueAxis
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QDialog, \
    QSplashScreen, QCheckBox, QLineEdit, QTabWidget, QListWidgetItem, QListWidget, QMenu
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QDesktopServices, QColor
from PyQt6.QtCore import Qt, QTimer, QUrl
from modbus import ModbusClient
from settings_dialog import SettingsDialog
import pandas as pd
import math
import os

################################# 2. Инициализация и настройка окна #################################
class SpectrumWindow(QMainWindow):
    def __init__(self, modbus):
        super().__init__()
        self.modbus_client = modbus
        self.setWindowTitle("Спектр импульсов")
        self.setWindowIcon(QIcon("M-Photoroom.png"))

        # Инициализируем словари для серий
        self.alfa_series_dict = {}
        self.beta_series_dict = {}

        # Создаем вкладки
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Вкладка "Menu"
        self.tab0 = QWidget()
        self.tabs.addTab(self.tab0, "Menu")
        menu_layout = QVBoxLayout()
        # Поле для ввода имени папки
        self.folder_input = QLineEdit("098")  # По умолчанию папка "098"
        self.folder_input.setPlaceholderText("Введите имя папки и нажмите ENTER")
        self.folder_input.returnPressed.connect(self.load_xls_files)  # Обработка нажатия ENTER
        menu_layout.addWidget(self.folder_input)

        # Список для отображения файлов .xls
        self.file_list = QListWidget()
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)  # Обработка правого клика
        menu_layout.addWidget(self.file_list)
        # Кнопка "Экспорт в Excel"
        self.export_button = QPushButton("Экспорт в Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        menu_layout.addWidget(self.export_button)
        self.tab0.setLayout(menu_layout)
        # Загружаем файлы .xls из папки по умолчанию
        self.load_xls_files()

        # Первая вкладка
        self.tab1 = QWidget()
        self.tabs.addTab(self.tab1, "Alfa chart")

        # Создаем график для первой вкладки
        self.chart = QChart()
        self.chart.setTitle("Спектр импульсов (0-1023)")
        self.series = QLineSeries()
        self.series.setName("Импульсы")
        try:
            self.spectrum_values = self.update_spectrum()
        except Exception as e:
            self.show_error_message(str(e))
            self.spectrum_values = []
        self.chart.addSeries(self.series)
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Точка спектра")
        self.axis_x.setRange(0, 1023)
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Значение импульса")

        points = self.series.points()
        if points:
            y_values = [point.y() for point in points]
            self.axis_y.setRange(min(y_values), max(y_values))
        else:
            self.axis_y.setRange(0, 1)

        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)
        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.log_checkbox = QCheckBox("Логарифмический масштаб")
        self.log_checkbox.stateChanged.connect(self.toggle_log_scale)

        layout = QVBoxLayout()
        layout.addWidget(self.chart_view)
        layout.addWidget(self.log_checkbox)
        self.tab1.setLayout(layout)

        # Вторая вкладка
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab2, "Beta chart")

        # Создаем график для второй вкладки
        self.beta_chart = QChart()
        self.beta_chart.setTitle("Beta chart")
        self.beta_series = QLineSeries()
        self.beta_series.setName("Beta данные")
        self.beta_chart.addSeries(self.beta_series)

        self.beta_axis_x = QValueAxis()
        self.beta_axis_x.setTitleText("Точка")
        self.beta_axis_x.setRange(0, 100)
        self.beta_axis_y = QValueAxis()
        self.beta_axis_y.setTitleText("Значение")

        self.beta_chart.addAxis(self.beta_axis_x, Qt.AlignmentFlag.AlignBottom)
        self.beta_chart.addAxis(self.beta_axis_y, Qt.AlignmentFlag.AlignLeft)
        self.beta_series.attachAxis(self.beta_axis_x)
        self.beta_series.attachAxis(self.beta_axis_y)

        self.beta_chart_view = QChartView(self.beta_chart)
        self.beta_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        beta_layout = QVBoxLayout()
        beta_layout.addWidget(self.beta_chart_view)
        self.tab2.setLayout(beta_layout)

    def load_xls_files(self):
        """Загружает список файлов .xls из указанной папки."""
        folder_name = self.folder_input.text()  # Получаем имя папки из поля ввода
        folder_path = os.path.join(os.getcwd(), folder_name)  # Полный путь к папке

        self.file_list.clear()  # Очищаем список перед загрузкой новых файлов

        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            # Получаем список файлов .xls в папке
            xls_files = [f for f in os.listdir(folder_path) if f.endswith(".xls")]
            for file_name in xls_files:
                item = QListWidgetItem(file_name)
                self.file_list.addItem(item)
        else:
            # Если папка не существует, выводим сообщение
            self.show_warning_message(f"Папка '{folder_name}' не найдена.")

    def show_context_menu(self, pos):
        """Отображает контекстное меню при правом клике на файл."""
        context_menu = QMenu(self)  # Создаем меню
        open_action = context_menu.addAction("Открыть")  # Добавляем кнопку "Открыть"
        load_alfa_action = context_menu.addAction("Загрузить Alfa")  # Добавляем кнопку "Загрузить Alfa"
        load_beta_action = context_menu.addAction("Загрузить Beta")  # Добавляем кнопку "Загрузить Beta"
        disable_action = context_menu.addAction("Отключить")  # Добавляем кнопку "Отключить"

        # Связываем действия с методами
        open_action.triggered.connect(lambda: self.open_xls_file(pos))
        load_alfa_action.triggered.connect(lambda: self.change_color(pos, 'alfa'))
        load_beta_action.triggered.connect(lambda: self.change_color(pos, 'beta'))
        load_alfa_action.triggered.connect(lambda: self.check_color_and_load_data(pos))  # Загрузка данных для Alfa
        load_beta_action.triggered.connect(lambda: self.check_color_and_load_data(pos))  # Загрузка данных для Beta
        disable_action.triggered.connect(lambda: self.change_color(pos, 'disable'))

        context_menu.exec(self.file_list.mapToGlobal(pos))  # Показываем меню в точке правого клика

    def change_color(self, pos, action_type):
        """Меняет цвет фона элемента в зависимости от действия и отображает/удаляет графики."""
        index = self.file_list.indexAt(pos)
        item = self.file_list.itemFromIndex(index)

        if action_type == 'alfa':
            item.setBackground(QColor(144, 238, 144))  # Салатовый для "Загрузить Alfa"
            self.add_or_remove_chart(item.text(), 'alfa', True)
        elif action_type == 'beta':
            item.setBackground(QColor(173, 216, 230))  # Голубой для "Загрузить Beta"
            self.add_or_remove_chart(item.text(), 'beta', True)
        elif action_type == 'disable':
            item.setBackground(Qt.GlobalColor.white)  # Обесцвечиваем поле для "Отключить"
            self.add_or_remove_chart(item.text(), 'alfa', False)
            self.add_or_remove_chart(item.text(), 'beta', False)

    def add_or_remove_chart(self, file_name, chart_type, add):
        """Добавляет или удаляет график в зависимости от состояния."""
        if chart_type == 'alfa' and not hasattr(self, 'alfa_series_dict'):
            self.alfa_series_dict = {}  # Инициализируем словарь, если его нет
        elif chart_type == 'beta' and not hasattr(self, 'beta_series_dict'):
            self.beta_series_dict = {}  # Инициализируем словарь, если его нет

        if add:
            if chart_type == 'alfa' and file_name not in self.alfa_series_dict:
                self.load_data_for_chart('alfa', file_name)
            elif chart_type == 'beta' and file_name not in self.beta_series_dict:
                self.load_data_for_chart('beta', file_name)
        else:
            if chart_type == 'alfa':
                self.remove_specific_chart('alfa', file_name)
            elif chart_type == 'beta':
                self.remove_specific_chart('beta', file_name)

    def open_xls_file(self, pos):
        """Открывает выбранный файл .xls при правом клике."""
        index = self.file_list.indexAt(pos)
        item = self.file_list.itemFromIndex(index)
        folder_name = self.folder_input.text()  # Получаем имя папки из поля ввода
        folder_path = os.path.join(os.getcwd(), folder_name)  # Полный путь к папке
        file_name = item.text()  # Получаем имя файла из выбранного элемента
        file_path = os.path.join(folder_path, file_name)  # Полный путь к файлу

        if os.path.exists(file_path):
            # Открываем файл с помощью стандартного приложения
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            self.show_warning_message(f"Файл '{file_name}' не найден.")

    def remove_specific_chart(self, chart_type, file_name):
        """Удаляет конкретный график, связанный с файлом."""
        if chart_type == 'alfa':
            if file_name in self.alfa_series_dict:
                series_to_remove = self.alfa_series_dict[file_name]
                self.chart.removeSeries(series_to_remove)
                del self.alfa_series_dict[file_name]
        elif chart_type == 'beta':
            if file_name in self.beta_series_dict:
                series_to_remove = self.beta_series_dict[file_name]
                self.beta_chart.removeSeries(series_to_remove)
                del self.beta_series_dict[file_name]

    def check_color_and_load_data(self, pos):
        """Проверяет цвет фона элемента и загружает данные из Excel в соответствующий график."""
        index = self.file_list.indexAt(pos)
        item = self.file_list.itemFromIndex(index)

        # Получаем цвет фона элемента
        background_color = item.background().color()

        # Проверяем цвет фона
        if background_color == QColor(144, 238, 144):  # Салатовый цвет для 'Alfa'
            self.load_data_for_chart('alfa', item.text())
        elif background_color == QColor(173, 216, 230):  # Голубой цвет для 'Beta'
            self.load_data_for_chart('beta', item.text())

    def load_data_for_chart(self, chart_type, file_name):
        """Загружает данные из файла Excel и отображает на соответствующем графике."""
        folder_name = self.folder_input.text()  # Получаем имя папки из поля ввода
        folder_path = os.path.join(os.getcwd(), folder_name)  # Полный путь к папке
        file_path = os.path.join(folder_path, file_name)  # Полный путь к файлу

        if not os.path.exists(file_path):
            self.show_warning_message(f"Файл '{file_name}' не найден.")
            return

        try:
            # Чтение данных из Excel
            df = pd.read_excel(file_path)

            # Проверяем структуру данных
            if 'Канал' not in df.columns or 'Кол-во импульсов' not in df.columns:
                self.show_warning_message(f"Неверный формат данных в файле '{file_name}'.")
                return

            # Заменяем первые три значения импульсов на 0
            df.loc[0:2, 'Кол-во импульсов'] = 0  # Заменяем первые 3 строки на 0 в колонке 'Кол-во импульсов'

            # Отображаем данные на графиках
            if chart_type == 'alfa':
                self.update_alfa_chart(df, file_name)
            elif chart_type == 'beta':
                self.update_beta_chart(df, file_name)

        except Exception as e:
            self.show_error_message(f"Ошибка при загрузке данных из файла: {str(e)}")

    def update_alfa_chart(self, df, file_name):
        """Обновляет график на вкладке Alfa с данными из Excel."""
        if file_name in self.alfa_series_dict:
            # Если график уже есть, не добавляем новый
            return
        file_name_split = file_name.split()[1]
        alfa_series = QLineSeries()
        alfa_series.setName(f"({file_name_split})")

        # Проходим по строкам DataFrame и добавляем точки на график
        for index, row in df.iterrows():
            x = row['Канал']
            y = row['Кол-во импульсов']
            alfa_series.append(x, y)

        # Сохраняем серию в словарь
        if not hasattr(self, 'alfa_series_dict'):
            self.alfa_series_dict = {}  # Создаем словарь, если он ещё не существует
        self.alfa_series_dict[file_name] = alfa_series

        self.chart.addSeries(alfa_series)
        alfa_series.attachAxis(self.axis_x)
        alfa_series.attachAxis(self.axis_y)

        # Обновляем оси
        self.axis_x.setRange(df['Канал'].min(), df['Канал'].max())
        self.axis_y.setRange(df['Кол-во импульсов'].min(), df['Кол-во импульсов'].max())

    def update_beta_chart(self, df, file_name):
        """Обновляет график на вкладке Beta с данными из Excel."""
        if file_name in self.beta_series_dict:
            # Если график уже есть, не добавляем новый
            return

        file_name_split = file_name.split()[1]
        beta_series = QLineSeries()
        beta_series.setName(f"({file_name_split})")

        # Проходим по строкам DataFrame и добавляем точки на график
        for index, row in df.iterrows():
            x = row['Канал']
            y = row['Кол-во импульсов']
            beta_series.append(x, y)

        # Сохраняем серию в словарь
        if not hasattr(self, 'beta_series_dict'):
            self.beta_series_dict = {}  # Создаем словарь, если он ещё не существует
        self.beta_series_dict[file_name] = beta_series

        self.beta_chart.addSeries(beta_series)
        beta_series.attachAxis(self.beta_axis_x)
        beta_series.attachAxis(self.beta_axis_y)

        # Обновляем оси
        self.beta_axis_x.setRange(df['Канал'].min(), df['Канал'].max())
        self.beta_axis_y.setRange(df['Кол-во импульсов'].min(), df['Кол-во импульсов'].max())

    ##########################################################################

    # Метод для обновления спектра
    def update_spectrum(self):
        spectrum_values = self.modbus_client.read_spectrum(
            start_register=0x0100,
            num_registers=1024,
            slave_address=1
        )

        self.series.clear()
        for i, value in enumerate(spectrum_values):
            display_value = 0 if i < 2 else value
            self.series.append(i, display_value)

        self.spectrum_values = spectrum_values
        return spectrum_values

    # Метод для переключения между логарифмическим и линейным масштабом
    def toggle_log_scale(self, state):
        if state == Qt.CheckState.Checked.value:
            self.apply_log_scale()
        else:
            self.apply_linear_scale()

    # Метод для применения логарифмического масштаба
    def apply_log_scale(self):
        if not hasattr(self, "original_series"):
            self.original_series = self.series

        log_axis_y = QLogValueAxis()
        log_axis_y.setTitleText("Значение импульса (логарифмический масштаб)")

        points = self.original_series.points()
        if not points:
            log_axis_y.setRange(1, 10)
            return

        y_values = [point.y() for point in points]
        log_y_values = y_values.copy()
        if len(log_y_values) >= 2:
            log_y_values[0] = max(log_y_values[0], 1)
            log_y_values[1] = max(log_y_values[1], 1)

        log_y_values = [y for y in log_y_values if y > 0]

        if log_y_values:
            log_axis_y.setRange(min(log_y_values), max(log_y_values))
        else:
            log_axis_y.setRange(1, 10)

        log_series = QLineSeries()
        for i, y in enumerate(log_y_values):
            log_series.append(i, y)

        self.chart.removeAxis(self.axis_y)
        self.chart.addAxis(log_axis_y, Qt.AlignmentFlag.AlignLeft)

        self.chart.removeSeries(self.series)
        self.chart.addSeries(log_series)
        log_series.attachAxis(log_axis_y)

        self.series = log_series
        self.axis_y = log_axis_y

    # Метод для применения линейного масштаба
    def apply_linear_scale(self):
        if not hasattr(self, "original_series"):
            return

        linear_axis_y = QValueAxis()
        linear_axis_y.setTitleText("Значение импульса")

        points = self.original_series.points()
        if points:
            y_values = [point.y() for point in points]
            linear_axis_y.setRange(min(y_values), max(y_values))
        else:
            linear_axis_y.setRange(0, 1)

        self.chart.removeAxis(self.axis_y)
        self.chart.addAxis(linear_axis_y, Qt.AlignmentFlag.AlignLeft)

        self.chart.removeSeries(self.series)
        self.chart.addSeries(self.original_series)
        self.original_series.attachAxis(linear_axis_y)

        self.series = self.original_series
        self.axis_y = linear_axis_y

    # Метод для экспорта данных в Excel
    def export_to_excel(self):
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

    # Метод для показа информационного сообщения
    def show_info_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Информация")
        msg_box.setText(message)
        msg_box.exec()

    # Метод для показа предупреждения
    def show_warning_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Предупреждение")
        msg_box.setText(message)
        msg_box.exec()

    # Метод для показа сообщения об ошибке
    def show_error_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Ошибка")
        msg_box.setText(message)
        msg_box.exec()


# Основной блок запуска приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("app_icon.png"))

    dialog = SettingsDialog()
    if dialog.exec() == QDialog.DialogCode.Rejected:
        sys.exit(0)

    settings = dialog.get_settings()

    splash = QSplashScreen(QPixmap("Micasensor.png"))
    splash.showMessage("Загрузка...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                       Qt.GlobalColor.white)
    splash.show()

    app.processEvents()
    modbus = ModbusClient(
        port=settings["port"],
        baud_rate=settings["baud_rate"],
        parity=settings["parity"],
        stop_bits=settings["stop_bits"],
        byte_size=settings["byte_size"],
        timeout=settings["timeout"]
    )

    QTimer.singleShot(2000, splash.close)

    window = SpectrumWindow(modbus)
    window.resize(800, 600)

    QTimer.singleShot(2000, window.show)

    sys.exit(app.exec())