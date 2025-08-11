# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import os
from PyQt6.QtCharts import QLineSeries
from Beta_math import update_calibration_button_state

NUD_b = 5  # Константа для NUD_b
VUD_b = 200  # Константа для VUD_b

def calculate_fon_sum(fon_data, nud_b=5, vud_b=200):
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

    return fon_sum


def calculate_activity_am241(am241_data, fon_data, nud_b=5, vud_b=200):
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

    return activity


def calculate_regression_coefficients(parent):
    """
    Вычисляет коэффициенты линейной регрессии [b, a] для уравнения y = a * x + b.
    Использует Ben как x, а Bch как y.
    Возвращает вектор [b, a] в соответствии с Mathcad.
    """
    # Проверяем наличие атрибутов
    if not hasattr(parent, 'Ben') or not hasattr(parent, 'Bch'):
        print("Ошибка: Ben или Bch отсутствуют в объекте parent.")
        return 0.0, 0.0

    x = parent.Bch
    y = parent.Ben

    n = len(x)
    if n == 0 or len(y) != n:
        print("Ошибка: Массивы Ben или Bch пусты или имеют разную длину.")
        return 0.0, 0.0

    # Вычисляем суммы
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi * xi for xi in x)

    # Вычисляем коэффициенты
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)  # a
    intercept = (sum_y - slope * sum_x) / n  # b

    print(f"Коэффициенты линейной регрессии: intercept={intercept:.6f}, slope={slope:.6f}")
    return intercept, slope  # Возвращаем [b, a]


def calculate_activity_c14(parent, c14_data, fon_data, nud_b=5, vud_b=200):

    if not c14_data or not fon_data or len(c14_data) <= vud_b or len(fon_data) <= vud_b:
        print("Массивы c14_data или fon_data пусты или слишком короткие.")
        return 0.0

    c14_0 = c14_data[0]
    fon_0 = fon_data[0]
    if c14_0 == 0 or fon_0 == 0:
        print("Предупреждение: c14_0 или fon_0 равно 0. Деление на 0 невозможно, возвращаем 0.")
        return 0.0

    # Вычисление активности A_c14
    activity = sum((c14_data[i] / c14_0 - fon_data[i] / fon_0) for i in range(nud_b, vud_b + 1))
    print(f"Активность A_c14 = {activity:.3f}")

    # Вычисление массива c14s для i от 0 до 100
    if activity == 0:
        print("Предупреждение: A_c14 равно 0. Деление на 0 невозможно, c14s устанавливается в 0.")
        parent.c14s_data = [0.0] * 101  # Массив из 101 элемента (0 до 100)
    else:
        c14s = []
        for i in range(101):  # i от 0 до 100
            if i < len(c14_data) and i < len(fon_data):  # Проверка на доступность данных
                term = (c14_data[i] / c14_0 - fon_data[i] / fon_0) / activity
                c14s.append(term)
            else:
                c14s.append(0.0)  # Заполнение нулями, если данных недостаточно
        parent.c14s_data = c14s
        print(f"Массив c14s (i от 0 до 100): {c14s[:10]}... (показаны первые 10 элементов, всего {len(c14s)})")

    # Поиск максимального элемента в c14_data и его индекса
    max_c14_value = max(c14_data)
    max_c14_index = c14_data.index(max_c14_value)
    print(f"Максимальный элемент в массиве c14_data: {max_c14_value:.3f}, индекс: {max_c14_index}")

    # Поиск первого элемента в c14s, меньшего 0.005, в диапазоне от max_c14_index до 100
    threshold = 0.005
    found_index = -1
    for i in range(max_c14_index, 101):
        if i < len(c14s) and c14s[i] < threshold:
            found_index = i
            break

    if found_index != -1:
        print(f"Первый элемент в c14s, меньший {threshold}, найден на индексе {found_index}: {c14s[found_index]:.6f}")
    else:
        print(f"Элемент в c14s, меньший {threshold}, не найден в диапазоне от {max_c14_index} до 100.")

    # Формирование и сохранение массивов Ben и Bch, если условия выполнены
    if hasattr(parent, 'cs137_peak_coords') and parent.cs137_peak_coords and found_index != -1:
        cs_peak_x = parent.cs137_peak_coords[0][0]
        # Bch: [found_index, cs_peak_x]
        parent.Bch = np.array([found_index, cs_peak_x])
        # Ben: Константы [156.475, 624.216]
        parent.Ben = np.array([156.475, 624.216])
        print(f"Массив Bch (ugler и пик Cs-137): {parent.Bch}")
        print(f"Массив Ben (константы): {parent.Ben}")
    else:
        print("Условия для формирования массивов Ben и Bch не выполнены: либо пик Cs-137, либо found_index отсутствуют.")

    # Расчет коэффициентов линейной регрессии, если Ben и Bch доступны
    if hasattr(parent, 'Ben') and hasattr(parent, 'Bch'):
        AB, BB = calculate_regression_coefficients(parent)  # AB — intercept (b), BB — slope (a)
        if AB is not None and BB is not None:
            print(f"Коэффициенты линейной регрессии: AB = {AB:.6f}, BB = {BB:.6f}")
            parent.beta_calibration_coefficients = (AB, BB)
            # Сохраняем коэффициенты в parent для дальнейшего использования
            parent.calibration_coefficients = (AB, BB)

            # Вычисляем Enewb_i для i = 12
            i = 12
            Enewb_i = AB + BB * i
            print(f"Enewb_{i} = {Enewb_i:.3f}")

            # Вычисляем pb(e) для e = 53.818 и e = 3000
            if BB == 0:
                print("Ошибка: BB равен 0, вычисление pb(e) невозможно.")
            else:
                e_values = [53.818, 3000]
                for e in e_values:
                    pb_e = (e - AB) / BB
                    print(f"pb({e}) = {pb_e:.3f}")

    # Убедимся, что A_sr вычислен (если данные для SrY90 доступны)
    if hasattr(parent, 'sry90_data') and parent.sry90_data:
        A_sr = calculate_activity_sry90(parent.sry90_data, parent.fon_data, nud_b, vud_b)
        parent.A_sr = A_sr  # Сохраняем A_sr в parent для дальнейшего использования
    elif hasattr(parent, 'A_sr'):
        print(f"A_sr уже вычислен: {parent.A_sr:.3f}")
    else:
        print("Предупреждение: Данные для SrY90 отсутствуют, A_sr не вычислен.")

    # Вычисляем k1c0, если A_sr доступен
    if hasattr(parent, 'A_sr'):
        A_sr = parent.A_sr
        if A_sr == 0:
            print("Ошибка: A_sr равен 0, вычисление k1c0 невозможно.")
        else:
            denominator = getattr(parent, 'k1c0_denominator', 314.5)
            k1c0 = (A_sr / denominator) ** (-1)
            print(f"Значение k1c0: {k1c0:.3f}")
            parent.k1c0 = k1c0
    else:
        print("Ошибка: A_sr отсутствует, вычисление k1c0 невозможно.")

    return activity


def calculate_activity_cs137(cs137_data, fon_data, nud_b=5, vud_b=200):
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

    return activity


def calculate_activity_sry90(sry90_data, fon_data, nud_b=5, vud_b=200):
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

    parent.fon_sum = calculate_fon_sum(fon_data)

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
        calculate_activity_c14(parent, parent.c14_data, parent.fon_data)
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

