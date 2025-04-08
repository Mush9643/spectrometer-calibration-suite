from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QDialog, QDialogButtonBox, QCheckBox, QFormLayout, QLabel, \
    QHBoxLayout, QWidget
from PyQt6.QtCharts import QChart, QChartView, QValueAxis, QLineSeries, QLogValueAxis
from PyQt6.QtGui import QPainter, QColor, QFont
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
    calibration_button.setFixedHeight(50)
    calibration_button.setFont(QFont("Montserrat", 14, QFont.Weight.Bold))
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
    dialog.resize(700, 500)

    # Стиль для диалогового окна
    dialog.setStyleSheet("""
        QDialog {
            background-color: #F8FAFC;  /* Светлый фон */
            border: 1px solid #D3D9DE;
            border-radius: 10px;
        }
    """)

    calibration_chart = QChart()
    calibration_chart.setTitle("(Калибровка Beta)")

    # Стиль для графика
    calibration_chart.setBackgroundVisible(True)
    calibration_chart.setBackgroundBrush(QColor("#FFFFFF"))  # Белый фон графика
    calibration_chart.setPlotAreaBackgroundVisible(True)
    calibration_chart.setPlotAreaBackgroundBrush(QColor("#F8FAFC"))  # Светлый фон области графика
    title_font = QFont()
    title_font.setPointSize(16)
    title_font.setBold(True)
    calibration_chart.setTitleFont(title_font)
    calibration_chart.setTitleBrush(QColor("#2D3748"))  # Темный цвет заголовка

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

    # Отрисовка красных прямых
    p2700 = getattr(parent, 'beta_p2700', None)
    if p2700 is not None and p2700 <= 500:
        line_x200 = QLineSeries()
        line_x200.setName("Line x=200")
        line_x200.setColor(QColor(255, 0, 0))
        line_x200.append(QPointF(200, 1))
        line_x200.append(QPointF(200, max_y_value * 1.1))
        calibration_chart.addSeries(line_x200)

        line_p2700 = QLineSeries()
        line_p2700.setName("Line x=P(2700)")
        line_p2700.setColor(QColor(255, 0, 0))
        line_p2700.append(QPointF(p2700, 1))
        line_p2700.append(QPointF(p2700, max_y_value * 1.1))
        calibration_chart.addSeries(line_p2700)

    axis_x = QValueAxis()
    axis_x.setTitleText("Канал")
    axis_x.setRange(0, 500)
    axis_x.setGridLineVisible(True)
    axis_x.setLabelsColor(QColor("#4A5568"))  # Темно-серый цвет подписей
    axis_x.setTitleBrush(QColor("#2D3748"))  # Темный цвет заголовка оси
    axis_font = QFont()
    axis_font.setPointSize(10)
    axis_x.setLabelsFont(axis_font)
    axis_x.setTitleFont(axis_font)

    axis_y = QValueAxis()
    axis_y.setTitleText("Нормализованное значение")
    axis_y.setRange(1, max_y_value * 1.1)
    axis_y.setGridLineVisible(True)
    axis_y.setLabelsColor(QColor("#4A5568"))
    axis_y.setTitleBrush(QColor("#2D3748"))
    axis_y.setLabelsFont(axis_font)
    axis_y.setTitleFont(axis_font)

    calibration_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    calibration_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    for series in calibration_chart.series():
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

    chart_view = QChartView(calibration_chart)
    chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
    chart_view.setStyleSheet("""
        QChartView {
            border: 1px solid #D3D9DE;
            border-radius: 5px;
            background-color: #FFFFFF;
        }
    """)

    log_checkbox = QCheckBox("Логарифмический масштаб")
    log_checkbox.setStyleSheet("""
        QCheckBox {
            font-size: 12px;
            color: #2D3748;
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #D3D9DE;
            border-radius: 3px;
            background-color: #FFFFFF;
        }
        QCheckBox::indicator:checked {
            background-color: #A3BFFA;
            border: 1px solid #A3BFFA;
            image: url(:/icons/check.png);  /* Если есть иконка для галочки */
        }
    """)

    def toggle_log_scale(state):
        nonlocal axis_y
        if state == Qt.CheckState.Checked.value:
            new_axis_y = QLogValueAxis()
            new_axis_y.setTitleText("Нормализованное значение (лог)")
            new_axis_y.setBase(10.0)
            new_axis_y.setRange(1, max_y_value * 1.1)
            new_axis_y.setMinorTickCount(9)
            new_axis_y.setLabelsColor(QColor("#4A5568"))
            new_axis_y.setTitleBrush(QColor("#2D3748"))
            new_axis_y.setLabelsFont(axis_font)
            new_axis_y.setTitleFont(axis_font)
        else:
            new_axis_y = QValueAxis()
            new_axis_y.setTitleText("Нормализованное значение")
            new_axis_y.setRange(1, max_y_value * 1.1)
            new_axis_y.setLabelsColor(QColor("#4A5568"))
            new_axis_y.setTitleBrush(QColor("#2D3748"))
            new_axis_y.setLabelsFont(axis_font)
            new_axis_y.setTitleFont(axis_font)

        calibration_chart.removeAxis(axis_y)
        calibration_chart.addAxis(new_axis_y, Qt.AlignmentFlag.AlignLeft)
        for series in calibration_chart.series():
            series.detachAxis(axis_y)
            series.attachAxis(new_axis_y)
        axis_y = new_axis_y

    log_checkbox.stateChanged.connect(toggle_log_scale)

    focus_checkbox = QCheckBox("Фокусировать на красных линиях")
    focus_checkbox.setEnabled(p2700 is not None and p2700 <= 500)
    focus_checkbox.setStyleSheet("""
        QCheckBox {
            font-size: 12px;
            color: #2D3748;
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #D3D9DE;
            border-radius: 3px;
            background-color: #FFFFFF;
        }
        QCheckBox::indicator:checked {
            background-color: #A3BFFA;
            border: 1px solid #A3BFFA;
            image: url(:/icons/check.png);  /* Если есть иконка для галочки */
        }
    """)

    def toggle_focus(state):
        nonlocal axis_x, axis_y
        if state == Qt.CheckState.Checked.value and p2700 is not None:
            x_min = min(200, p2700) - 10
            x_max = max(200, p2700) + 10
            x_min = max(0, x_min)
            x_max = min(500, x_max)
            axis_x.setRange(x_min, x_max)

            max_y_in_range = 1
            for series in calibration_chart.series():
                if "Line" in series.name():
                    continue
                for point in series.points():
                    if x_min <= point.x() <= x_max:
                        max_y_in_range = max(max_y_in_range, point.y())
            axis_y.setRange(1, max_y_in_range * 1.1)
        else:
            axis_x.setRange(0, 500)
            axis_y.setRange(1, max_y_value * 1.1)

        chart_view.update()

    focus_checkbox.stateChanged.connect(toggle_focus)

    # Информационная панель с активностями
    info_layout = QFormLayout()
    if hasattr(parent, 'am241_activity'):
        info_layout.addRow("A_am:", QLabel(f"{parent.am241_activity:.3f}"))
    if hasattr(parent, 'sry90_activity'):
        info_layout.addRow("A_sr:", QLabel(f"{parent.sry90_activity:.3f}"))




    # Компоновка диалогового окна
    layout = QVBoxLayout()
    layout.addWidget(chart_view)
    controls_layout = QHBoxLayout()
    controls_layout.addWidget(log_checkbox)
    controls_layout.addWidget(focus_checkbox)
    controls_layout.addStretch()
    layout.addLayout(controls_layout)
    layout.setSpacing(10)  # Увеличиваем расстояние между элементами
    layout.setContentsMargins(15, 15, 15, 15)  # Добавляем отступы
    dialog.setLayout(layout)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Калибровка подтверждена")