<p align="center">
  <img src="src/SaMPH_Images/planing-hull-app-logo.png" alt="SaMPH-Hull Logo" width="180"/>
</p>

<h1 align="center">SaMPH-Hull</h1>

<p align="center">
  <strong>Savitsky Method for Planing Hull Hydrodynamic Analysis</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#methodology">Methodology</a> •
  <a href="#screenshots">Screenshots</a> •
  <a href="#citation">Citation</a> •
  <a href="#license">License</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52?logo=qt&logoColor=white" alt="PySide6"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License MIT"/>
  <img src="https://img.shields.io/badge/platform-Windows%20|%20macOS%20|%20Linux-lightgrey" alt="Platform"/>
</p>

---

## Overview

**SaMPH-Hull** is a desktop application for the hydrodynamic performance analysis of high-speed planing hulls. It implements the well-established **Savitsky empirical method** to predict resistance, trim, sinkage, and wake characteristics of planing craft in calm water — all wrapped in a modern, user-friendly GUI.

> **Why SaMPH-Hull?**  
> CFD simulations take hours; SaMPH-Hull delivers validated results in **milliseconds**, making it ideal for preliminary design, parametric studies, and classroom teaching.

---

## Features

### 🚀 Core Analysis
- **Full Savitsky method implementation** — automatic equilibrium trim finding via numerical root-solving (`scipy.optimize.brentq`)
- **Resistance decomposition** — hydrodynamic, spray (whisker), and air drag components
- **Wake profile calculation** — based on Savitsky & Michael (2010)
- **Wetted surface, center of pressure, and sinkage** estimation

### 🖥️ Modern GUI
- Dark-themed, professional interface built with **PySide6 / Qt6**
- **Tabbed workflow**: Home → Input → Results
- Interactive **charts** with tooltips (QtCharts)
- Real-time **input validation** and speed preview
- Comprehensive **log console** and status bar

### 📊 Flexible I/O
- **Discrete-speed mode** — analyse specific speed points
- **Continuous-speed mode** — define a range with increment
- **Excel import/export** (`openpyxl`) with formatted templates
- **PDF report generation** (`reportlab`) with charts and tables
- One-click copy/open of result file paths

### 🤖 AI Assistant
- Built-in **AI chat panel** (supports OpenAI-compatible endpoints)
- Automatic **result evaluation** — sends hull parameters and outputs to the LLM for design feedback
- Chat history management with persistent storage
- Markdown, LaTeX, and code-highlighted rendering in chat bubbles

### 🌐 Multilingual
- English / 中文 interface with auto-detection based on system locale
- Dynamic language switching at runtime

---

## Installation

### Prerequisites

- **Python 3.8+** (3.10+ recommended)
- **pip** package manager

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/SaMPH-Hull.git
cd SaMPH-Hull

# Create a virtual environment (recommended)
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch the application
python src/Main.py
```

### Build Standalone Executable (Windows)

```bash
# Single-file EXE
Generate_single_exe.bat

