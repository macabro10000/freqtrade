# MODELOS

Los modelos apoyan la decisión; no generan órdenes por sí mismos.

Separación:
- TRAIN
- VALIDATION
- TEST
- WALK-FORWARD

Salidas posibles:
- probabilidad LONG
- probabilidad SHORT
- probabilidad NO_TRADE
- retorno esperado
- riesgo/volatilidad esperada
- horizonte esperado

Toda predicción debe conservar versión del modelo, periodo de entrenamiento y features utilizadas.
