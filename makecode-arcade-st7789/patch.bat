@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%~dp0patch_uf2.py" %*
  goto :after
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python "%~dp0patch_uf2.py" %*
  goto :after
)

echo 没有找到 Python。请先安装 https://www.python.org/downloads/
echo 安装时勾选 "Add python.exe to PATH"。
echo 不要用 python3：Windows 上它经常是空的微软商店跳转，不会真正运行脚本。
exit /b 1

:after
if errorlevel 1 (
  echo.
  echo 补丁失败。请把上面的红色/英文报错整段复制下来。
  pause
  exit /b 1
)
echo.
echo 完成后当前文件夹应出现 *-st7789.uf2
dir /b *-st7789.uf2
pause
