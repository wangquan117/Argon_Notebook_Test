@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

rem Drag a MakeCode Arcade .uf2 onto this file (or pass it as an argument).
rem Uses the same options that worked on this board: --madctl 0x40

set "HERE=%~dp0"
set "PYSCRIPT=%HERE%patch_uf2.py"
set "MADCTL=0x40"

if not exist "%PYSCRIPT%" (
  echo [错误] 找不到 "%PYSCRIPT%"
  echo 请把 PATCH_GAME1.bat 和 patch_uf2.py 放在同一文件夹（例如 D:\downlo）。
  echo 下载脚本:
  echo   Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/wangquan117/Argon_Notebook_Test/cursor/st7789-color-fix-2a90/makecode-arcade-st7789/patch_uf2.py" -OutFile "D:\downlo\patch_uf2.py"
  goto :end_fail
)

set "PYEXE="
set "PYOPT="
where py >nul 2>nul
if not errorlevel 1 (
  set "PYEXE=py"
  set "PYOPT=-3"
) else (
  where python >nul 2>nul
  if not errorlevel 1 (
    set "PYEXE=python"
    set "PYOPT="
  )
)

if not defined PYEXE (
  echo [错误] 没有找到 Python。请安装 https://www.python.org/downloads/ 并勾选 Add python.exe to PATH
  echo 不要用 python3（Windows 商店占位符）。
  goto :end_fail
)

if "%~1"=="" (
  echo 用法: 把 MakeCode 下载的 .uf2 拖到 PATCH_GAME1.bat 上。
  echo 或:
  echo   PATCH_GAME1.bat "D:\downlo\arcade-Avoid-the-Fans-2.uf2"
  echo.
  echo 成功后会在原文件旁边生成 文件名-st7789.uf2（MADCTL=%MADCTL%）
  goto :end_fail
)

set "FAIL=0"
:loop
if "%~1"=="" goto :after_loop

set "IN=%~1"
set "EXT=%~x1"
set "NAME=%~n1"

if /I not "%EXT%"==".uf2" (
  echo [跳过] 不是 UF2: "%IN%"
  goto :next
)

echo %NAME% | findstr /I /C:"-st7789" >nul
if not errorlevel 1 (
  echo [跳过] 已经是补丁结果: "%IN%"
  goto :next
)

if not exist "%IN%" (
  echo [错误] 找不到文件: "%IN%"
  set "FAIL=1"
  goto :next
)

set "OUT=%~dpn1-st7789.uf2"
echo.
echo ========== 正在处理 ==========
echo 输入: "%IN%"
echo 输出: "%OUT%"
echo Python: %PYEXE% %PYOPT%
echo MADCTL=%MADCTL%
echo.

if defined PYOPT (
  %PYEXE% %PYOPT% "%PYSCRIPT%" "%IN%" -o "%OUT%" --madctl %MADCTL%
) else (
  %PYEXE% "%PYSCRIPT%" "%IN%" -o "%OUT%" --madctl %MADCTL%
)
if errorlevel 1 (
  echo [失败] "%IN%"
  set "FAIL=1"
) else (
  echo [完成] 请只烧录 "%OUT%" ，不要再烧原来的 MakeCode uf2。
)

:next
shift
goto :loop

:after_loop
echo.
if "%FAIL%"=="1" goto :end_fail
echo 全部完成。BOOTSEL 后把 *-st7789.uf2 拖进 RPI-RP2。
pause
exit /b 0

:end_fail
echo.
pause
exit /b 1
