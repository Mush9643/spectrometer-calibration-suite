import math
import os
import pandas as pd
import numpy as np
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QScatterSeries, QLogValueAxis
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QMessageBox, QLabel
from PyQt6.QtCore import Qt

# Массив констант Era226
Era226 = [661.66, 60]

# Массив энергий Ep (в кэВ)
Ep = np.array([80, 146, 400, 850, 1500, 2515])

def print_gamma_impulses(main_window):
    """
    Выводит в консоль массивы данных из столбца 'Кол-во импульсов' для всех файлов,
    отмеченных пурпурным цветом (Gamma-файлов).
    """
    PURPLE_COLOR = QColor(147, 112, 219)
    folder_name = main_window.folder_input.text()
    if not folder_name:
        print("Ошибка: Папка не выбрана.")
        return

    folder_path = os.path.join(os.getcwd(), folder_name)
    if not os.path.exists(folder_path):
        print(f"Ошибка: Папка '{folder_path}' не существует.")
        return

    gamma_files_found = 0
    for i in range(main_window.file_list.count()):
        item = main_window.file_list.item(i)
        if item is None:
            continue

        if item.background().color() == PURPLE_COLOR:
            file_name = item.text()
            file_path = os.path.join(folder_path, file_name)
            if not os.path.exists(file_path):
                print(f"Файл '{file_name}' не найден по пути: {file_path}")
                continue

            try:
                df = pd.read_excel(file_path)
                if 'Кол-во импульсов' not in df.columns:
                    print(f"В файле '{file_name}' отсутствует столбец 'Кол-во импульсов'.")
                    continue
                impulses = df['Кол-во импульсов'].tolist()
                print(f"\nМассив 'Кол-во импульсов' для файла '{file_name}':")
                print(impulses)
                gamma_files_found += 1
            except Exception as e:
                print(f"Ошибка при обработке файла '{file_name}': {str(e)}")
                continue

    if gamma_files_found == 0:
        print("Не найдено файлов, отмеченных пурпурным цветом (Gamma-файлов).")