# One-directory bundle (faster startup)
Generate_onedir_exe.bat
```

The compiled output is placed in the `dist/` folder.

---

## Quick Start

1. **Launch** the application — you will be greeted by the Home page.
2. **Click** *"New Input"* to open the Input page.
3. **Enter hull parameters** or **import** an Excel template from the `Examples/` folder:

   | Parameter          | Example Value |
   | ------------------ | ------------- |
   | Ship Length *L*    | 8.0 m         |
   | Ship Beam *B*      | 1.6 m         |
   | Mass               | 3 017 kg      |
   | Deadrise Angle *β* | 20°           |
   | LCG from Transom   | 3.28 m        |
   | VCG from Keel      | 0.47 m        |
   | Draft              | 0.40 m        |
   | Speed Range        | 5 – 16 m/s    |

4. **Click** *"Perform Calculation"*.
5. **View** interactive result charts (Resistance, Trim, Sinkage, etc.) in the Results tabs.
6. **Export** results to Excel or generate a PDF report.

### Example Input Files

Ready-to-use Excel templates are provided in the `Examples/` directory:

| File                            | Description                         |
| ------------------------------- | ----------------------------------- |
| `input_example.xlsx`            | Discrete-speed input template       |
| `input_example_continuous.xlsx` | Continuous-speed range template     |
| `input_GPPH.xlsx`               | Generic Prismatic Planing Hull case |
| `input_Southampton_Type_C.xlsx` | Southampton Type C hull case        |

---

## Methodology

SaMPH-Hull solves for the **equilibrium planing condition** by simultaneously satisfying vertical force balance and pitching moment balance:

### Governing Equations

| Equation                                                                                   | Description                      |
| ------------------------------------------------------------------------------------------ | -------------------------------- |
| $C_{L_0} = \tau^{1.1} \left(0.012\lambda^{0.5} + \frac{0.0055\lambda^{2.5}}{C_v^2}\right)$ | Lift coefficient (zero deadrise) |
| $C_{L_\beta} = C_{L_0} - 0.0065\beta \cdot C_{L_0}^{0.60}$                                 | Deadrise correction              |
| $D_f = \frac{\rho V_m^2 \lambda B^2 C_f}{2\cos\beta}$                                      | Frictional drag                  |
| $R_T = R_{\text{hydro}} + R_{\text{spray}} + R_{\text{air}}$                               | Total resistance                 |

### Solution Workflow

```
For each speed V:
  1. Compute beam Froude number  Cv = V / √(g·B)
  2. Assume trim angle τ
  3. Solve for lift coefficient CL₀ and wetted-length ratio λ
  4. Calculate lift, drag, center of pressure
  5. Evaluate pitching moment about CG
  6. Iterate τ (Brent's method) until moment ≈ 0
  7. Record equilibrium Rt, τ, sinkage, wake profile
```


---

## Project Structure

```
SaMPH-Hull/
├── src/
│   ├── Main.py                          # Application entry point
│   ├── Savitsky_Method/
│   │   └── Savitsky_Calculation.py      # Core Savitsky equations & solver
│   ├── SaMPH_GUI/
│   │   ├── GUI_SaMPH.py                # Main window assembly
│   │   ├── Page_Home.py                # Home / welcome page
│   │   ├── Page_Input.py               # Hull parameter input form
│   │   ├── Page_Result.py              # Interactive result charts
│   │   ├── Item_Right_AIChat.py        # AI chat panel
│   │   ├── Item_SettingPage.py         # Settings dialog
│   │   ├── Language_Manager.py         # i18n manager
│   │   ├── Theme_SaMPH.py             # Global QSS stylesheet
│   │   └── Item_*.py                   # Toolbar, menubar, sidebar, etc.
│   ├── SaMPH_Operations/
│   │   ├── Operation_Computing.py      # Calculation controller & threading
│   │   ├── Operation_InputPage.py      # Import/export Excel logic
│   │   ├── Operation_GenerateReport.py # PDF report generation
│   │   └── Operation_*.py             # Other business logic
│   ├── SaMPH_AI/
│   │   ├── Operation_Chat_Controller.py # AI backend communication
│   │   └── Operation_Bubble_Message.py  # Chat bubble rendering
│   ├── SaMPH_Utils/
│   │   └── Utils.py                    # Paths, LaTeX rendering, helpers
│   └── SaMPH_Images/                   # Icons, logos, backgrounds
├── Examples/                            # Sample Excel input files
├── usr/                                 # User data, settings, chat history
├── requirements.txt                     # Python dependencies
├── Generate_single_exe.bat              # PyInstaller single-file build
├── Generate_onedir_exe.bat              # PyInstaller one-dir build
└── README.md
```

---

## Applicability & Limitations

### ✅ Valid Range

- **Hull type**: Prismatic planing surfaces with flat transom
- **Deadrise angle**: 10° – 30°
- **Beam Froude number**: C_v > 1.0 (planing regime)
- **Trim angle**: 0.5° – 15°

### ⚠️ Not Captured

- Irregular hull geometry (variable deadrise, stepped hulls)
- Waves / seaway effects
- Appendage drag (shafts, struts, rudders)
- Propeller–hull interaction
- Dynamic stability

---

## Future Roadmap

- [ ] Integration of additional empirical methods (Blount & Fox, Zarnick)
- [ ] Automated hull form optimisation module
- [ ] Seaway / added-resistance module
- [ ] Appendage drag library
- [ ] 3D hull & wake visualisation
- [ ] Systematic series database support

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

**Author**: Shanqin Jin  
**Affiliation**: Memorial University of Newfoundland  
**Contact**: sjin@mun.ca

This software was developed as part of research in high-speed marine vessel hydrodynamics at Memorial University of Newfoundland. The implementation is based on publicly available research and validated against published experimental data.

---

<p align="center">
  <sub>Made with ❤️ for the naval architecture community</sub>
</p>
