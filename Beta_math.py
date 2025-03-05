from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QDialog
from PyQt6.QtCharts import QChart, QChartView, QValueAxis
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt


def add_beta_calibration_button(parent):
    """
    Добавляет кнопку 'Калибровка' на вкладку Beta chart и связывает её с открытием окна калибровки.

    Args:
        parent: Экземпляр SpectrumWindow, к которому добавляется кнопка.
    """
    # Создаем кнопку "Калибровка"
    calibration_button = QPushButton("Калибровка")
    calibration_button.clicked.connect(lambda: show_calibration_dialog(parent))

    # Добавляем кнопку в layout вкладки Beta
    beta_layout = parent.tab2.layout()
    if isinstance(beta_layout, QVBoxLayout):
        beta_layout.addWidget(calibration_button)


def show_calibration_dialog(parent):
    """
    Открывает диалоговое окно с пустым графиком для калибровки Beta chart.

    Args:
        parent: Экземпляр SpectrumWindow, передаваемый как родительский объект.
    """
    # Создаем диалоговое окно
    dialog = QDialog(parent)
    dialog.setWindowTitle("Калибровка Beta")
    dialog.resize(600, 400)

    # Создаем пустой график
    calibration_chart = QChart()
    calibration_chart.setTitle("График калибровки Beta")

    # Оси для графика
    axis_x = QValueAxis()
    axis_x.setTitleText("Точка")
    axis_x.setRange(0, 100)  # Устанавливаем начальный диапазон по X
    axis_y = QValueAxis()
    axis_y.setTitleText("Значение")
    axis_y.setRange(0, 100)  # Устанавливаем начальный диапазон по Y

    calibration_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    calibration_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)

    # Создаем виджет для отображения графика
    chart_view = QChartView(calibration_chart)
    chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Настраиваем layout для диалогового окна
    layout = QVBoxLayout()
    layout.addWidget(chart_view)
    dialog.setLayout(layout)

    # Показываем диалоговое окно
    dialog.exec()
