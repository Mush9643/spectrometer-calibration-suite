from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QDialog, QDialogButtonBox
from PyQt6.QtCharts import QChart, QChartView, QValueAxis, QLineSeries
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt


def add_beta_calibration_button(parent):
    """
    Добавляет кнопку 'Калибровка' на вкладку Beta chart и управляет её состоянием.

    Args:
        parent: Экземпляр SpectrumWindow, к которому добавляется кнопка.
    """
    # Создаем кнопку "Калибровка"
    calibration_button = QPushButton("Калибровка")
    calibration_button.clicked.connect(lambda: show_calibration_dialog(parent))

    # Изначально кнопка отключена
    calibration_button.setEnabled(False)
    parent.beta_calibration_button = calibration_button  # Сохраняем ссылку в объекте parent

    # Добавляем кнопку в layout вкладки Beta
    beta_layout = parent.tab2.layout()
    if beta_layout is None:
        beta_layout = QVBoxLayout()
        parent.tab2.setLayout(beta_layout)
    if isinstance(beta_layout, QVBoxLayout):
        beta_layout.addWidget(calibration_button)
    else:
        raise ValueError("Layout вкладки Beta не является QVBoxLayout")

    # Проверяем состояние графиков при инициализации
    update_calibration_button_state(parent)


def update_calibration_button_state(parent):
    """
    Проверяет наличие графиков с "Am241" и "SrY90" в именах и обновляет состояние кнопки.

    Args:
        parent: Экземпляр SpectrumWindow.
    """
    if not hasattr(parent, 'beta_calibration_button'):
        return

    # Проверяем имена серий в beta_series_dict
    series_names = [series.name() for series in parent.beta_series_dict.values()]
    has_am241 = any("Am241" in name for name in series_names)
    has_sry90 = any("SrY90" in name for name in series_names)

    # Активируем кнопку только если оба условия выполнены
    parent.beta_calibration_button.setEnabled(has_am241 and has_sry90)


def show_calibration_dialog(parent):
    """
    Открывает диалоговое окно с графиком для калибровки Beta.

    Args:
        parent: Экземпляр SpectrumWindow, передаваемый как родительский объект.
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle("Калибровка Beta")
    dialog.resize(600, 400)

    calibration_chart = QChart()
    calibration_chart.setTitle("График калибровки Beta (Am241 и SrY90)")

    # Загружаем данные из beta_series_dict для Am241 и SrY90
    for file_name, series in parent.beta_series_dict.items():
        if "Am241" in series.name() or "SrY90" in series.name():
            calibration_series = QLineSeries()
            calibration_series.setName(series.name())
            for point in series.points():
                calibration_series.append(point.x(), point.y())
            calibration_chart.addSeries(calibration_series)

    # Настройка осей
    axis_x = QValueAxis()
    axis_x.setTitleText("Канал")
    axis_x.setRange(0, 1023)  # Соответствует диапазону данных
    axis_y = QValueAxis()
    axis_y.setTitleText("Значение")
    max_y = max([point.y() for s in calibration_chart.series() for point in s.points()] or [100])
    axis_y.setRange(0, max_y * 1.1)

    calibration_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    calibration_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    for series in calibration_chart.series():
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

    chart_view = QChartView(calibration_chart)
    chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Кнопки ОК и Отмена
    button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)

    layout = QVBoxLayout()
    layout.addWidget(chart_view)
    layout.addWidget(button_box)
    dialog.setLayout(layout)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Калибровка подтверждена")


# Необходимо обновить основной код SpectrumWindow для вызова проверки состояния
def integrate_with_spectrum_window(parent):
    """
    Пример интеграции с классом SpectrumWindow.
    Вызывать эту функцию после изменений в beta_series_dict.
    """
    update_calibration_button_state(parent)