#!/usr/bin/env python
import os
import sys
import subprocess

os.chdir(r'C:\Users\luis1\Desktop\BarberPro-Python')
sys.path.insert(0, r'C:\Users\luis1\Desktop\BarberPro-Python')

print("\n" + "="*60)
print("        🚀 BARBERPRO FASTAPI SERVER")
print("="*60 + "\n")

print("📍 Instalando dependencias...")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"], check=False)

print("✅ Dependencias listas\n")
print("🚀 Iniciando servidor en http://localhost:8000")
print("📚 Documentación en http://localhost:8000/docs\n")
print("="*60 + "\n")

os.system(r'python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload')
