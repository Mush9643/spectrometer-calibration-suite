import sys
from PyQt6.QtCharts import QChart, QLineSeries, QValueAxis, QChartView, QLogValueAxis, QAbstractSeries
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QDialog, \
    QSplashScreen, QCheckBox, QLineEdit, QTabWidget, QListWidgetItem, QListWidget, QMenu, QHBoxLayout
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QDesktopServices, QColor
from PyQt6.QtCore import Qt, QTimer, QUrl
from modbus import ModbusClient  # Импортируем ModbusClient из файла modbus.py
from settings_dialog import SettingsDialog  # Импортируем диалоговое окно настроек
from spectrum_addition import SpectrumAddition
import pandas as pd  # Для работы с Excel
from math_utils import highlight_am241_peak
from math_utils import highlight_rn_peaks
from math_utils import add_calibration_button
from Beta_math import add_beta_calibration_button
from Beta_math import update_calibration_button_state
from fon_math import process_fon_data
import os

##########################################################################
# Класс основного окна приложения
##########################################################################

class SpectrumWindow(QMainWindow):
    def __init__(self, modbus):
        super().__init__()
        self.fon_processed = False
        self.modbus_client = modbus
        self.setWindowTitle("Спектр импульсов")
        self.setWindowIcon(QIcon("M-Photoroom.png"))

        # Словарь для хранения использованных цветов для Alfa и Beta
        self.used_alfa_colors = {}  # Ключ — имя файла, значение — QColor
        self.used_beta_colors = {}  # Ключ — имя файла, значение — QColor
        # Список уникальных цветов (RGB)
        self.available_colors = [

            QColor(255, 206, 86),  # Жёлтый
            QColor(75, 192, 192),  # Бирюзовый
            QColor(153, 102, 255),  # Фиолетовый
            QColor(255, 159, 64),  # Оранжевый
            QColor(0, 128, 0),  # Зелёный
            QColor(128, 0, 128),  # Пурпурный
            QColor(255, 165, 0),  # Золотой
            QColor(0, 191, 255)]  # Глубокий голубой

        # Словарь для хранения массивов данных Alfa
        self.alfa_data_arrays = {}
        self.first_impulse_values = {}

        # Инициализируем серию для точек P90 (вертикальные линии)
        self.p90_series = {}
        self.calibration_coefficients = None

        # Словарь для хранения точек пиков
        self.peak_points = {}

        # Словарь для хранения CheckBox
        self.alfa_checkboxes = {}
        self.beta_checkboxes = {}

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

        self.spectrum_addition = SpectrumAddition(self)
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

        # Добавляем кнопку "Калибровка" после создания chart_view
        add_calibration_button(self)

        self.tab1.setLayout(layout)

        # Вторая вкладка (Beta chart)
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

        self.beta_log_checkbox = QCheckBox("Логарифмический масштаб")
        self.beta_log_checkbox.stateChanged.connect(self.toggle_beta_log_scale)

        beta_layout = QVBoxLayout()
        beta_layout.addWidget(self.beta_chart_view)
        beta_layout.addWidget(self.beta_log_checkbox)

        self.tab2.setLayout(beta_layout)

        # Добавляем кнопку калибровки
        add_beta_calibration_button(self)

    ##########################################################################
    # Методы для работы с файлами и контекстным меню
    ##########################################################################

    def load_xls_files(self):
        """Загружает список файлов .xls и .xlsx из указанной папки."""
        folder_name = self.folder_input.text()  # Получаем имя папки из поля ввода
        folder_path = os.path.join(os.getcwd(), folder_name)  # Полный путь к папке

        self.file_list.clear()  # Очищаем список перед загрузкой новых файлов

        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            # Получаем список файлов .xls и .xlsx в папке
            xls_files = [f for f in os.listdir(folder_path) if f.endswith((".xls", ".xlsx"))]
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

        if item is None:
            return  # Защита от некорректного индекса

        file_name = item.text()
        folder_name = self.folder_input.text()
        folder_path = os.path.join(os.getcwd(), folder_name)
        file_path = os.path.join(folder_path, file_name)

        impulse_value = self.read_first_impulse_value(file_path)

        if impulse_value is not None:
            print(f"Значение 'Кол-во импульсов' для файла '{file_name}' (первая строка): {impulse_value}")
            self.first_impulse_values[file_name] = impulse_value # Сохраняем значение

        if action_type == 'alfa':
            item.setBackground(QColor(144, 238, 144))  # Салатовый для "Загрузить Alfa"
            self.add_or_remove_chart(item.text(), 'alfa', True)
        elif action_type == 'beta':
            item.setBackground(QColor(173, 216, 230))  # Голубой для "Загрузить Beta"
            self.add_or_remove_chart(item.text(), 'beta', True)
        elif action_type == 'disable':
            item.setBackground(Qt.GlobalColor.white)  # Обесцвечиваем поле для "Отключить"
            file_name = item.text()
            # Удаляем график и все связанные данные для обоих типов
            self.add_or_remove_chart(file_name, 'alfa', False)
            self.add_or_remove_chart(file_name, 'beta', False)
            # Очищаем пики и другие зависимости, связанные с Rn
            self.cleanup_rn_data(file_name)

    def read_first_impulse_value(self, file_path):
        """Читает значение 'Кол-во импульсов' из первой строки файла Excel."""
        if not os.path.exists(file_path):
            self.show_warning_message(f"Файл '{os.path.basename(file_path)}' не найден.")
            return None

        try:
            df = pd.read_excel(file_path)
            if 'Кол-во импульсов' not in df.columns:
                self.show_warning_message(
                    f"Столбец 'Кол-во импульсов' не найден в файле '{os.path.basename(file_path)}'.")
                return None

            # Берем значение из первой строки столбца 'Кол-во импульсов'
            first_impulse = df.iloc[0]['Кол-во импульсов']
            return first_impulse

        except Exception as e:
            self.show_error_message(f"Ошибка при чтении данных из файла: {str(e)}")
            return None

    def cleanup_rn_data(self, file_name):
        """Очищает все данные, связанные с графиком Rn."""
        # Удаляем пики из peak_points, если они существуют
        if file_name in self.peak_points:
            peak_series = self.peak_points.pop(file_name, None)
            if peak_series and isinstance(peak_series, dict):
                for peak in peak_series.values():
                    if peak and self.chart.series().contains(peak):
                        self.chart.removeSeries(peak)
            elif peak_series and self.chart.series().contains(peak_series):
                self.chart.removeSeries(peak_series)

        # Пересчитываем линии P90, если график Rn был удален
        if "Rn" in file_name:
            self.highlight_p90_points()  # Обновляем линии P90, если они зависят от Rn

    def save_alfa_data(self, file_name):
        """Сохраняет вторую строку из файла .xls в alfa_data_arrays."""
        folder_name = self.folder_input.text()
        folder_path = os.path.join(os.getcwd(), folder_name)
        file_path = os.path.join(folder_path, file_name)

        if not os.path.exists(file_path):
            self.show_warning_message(f"Файл '{file_name}' не найден.")
            return

        try:
            df = pd.read_excel(file_path)
            if 'Канал' not in df.columns or 'Кол-во импульсов' not in df.columns:
                self.show_warning_message(f"Неверный формат данных в файле '{file_name}'.")
                return
            # Берем только вторую строку (индекс 1)
            if len(df) < 2:
                self.show_warning_message(f"В файле '{file_name}' менее 2 строк.")
                return
            second_row = df.iloc[0]  # Вторая строка
            channel = int(second_row['Канал'])
            impulses = second_row['Кол-во импульсов']
            self.alfa_data_arrays[file_name] = [channel, impulses]  # Сохраняем как список [Канал, Кол-во импульсов]
            print(f"Вторая строка из файла '{file_name}' сохранена: Канал={channel}, Импульсы={impulses}")
        except Exception as e:
            self.show_error_message(f"Ошибка при сохранении данных из файла: {str(e)}")

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
        try:
            if chart_type == 'alfa':
                if file_name in self.alfa_series_dict:
                    series_to_remove = self.alfa_series_dict[file_name]
                    self.chart.removeSeries(series_to_remove)

                    # Удаляем точку/пики, если они существуют
                    series_name = series_to_remove.name()
                    if series_name in self.peak_points:
                        peak_data = self.peak_points.pop(series_name)
                        if isinstance(peak_data, dict):  # Для Rn пиков (словарь)
                            for peak_series in peak_data.values():
                                if isinstance(peak_series, QAbstractSeries):
                                    self.chart.removeSeries(peak_series)
                        elif isinstance(peak_data, QAbstractSeries):  # Для Am241 пика
                            self.chart.removeSeries(peak_data)

                    # Освобождаем цвет для повторного использования
                    if file_name in self.used_alfa_colors:
                        del self.used_alfa_colors[file_name]

                    del self.alfa_series_dict[file_name]
            elif chart_type == 'beta':
                if file_name in self.beta_series_dict:
                    series_to_remove = self.beta_series_dict[file_name]
                    self.beta_chart.removeSeries(series_to_remove)

                    # Освобождаем цвет для повторного использования
                    if file_name in self.used_beta_colors:
                        del self.used_beta_colors[file_name]

                    del self.beta_series_dict[file_name]
                    # Обновляем состояние кнопки после удаления графика
                    update_calibration_button_state(self)
        except Exception as e:
            self.show_error_message(f"Ошибка при удалении графика: {str(e)}")

        if chart_type == 'beta' and file_name in self.beta_series_dict:
            series_to_remove = self.beta_series_dict[file_name]
            self.beta_chart.removeSeries(series_to_remove)
            del self.beta_series_dict[file_name]
            update_calibration_button_state(self)  # Обновляем состояние кнопки

    ##########################################################################
    # Методы для работы с графиками и данными
    ##########################################################################

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

    def update_y_axis_range(self):
        """Пересчитывает диапазон оси Y на основе всех имеющихся серий Alfa."""
        max_y = max((max((point.y() for point in series.points()), default=0)
                     for series in self.alfa_series_dict.values()), default=0)
        self.axis_y.setRange(0, max_y * 1.1)

    def update_beta_y_axis_range(self):
        """Пересчитывает диапазон оси Y на основе всех имеющихся серий Beta."""
        max_y = max((max((point.y() for point in series.points()), default=0)
                     for series in self.beta_series_dict.values()), default=0)
        self.beta_axis_y.setRange(0, max_y * 1.1)

    def adjust_y_axis_for_series(self, series, state):
        """Настраивает ось Y для графика Alfa в зависимости от состояния CheckBox."""
        if series is None or series.count() == 0:
            return

        if state == Qt.CheckState.Checked.value:
            max_y = max(point.y() for point in series.points()) if series.count() > 0 else 0
            self.axis_y.setRange(0, max_y * 1.1)
        else:
            self.update_y_axis_range()

    def adjust_beta_y_axis_for_series(self, series, state):
        """Настраивает ось Y для графика Beta в зависимости от состояния CheckBox."""
        if series is None or series.count() == 0:
            return

        if state == Qt.CheckState.Checked.value:
            max_y = max(point.y() for point in series.points()) if series.count() > 0 else 0
            self.beta_axis_y.setRange(0, max_y * 1.1)
        else:
            self.update_beta_y_axis_range()

    def highlight_p90_points(self):
        """Отмечает вертикальными красными линиями позиции P90 на графике Alfa chart."""
        # Удаляем старые серии, если они существуют
        for series in list(self.p90_series.values()):
            self.chart.removeSeries(series)
        self.p90_series.clear()

        # Координаты x для P90
        p90_x_values = [221, 391, 523, 574, 589, 762]

        # Находим максимальное значение y для установки высоты линий
        max_y = max((max((point.y() for point in series.points()), default=1)
                     for series in self.alfa_series_dict.values()), default=1000)

        # Создаем вертикальные линии для каждой координаты x
        for x in p90_x_values:
            line_series = QLineSeries()
            line_series.setName(f"P90 at x={x}")
            line_series.setColor(QColor(255, 0, 0))  # Красный цвет
            line_series.append(x, 0)  # Начало линии
            line_series.append(x, max_y * 1.1)  # Конец линии (с запасом выше максимума)
            self.chart.addSeries(line_series)
            line_series.attachAxis(self.axis_x)
            line_series.attachAxis(self.axis_y)
            self.p90_series[x] = line_series

    def update_alfa_chart(self, df, file_name):
        """
        Обновляет график на вкладке Alfa с учетом всех графиков и добавляет линии P90.
        """
        if file_name in self.alfa_series_dict:
            return

        alfa_series = QLineSeries()
        second_word = file_name.split()[1] if len(file_name.split()) > 1 else file_name
        alfa_series.setName(f"({second_word})")

        df_filtered = df[(df['Канал'] >= 200) & (df['Канал'] <= 1023)]
        for _, row in df_filtered.iterrows():
            alfa_series.append(row['Канал'], row['Кол-во импульсов'])

        color = self.get_unique_color(file_name, 'alfa')
        alfa_series.setColor(color)

        self.alfa_series_dict[file_name] = alfa_series
        if not hasattr(self, "original_alfa_series"):
            self.original_alfa_series = {}
        # Сохраняем серию и её цвет как кортеж (серия, цвет)
        self.original_alfa_series[file_name] = (alfa_series, color)
        self.chart.addSeries(alfa_series)
        alfa_series.attachAxis(self.axis_x)
        alfa_series.attachAxis(self.axis_y)

        # Вызываем highlight_am241_peak и highlight_rn_peaks с передачей self как parent_window
        highlight_am241_peak(self.chart, alfa_series, self.peak_points)
        highlight_rn_peaks(self.chart, alfa_series, self.peak_points, self)

        # Явно сохраняем calibration_coefficients, если они вычислены
        if "Rn" in file_name and self.calibration_coefficients is None:
            print("Обновляем calibration_coefficients для файла Rn...")
            if hasattr(self, 'calibration_coefficients') and self.calibration_coefficients is not None:
                print(
                    f"Текущие коэффициенты: intercept={self.calibration_coefficients[0]:.3f}, slope={self.calibration_coefficients[1]:.3f}")
            else:
                print("Коэффициенты еще не вычислены, пытаемся обновить...")
                from math_utils import calculate_calibration_coefficients_fallback
                intercept, slope = calculate_calibration_coefficients_fallback(self)
                if intercept != 0.0 or slope != 0.0:
                    self.calibration_coefficients = (intercept, slope)
                    print(f"Резервно вычисленные коэффициенты: intercept={intercept:.3f}, slope={slope:.3f}")

        if file_name in self.alfa_checkboxes:
            old_checkbox = self.alfa_checkboxes.pop(file_name)
            old_checkbox.setParent(None)
            old_checkbox.deleteLater()

        checkbox = QCheckBox(f"Активировать масштаб для {second_word}")
        checkbox.stateChanged.connect(
            lambda state, series=alfa_series: self.adjust_y_axis_for_series(series, state))
        self.alfa_checkboxes[file_name] = checkbox

        layout = self.tab1.layout()
        if isinstance(layout, QVBoxLayout):
            layout.addWidget(checkbox)

        self.update_y_axis_range()

        # Вызываем метод для добавления линий P90
        self.highlight_p90_points()

    def update_beta_chart(self, df, file_name):
        """
        Обновляет график на вкладке Beta с учетом всех графиков.

        Args:
            df (pandas.DataFrame): Данные из Excel-файла.
            file_name (str): Имя файла, по которому строится график.
        """
        # Если график уже есть, не добавляем новый
        if file_name in self.beta_series_dict:
            return

        # Извлекаем второе слово из имени файла для названия серии
        second_word = file_name.split()[1] if len(file_name.split()) > 1 else file_name
        series_name = f"({second_word})"

        # Проверяем, является ли график фоновым, до его добавления
        if "фона" in series_name.lower():
            # Создаем временную серию для передачи в process_fon_data
            beta_series = QLineSeries()
            beta_series.setName(series_name)
            for _, row in df.iterrows():
                beta_series.append(row['Канал'], row['Кол-во импульсов'])
            # Временно добавляем серию в beta_series_dict для process_fon_data
            self.beta_series_dict[file_name] = beta_series
            process_fon_data(self)  # Удаляет серию и выводит данные
            return  # Прерываем выполнение, чтобы не добавлять чекбокс и не обновлять ось

        # Если это не фоновый график, продолжаем как обычно
        beta_series = QLineSeries()
        beta_series.setName(series_name)

        # Заполняем серию данными из DataFrame
        for _, row in df.iterrows():
            beta_series.append(row['Канал'], row['Кол-во импульсов'])

        # Выбираем уникальный цвет для серии
        color = self.get_unique_color(file_name, 'beta')
        beta_series.setColor(color)

        # Сохраняем серию в словари
        self.beta_series_dict[file_name] = beta_series
        if not hasattr(self, "original_beta_series"):
            self.original_beta_series = {}
        self.original_beta_series[file_name] = (beta_series, color)

        # Добавляем серию на график и привязываем оси
        self.beta_chart.addSeries(beta_series)
        beta_series.attachAxis(self.beta_axis_x)
        beta_series.attachAxis(self.beta_axis_y)

        # Удаляем старый CheckBox, если он есть
        if file_name in self.beta_checkboxes:
            old_checkbox = self.beta_checkboxes.pop(file_name)
            old_checkbox.setParent(None)
            old_checkbox.deleteLater()

        # Создаем CheckBox
        checkbox = QCheckBox(f"Активировать масштаб для {second_word}")
        checkbox.stateChanged.connect(
            lambda state, series=beta_series: self.adjust_beta_y_axis_for_series(series, state))
        self.beta_checkboxes[file_name] = checkbox

        # Добавляем CheckBox в layout вкладки Beta
        layout = self.tab2.layout()
        if isinstance(layout, QVBoxLayout):
            layout.addWidget(checkbox)

        # Обновляем диапазон оси Y
        self.update_beta_y_axis_range()

        # Обновляем состояние кнопки калибровки
        update_calibration_button_state(self)

    def get_unique_color(self, file_name, chart_type):
        """Выбирает уникальный цвет для новой серии, избегая повторений."""
        if chart_type == 'alfa':
            used_colors = self.used_alfa_colors
            available_colors = self.available_colors.copy()
        else:  # 'beta'
            used_colors = self.used_beta_colors
            available_colors = self.available_colors.copy()

        # Удаляем уже использованные цвета из доступных
        for color in used_colors.values():
            if color in available_colors:
                available_colors.remove(color)

        if not available_colors:  # Если все цвета использованы, сбрасываем или генерируем новые
            available_colors = self.available_colors.copy()  # Сбрасываем к начальному набору
            # Можно также генерировать случайные цвета:
            # import random
            # r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
            # return QColor(r, g, b)

        # Выбираем первый доступный цвет
        color = available_colors[0]
        used_colors[file_name] = color  # Сохраняем цвет для этого файла
        return color

    ##########################################################################
    # Методы для работы с графиками и масштабированием
    ##########################################################################

    def update_spectrum(self):
        """Обновляет спектр импульсов."""
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

    def toggle_log_scale(self, state):
        """Переключает между логарифмическим и линейным масштабом для всех серий Alfa."""
        if state == Qt.CheckState.Checked.value:
            self.apply_log_scale()
        else:
            self.apply_linear_scale()
        # Перерисовываем линии P90 после смены масштаба
        self.highlight_p90_points()

    def toggle_beta_log_scale(self, state):
        """Переключает между логарифмическим и линейным масштабом для всех серий Beta."""
        if state == Qt.CheckState.Checked.value:
            self.apply_beta_log_scale()
        else:
            self.apply_beta_linear_scale()

    def apply_log_scale(self):
        """Применяет логарифмический масштаб ко всем сериям Alfa с началом оси Y от 1."""
        if not hasattr(self, "original_alfa_series"):
            self.original_alfa_series = {}

        # Создаем логарифмическую ось Y
        log_axis_y = QLogValueAxis()
        log_axis_y.setTitleText("Значение импульса (логарифмический масштаб)")
        log_axis_y.setBase(10.0)
        log_axis_y.setMinorTickCount(9)  # Увеличиваем количество делений для точности

        # Удаляем старую ось Y
        self.chart.removeAxis(self.axis_y)

        # Удаляем все текущие серии из графика
        for series in self.alfa_series_dict.values():
            self.chart.removeSeries(series)

        # Создаем новые логарифмические серии
        new_series_dict = {}
        global_max_y = float('-inf')

        # Минимальное значение для логарифма (ниже 1 не допускаем)
        min_y_threshold = 1.0

        # Обрабатываем данные для каждой серии
        for file_name, (original_series, color) in self.original_alfa_series.items():
            log_series = QLineSeries()
            log_series.setName(original_series.name())
            log_series.setColor(color)  # Сохраняем цвет оригинальной серии

            # Преобразуем данные для логарифмического масштаба
            for point in original_series.points():
                x, y = point.x(), point.y()
                # Устанавливаем минимальное значение y как 1 для корректного отображения
                y_log = max(y, min_y_threshold)
                log_series.append(x, y_log)
                global_max_y = max(global_max_y, y_log)

            new_series_dict[file_name] = log_series
            self.chart.addSeries(log_series)
            log_series.attachAxis(self.axis_x)

        # Устанавливаем диапазон логарифмической оси, начиная с 1
        log_axis_y.setRange(min_y_threshold, global_max_y * 1.5)  # Фиксируем минимум на 1

        # Добавляем новую ось и привязываем серии
        self.chart.addAxis(log_axis_y, Qt.AlignmentFlag.AlignLeft)
        for series in new_series_dict.values():
            series.attachAxis(log_axis_y)

        # Обновляем словари и текущую ось
        self.alfa_series_dict = new_series_dict
        self.axis_y = log_axis_y

        # Перерисовываем пики
        self.reapply_peaks()

    def apply_linear_scale(self):
        """Применяет линейный масштаб ко всем сериям Alfa."""
        if not hasattr(self, "original_alfa_series"):
            return

        # Создаем линейную ось Y
        linear_axis_y = QValueAxis()
        linear_axis_y.setTitleText("Значение импульса")

        # Удаляем старую ось Y
        self.chart.removeAxis(self.axis_y)

        # Удаляем все текущие серии
        for series in self.alfa_series_dict.values():
            self.chart.removeSeries(series)

        # Восстанавливаем оригинальные серии с их цветами
        self.alfa_series_dict = {}
        global_max_y = float('-inf')

        for file_name, (original_series, color) in self.original_alfa_series.items():
            original_series.setColor(color)  # Убеждаемся, что цвет сохранён
            self.alfa_series_dict[file_name] = original_series
            self.chart.addSeries(original_series)
            original_series.attachAxis(self.axis_x)
            y_values = [point.y() for point in original_series.points()]
            if y_values:
                global_max_y = max(global_max_y, max(y_values))

        # Устанавливаем диапазон линейной оси
        linear_axis_y.setRange(0, global_max_y * 1.1 if global_max_y > 0 else 1)
        self.chart.addAxis(linear_axis_y, Qt.AlignmentFlag.AlignLeft)
        for series in self.alfa_series_dict.values():
            series.attachAxis(linear_axis_y)

        # Обновляем текущую ось
        self.axis_y = linear_axis_y

        # Перерисовываем пики
        self.reapply_peaks()

    def apply_beta_log_scale(self):
        """Применяет логарифмический масштаб ко всем сериям Beta с началом оси Y от 1."""
        if not hasattr(self, "original_beta_series"):
            self.original_beta_series = {}

        # Создаем логарифмическую ось Y
        beta_log_axis_y = QLogValueAxis()
        beta_log_axis_y.setTitleText("Значение импульса (логарифмический масштаб)")
        beta_log_axis_y.setBase(10.0)
        beta_log_axis_y.setMinorTickCount(9)  # Увеличиваем количество делений для точности

        # Удаляем старую ось Y
        self.beta_chart.removeAxis(self.beta_axis_y)

        # Удаляем все текущие серии из графика
        for series in self.beta_series_dict.values():
            self.beta_chart.removeSeries(series)

        # Создаем новые логарифмические серии
        new_series_dict = {}
        global_max_y = float('-inf')

        # Минимальное значение для логарифма (ниже 1 не допускаем)
        min_y_threshold = 1.0

        # Обрабатываем данные для каждой серии
        for file_name, (original_series, color) in self.original_beta_series.items():
            log_series = QLineSeries()
            log_series.setName(original_series.name())
            log_series.setColor(color)  # Сохраняем цвет оригинальной серии

            # Преобразуем данные для логарифмического масштаба
            for point in original_series.points():
                x, y = point.x(), point.y()
                # Устанавливаем минимальное значение y как 1 для корректного отображения
                y_log = max(y, min_y_threshold)
                log_series.append(x, y_log)
                global_max_y = max(global_max_y, y_log)

            new_series_dict[file_name] = log_series
            self.beta_chart.addSeries(log_series)
            log_series.attachAxis(self.beta_axis_x)

        # Устанавливаем диапазон логарифмической оси, начиная с 1
        beta_log_axis_y.setRange(min_y_threshold, global_max_y * 1.5)  # Фиксируем минимум на 1

        # Добавляем новую ось и привязываем серии
        self.beta_chart.addAxis(beta_log_axis_y, Qt.AlignmentFlag.AlignLeft)
        for series in new_series_dict.values():
            series.attachAxis(beta_log_axis_y)

        # Обновляем словари и текущую ось
        self.beta_series_dict = new_series_dict
        self.beta_axis_y = beta_log_axis_y

    def apply_beta_linear_scale(self):
        """Применяет линейный масштаб ко всем сериям Beta."""
        if not hasattr(self, "original_beta_series"):
            return

        # Создаем линейную ось Y
        beta_linear_axis_y = QValueAxis()
        beta_linear_axis_y.setTitleText("Значение")

        # Удаляем старую ось Y
        self.beta_chart.removeAxis(self.beta_axis_y)

        # Удаляем все текущие серии
        for series in self.beta_series_dict.values():
            self.beta_chart.removeSeries(series)

        # Восстанавливаем оригинальные серии с их цветами
        self.beta_series_dict = {}
        global_max_y = float('-inf')

        for file_name, (original_series, color) in self.original_beta_series.items():
            original_series.setColor(color)  # Убеждаемся, что цвет сохранён
            self.beta_series_dict[file_name] = original_series
            self.beta_chart.addSeries(original_series)
            original_series.attachAxis(self.beta_axis_x)
            y_values = [point.y() for point in original_series.points()]
            if y_values:
                global_max_y = max(global_max_y, max(y_values))

        # Устанавливаем диапазон линейной оси
        beta_linear_axis_y.setRange(0, global_max_y * 1.1 if global_max_y > 0 else 1)
        self.beta_chart.addAxis(beta_linear_axis_y, Qt.AlignmentFlag.AlignLeft)
        for series in self.beta_series_dict.values():
            series.attachAxis(beta_linear_axis_y)

        # Обновляем текущую ось
        self.beta_axis_y = beta_linear_axis_y

    def reapply_peaks(self):
        """Перерисовывает пики после смены масштаба."""
        # Удаляем старые пики
        for peak_data in self.peak_points.values():
            if isinstance(peak_data, dict):
                for peak_series in peak_data.values():
                    if peak_series in self.chart.series():
                        self.chart.removeSeries(peak_series)
            elif peak_data in self.chart.series():
                self.chart.removeSeries(peak_data)

        # Переприменяем пики для всех серий
        self.peak_points.clear()
        for series in self.alfa_series_dict.values():
            highlight_am241_peak(self.chart, series, self.peak_points)
            highlight_rn_peaks(self.chart, series, self.peak_points, self)

    ##########################################################################
    # Методы для работы с экспортом данных и сообщениями
    ##########################################################################

    def export_to_excel(self):
        """Экспортирует данные спектра в Excel."""
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
        """Показывает информационное сообщение."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Информация")
        msg_box.setText(message)
        msg_box.exec()

    def show_warning_message(self, message):
        """Показывает предупреждение."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Предупреждение")
        msg_box.setText(message)
        msg_box.exec()

    def show_error_message(self, message):
        """Показывает сообщение об ошибке."""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Ошибка")
        msg_box.setText(message)
        msg_box.exec()

##########################################################################
# Основной блок запуска приложения
##########################################################################

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