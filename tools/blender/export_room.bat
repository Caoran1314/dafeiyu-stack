@echo off
REM 重新生成房型 room.glb（双击即可）
set BLENDER=%LOCALAPPDATA%\Programs\Blender Foundation\Blender 4.5\blender.exe
set OUT=%~dp0..\..\plugins\dafeiyu_room\pages\room\model\room.glb
"%BLENDER%" --background --python "%~dp0build_room.py" -- --out "%OUT%"
echo.
echo 导出完成: %OUT%
pause
