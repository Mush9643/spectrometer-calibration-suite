from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QDialog, QDialogButtonBox, QCheckBox, QFormLayout, QLabel
from PyQt6.QtCharts import QChart, QChartView, QValueAxis, QLineSeries, QLogValueAxis
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt, QPointF


def add_beta_calibration_button(parent):
    """
    Добавляет кнопку 'Калибровка' на вкладку Beta chart и управляет её состоянием.

    Args:
        parent: Экземпляр SpectrumWindow, к которому добавляется кнопка.
    """
    calibration_button = QPushButton("Калибровка")
    calibration_button.clicked.connect(lambda: show_calibration_dialog(parent))
    calibration_button.setEnabled(False)
    parent.beta_calibration_button = calibration_button

    beta_layout = parent.tab2.layout()
    if beta_layout is None:
        beta_layout = QVBoxLayout()
        parent.tab2.setLayout(beta_layout)
    if isinstance(beta_layout, QVBoxLayout):
        beta_layout.addWidget(calibration_button)
    else:
        raise ValueError("Layout вкладки Beta не является QVBoxLayout")

    update_calibration_button_state(parent)

def update_calibration_button_state(parent):
    """
    Проверяет наличие графиков с "Am241" и "SrY90" в именах и обновляет состояние кнопки.

    Args:
        parent: Экземпляр SpectrumWindow.
    """
    if not hasattr(parent, 'beta_calibration_button'):
        return

    series_names = [series.name() for series in parent.beta_series_dict.values()]
    has_am241 = any("Am241" in name for name in series_names)
    has_sry90 = any("SrY90" in name for name in series_names)

    parent.beta_calibration_button.setEnabled(has_am241 and has_sry90)
    if not has_am241 and not has_sry90:
        parent.beta_calibration_button.setToolTip("Требуются графики Am241 и SrY90")
    elif not has_am241:
        parent.beta_calibration_button.setToolTip("Требуется график Am241")
    elif not has_sry90:
        parent.beta_calibration_button.setToolTip("Требуется график SrY90")
    else:
        parent.beta_calibration_button.setToolTip("Готово к калибровке")

def add_beta_calibration_button(parent):
    """
    Добавляет кнопку 'Калибровка' на вкладку Beta chart и управляет её состоянием.

    Args:
        parent: Экземпляр SpectrumWindow, к которому добавляется кнопка.
    """
    calibration_button = QPushButton("Калибровка")
    calibration_button.clicked.connect(lambda: show_calibration_dialog(parent))
    calibration_button.setEnabled(False)
    parent.beta_calibration_button = calibration_button

    beta_layout = parent.tab2.layout()
    if beta_layout is None:
        beta_layout = QVBoxLayout()
        parent.tab2.setLayout(beta_layout)
    if isinstance(beta_layout, QVBoxLayout):
        beta_layout.addWidget(calibration_button)
    else:
        raise ValueError("Layout вкладки Beta не является QVBoxLayout")

    update_calibration_button_state(parent)

def update_calibration_button_state(parent):
    """
    Проверяет наличие графиков с "Am241" и "SrY90" в именах и обновляет состояние кнопки.

    Args:
        parent: Экземпляр SpectrumWindow.
    """
    if not hasattr(parent, 'beta_calibration_button'):
        return

    series_names = [series.name() for series in parent.beta_series_dict.values()]
    has_am241 = any("Am241" in name for name in series_names)
    has_sry90 = any("SrY90" in name for name in series_names)

    parent.beta_calibration_button.setEnabled(has_am241 and has_sry90)
    if not has_am241 and not has_sry90:
        parent.beta_calibration_button.setToolTip("Требуются графики Am241 и SrY90")
    elif not has_am241:
        parent.beta_calibration_button.setToolTip("Требуется график Am241")
    elif not has_sry90:
        parent.beta_calibration_button.setToolTip("Требуется график SrY90")
    else:
        parent.beta_calibration_button.setToolTip("Готово к калибровке")