def calculate_peaks(main_window):
    """
    Вычисляет пики для Cs-137 и Am-241 по формулам из Mathcad для всех Gamma-файлов,
    отмеченных пурпурным цветом, и вычисляет границы пика для Cs-137 по формуле.
    Также вычисляет S1 и S2 для Cs-137 по формулам из Mathcad.
    """
    PURPLE_COLOR = QColor(147, 112, 219)
    folder_name = main_window.folder_input.text()
    if not folder_name:
        print("Ошибка: Папка не выбрана.")
        return {}

    folder_path = os.path.join(os.getcwd(), folder_name)
    if not os.path.exists(folder_path):
        print(f"Ошибка: Папка '{folder_path}' не существует.")
        return {}

    peaks = {}
    m_cs137 = None
    m_am241 = None

    for i in range(main_window.file_list.count()):
        item = main_window.file_list.item(i)
        if item is None or item.background().color() != PURPLE_COLOR:
            continue

        file_name = item.text().lower()
        file_path = os.path.join(folder_path, item.text())
        if not os.path.exists(file_path):
            print(f"Файл '{file_name}' не найден по пути: {file_path}")
            continue

        try:
            df = pd.read_excel(file_path)
            if 'Кол-во импульсов' not in df.columns:
                print(f"В файле '{file_name}' отсутствует столбец 'Кол-во импульсов'.")
                continue
            impulses = df['Кол-во импульсов'].to_numpy()

            if any(keyword in file_name for keyword in ["cs", "cs137", "cs_gamma"]):
                submatrix = impulses[580:791]
                if len(submatrix) == 0:
                    print(f"Диапазон 580–790 пуст для файла '{file_name}'.")
                    continue
                max_value = np.max(submatrix)
                max_index_in_submatrix = np.argmax(submatrix)
                peak_channel = 580 + max_index_in_submatrix
                peaks[item.text()] = (peak_channel, max_value)
                main_window.gamma_peaks[item.text()] = (peak_channel, max_value)
                m_cs137 = peak_channel - 512
                print(f"Пик для Cs-137 (файл '{item.text()}'): канал {peak_channel}, значение {max_value}")

                # Вычисляем границы пика P для Cs-137 по формуле
                if m_cs137 is not None:
                    Pm = m_cs137 + 512
                    sqrt_Pm = math.sqrt(Pm)  # Вычисляем квадратный корень из Pm
                    P = [
                        math.floor(Pm - 1.5 * 0.63 * sqrt_Pm),  # P_0
                        math.floor(Pm - 0.63 * sqrt_Pm),        # P_1
                        math.floor(Pm + 0.63 * sqrt_Pm),        # P_2
                        math.floor(Pm + 1.5 * 0.63 * sqrt_Pm)   # P_3
                    ]
                    print(f"Считаем разрешение по цезию")
                    print(f"###############################")
                    print(f"P для Cs-137 (файл '{item.text()}'): {P}")

                    # Вычисляем S1 и S2 для файла 'cs_gamma.xls'
                    if "cs_gamma.xls" in file_name:
                        # Нормализация: Sp_i = Cs_i / Cs_0
                        Cs = impulses  # Массив 'Кол-во импульсов'
                        if len(Cs) == 0 or Cs[0] == 0:
                            print(f"Ошибка: Массив 'Кол-во импульсов' пуст или Cs_0 = 0 для файла '{file_name}'.")
                            continue
                        Sp = Cs / Cs[0]  # Нормализованный массив

                        # Вычисляем S1 = (сумма Sp_i от P_0 до P_1) / (P_1 - P_0 + 1)
                        P_0 = P[0]
                        P_1 = P[1]
                        P_2 = P[2]
                        P_3 = P[3]
                        print(f"P0: {P_0}")
                        print(f"P1: {P_1}")
                        print(f"P2: {P_2}")
                        print(f"P3: {P_3}")
                        if P_1 < P_0 or P_1 >= len(Sp) or P_0 < 0:
                            print(f"Ошибка: Неверные границы P_0={P_0} или P_1={P_1} для файла '{file_name}'.")
                            continue
                        sum_Sp1 = np.sum(Sp[P_0:P_1 + 1])  # Сумма от P_0 до P_1 включительно
                        S1 = sum_Sp1 / (P_1 - P_0 + 1)
                        print(f"S1 для Cs-137 (файл '{item.text()}'): {S1}")
                        if P_3 < P_2 or P_3 >= len(Sp) or P_2 < 0:
                            print(f"Ошибка: Неверные границы P_2={P_2} или P_3={P_3} для файла '{file_name}'.")
                            continue
                        sum_Sp2 = np.sum(Sp[P_2:P_3 + 1])  # Сумма от P_2 до P_3 включительно
                        S2 = sum_Sp2 / (P_3 - P_2 + 1)
                        print(f"S2 для Cs-137 (файл '{item.text()}'): {S2}")
                        Sa = (S1 - S2) * 2 / (P_1 + P_0 - P_2 - P_3)
                        Sb = S1-Sa * (P_1+P_0)/2
                        print(f"a = {Sa}")
                        print(f"b = {Sb}")

            elif any(keyword in file_name for keyword in ["am", "am241", "am_gamma"]):
                if file_name in ["98_fon_2_gamma.xls", "98_fon_gamma.xls", "th232_gamma.xls"]:
                    continue
                submatrix = impulses[1:541]
                if len(submatrix) == 0:
                    print(f"Диапазон 1–540 пуст для файла '{file_name}'.")
                    continue
                max_value = np.max(submatrix)
                max_index_in_submatrix = np.argmax(submatrix)
                peak_channel = 1 + max_index_in_submatrix
                peaks[item.text()] = (peak_channel, max_value)
                main_window.gamma_peaks[item.text()] = (peak_channel, max_value)
                m_am241 = peak_channel - 512
                print(f"Пик для Am-241 (файл '{item.text()}'): канал {peak_channel}, значение {max_value}")

        except Exception as e:
            print(f"Ошибка при обработке файла '{file_name}': {str(e)}")
            continue

    if not peaks:
        print("Не найдено Gamma-файлов с именами, содержащими 'cs', 'cs137', 'cs_gamma', 'am', 'am241' или 'am_gamma'.")
    else:
        Rbntu = [m_cs137 if m_cs137 is not None else 0, m_am241 if m_am241 is not None else 0]
        print(f"Массив Rbntu = [m_cs137, m_am241]: {Rbntu}")

    return peaks


