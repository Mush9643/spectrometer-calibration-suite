import pandas as pd
import os
from PyQt6.QtCharts import QLineSeries
from Beta_math import update_calibration_button_state

def calculate_fon_sum(fon_data, nud_b=10, vud_b=200):
    """
    Вычисляет сумму по формуле fon_И = Σ (fon_i / fon_0) для i от NUD_b до VUD_b.
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
    print(f"Вычисленное значение fon_И (сумма от NUD_b={nud_b} до VUD_b={vud_b}): {fon_sum:.2f}")
    return fon_sum

def process_fon_data(parent, fon_data, file_name):
    """
    Обрабатывает график с фразой 'фона' в имени на вкладке Beta chart.
    """
    fon_processed = getattr(parent, 'fon_processed', False)
    if isinstance(fon_processed, pd.Series):
        fon_processed = fon_processed.iloc[0] if not fon_processed.empty else False
    if fon_processed:
        print("Фоновый график уже обработан, пропускаем повторную обработку.")
        return []

    series_to_remove = parent.beta_series_dict[file_name]
    parent.beta_chart.removeSeries(series_to_remove)
    if file_name in parent.used_beta_colors:
        del parent.used_beta_colors[file_name]
    if file_name in parent.beta_checkboxes:
        checkbox = parent.beta_checkboxes.pop(file_name)
        checkbox.setParent(None)
        checkbox.deleteLater()
    del parent.beta_series_dict[file_name]
    print(f"График '{series_to_remove.name()}' удалён с вкладки Beta chart.")

    parent.fon_data = fon_data
    print(f"Оригинальные данные из столбца 'Кол-во импульсов' файла '{file_name}': {fon_data[:5]}...")
    print(f"Количество элементов в массиве фона: {len(fon_data)}")

    calculate_fon_sum(fon_data)

    parent.fon_processed = True
    update_calibration_button_state(parent)
    return fon_data

def process_isotope_data(parent, isotope_data, file_name):
    """
    Обрабатывает данные изотопов (Am241, C14, Cs137, SrY90) и выводит их в консоль.
    """
    if "Am241" in file_name:
        parent.am241_data = isotope_data
        print(f"Оригинальные данные из столбца 'Кол-во импульсов' файла '{file_name}':")
        print(parent.am241_data)
        print(f"Количество элементов в массиве Am241: {len(parent.am241_data)}")
    elif "C14" in file_name:
        parent.c14_data = isotope_data
        print(f"Оригинальные данные из столбца 'Кол-во импульсов' файла '{file_name}':")
        print(parent.c14_data)
        print(f"Количество элементов в массиве C14: {len(parent.c14_data)}")
    elif "Cs137" in file_name:
        parent.cs137_data = isotope_data
        print(f"Оригинальные данные из столбца 'Кол-во импульсов' файла '{file_name}':")
        print(parent.cs137_data)
        print(f"Количество элементов в массиве Cs137: {len(parent.cs137_data)}")
    elif "SrY90" in file_name:
        parent.sry90_data = isotope_data
        print(f"Оригинальные данные из столбца 'Кол-во импульсов' файла '{file_name}':")
        print(parent.sry90_data)
        print(f"Количество элементов в массиве SrY90: {len(parent.sry90_data)}")