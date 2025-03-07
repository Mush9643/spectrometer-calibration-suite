import numpy as np
from PyQt6.QtCharts import QScatterSeries, QLineSeries, QChart, QValueAxis, QChartView
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget, QDialog, QLabel, QLineEdit, QFormLayout
from PyQt6.QtCore import Qt, QPointF

# Константы
ERA226 = [7686.82, 6002.35, 8784.86]  # Значения энергии для пиков Rn
P90 = [2700, 4385.6, 5687.5, 6192.35, 6337.7, 8044.6]  # Значения энергии для P90

def print_alfa_data_arrays(parent_window):
    """Выводит в консоль данные второй строки всех сохранённых массивов Alfa."""
    if not hasattr(parent_window, 'alfa_data_arrays') or not parent_window.alfa_data_arrays:
        print("Нет сохранённых данных Alfa для вывода.")
        return

    print("\n=== Сохранённые данные Alfa (вторая строка) ===")
    print("Файл              | Канал | Кол-во импульсов")
    print("---------------------------------------------")
    for file_name, data in parent_window.alfa_data_arrays.items():
        channel, impulses = data  # Распаковываем список
        print(f"{file_name:17s} | {channel:5d} | {impulses}")
    print("=============================================\n")

def calculate_linear_regression(x, y):
    """Вычисляет коэффициенты линейной регрессии методом наименьших квадратов."""
    n = len(x)
    if n == 0 or len(y) != n:
        return 0.0, 0.0

    sum_x, sum_y = sum(x), sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi * xi for xi in x)

    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    intercept = (sum_y - slope * sum_x) / n
    return intercept, slope

def highlight_am241_peak(chart, series, peak_points):
    """Отмечает пик Am241 на графике как точку максимального значения."""
    if "Am241" not in series.name():
        return

    points = series.points()
    if not points:
        return

    max_point = max(points, key=lambda p: p.y())
    scatter_series = QScatterSeries()
    scatter_series.setName(f"{series.name()} Peak")
    scatter_series.setMarkerSize(10)
    scatter_series.append(max_point)
    chart.addSeries(scatter_series)
    scatter_series.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
    scatter_series.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])
    peak_points[series.name()] = scatter_series
    print(f"Пик Am241: x={max_point.x()}, y={max_point.y()}")