def plot_peaks(main_window, peaks):
    """
    Отображает пики на графике во вкладке Gamma, используя QChart, с учетом текущего масштаба.
    """
    if not hasattr(main_window, 'gamma_chart'):
        print("Ошибка: График Gamma (gamma_chart) не найден в main_window.")
        return

    # Удаляем старые серии пиков
    if not hasattr(main_window, 'gamma_peak_series'):
        main_window.gamma_peak_series = {}
    for series in main_window.gamma_peak_series.values():
        main_window.gamma_chart.removeSeries(series)
    main_window.gamma_peak_series.clear()

    # Проверяем текущий масштаб
    is_log_scale = isinstance(main_window.gamma_axis_y, QLogValueAxis)
    min_y_threshold = 1.0 if is_log_scale else 0.0

    # Добавляем новые пики
    for file_name, (peak_channel, peak_value) in peaks.items():
        color = QColor(255, 0, 0) if any(
            keyword in file_name.lower() for keyword in ["cs", "cs137", "cs_gamma"]) else QColor(0, 0, 255)
        scatter_series = QScatterSeries()
        scatter_series.setName(f"Пик {file_name}")

        # Корректируем Y-координату для логарифмического масштаба
        display_value = max(peak_value, min_y_threshold) if is_log_scale else peak_value
        scatter_series.append(peak_channel, display_value)

        scatter_series.setMarkerShape(QScatterSeries.MarkerShape.MarkerShapeCircle)
        scatter_series.setMarkerSize(7)
        scatter_series.setColor(color)
        scatter_series.setBorderColor(color)

        main_window.gamma_chart.addSeries(scatter_series)
        scatter_series.attachAxis(main_window.gamma_axis_x)
        scatter_series.attachAxis(main_window.gamma_axis_y)
        main_window.gamma_peak_series[file_name] = scatter_series

    print("Пики отображены на графике Gamma.")


