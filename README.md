# Radiation Detector Calibration System

> Desktop application for calibration of Alpha, Beta, and Gamma radiation detectors, developed as a bachelor's diploma project in collaboration with **Mikasensor LLC**.

---

## Overview

This application automates the calibration workflow for dosimetric equipment. It connects to physical detectors via **Modbus RTU** over a serial interface, reads raw spectral data, and applies mathematical models to produce calibration curves for three radiation types.

The system was built for real production use and is capable of handling measurement data from actual radioactive reference sources (Am-241, Sr/Y-90, Cs-137 and others).

---

## Features

- **Live spectrum acquisition** via Modbus RTU (RS-485/RS-232)
- **Alpha, Beta, Gamma calibration** — separate mathematical models per radiation type
- **Spectrum visualization** — interactive charts with logarithmic scale toggle
- **Spectrum arithmetic** — sum multiple measurement files into a composite spectrum
- **Background subtraction** — fon (background) measurement isolation
- **Calibration dialog** — visual alignment of reference source peaks with channel markers
- **Configurable serial connection** — port, baud rate, parity, stop bits, timeout via settings dialog
- **Excel export** — measurement data saved as `.xlsx` for further analysis

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| GUI framework | PyQt6 |
| Charts | PyQt6.QtCharts |
| Hardware communication | pymodbus (Modbus RTU) |
| Data processing | pandas, numpy |
| File I/O | openpyxl |

---

## Project Structure

```
Diploma/
├── main.py                  # Main window, UI orchestration, spectrum loading
├── Beta_math.py             # Beta calibration logic and calibration dialog
├── gamma_math.py            # Gamma calibration calculations
├── fon_math.py              # Background (fon) spectrum processing
├── math_utils.py            # Shared mathematical utilities
├── modbus.py                # Modbus RTU client wrapper
├── settings_dialog.py       # Serial connection settings UI
├── side_window_filler.py    # Side panel UI population
├── spectrum_addition.py     # Spectrum summation feature
├── lib/
│   └── Pictures/            # Application icons and images
└── requirements.txt
```

---

## Getting Started

### Prerequisites

```bash
Python 3.11+
```

### Installation

```bash
git clone https://github.com/Mush9643/Diploma.git
cd Diploma
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running

```bash
python main.py
```

### Hardware Setup

Connect a compatible radiation detector via RS-485/RS-232 adapter. Configure the serial port parameters in the **Settings** dialog (default: COM3, 115200 baud, 8N1).

---

## Calibration Workflow

1. Load measurement files from the target folder
2. Select spectra for reference isotopes (e.g. Am-241 and Sr/Y-90 for Beta calibration)
3. Open the **Calibration** dialog — the system highlights reference peaks with red markers
4. Confirm calibration — coefficients are computed and stored
5. Export results to Excel

---

## Background

Developed as a bachelor's degree final project in **Software Engineering**. The application was subsequently adopted for internal use at **Mikasensor LLC** (Minsk, Belarus), a company specializing in radiation measurement instrumentation.

---

## License

This project is not currently open-sourced for external contributions. The code is shared for portfolio and demonstration purposes.
