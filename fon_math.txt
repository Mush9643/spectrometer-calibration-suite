# -*- coding: utf-8 -*-
import pandas as pd
import os
from PyQt6.QtCharts import QLineSeries
from Beta_math import update_calibration_button_state


def write_to_result_file(value_name, value):
    """
    Записывает результат в файл Result.txt. Если файла нет, создаёт его и добавляет подпись.
    """
    file_path = "Result.txt"
    file_exists = os.path.exists(file_path)

    with open(file_path, 'a', encoding='utf-8') as f:
        # Если файл создаётся впервые, добавляем подпись
        if not file_exists:
            f.write("Скорости счёта в бета канале от различных изотопов\n")
        # Записываем значение
        f.write(f"{value_name}: {value:.3f}\n")


def calculate_fon_sum(fon_data, nud_b=10, vud_b=200):
    """
    Вычисляет сумму по формуле fon_И = Σ (fon_i / fon_0) для i от NUD_b до VUD_b.
    """
    if not fon_data or len(fon_data) <= vud_b:
        print("Массив fon_data пуст или слишком короткий. Невозможно вычислить fon_И.")
        return 0.0

    fon_0 = fon_data[0]
    if fon_0 == 0:
        print("Предупреждение: fon_0 равно 0. Деление на 0 невозможно, возвращаем 0.")
        return 0.0

    if nud_b < 0 or vud_b >= len(fon_data) or nud_b > vud_b:
        print(f"Ошибка: Неверный диапазон NUD_b={nud_b}, VUD_b={vud_b}. Длина массива: {len(fon_data)}.")
        return 0.0

    fon_sum = sum(fon_data[i] / fon_0 for i in range(nud_b, vud_b + 1))
    print(f"Вычисленное значение fon_И (сумма от NUD_b={nud_b} до VUD_b={vud_b}): {fon_sum:.3f}")

    # Записываем результат в файл
    write_to_result_file("fon_И", fon_sum)

    return fon_sum


def calculate_activity_am241(am241_data, fon_data, nud_b=10, vud_b=200):
    """
    Вычисляет активность A_am по формуле Σ (M2_i / M2_0 - fon_i / fon_0).
    Предполагается, что am241_data соответствует M2_i.
    """
    if not am241_data or not fon_data or len(am241_data) <= vud_b or len(fon_data) <= vud_b:
        print("Массивы am241_data или fon_data пусты или слишком короткие.")
        return 0.0

    am241_0 = am241_data[0]
    fon_0 = fon_data[0]
    if am241_0 == 0 or fon_0 == 0:
        print("Предупреждение: am241_0 или fon_0 равно 0. Деление на 0 невозможно, возвращаем 0.")
        return 0.0

    activity = sum((am241_data[i] / am241_0 - fon_data[i] / fon_0) for i in range(nud_b, vud_b + 1))
    print(f"Активность A_am (от NUD_b={nud_b} до VUD_b={vud_b}): {activity:.3f}")

    # Записываем результат в файл
    write_to_result_file("A_am", activity)

    return activity


def calculate_activity_c14(c14_data, fon_data, nud_b=10, vud_b=200):
    """
    Вычисляет активность A_c14 по формуле Σ (C14_i / C14_0 - fon_i / fon_0).
    """
    if not c14_data or not fon_data or len(c14_data) <= vud_b or len(fon_data) <= vud_b:
        print("Массивы c14_data или fon_data пусты или слишком короткие.")
        return 0.0

    c14_0 = c14_data[0]
    fon_0 = fon_data[0]
    if c14_0 == 0 or fon_0 == 0:
        print("Предупреждение: c14_0 или fon_0 равно 0. Деление на 0 невозможно, возвращаем 0.")
        return 0.0

    activity = sum((c14_data[i] / c14_0 - fon_data[i] / fon_0) for i in range(nud_b, vud_b + 1))
    print(f"Активность A_c14 (от NUD_b={nud_b} до VUD_b={vud_b}): {activity:.3f}")

    # Записываем результат в файл
    write_to_result_file("A_c14", activity)

    return activity


