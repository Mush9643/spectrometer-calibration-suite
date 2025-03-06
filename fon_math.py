import pandas as pd
import os
from PyQt6.QtCharts import QLineSeries
from Beta_math import update_calibration_button_state

def calculate_fon_sum(fon_data, nud_b=10, vud_b=200):
    """
    Вычисляет сумму по формуле fon_И = Σ (fon_i / fon_0) для i от NUD_b до VUD_b.

    Args:
        fon_data (list): Массив значений из столбца 'Кол-во импульсов'.
        nud_b (int): Нижняя граница диапазона (NUD_b), по умолчанию 10.
        vud_b (int): Верхняя граница диапазона (VUD_b), по умолчанию 200.

    Returns:
        float: Значение fon_И по формуле.
    """
    if not fon_data:
        print("Массив fon_data пуст. Невозможно вычислить fon_И.")
        return 0.0

    fon_0 = fon_data[0]
    if fon_0 == 0:
        print("Предупреждение: fon_0 равно 0. Деление на 0 невозможно, возвращаем 0.")
        return 0.0

    if nud_b < 0 or vud_b >= len(fon_data) or nud_b > vud_b:
        print(f"Ошибка: Неверный диапазон NUD_b={nud_b}, VUD_b={vud_b}. Длина массива: {len(fon_data)}.")
        return 0.0

    fon_sum = sum(fon_data[i] / fon_0 for i in range(nud_b, vud_b + 1))
    print(f"Вычисленное значение fon_И (сумма от NUD_b={nud_b} до VUD_b={vud_b}):  {fon_sum:.3f}")
    return fon_sum

def process_fon_data(parent):
    """
    Обрабатывает график с фразой 'фона' в имени на вкладке Beta chart: удаляет его,
    извлекает данные из второго столбца Excel-файла, выводит их в консоль и вычисляет fon_И.

    Args:
        parent: Экземпляр SpectrumWindow, содержащий beta_series_dict и данные.
    Returns:
        list: Массив значений из второго столбца Excel-файла (или пустой список, если график не найден).
    """
    # Проверяем, был ли уже обработан фоновый график
    if hasattr(parent, 'fon_processed') and parent.fon_processed:
        print("Фоновый график уже обработан, пропускаем повторную обработку.")
        return []

    # Ищем график с "фона" в имени
    fon_file_name = None
    for file_name, series in list(parent.beta_series_dict.items()):
        if "фона" in series.name().lower():
            fon_file_name = file_name
            break

    if fon_file_name is None:
        print("График с фразой 'фона' в имени не найден на вкладке Beta chart.")
        return []

    # Удаляем график
    series_to_remove = parent.beta_series_dict[fon_file_name]
    parent.beta_chart.removeSeries(series_to_remove)
    if fon_file_name in parent.used_beta_colors:
        del parent.used_beta_colors[fon_file_name]
    if fon_file_name in parent.beta_checkboxes:
        checkbox = parent.beta_checkboxes.pop(fon_file_name)
        checkbox.setParent(None)
        checkbox.deleteLater()
    del parent.beta_series_dict[fon_file_name]


    # Обновляем состояние кнопки калибровки
    update_calibration_button_state(parent)

    # Извлекаем данные из Excel-файла
    folder_name = parent.folder_input.text()
    folder_path = os.path.join(os.getcwd(), folder_name)
    file_path = os.path.join(folder_path, fon_file_name)

    if not os.path.exists(file_path):
        print(f"Файл '{fon_file_name}' не найден по пути: {file_path}")
        return []

    try:
        df = pd.read_excel(file_path)
        if 'Кол-во импульсов' not in df.columns:
            print(f"Столбец 'Кол-во импульсов' не найден в файле '{fon_file_name}'.")
            return []

        fon_data = df['Кол-во импульсов'].tolist()


        # Вычисляем fon_И по формуле
        calculate_fon_sum(fon_data, nud_b=10, vud_b=200)

        # Устанавливаем флаг обработки
        parent.fon_processed = True
        return fon_data

    except Exception as e:
        print(f"Ошибка при чтении файла '{fon_file_name}': {str(e)}")
        return []