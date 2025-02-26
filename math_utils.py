import numpy as np
from PyQt6.QtCharts import QScatterSeries, QLineSeries, QChart, QValueAxis, QChartView
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget, QDialog, QLabel, QLineEdit, QFormLayout
from PyQt6.QtCore import Qt, QPointF

# Константы Era226
Era226 = [6002.35, 7686.82, 8784.86]


def calculate_linear_regression(x, y):
    """
    Вычисляет коэффициенты линейной регрессии (a, b) методом наименьших квадратов.

    :param x: Список значений независимой переменной (координаты x пиков)
    :param y: Список значений зависимой переменной (Era226)
    :return: Кортеж (a, b) — пересечение с осью Y и наклон прямой
    """
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi * xi for xi in x)

    # Расчёт наклона b
    b = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    # Расчёт пересечения с осью Y (a)
    a = (sum_y - b * sum_x) / n

    return a, b


def highlight_am241_peak(chart, series, peak_points):
    """
    Отмечает пик Am241 на графике.

    :param chart: QChart объект, содержащий график
    :param series: QLineSeries объект, представляющий загружаемый график
    :param peak_points: Словарь для хранения точек пиков
    """
    series_name = series.name()
    if "Am241" in series_name:
        points = series.points()
        if not points:
            return

        max_point = max(points, key=lambda point: point.y())

        scatter_series = QScatterSeries()
        scatter_series.setName(f"{series_name} Peak")
        scatter_series.setMarkerSize(10)
        scatter_series.append(max_point)

        chart.addSeries(scatter_series)
        scatter_series.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
        scatter_series.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])

        peak_points[series_name] = scatter_series

        print(f"Пик Am241: x={max_point.x()}, y={max_point.y()}")


def highlight_rn_peaks(chart, series, peak_points):
    """
    Отмечает три ключевые точки на графике Rn и вычисляет коэффициенты аппроксимации.

    :param chart: QChart объект, содержащий график
    :param series: QLineSeries объект, представляющий загружаемый график
    :param peak_points: Словарь для хранения точек пиков
    """
    series_name = series.name()
    if "Rn" not in series_name:
        return

    points = series.points()
    if not points:
        return

    max_point = max(points, key=lambda point: point.y())
    max_x, max_y = max_point.x(), max_point.y()

    left_points = [point for point in points if point.x() < max_x - 150]
    second_max_point = max(left_points, key=lambda point: point.y()) if left_points else None

    right_points = [point for point in points if point.x() > max_x + 40]
    third_max_point = max(right_points, key=lambda point: point.y()) if right_points else None

    def create_scatter_series(point, name_suffix):
        scatter_series = QScatterSeries()
        scatter_series.setName(f"{series_name} {name_suffix}")
        scatter_series.setMarkerSize(10)
        scatter_series.append(point)
        return scatter_series

    # Создание серий для пиков
    first_peak = create_scatter_series(max_point, "First Peak")
    chart.addSeries(first_peak)
    first_peak.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
    first_peak.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])

    second_peak = None
    third_peak = None

    if second_max_point:
        second_peak = create_scatter_series(second_max_point, "Second Peak")
        chart.addSeries(second_peak)
        second_peak.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
        second_peak.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])

    if third_max_point:
        third_peak = create_scatter_series(third_max_point, "Third Peak")
        chart.addSeries(third_peak)
        third_peak.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
        third_peak.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])

    # Сохранение пиков в словаре
    peak_points[series_name] = {
        "first": first_peak,
        "second": second_peak,
        "third": third_peak
    }

    # Вывод информации о пиках
    print(f"Первый пик Rn: x={max_x}, y={max_y}")
    if second_max_point:
        print(f"Второй пик Rn: x={second_max_point.x()}, y={second_max_point.y()}")
    if third_max_point:
        print(f"Третий пик Rn: x={third_max_point.x()}, y={third_max_point.y()}")

    # Расчёт коэффициентов линейной регрессии на основе координат x пиков и значений Era226
    x_values = []
    if max_point:
        x_values.append(max_x)
    if second_max_point:
        x_values.append(second_max_point.x())
    if third_max_point:
        x_values.append(third_max_point.x())

    # Используем Era226 как значения y, предполагая, что они соответствуют пикам по порядку
    if len(x_values) == len(Era226):  # Проверяем, что количество пиков совпадает с количеством значений Era226
        a, b = calculate_linear_regression(x_values, Era226)
        print(f"Коэффициенты линейной регрессии для пиков Rn: a = {a:.3f} b {b:.3f}x")
        print(f"Enewa = {a + b * 1023:.3f}")
    else:
        print("Количество пиков не совпадает с количеством значений Era226 для расчёта регрессии.")