def calculate_activity_cs137(cs137_data, fon_data, nud_b=10, vud_b=200):
    """
    Вычисляет активность A_cs137 по формуле Σ (cs137_nash_i / cs137_nash_0 - fon_i / fon_0).
    """
    if not cs137_data or not fon_data or len(cs137_data) <= vud_b or len(fon_data) <= vud_b:
        print("Массивы cs137_data или fon_data пусты или слишком короткие.")
        return 0.0

    cs137_0 = cs137_data[0]
    fon_0 = fon_data[0]
    if cs137_0 == 0 or fon_0 == 0:
        print("Предупреждение: cs137_0 или fon_0 равно 0. Деление на 0 невозможно, возвращаем 0.")
        return 0.0

    activity = sum((cs137_data[i] / cs137_0 - fon_data[i] / fon_0) for i in range(nud_b, vud_b + 1))
    print(f"Активность A_cs137 (от NUD_b={nud_b} до VUD_b={vud_b}): {activity:.3f}")

    # Записываем результат в файл
    write_to_result_file("A_cs137", activity)

    return activity


def calculate_activity_sry90(sry90_data, fon_data, nud_b=10, vud_b=200):
    """
    Вычисляет активность A_sr по формуле Σ (SrY_i / SrY_0 - fon_i / fon_0).
    """
    if not sry90_data or not fon_data or len(sry90_data) <= vud_b or len(fon_data) <= vud_b:
        print("Массивы sry90_data или fon_data пусты или слишком короткие.")
        return 0.0

    sry90_0 = sry90_data[0]
    fon_0 = fon_data[0]
    if sry90_0 == 0 or fon_0 == 0:
        print("Предупреждение: sry90_0 или fon_0 равно 0. Деление на 0 невозможно, возвращаем 0.")
        return 0.0

    activity = sum((sry90_data[i] / sry90_0 - fon_data[i] / fon_0) for i in range(nud_b, vud_b + 1))
    print(f"Активность A_sr (от NUD_b={nud_b} до VUD_b={vud_b}): {activity:.3f}")

    # Записываем результат в файл
    write_to_result_file("A_sr", activity)

    return activity


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
    print(f"Значение с индексом 0 (fon_0): {fon_data[0]}")
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
        print(isotope_data)
        print(f"Значение с индексом 0 (am241_0): {isotope_data[0]}")
        print(f"Количество элементов в массиве Am241: {len(parent.am241_data)}")
        calculate_activity_am241(parent.am241_data, parent.fon_data)
    elif "C14" in file_name:
        parent.c14_data = isotope_data
        print(f"Оригинальные данные из столбца 'Кол-во импульсов' файла '{file_name}':")
        print(isotope_data)
        print(f"Значение с индексом 0 (c14_0): {isotope_data[0]}")
        print(f"Количество элементов в массиве C14: {len(parent.c14_data)}")
        calculate_activity_c14(parent.c14_data, parent.fon_data)
    elif "Cs137" in file_name:
        parent.cs137_data = isotope_data
        print(f"Оригинальные данные из столбца 'Кол-во импульсов' файла '{file_name}':")
        print(isotope_data)
        print(f"Значение с индексом 0 (cs137_0): {isotope_data[0]}")
        print(f"Количество элементов в массиве Cs137: {len(parent.cs137_data)}")
        calculate_activity_cs137(parent.cs137_data, parent.fon_data)
    elif "SrY90" in file_name:
        parent.sry90_data = isotope_data
        print(f"Оригинальные данные из столбца 'Кол-во импульсов' файла '{file_name}':")
        print(isotope_data)
        print(f"Значение с индексом 0 (sry90_0): {isotope_data[0]}")
        print(f"Количество элементов в массиве SrY90: {len(parent.sry90_data)}")
        calculate_activity_sry90(parent.sry90_data, parent.fon_data)

