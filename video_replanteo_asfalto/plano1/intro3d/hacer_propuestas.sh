#!/bin/bash
cd "$(dirname "$0")"
python3 propuestas_pcia.py -- --head naranja --out prop_A > prop_A.log 2>&1
python3 propuestas_pcia.py -- --head blanca --out prop_B > prop_B.log 2>&1
blender -b -P propuestas_pcia.py -- --head naranja --out prop_C > prop_C.log 2>&1
echo TERMINADO