class CalibrationDialog(QDialog):
    """
    Диалоговое окно для калибровки с отображением графика F(t).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Калибровка")
        self.setFixedSize(600, 400)  # Увеличиваем размер для графика

        # Получаем коэффициенты a и b из родительского окна (SpectrumWindow)
        self.parent_window = parent
        self.a, self.b = self.get_calibration_coefficients()

        # Создаем layout для диалога
        layout = QVBoxLayout()

        # Создаем график
        self.calibration_chart = QChart()
        self.calibration_chart.setTitle("График F(t) = a + b * t")

        # Создаем серию для F(t)
        f_series = QLineSeries()
        f_series.setName("F(t)")
        t_range = np.linspace(400, 900, 100)  # Диапазон t от 400 до 900
        for t in t_range:
            f_t = self.a + self.b * t  # Формула F(t) = a + b * t
            f_series.append(QPointF(t, f_t))

        # Добавляем серию на график
        self.calibration_chart.addSeries(f_series)

        # Настраиваем оси
        axis_x = QValueAxis()
        axis_x.setTitleText("t")
        axis_x.setRange(400, 900)
        axis_x.setTickCount(6)  # Устанавливаем количество делений (5 интервалов + начало)

        axis_y = QValueAxis()
        axis_y.setTitleText("F(t)")
        # Устанавливаем диапазон оси Y на основе значений F(t)
        y_values = [self.a + self.b * t for t in t_range]
        axis_y.setRange(min(y_values), max(y_values))

        self.calibration_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        self.calibration_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        f_series.attachAxis(axis_x)
        f_series.attachAxis(axis_y)

        # Создаем виджет для отображения графика
        chart_view = QChartView(self.calibration_chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Добавляем график в layout
        layout.addWidget(chart_view)

        # Устанавливаем layout для диалога
        self.setLayout(layout)

    def get_calibration_coefficients(self):
        """
        Получает коэффициенты a и b из родительского окна (SpectrumWindow),
        вычисленные в highlight_rn_peaks.
        """
        # Здесь предполагается, что коэффициенты a и b хранятся в родительском окне
        # или были вычислены в highlight_rn_peaks и доступны через атрибуты
        if hasattr(self.parent_window, 'calibration_coefficients'):
            return self.parent_window.calibration_coefficients
        else:
            # Если коэффициенты не сохранены, вычисляем их заново (упрощённый подход)
            x_values = []
            for series_name, peaks in self.parent_window.peak_points.items():
                if "Rn" in series_name:
                    if peaks.get("first"):
                        x_values.append(peaks["first"].points()[0].x())
                    if peaks.get("second"):
                        x_values.append(peaks["second"].points()[0].x())
                    if peaks.get("third"):
                        x_values.append(peaks["third"].points()[0].x())

            if len(x_values) == len(Era226):
                a, b = calculate_linear_regression(x_values, Era226)
                return a, b
            return 0.0, 0.0  # Значения по умолчанию, если данные отсутствуют


def add_calibration_button(window):
    """
    Добавляет кнопку "Калибровка" на вкладку "Alfa chart" и связывает её с диалоговым окном.

    :param window: Экземпляр класса SpectrumWindow
    """
    # Создаём кнопку
    calibration_button = QPushButton("Калибровка")
    calibration_button.clicked.connect(lambda: CalibrationDialog(window).exec())

    # Получаем layout вкладки "Alfa chart"
    layout = window.tab1.layout()
    if isinstance(layout, QVBoxLayout):
        # Если layout существует, добавляем кнопку в конец
        layout.addWidget(calibration_button)
    else:
        # Если layout ещё не создан, создаём его
        new_layout = QVBoxLayout()
        if hasattr(window, 'chart_view'):
            new_layout.addWidget(window.chart_view)
        else:
            print("Предупреждение: chart_view не найден. Используем только кнопку.")
        if hasattr(window, 'log_checkbox'):
            new_layout.addWidget(window.log_checkbox)
        new_layout.addWidget(calibration_button)
        window.tab1.setLayout(new_layout)