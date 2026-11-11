#!/usr/bin/env bash
set -e

echo "=== Instalando dependências de sistema (GDAL) ==="
sudo apt-get update
sudo apt-get install -y libgdal-dev g++ python3-dev

echo "=== Instalando pacotes Python do requirements.txt ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Instalando binding do GDAL para Python compatível com o sistema ==="
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
pip install GDAL=="$(gdal-config --version).*"

echo "=== Concluído com sucesso! Agora você pode rodar os scripts ==="
