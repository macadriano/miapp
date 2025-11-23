# Script PowerShell para descargar modelo de Sofia

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "DESCARGAR MODELO DE VECTORIZACION PARA SOFIA" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Este script descargara el modelo de sentence-transformers" -ForegroundColor Yellow
Write-Host "para que Sofia funcione offline sin necesidad de internet." -ForegroundColor Yellow
Write-Host ""
Write-Host "IMPORTANTE: Necesitas tener conexion a internet para descargar." -ForegroundColor Red
Write-Host ""

# Descargar modelo
python manage.py descargar_modelo

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "DESCARGA COMPLETADA" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan

Read-Host "Presiona Enter para continuar"