class CalibrationWindow(QDialog):

    def __init__(self, parent=None, peaks=None, rbntu=None):
        super().__init__(parent)
        self.pn_values = None
        self.setWindowTitle("Калибровка Gamma")
        self.setGeometry(100, 100, 800, 600)

        try:
            # Создаём график
            self.calibration_chart = QChart()
            self.calibration_chart.setTitle("Калибровочный график Gamma")
            self.calibration_chart.legend().show()

            # Ось X
            self.axis_x = QValueAxis()
            self.axis_x.setTitleText("Каналы")
            self.axis_x.setRange(0, 400)  # Диапазон X: 0–400
            self.calibration_chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)

            # Ось Y
            self.axis_y = QValueAxis()
            self.axis_y.setTitleText("Энергия (кэВ)")
            self.axis_y.setRange(0, 4000)  # Диапазон Y: 0–4000
            self.calibration_chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

            # Переменные для коэффициентов
            a, b = 0, 0
            # Переменные для хранения X-координат пиков
            cs137_x, am241_x = None, None

            # Построение калибровочной прямой, если передан Rbntu
            if rbntu and len(rbntu) == 2:
                # Вычисляем коэффициенты прямой по сдвинутым каналам (Rbntu)
                x1, x2 = rbntu[0], rbntu[1]  # Каналы: Cs-137 (137), Am-241 (14)
                y1, y2 = Era226[0], Era226[1]  # Энергии: Cs-137 (661.66), Am-241 (60)
                b = (y2 - y1) / (x2 - x1)  # Наклон
                a = y1 - b * x1  # Свободный член

                # Создаём серию для прямой
                calibration_line = QLineSeries()
                calibration_line.setName("Калибровочная прямая")
                calibration_line.setPen(QColor(0, 128, 0))  # Зелёный цвет

                # Добавляем две точки для прямой (t = 0 и t = 400 на графике)
                t_min, t_max = 0, 400  # Диапазон X графика (после сдвига)
                f_t_min = a + b * t_min
                f_t_max = a + b * t_max
                calibration_line.append(t_min, f_t_min)
                calibration_line.append(t_max, f_t_max)

                # Добавляем серию на график
                self.calibration_chart.addSeries(calibration_line)
                calibration_line.attachAxis(self.axis_x)
                calibration_line.attachAxis(self.axis_y)

            # Добавляем пики Cs-137 и Am-241 с энергиями из Era226, сдвигая каналы только для отображения
            if peaks:
                for file_name, (peak_channel, _) in peaks.items():
                    scatter_series = QScatterSeries()
                    shifted_channel = peak_channel - 512  # Сдвигаем канал влево на 512 только для отображения
                    if any(keyword in file_name.lower() for keyword in ["cs", "cs137", "cs_gamma"]):
                        scatter_series.setName("Пик Cs-137")
                        energy = Era226[0]  # 661.66 кэВ
                        scatter_series.setColor(QColor(255, 0, 0))  # Красный
                        scatter_series.setBorderColor(QColor(255, 0, 0))
                        cs137_x = shifted_channel  # Сохраняем X-координату
                    elif any(keyword in file_name.lower() for keyword in ["am", "am241", "am_gamma"]):
                        scatter_series.setName("Пик Am-241")
                        energy = Era226[1]  # 60 кэВ
                        scatter_series.setColor(QColor(0, 0, 255))  # Синий
                        scatter_series.setBorderColor(QColor(0, 0, 255))
                        am241_x = shifted_channel  # Сохраняем X-координату
                    else:
                        continue

                    scatter_series.append(shifted_channel, energy)
                    scatter_series.setMarkerShape(QScatterSeries.MarkerShape.MarkerShapeCircle)
                    scatter_series.setMarkerSize(7)
                    self.calibration_chart.addSeries(scatter_series)
                    scatter_series.attachAxis(self.axis_x)
                    scatter_series.attachAxis(self.axis_y)

            # Пустая серия, если ничего не добавлено
            if not peaks and not rbntu:
                self.dummy_series = QLineSeries()
                self.dummy_series.setName("Пустая серия")
                self.dummy_series.append(0, 0)
                self.calibration_chart.addSeries(self.dummy_series)
                self.dummy_series.attachAxis(self.axis_x)
                self.dummy_series.attachAxis(self.axis_y)

            # Представление графика
            self.chart_view = QChartView(self.calibration_chart)
            self.chart_view.setRenderHints(QPainter.RenderHint.Antialiasing)

            # Компоновка
            layout = QVBoxLayout()
            layout.addWidget(self.chart_view)
            ka = b
            kb = a
            if ka != 0:
                Pn = np.round((Ep - kb) / ka).astype(int)
                self.pn_values = Pn.tolist()
                print(f"Вычислен и сохранён массив Pn: {self.pn_values}")

            else:
                print("Коэффициент ka равен 0, Pn не вычислен.")
            # Формируем текст для QLabel
            label_text = f"Энергии наших окон компенсационных Pn для Ep = {Ep}: {Pn}"
            label_text += f"\nКоэффициенты прямой: b = {a:.2f}, a = {b:.4f}"
            if cs137_x is not None:
                label_text += f"\nX-координата пика Cs-137: {cs137_x:.2f}"
            if am241_x is not None:
                label_text += f"\nX-координата пика Am-241: {am241_x:.2f}"
            coefficients_label = QLabel(label_text)
            layout.addWidget(coefficients_label)

            self.setLayout(layout)

        except Exception as e:
            print(f"Ошибка при создании CalibrationWindow: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать окно калибровки: {str(e)}")

    def get_pn_values(self):
        return self.pn_values

def perform_calibration(main_window):
    """
    Открывает окно калибровки с графиком для вкладки Gamma.
    """
    try:

        # Получаем Rbntu из calculate_peaks
        peaks = main_window.gamma_peaks
        rbntu = None
        if peaks:
            m_cs137 = None
            m_am241 = None
            for file_name, (peak_channel, _) in peaks.items():
                if any(keyword in file_name.lower() for keyword in ["cs", "cs137", "cs_gamma"]):
                    m_cs137 = peak_channel - 512
                elif any(keyword in file_name.lower() for keyword in ["am", "am241", "am_gamma"]):
                    m_am241 = peak_channel - 512
            rbntu = [m_cs137 if m_cs137 is not None else 0, m_am241 if m_am241 is not None else 0]
            print(f"Массив Rbntu для калибровки: {rbntu}")

        calibration_window = CalibrationWindow(parent=None, peaks=peaks, rbntu=rbntu)
        calibration_window.exec()
        # Получаем Pn после закрытия окна
        pn_values = calibration_window.get_pn_values()
        if pn_values is not None:
            main_window.gamma_pn_values = pn_values
            print(f"Pn сохранён в main_window: {main_window.gamma_pn_values}")
        print("Окно калибровки закрыто.")
    except Exception as e:
        print(f"Ошибка в perform_calibration: {str(e)}")
        QMessageBox.critical(main_window, "Ошибка", f"Не удалось открыть окно калибровки: {str(e)}")



