# PIPELINE ALFA OMEGA

1. DATA — ingestión de OHLCV y fuentes auxiliares disponibles.
2. VALIDATION — timestamps, orden, duplicados, gaps, OHLC y cobertura.
3. FEATURES — precio, volumen, volatilidad, VWAP y contexto.
4. SMC — HH/HL/LH/LL, BOS, CHOCH, liquidez, FVG y Order Blocks.
5. PROPRIETARY — los 3 indicadores convertidos en features causales.
6. MODEL — ML/FreqAI.
7. SIGNAL — LONG, SHORT o NO_TRADE.
8. BACKTEST — entradas, stops, objetivos y salidas.
9. WALK_FORWARD — entrenamiento y evaluación temporal fuera de muestra.
10. EVALUATION — métricas por mercado, timeframe y régimen.
11. LEARNING LOOP — incorporación controlada de nuevos resultados.

Ninguna fase puede ocultar información futura a una fase anterior.