def highlight_rn_peaks(chart, series, peak_points, parent_window=None):
    """Отмечает три пика Rn, вычисляет линейную регрессию, сохраняет коэффициенты и вычисляет ra, am_rate и k1p9."""
    if "Rn" not in series.name():
        return

    points = series.points()
    if not points:
        return

    # Поиск трёх пиков
    max_point = max(points, key=lambda p: p.y())
    max_x, max_y = max_point.x(), max_point.y()

    left_points = [p for p in points if p.x() < max_x - 150]
    second_peak = max(left_points, key=lambda p: p.y()) if left_points else None

    right_points = [p for p in points if p.x() > max_x + 40]
    third_peak = max(right_points, key=lambda p: p.y()) if right_points else None

    def add_peak_series(point, name_suffix):
        scatter = QScatterSeries()
        scatter.setName(f"{series.name()} {name_suffix}")
        scatter.setMarkerSize(10)
        scatter.append(point)
        chart.addSeries(scatter)
        scatter.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
        scatter.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])
        return scatter

    peaks = {"first": add_peak_series(max_point, "First Peak")}
    if second_peak:
        peaks["second"] = add_peak_series(second_peak, "Second Peak")
    if third_peak:
        peaks["third"] = add_peak_series(third_peak, "Third Peak")

    peak_points[series.name()] = peaks

    # Логи пиков
    print(f"Первый пик Rn: x={max_x}, y={max_y}")
    if second_peak:
        print(f"Второй пик Rn: x={second_peak.x()}, y={second_peak.y()}")
    if third_peak:
        print(f"Третий пик Rn: x={third_peak.x()}, y={third_peak.y()}")

    # Расчет регрессии
    x_values = [peak.points()[0].x() for peak in peaks.values() if peak]
    if len(x_values) > 0:
        y_values = ERA226[:len(x_values)]  # Используем только соответствующее количество значений
        intercept, slope = calculate_linear_regression(x_values, y_values)
        print(f"Коэффициенты: intercept={intercept:.3f}, slope={slope:.3f}")
        print(f"Enewa = {intercept + slope * 1023:.3f}")
        for e in P90:
            p_value = round((e - intercept) / slope)
            print(f"P({e}) = {p_value}")
            if e == 2700 and parent_window is not None:
                parent_window.beta_p2700 = p_value  # Сохраняем P(2700) для бета-канала

        # Сохраняем коэффициенты в parent_window
        if parent_window is not None:
            if hasattr(parent_window, 'calibration_coefficients'):
                parent_window.calibration_coefficients = (intercept, slope)
            else:
                parent_window.calibration_coefficients = (intercept, slope)
                print("Создан новый атрибут calibration_coefficients в родительском окне.")
        else:
            parent = chart.parent()
            if parent is not None and hasattr(parent, '__dict__'):
                if hasattr(parent, 'calibration_coefficients'):
                    parent.calibration_coefficients = (intercept, slope)
                else:
                    parent.calibration_coefficients = (intercept, slope)
                    print("Создан новый атрибут calibration_coefficients в родительском окне через chart.parent().")
            else:
                print("Предупреждение: Не удалось найти родительский объект для сохранения calibration_coefficients.")

        # Вызываем calculate_ra, calculate_am_rate и calculate_k1p9
        if parent_window:
            calculate_ra(parent_window)
            calculate_am_rate(parent_window)
            calculate_k1p9(parent_window)
    else:
        print("Предупреждение: Недостаточно пиков Rn для расчета регрессии.")

def calculate_ra(parent_window):
    """Вычисляет ra как отношение суммы Rn_i в диапазоне от ch0 до ch2-1 к сумме Rn_i в диапазоне от ch2 до ch3-1."""
    if not hasattr(parent_window, 'alfa_series_dict') or not parent_window.alfa_series_dict:
        print("Ошибка: Нет данных для вычисления ra.")
        return

    if not hasattr(parent_window, 'calibration_coefficients'):
        print("Ошибка: Коэффициенты калибровки отсутствуют.")
        return

    # Получаем коэффициенты регрессии a (intercept) и b (slope)
    intercept, slope = parent_window.calibration_coefficients

    # Получаем значения каналов (ch) для P90
    P90 = [2700, 4385.6, 5687.5, 6192.35, 6337.7, 8044.6]  # Как в вашем коде
    ch_values = [round((e - intercept) / slope) for e in P90]

    # Проверяем, что есть достаточно значений ch (нужны ch0, ch2, ch3)
    if len(ch_values) < 4:
        print("Ошибка: Недостаточно значений каналов для вычисления ra (требуется минимум 4 значения).")
        return

    # Используем ch0, ch2, ch3 из ch_values
    ch0 = ch_values[0]  # Начальный канал для числителя
    ch2 = ch_values[2]  # Конечный канал для числителя (ch2-1) и начальный для знаменателя
    ch3 = ch_values[3]  # Конечный канал для знаменателя (ch3-1)

    # Проверяем, что каналы в правильном порядке
    if ch0 >= ch2 or ch2 >= ch3:
        print("Ошибка: Каналы должны быть в порядке ch0 < ch2 < ch3.")
        return

    # Проходим только по сериям, чьи имена содержат 'Rn'
    numerator_sum = 0
    denominator_sum = 0
    found_rn_series = False

    for series_name, series in parent_window.alfa_series_dict.items():
        if "Rn" in series_name:
            found_rn_series = True
            points = series.points()

            # Собираем все y-значения (Rn_i) для числителя (ch0 до ch2-1)
            rn_numerator_values = []
            for point in points:
                x, y = point.x(), point.y()
                if ch0 <= x < ch2:  # Проверяем диапазон [ch0, ch2-1]
                    rn_numerator_values.append(y)

            # Собираем все y-значения (Rn_i) для знаменателя (ch2 до ch3-1)
            rn_denominator_values = []
            for point in points:
                x, y = point.x(), point.y()
                if ch2 <= x < ch3:  # Проверяем диапазон [ch2, ch3-1]
                    rn_denominator_values.append(y)

            if rn_numerator_values:
                numerator_sum += np.sum(rn_numerator_values)
                print(f"Сумма Rn_i для числителя серии {series_name} в диапазоне от {ch0} до {ch2 - 1}: {np.sum(rn_numerator_values)}")
            else:
                print(f"Не найдено точек в диапазоне от {ch0} до {ch2 - 1} для серии {series_name}.")

            if rn_denominator_values:
                denominator_sum += np.sum(rn_denominator_values)
                print(f"Сумма Rn_i для знаменателя серии {series_name} в диапазоне от {ch2} до {ch3 - 1}: {np.sum(rn_denominator_values)}")
            else:
                print(f"Не найдено точек в диапазоне от {ch2} до {ch3 - 1} для серии {series_name}.")

    if found_rn_series:
        if denominator_sum == 0:
            print("Ошибка: Знаменатель ra равен 0, вычисление невозможно.")
            return

        # Вычисляем ra
        ra = numerator_sum / denominator_sum
        print(f"\nЗначение ra: {ra:.3f}")
        # Сохраняем ra в parent_window для дальнейшего использования, если нужно
        if hasattr(parent_window, 'ra_value'):
            parent_window.ra_value = ra
        else:
            parent_window.ra_value = ra
            print("Создан новый атрибут ra_value в родительском окне.")
    else:
        print("Предупреждение: Не найдено серий с 'Rn' в имени.")

