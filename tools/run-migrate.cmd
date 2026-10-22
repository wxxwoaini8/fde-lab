@echo off
chcp 65001 >nul
title CodeBuddy migration
echo.
echo  ============================================
echo   CodeBuddy CN data migration to D drive
echo  ============================================
echo.
echo  Make sure CodeBuddy CN is fully closed
echo  (including the tray icon).
echo.
pause
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0migrate-codebuddy.ps1"
