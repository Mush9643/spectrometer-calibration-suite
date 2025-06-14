import pytest
import numpy as np
from unittest.mock import Mock
from PyQt6.QtCore import QPointF
from PyQt6.QtCharts import QLineSeries
from math_utils import calculate_linear_regression, calculate_point_to_line_distances, calculate_ra, calculate_am_rate, calculate_k1p9

# Тест 1: Проверка линейной регрессии
def test_calculate_linear_regression():
    x = [1, 2, 3]
    y = [2, 4, 6]
    intercept, slope = calculate_linear_regression(x, y)
    np.testing.assert_almost_equal(intercept, 0.0, decimal=5)
    np.testing.assert_almost_equal(slope, 2.0, decimal=5)

# Тест 2: Проверка линейной регрессии с пустыми данными
def test_calculate_linear_regression_empty():
    x, y = [], []
    intercept, slope = calculate_linear_regression(x, y)
    assert intercept == 0.0
    assert slope == 0.0

# Тест 3: Проверка вычисления расстояний до прямой
def test_calculate_point_to_line_distances():
    x_values = [1, 2, 3]
    y_values = [2, 4, 6]
    slope = 2.0
    intercept = 0.0
    distances = calculate_point_to_line_distances(x_values, y_values, slope, intercept)
    expected = [0.0, 0.0, 0.0]  # Точки лежат на прямой y = 2x
    np.testing.assert_array_almost_equal(distances, expected, decimal=5)

# Тест 4: Проверка вычисления ra
def test_calculate_ra():
    parent_window = Mock()
    parent_window.calibration_coefficients = (0.0, 2.0)  # intercept=0, slope=2
    series = QLineSeries()
    # Точки: одна в диапазоне числителя (1350 <= x < 2843.75), другая в диапазоне знаменателя (2843.75 <= x < 3096.175)
    series.append([QPointF(1350, 10), QPointF(2844, 20)])  # ch0=1350, ch2=2843.75, ch3=3096.175
    parent_window.alfa_series_dict = {"Rn1": series}
    calculate_ra(parent_window)
    assert hasattr(parent_window, 'ra_value')
    np.testing.assert_almost_equal(parent_window.ra_value, 0.5, decimal=5)  # 10 / 20 = 0.5

# Тест 5: Проверка вычисления am_rate и k1p9
def test_calculate_am_rate_and_k1p9():
    parent_window = Mock()
    parent_window.calibration_coefficients = (0.0, 2.0)  # intercept=0, slope=2
    series = QLineSeries()
    series.append([QPointF(1350, 100), QPointF(2000, 200)])  # ch0=1350, ch2=2843.75
    parent_window.alfa_series_dict = {"Am241_1": series}
    parent_window.alfa_data_arrays = {"Am241_1.xlsx": (1350, 200)}
    calculate_am_rate(parent_window)
    assert hasattr(parent_window, 'am_rate_value')
    np.testing.assert_almost_equal(parent_window.am_rate_value, 1.5, decimal=5)  # (100 + 200) / 200 = 1.5
    calculate_k1p9(parent_window)
    assert hasattr(parent_window, 'k1p9_value')
    np.testing.assert_almost_equal(parent_window.k1p9_value, 568.0, decimal=5)  # (1.5 / 852)^(-1) = 568