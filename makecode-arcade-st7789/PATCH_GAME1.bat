@echo off
setlocal EnableDelayedExpansion

rem Drag a MakeCode Arcade .uf2 onto this BAT, or pass the path as %1.
rem Same flags as the working PowerShell command: --madctl 0x40

set "HERE=%~dp0"
set "PYSCRIPT=%HERE%patch_uf2.py"
set "MADCTL=0x40"

if not exist "%PYSCRIPT%" (
  echo ERROR: patch_uf2.py not found next to PATCH_GAME1.bat
  echo Put both files in the same folder, e.g. D:\downlo
  goto FAIL
)

set "PYEXE="
set "PYOPT="
where py >nul 2>&1
if not errorlevel 1 (
  set "PYEXE=py"
  set "PYOPT=-3"
) else (
  where python >nul 2>&1
  if not errorlevel 1 (
    set "PYEXE=python"
    set "PYOPT="
  )
)

if not defined PYEXE (
  echo ERROR: Python not found. Install from python.org and check Add python.exe to PATH.
  echo Do not use python3 on Windows.
  goto FAIL
)

if "%~1"=="" (
  echo Usage: drag a MakeCode .uf2 onto PATCH_GAME1.bat
  echo    or: PATCH_GAME1.bat "D:\downlo\arcade-Avoid-the-Fans-2.uf2"
  echo Output: same folder, name-st7789.uf2  MADCTL=%MADCTL%
  goto FAIL
)

set "FAIL=0"

:LOOP
if "%~1"=="" goto DONE

set "IN=%~1"
set "EXT=%~x1"
set "BN=%~n1"

if /I not "%EXT%"==".uf2" (
  echo SKIP not uf2: "%IN%"
  goto NEXT
)

if /I "!BN:~-7!"=="-st7789" (
  echo SKIP already patched: "%IN%"
  goto NEXT
)

if not exist "%IN%" (
  echo ERROR missing: "%IN%"
  set "FAIL=1"
  goto NEXT
)

set "OUT=%~dpn1-st7789.uf2"
echo.
echo ===== patching =====
echo IN : "%IN%"
echo OUT: "%OUT%"
echo MADCTL=%MADCTL%
echo.

if defined PYOPT (
  %PYEXE% %PYOPT% "%PYSCRIPT%" "%IN%" -o "%OUT%" --madctl %MADCTL%
) else (
  %PYEXE% "%PYSCRIPT%" "%IN%" -o "%OUT%" --madctl %MADCTL%
)
if errorlevel 1 (
  echo FAILED "%IN%"
  set "FAIL=1"
) else (
  echo OK flash only "%OUT%"
)

:NEXT
shift
goto LOOP

:DONE
echo.
if "%FAIL%"=="1" goto FAIL
echo All done. Output is about 4MB (E14 pad). BOOTSEL and copy *-st7789.uf2 to RPI-RP2.
echo Wait until RPI-RP2 disappears. Do not unplug early.
pause
exit /b 0

:FAIL
echo.
pause
exit /b 1
