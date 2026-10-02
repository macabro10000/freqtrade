# ALFA OMEGA TRADING

ALFA OMEGA es la capa de investigación, análisis y aprendizaje construida sobre Freqtrade.

## Objetivo
Construir un sistema que procese datos históricos y datos disponibles del mercado, calcule features causales, incorpore SMC/liquidez/FVG/Order Blocks/VWAP/volumen/volatilidad y los 3 indicadores propietarios, entrene ML/FreqAI sin fuga de información, pruebe estrategias, valide fuera de muestra y produzca señales explicables de entrada/salida.

## Mercados de esta fase
- BTC/USD
- XAU/USD

EUR/USD queda fuera de la fase actual hasta nueva decisión explícita.

## Timeframes
Datos: 1m, 5m, 15m, 1h, 4h, 1d, 1w.
Decisión principal: 5m, 15m, 1h, 4h, 1d.

## Arquitectura
DATA → VALIDATION → FEATURES → SMC/LIQUIDITY → PROPRIETARY INDICATORS → MODEL/FreqAI → SIGNAL ENGINE → BACKTEST → WALK-FORWARD → EVALUATION → LEARNING LOOP

## Principios obligatorios
- No look-ahead bias.
- Separación estricta entre train, validation y test.
- Ninguna señal histórica utiliza información futura.
- Los indicadores propietarios son features, no órdenes automáticas.
- El sistema puede decidir NO_TRADE.
- Investigación/backtesting queda separado de ejecución real.
- No se elimina código histórico sin trazabilidad.

## Estado
Esta rama es la reconstrucción limpia. El repositorio contenía principalmente estructura y recuperación de entorno; no contenía una estrategia ALFA OMEGA operativa dentro de user_data/strategies. Primero corregimos arquitectura y contratos; después incorporamos los tres indicadores y los modelos.
