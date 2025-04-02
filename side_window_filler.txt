from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHeaderView


class SideWindow(QWidget):
    def __init__(self, main_geometry):
        super().__init__()
        self.setWindowTitle("Дополнительное окно")

        # Вычисляем параметры для нового окна
        main_x = main_geometry.x()
        main_y = main_geometry.y()
        main_width = main_geometry.width()
        main_height = main_geometry.height()
        side_width = (main_width // 2) * 0.8  # Ширина в два раза меньше, затем уменьшаем на 20%
        side_x = main_x + main_width  # Располагаем справа от основного окна
        side_y = main_y  # Та же высота, что у основного окна
        side_height = main_height
        self.setGeometry(side_x, side_y, int(side_width), side_height)

        # Применяем улучшенный стиль
        self.setStyleSheet("""
            QWidget {
                background-color: #F8FAFC;
                font-family: 'Montserrat', sans-serif;
            }
            QLabel#titleLabel {
                font-size: 18px;
                font-weight: 600;
                color: #4A4A4A;
                padding: 10px 10px 5px 10px;
                border-bottom: 1px solid #E2E8F0;
            }
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #4A4A4A;
                border-radius: 8px;
                font-family: 'Montserrat', sans-serif;
                font-size: 13px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            QHeaderView::section {
                background-color: #4A4A4A;
                color: #FFFFFF;
                padding: 10px;
                border: none;
                border-bottom: 1px solid #E2E8F0;
                font-weight: 600;
                font-size: 15px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #E2E8F0;
                color: #1A202C;
            }
            QTableWidget::item:alternate {
                background-color: #F8FAFC;
            }
            QTableWidget::item:selected {
                background-color: #E2E8F0;
                color: #1A202C;
            }
            QPushButton#fillButton {
                background-color: #4A4A4A;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
                max-width: 150px;
            }
            QPushButton#fillButton:hover {
                background-color: #5A5A5A;
            }
            QPushButton#fillButton:pressed {
                background-color: #3A3A3A;
            }
        """)

        # Создаем layout для окна
        side_layout = QVBoxLayout()
        side_layout.setContentsMargins(20, 20, 20, 20)
        side_layout.setSpacing(20)

        # Добавляем заголовок
        title_label = QLabel("Дополнительное окно")
        title_label.setObjectName("titleLabel")
        side_layout.addWidget(title_label)

        # Создаем таблицу
        self.side_table = QTableWidget()
        self.side_table.setColumnCount(2)
        self.side_table.setRowCount(22)
        self.side_table.setHorizontalHeaderLabels(["Параметр", "Значение"])

        # Данные для таблицы (столбец "Значение" пустой)
        data = [
            ("a (Alfa)", ""),
            ("b (Alfa)", ""),
            ("НУД α, № канала (2700)", ""),
            ("ВУД ROI 3, № канала (4385.6)", ""),
            ("НУД ROI 2, № канала (5687.5)", ""),
            ("НУД ROI 6, № канала (6192.35)", ""),
            ("НУД ROI 4, № канала (6337.7)", ""),
            ("НУД ROI 5, № канала (8044.6)", ""),
            ("K(Po218)", ""),
            ("k1p9", ""),
            ("Пик Am241", ""),
            ("НУД β", ""),
            ("ВУД β", ""),
            ("k1c0", ""),
            ("a (Beta)", ""),
            ("b (Beta)", ""),
            ("Pn (80 кэВ)", ""),
            ("Pn (146 кэВ)", ""),
            ("Pn (400 кэВ)", ""),
            ("Pn (850 кэВ)", ""),
            ("Pn (1500 кэВ)", ""),
            ("Pn (2515 кэВ)", ""),

        ]

        # Заполняем таблицу
        for row, (param, value) in enumerate(data):
            param_item = QTableWidgetItem(param)
            param_item.setFlags(param_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.side_table.setItem(row, 0, param_item)
            value_item = QTableWidgetItem(value)
            self.side_table.setItem(row, 1, value_item)

        # Настраиваем таблицу
        self.side_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.side_table.setAlternatingRowColors(True)
        self.side_table.setShowGrid(False)
        self.side_table.verticalHeader().setVisible(False)

        # Добавляем таблицу в layout
        side_layout.addWidget(self.side_table)

        # Добавляем кнопку "Заполнить значения"
        fill_button = QPushButton("Заполнить значения")
        fill_button.setObjectName("fillButton")
        fill_button.clicked.connect(self.fill_values)

        # Горизонтальный layout для кнопки (центрирование)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(fill_button)
        button_layout.addStretch()

        side_layout.addLayout(button_layout)

        # Устанавливаем layout для окна
        self.setLayout(side_layout)

    def fill_values(self):
        """Заполняет столбец 'Значение' числами от 1 до 24."""
        for row in range(self.side_table.rowCount()):
            value_item = QTableWidgetItem(str(row + 1))
            self.side_table.setItem(row, 1, value_item)