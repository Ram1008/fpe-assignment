@echo off
rem Windows Batch script wrapper to redirect 'make' commands to 'make.ps1'
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0make.ps1" %*
