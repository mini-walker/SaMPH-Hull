@echo off
echo =============================================
echo Cleaning old build and dist folders...
echo =============================================

if exist EXE\build rmdir /s /q EXE\build
if exist EXE\dist rmdir /s /q EXE\dist
if exist SaMPH.spec del SaMPH.spec

echo.
echo =============================================
echo Running PyInstaller (ONEDIR - Faster mode)...
echo =============================================

REM =====================================================
REM ONEDIR Build configuration
REM =====================================================

pyinstaller ^
  --clean ^
  --onedir ^
  --windowed ^
  --name "SaMPH" ^
  --contents-directory "SaMPH_Internal" ^
  --workpath "EXE/build" ^
  --distpath "EXE/dist" ^
  --paths "src" ^
  --add-data "src/SaMPH_Images;SaMPH/SaMPH_Images" ^
  --hidden-import "matplotlib" ^
  --hidden-import "matplotlib.pyplot" ^
  --hidden-import "matplotlib.backends.backend_agg" ^
  --hidden-import "latex2mathml" ^
  --hidden-import "latex2mathml.converter" ^
  --hidden-import "scipy.special.cython_special" ^
  --collect-data "matplotlib" ^
  --collect-data "latex2mathml" ^
  --collect-data "reportlab" ^
  --exclude-module "tkinter" ^
  --exclude-module "IPython" ^
  --exclude-module "pandas" ^
  --exclude-module "setuptools" ^
  --icon "src/SaMPH_Images/planing-hull-app-logo.ico" ^
  src/Main.py

echo.
echo =============================================
echo Copying external resources to dist folder...
echo =============================================

REM Copy usr directory to dist/SaMPH/usr
if not exist "EXE\dist\SaMPH\usr" mkdir "EXE\dist\SaMPH\usr"
xcopy "usr" "EXE\dist\SaMPH\usr" /E /I /Y

REM Copy Examples to dist/SaMPH/Examples
if not exist "EXE\dist\SaMPH\Examples" mkdir "EXE\dist\SaMPH\Examples"
xcopy "Examples" "EXE\dist\SaMPH\Examples" /E /I /Y

echo.
echo =============================================
echo Build finished (ONEDIR mode)
echo Main EXE: %CD%\EXE\dist\SaMPH\SaMPH.exe
echo Distribute the entire folder: %CD%\EXE\dist\SaMPH\
echo =============================================
echo.
echo Benefits of ONEDIR:
echo - Much faster startup (3-5x)
echo - Smaller overall size
echo - Only ~30-50 MB total
echo =============================================

pause
