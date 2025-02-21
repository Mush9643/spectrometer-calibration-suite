from PyQt6.QtCharts import QScatterSeries
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QToolTip


def highlight_am241_peak(chart, series, peak_points):
    """
    Проверяет имя графика и если оно содержит "Am241",
    отмечает самую верхнюю точку на графике.

    :param chart: QChart объект, содержащий график
    :param series: QLineSeries объект, представляющий загружаемый график
    :param peak_points: Словарь для хранения точек пиков
    """
    # Проверяем имя графика
    series_name = series.name()
    if "Am241" in series_name:
        # Находим максимальную точку
        points = series.points()
        if not points:
            return

        max_point = max(points, key=lambda point: point.y())

        # Создаем точку для отметки
        scatter_series = QScatterSeries()
        scatter_series.setName(f"{series_name} Peak")
        scatter_series.setMarkerSize(10)  # Размер точки
        scatter_series.append(max_point)

        # Добавляем точку на график
        chart.addSeries(scatter_series)
        scatter_series.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
        scatter_series.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])

        # Сохраняем точку в словаре
        peak_points[series_name] = scatter_series

        # Показываем всплывающую подсказку с координатой x
        show_tooltip(chart, max_point)


def highlight_rn_peaks(chart, series, peak_points):
    """
    Проверяет имя графика и если оно содержит "Rn",
    отмечает три ключевые точки на графике:
    1. Самая высокая точка.
    2. Вторая самая высокая точка на отрезке слева (на 150 единиц).
    3. Третья самая высокая точка на отрезке справа (на 40 единиц).

    :param chart: QChart объект, содержащий график
    :param series: QLineSeries объект, представляющий загружаемый график
    :param peak_points: Словарь для хранения точек пиков
    """
    # Проверяем имя графика
    series_name = series.name()
    if "Rn" not in series_name:
        return  # Если имя не содержит "Rn", выходим

    # Находим все точки графика
    points = series.points()
    if not points:
        return

    # 1. Находим самую высокую точку
    max_point = max(points, key=lambda point: point.y())
    max_x, max_y = max_point.x(), max_point.y()

    # 2. Находим вторую самую высокую точку на отрезке слева (на 150 единиц)
    left_points = [point for point in points if point.x() < max_x - 150]
    second_max_point = max(left_points, key=lambda point: point.y()) if left_points else None

    # 3. Находим третью самую высокую точку на отрезке справа (на 40 единиц)
    right_points = [point for point in points if point.x() > max_x + 40]
    third_max_point = max(right_points, key=lambda point: point.y()) if right_points else None

    # Создаем маркеры для точек
    def create_scatter_series(point, name_suffix):
        scatter_series = QScatterSeries()
        scatter_series.setName(f"{series_name} {name_suffix}")
        scatter_series.setMarkerSize(10)  # Размер точки
        scatter_series.append(point)
        return scatter_series

    # Добавляем первую точку
    first_peak = create_scatter_series(max_point, "First Peak")
    chart.addSeries(first_peak)
    first_peak.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
    first_peak.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])

    # Добавляем вторую точку
    if second_max_point:
        second_peak = create_scatter_series(second_max_point, "Second Peak")
        chart.addSeries(second_peak)
        second_peak.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
        second_peak.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])

    # Добавляем третью точку
    if third_max_point:
        third_peak = create_scatter_series(third_max_point, "Third Peak")
        chart.addSeries(third_peak)
        third_peak.attachAxis(chart.axes(Qt.Orientation.Horizontal)[0])
        third_peak.attachAxis(chart.axes(Qt.Orientation.Vertical)[0])

    # Сохраняем точки в словаре
    peak_points[series_name] = {
        "first": first_peak,
        "second": second_peak if second_max_point else None,
        "third": third_peak if third_max_point else None
    }

    # Показываем всплывающие подсказки с координатами x
    show_tooltip(chart, max_point)
    if second_max_point:
        show_tooltip(chart, second_max_point)
    if third_max_point:
        show_tooltip(chart, third_max_point)


def show_tooltip(chart, point):
    """
    Показывает всплывающую подсказку с координатой x точки.

    :param chart: QChart объект, содержащий график
    :param point: QPointF объект, представляющий точку
    """
    # Получаем координаты точки
    x, y = point.x(), point.y()

    # Отладочный вывод
    print(f"Отображение подсказки для точки: x={x}, y={y}")

    # Преобразуем координаты в пиксели относительно виджета графика
    chart_view = chart.parent()  # Получаем родительский виджет (QChartView)
    if not chart_view:
        print("Ошибка: QChart не имеет родительского виджета!")
        return

    # Преобразуем координаты точки в координаты сцены
    scene_pos = chart.mapToScene(point)
    # Преобразуем координаты сцены в координаты виджета
    view_pos = chart_view.mapFromScene(scene_pos)
    # Преобразуем координаты виджета в глобальные координаты
    global_pos = chart_view.mapToGlobal(view_pos.toPoint())

    # Показываем всплывающую подсказку с задержкой
    QTimer.singleShot(100, lambda: QToolTip.showText(global_pos, f"x = {x:.2f}", chart_view))