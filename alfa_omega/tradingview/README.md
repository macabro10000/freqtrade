# TradingView — ALFA OMEGA BTCUSD

## Estado del indicador

Archivo: `alfa_omega/tradingview/ALFA_OMEGA_BTCUSD_SMC_Experimental.pine`

- Pine Script v6, indicador visual; no envía órdenes.
- Señales y eventos de estructura confirmados al cierre de vela.
- Swings confirmados, BOS/CHOCH y sesgo estructural.
- Barridos de liquidez con niveles previos a la vela actual.
- FVG de tres velas y filtro de desplazamiento.
- FVG direccional debe aparecer después del barrido.
- Equal Highs / Equal Lows mediante tolerancia ATR.
- Últimos Order Blocks aproximados: última vela contraria anterior al BOS, con búsqueda limitada.
- Filtro opcional de tendencia HTF usando exclusivamente la vela HTF anterior cerrada.
- Filtro opcional de premium/discount basado en el último swing high/low confirmado.
- Puntuación de confluencia de 0 a 100. **No es una probabilidad de ganar.**
- Niveles indicativos de entrada, SL y TP1/TP2/TP3 calculados con ATR.

## Validación pendiente

El repositorio no ejecuta el compilador de TradingView. El código guardado no se declara compilado hasta abrirlo en Pine Editor y añadirlo a un gráfico.

Protocolo manual sin coste:
1. Abrir BTCUSD en el proveedor exacto que se vaya a estudiar.
2. Abrir Pine Editor, pegar el contenido del archivo y pulsar Add to chart.
3. Registrar cualquier error de compilación exactamente.
4. Probar 5m, 15m y 1h, inicialmente con los filtros opcionales desactivados.
5. Comprobar que EQH/EQL y Order Blocks aparecen solo al confirmarse el evento.
6. Comprobar alertas en modo simulado.
7. Comparar señales con el motor Python y backtesting independiente.

## Limitaciones conocidas

- No hay todavía backtest validado de este Pine Script.
- No debe confundirse BTCUSD spot con BTCUSD_PERP COIN-M ni con BTCUSDT USD-M.
- El filtro de volumen depende del proveedor y del tipo de mercado.
- Order Blocks son una definición mecánica aproximada, no prueba de actividad institucional.
- El score representa confluencia de reglas, no probabilidad calibrada.
- SL/TP muestran niveles del último setup; no gestionan una posición abierta.
- No incorpora sizing, comisiones, slippage ni ejecución.
- Los datos HTF usan la última vela cerrada y por ello tienen un retraso intencional.

## Seguridad

Investigación y alertas visuales solamente. No conectar claves API ni activar ejecución automática. No usar con dinero real hasta completar compilación, pruebas, costes y validación fuera de muestra.