def calculate_am_rate(parent_window):
    """Вычисляет am_rate как отношение суммы M2_i в диапазоне от ch0 до ceil(ch2)-1 к M_0 из второй строки файла Am241."""
    if not hasattr(parent_window, 'alfa_data_arrays') or not parent_window.alfa_data_arrays:
        print("Ошибка: Нет данных в alfa_data_arrays для вычисления am_rate.")
        return

    if not hasattr(parent_window, 'alfa_series_dict') or not parent_window.alfa_series_dict:
        print("Ошибка: Нет данных в alfa_series_dict для вычисления am_rate.")
        return

    if not hasattr(parent_window, 'calibration_coefficients'):
        print("Ошибка: Коэффициенты калибровки отсутствуют.")
        return

    # Получаем коэффициенты регрессии
    intercept, slope = parent_window.calibration_coefficients

     # Как в вашем коде
    ch_values = [round((e - intercept) / slope) for e in P90]

    # Проверяем, что есть достаточно значений ch (нужны ch0, ch2)
    if len(ch_values) < 3:
        print("Ошибка: Недостаточно значений каналов для вычисления am_rate (требуется минимум 3 значения).")
        return

    # Используем ch0 и ch2 из ch_values
    ch0 = ch_values[0]  # Начальный канал для числителя
    ch2 = ch_values[2]  # Конечный канал для числителя (до ceil(ch2)-1)

    # Вычисляем ceil(ch2) - 1
    ch2_ceil = int(np.ceil(ch2)) - 1

    # Проверяем, что каналы в правильном порядке
    if ch0 >= ch2_ceil:
        print("Ошибка: Каналы должны быть в порядке ch0 < ceil(ch2)-1.")
        return

    # Числитель: суммируем M2_i (импульсы из графиков с "Am241")
    numerator_sum = 0
    found_am241_series = False

    for series_name, series in parent_window.alfa_series_dict.items():
        if "Am241" in series_name:
            found_am241_series = True
            points = series.points()
            points_dict = {p.x(): p.y() for p in points}  # Оптимизация доступа к точкам
            numerator_sum += sum(y for x, y in points_dict.items() if ch0 <= x <= ch2_ceil)
            print(f"Сумма M2_i для серии {series_name} в диапазоне от {ch0} до {ch2_ceil}: {numerator_sum}")

    if not found_am241_series:
        print("Предупреждение: Не найдено серий с 'Am241' в имени.")
        return

    # Знаменатель: M_0 из второй строки файла с "Am241" в alfa_data_arrays
    denominator_m0 = 0
    found_am241_file = False

    for file_name, data in parent_window.alfa_data_arrays.items():
        if "Am241" in file_name:
            found_am241_file = True
            _, impulses = data  # Извлекаем Кол-во импульсов из второй строки
            denominator_m0 = impulses
            print(f"M_0 из файла {file_name} (вторая строка): {denominator_m0}")
            break  # Берем первое совпадение, если несколько файлов

    if not found_am241_file:
        print("Предупреждение: Не найдено файлов с 'Am241' в имени в alfa_data_arrays.")
        return

    if denominator_m0 == 0:
        print("Ошибка: Знаменатель M_0 равен 0, вычисление невозможно.")
        return

    # Вычисляем am_rate
    am_rate = numerator_sum / denominator_m0
    print(f"\nЗначение am_rate: {am_rate:.3f}")

    # Сохраняем am_rate в parent_window для дальнейшего использования
    if hasattr(parent_window, 'am_rate_value'):
        parent_window.am_rate_value = am_rate
    else:
        parent_window.am_rate_value = am_rate
        print("Создан новый атрибут am_rate_value в родительском окне.")