def show_calibration_dialog(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Калибровка Beta")
    dialog.resize(600, 400)

    calibration_chart = QChart()
    calibration_chart.setTitle("График калибровки Beta (Am241 и SrY90, нормализованный)")

    max_y_value = 1
    for file_name, series in parent.beta_series_dict.items():
        if "Am241" in series.name() or "SrY90" in series.name():
            calibration_series = QLineSeries()
            calibration_series.setName(series.name())
            normalization_value = parent.first_impulse_values.get(file_name, 1.0)
            if normalization_value == 0:
                normalization_value = 1.0
            print(f"Нормализация для {file_name}: пока не делим на {normalization_value}")
            for point in series.points():
                if point.x() <= 500:
                    normalized_y = point.y()
                    normalized_y = max(normalized_y, 1.0)
                    calibration_series.append(point.x(), normalized_y)
                    max_y_value = max(max_y_value, normalized_y)
            calibration_chart.addSeries(calibration_series)

    # Отрисовка красных прямых только если beta_p2700 определён
    p2700 = getattr(parent, 'beta_p2700', None)
    if p2700 is not None and p2700 <= 500:  # Убеждаемся, что P(2700) в пределах графика
        # Вертикальная линия от x = 200
        line_x200 = QLineSeries()
        line_x200.setName("Line x=200")
        line_x200.setColor(QColor(255, 0, 0))  # Красный цвет
        line_x200.append(QPointF(200, 1))  # Начало
        line_x200.append(QPointF(200, max_y_value * 1.1))  # До верхней границы
        calibration_chart.addSeries(line_x200)

        # Вертикальная линия от x = P(2700)
        line_p2700 = QLineSeries()
        line_p2700.setName("Line x=P(2700)")
        line_p2700.setColor(QColor(255, 0, 0))  # Красный цвет
        line_p2700.append(QPointF(p2700, 1))  # Начало
        line_p2700.append(QPointF(p2700, max_y_value * 1.1))  # До верхней границы
        calibration_chart.addSeries(line_p2700)
    else:
        print("Предупреждение: P(2700) не рассчитан или выходит за пределы графика (500). Прямые не отображаются.")

    axis_x = QValueAxis()
    axis_x.setTitleText("Канал")
    axis_x.setRange(0, 500)

    axis_y = QValueAxis()
    axis_y.setTitleText("Нормализованное значение")
    axis_y.setRange(1, max_y_value * 1.1)

    calibration_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    calibration_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    for series in calibration_chart.series():
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

    chart_view = QChartView(calibration_chart)
    chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

    log_checkbox = QCheckBox("Логарифмический масштаб")

    def toggle_log_scale(state):
        nonlocal axis_y
        if state == Qt.CheckState.Checked.value:
            new_axis_y = QLogValueAxis()
            new_axis_y.setTitleText("Нормализованное значение (лог)")
            new_axis_y.setBase(10.0)
            new_axis_y.setRange(1, max_y_value * 1.1)
            new_axis_y.setMinorTickCount(9)
        else:
            new_axis_y = QValueAxis()
            new_axis_y.setTitleText("Нормализованное значение")
            new_axis_y.setRange(1, max_y_value * 1.1)

        calibration_chart.removeAxis(axis_y)
        calibration_chart.addAxis(new_axis_y, Qt.AlignmentFlag.AlignLeft)
        for series in calibration_chart.series():
            series.detachAxis(axis_y)
            series.attachAxis(new_axis_y)
        axis_y = new_axis_y

    log_checkbox.stateChanged.connect(toggle_log_scale)

    # Информационная панель с активностями
    info_layout = QFormLayout()
    if hasattr(parent, 'am241_activity'):
        info_layout.addRow("A_am:", QLabel(f"{parent.am241_activity:.3f}"))
    if hasattr(parent, 'sry90_activity'):
        info_layout.addRow("A_sr:", QLabel(f"{parent.sry90_activity:.3f}"))
    if p2700 is not None:
        info_layout.addRow("P(2700):", QLabel(f"{p2700:.2f}"))
    else:
        info_layout.addRow("P(2700):", QLabel("Не рассчитан"))

    button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)

    layout = QVBoxLayout()
    layout.addWidget(chart_view)
    layout.addWidget(log_checkbox)
    layout.addLayout(info_layout)
    layout.addWidget(button_box)
    dialog.setLayout(layout)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Калибровка подтверждена")