import numpy as np
from PyQt6.QtCharts import QScatterSeries
from PyQt6.QtCore import Qt

# Константы Era226
Era226_1, Era226_2, Era226_3 = 6002.35, 7686.82, 8784.86

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

    first_peak = create_scatter_series(max_point, "First Peak")
    chart.addSeries(first_peak)
    first_peak.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
    first_peak.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])

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

    peak_points[series_name] = {
        "first": first_peak,
        "second": second_peak if second_max_point else None,
        "third": third_peak if third_max_point else None
    }

    print(f"Первый пик Rn: x={max_x}, y={max_y}")
    if second_max_point:
        print(f"Второй пик Rn: x={second_max_point.x()}, y={second_max_point.y()}")
    if third_max_point:
        print(f"Третий пик Rn: x={third_max_point.x()}, y={third_max_point.y()}")

    # Вычисление коэффициентов аппроксимации
    if second_max_point and third_max_point:
        Rbntu = [max_x, second_max_point.x(), third_max_point.x()]
        Era226 = [Era226_1, Era226_2, Era226_3]

        coeffs = np.polyfit(Rbntu, Era226, 2)
        a, b, c = coeffs

        print(f"Коэффициенты аппроксимации: a={a}, b={b}, c={c}")