def calculate_k1p9(parent_window):
    """Вычисляет k1p9 как (am_rate / 852)^(-1)."""
    if not hasattr(parent_window, 'am_rate_value'):
        print("Ошибка: Значение am_rate отсутствует для вычисления k1p9.")
        return

    am_rate = parent_window.am_rate_value
    if am_rate == 0:
        print("Ошибка: am_rate равен 0, вычисление k1p9 невозможно.")
        return

    k1p9 = (am_rate / 852) ** (-1)
    print(f"Значение k1p9: {k1p9:.3f}")

    # Сохраняем k1p9 в parent_window для дальнейшего использования
    if hasattr(parent_window, 'k1p9_value'):
        parent_window.k1p9_value = k1p9
    else:
        parent_window.k1p9_value = k1p9
        print("Создан новый атрибут k1p9_value в родительском окне.")

class CalibrationDialog(QDialog):
    """Диалоговое окно калибровки с графиком F(t) и точками пиков."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Калибровка")
        self.setFixedSize(600, 500)
        self.parent_window = parent

        # Выводим данные массивов и значения ra/am_rate
        print_alfa_data_arrays(self.parent_window)

        layout = QVBoxLayout()

        # Получение данных
        self.intercept, self.slope = self.get_calibration_coefficients()
        self.x_values, self.y_values = self.get_peak_coordinates()
        self.am241_x = self.get_am241_x()

        # График
        chart = QChart()
        chart.setTitle("F(t) = a + b * t с точками калибровки")

        # Линия F(t)
        f_series = QLineSeries()
        f_series.setName(f"F(t) = {self.intercept:.2f} + {self.slope:.2f}t")
        t_range = np.linspace(400, 900, 100)
        for t in t_range:
            f_series.append(t, self.intercept + self.slope * t)
        chart.addSeries(f_series)

        # Точки Rn
        rn_series = QScatterSeries()
        rn_series.setName("Rn (Era226)")
        rn_series.setMarkerSize(10)
        rn_series.setColor(QColor(0, 255, 0))
        for x, y in zip(self.x_values, self.y_values):
            rn_series.append(x, y)
        chart.addSeries(rn_series)

        # Точка Am241
        if self.am241_x is not None:
            am241_series = QScatterSeries()
            am241_series.setName("Am241 (5485.56)")
            am241_series.setMarkerSize(10)
            am241_series.setColor(QColor(128, 0, 128))
            am241_series.append(self.am241_x, 5485.56)
            chart.addSeries(am241_series)
            if self.am241_x < 400 or self.am241_x > 900:
                print(f"Предупреждение: Точка Am241 (x={self.am241_x}) вне диапазона 400–900")
        else:
            print("Ошибка: Координата x для Am241 не найдена")

        # Оси
        axis_x = QValueAxis()
        axis_x.setTitleText("t (каналы)")
        axis_x.setRange(400, 900)

        axis_y = QValueAxis()
        axis_y.setTitleText("Энергия (кэВ)")
        all_y = [self.intercept + self.slope * t for t in t_range] + self.y_values
        if self.am241_x is not None:
            all_y.append(5485.56)
        axis_y.setRange(min(all_y) * 0.9, max(all_y) * 1.1)

        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        f_series.attachAxis(axis_x)
        f_series.attachAxis(axis_y)
        rn_series.attachAxis(axis_x)
        rn_series.attachAxis(axis_y)
        if self.am241_x is not None:
            am241_series.attachAxis(axis_x)
            am241_series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(chart_view)

        # Информационная панель
        info_layout = QFormLayout()
        info_layout.addRow("Intercept (a):", QLabel(f"{self.intercept:.2f}"))
        info_layout.addRow("Slope (b):", QLabel(f"{self.slope:.2f}"))
        info_layout.addRow("Enewa (t=1023):", QLabel(f"{self.intercept + self.slope * 1023:.2f}"))
        if self.am241_x is not None:
            info_layout.addRow("Am241 x:", QLabel(f"{self.am241_x:.2f}"))
        else:
            info_layout.addRow("Am241 x:", QLabel("Не найден"))

        # Добавляем ra и am_rate, если они существуют
        if hasattr(self.parent_window, 'ra_value'):
            info_layout.addRow("ra:", QLabel(f"{self.parent_window.ra_value:.3f}"))
        if hasattr(self.parent_window, 'am_rate_value'):
            info_layout.addRow("am_rate:", QLabel(f"{self.parent_window.am_rate_value:.3f}"))
        if hasattr(self.parent_window, 'k1p9_value'):
            info_layout.addRow("k1p9:", QLabel(f"{self.parent_window.k1p9_value:.3f}"))

        layout.addLayout(info_layout)

        # Вычисляем и выводим ra и am_rate
        calculate_ra(self.parent_window)
        calculate_am_rate(self.parent_window)
        calculate_k1p9(self.parent_window)

        self.setLayout(layout)

    def get_calibration_coefficients(self):
        """Получает или вычисляет коэффициенты регрессии."""
        if hasattr(self.parent_window, 'calibration_coefficients'):
            return self.parent_window.calibration_coefficients
        x_values, _ = self.get_peak_coordinates()
        if x_values:
            return calculate_linear_regression(x_values, ERA226[:len(x_values)])
        return 0.0, 0.0

    def get_peak_coordinates(self):
        """Извлекает координаты пиков Rn и соответствующие значения Era226."""
        x_values = []
        for series_name, peaks in self.parent_window.peak_points.items():
            if "Rn" in series_name:
                for peak_name in ["first", "second", "third"]:
                    if peak := peaks.get(peak_name):
                        x_values.append(peak.points()[0].x())
        return x_values, ERA226[:len(x_values)]

    def get_am241_x(self):
        """Получает координату x пика Am241."""
        for series_name, peak in self.parent_window.peak_points.items():
            if "Am241" in series_name and peak:
                return peak.points()[0].x()
        return None

def add_calibration_button(window):
    """Добавляет кнопку калибровки на вкладку Alfa chart."""
    button = QPushButton("Калибровка")
    button.clicked.connect(lambda: CalibrationDialog(window).exec())
    if layout := window.tab1.layout():
        layout.addWidget(button)
    else:
        layout = QVBoxLayout()
        layout.addWidget(window.chart_view if hasattr(window, 'chart_view') else QWidget())
        layout.addWidget(window.log_checkbox if hasattr(window, 'log_checkbox') else QWidget())
        layout.addWidget(button)
        window.tab1.setLayout(layout)