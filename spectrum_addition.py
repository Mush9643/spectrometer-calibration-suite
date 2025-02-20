import pandas as pd
import os
from PyQt6.QtWidgets import QPushButton, QMessageBox
from PyQt6.QtGui import QColor, QKeyEvent
from PyQt6.QtCore import Qt


class SpectrumAddition:
    def __init__(self, spectrum_window):
        """
        Инициализация функционала для сложения спектров.
        :param spectrum_window: Экземпляр главного окна SpectrumWindow.
        """
        self.spectrum_window = spectrum_window
        self.addition_mode = False  # Режим сложения спектров (включен/выключен)
        self.selected_files = set()  # Множество для хранения выделенных файлов
        self.press_enter_next_time = False  # Флаг для эмуляции нажатия Enter

        # Создаем кнопку "Сложение спектра"
        self.addition_button = QPushButton("Сложение спектра")
        self.addition_button.clicked.connect(self.toggle_addition_mode)

        # Добавляем кнопку в нижний угол вкладки "Menu"
        menu_layout = self.spectrum_window.tab0.layout()
        menu_layout.addWidget(self.addition_button)

        # Подключаем обработчик кликов по списку файлов
        self.spectrum_window.file_list.itemClicked.connect(self.handle_file_click)

    def toggle_addition_mode(self):
        """
        Переключает режим сложения спектров.
        Если режим выключается, выполняется сложение данных и сохранение в новый файл.
        """
        if self.addition_mode:
            # Если режим выключается, выполняем сложение данных
            self.sum_and_save_spectra()
            self.addition_button.setStyleSheet("")  # Сброс стиля
            self.addition_button.setText("Сложение спектра")

            # Если это второй раз, отправляем событие нажатия Enter
            if self.press_enter_next_time:
                self.simulate_enter_key()
                self.press_enter_next_time = False  # Сброс флага
            else:
                self.press_enter_next_time = True  # Устанавливаем флаг
        else:
            # Если режим включается, очищаем выделенные файлы
            self.selected_files.clear()
            self.addition_button.setStyleSheet("background-color: red; color: white;")
            self.addition_button.setText("Режим сложения (выкл)")

        self.addition_mode = not self.addition_mode

    def handle_file_click(self, item):
        """
        Обрабатывает клик по элементу списка файлов.
        :param item: Элемент списка файлов (QListWidgetItem).
        """
        if self.addition_mode:
            file_name = item.text()
            if file_name in self.selected_files:
                # Если файл уже выделен, снимаем выделение
                item.setBackground(QColor(255, 255, 255))  # Белый цвет
                self.selected_files.remove(file_name)
            else:
                # Если файл не выделен, выделяем его
                item.setBackground(QColor(255, 0, 0))  # Красный цвет
                self.selected_files.add(file_name)

    def sum_and_save_spectra(self):
        """
        Суммирует значения столбца "Кол-во импульсов" из выделенных файлов
        и сохраняет результат в новый файл.
        """
        if not self.selected_files:
            QMessageBox.warning(self.spectrum_window, "Ошибка", "Нет выделенных файлов для сложения.")
            return

        folder_name = self.spectrum_window.folder_input.text()
        folder_path = os.path.join(os.getcwd(), folder_name)

        # Инициализируем DataFrame для хранения суммы
        summed_df = None

        for file_name in self.selected_files:
            file_path = os.path.join(folder_path, file_name)
            if not os.path.exists(file_path):
                QMessageBox.warning(self.spectrum_window, "Ошибка", f"Файл '{file_name}' не найден.")
                continue

            try:
                # Читаем данные из файла
                df = pd.read_excel(file_path)

                # Проверяем, что файл содержит необходимые столбцы
                if 'Канал' not in df.columns or 'Кол-во импульсов' not in df.columns:
                    QMessageBox.warning(self.spectrum_window, "Ошибка",
                                        f"Неверный формат данных в файле '{file_name}'.")
                    continue

                if summed_df is None:
                    # Если это первый файл, инициализируем summed_df
                    summed_df = df.copy()
                else:
                    # Суммируем значения столбца "Кол-во импульсов"
                    summed_df['Кол-во импульсов'] += df['Кол-во импульсов']

            except Exception as e:
                QMessageBox.warning(self.spectrum_window, "Ошибка", f"Ошибка при чтении файла '{file_name}': {str(e)}")
                continue

        if summed_df is not None:
            # Сохраняем результат в новый файл
            output_file_name = "new spectrum.xlsx"
            output_file_path = os.path.join(folder_path, output_file_name)
            try:
                summed_df.to_excel(output_file_path, index=False)
                QMessageBox.information(self.spectrum_window, "Успех",
                                        f"Результат сохранен в файл '{output_file_name}'.")
            except Exception as e:
                QMessageBox.warning(self.spectrum_window, "Ошибка", f"Ошибка при сохранении файла: {str(e)}")

    def simulate_enter_key(self):
        """
        Эмулирует нажатие клавиши Enter.
        """
        event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
        self.spectrum_window.keyPressEvent(event)
