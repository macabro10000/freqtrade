# ALFA OMEGA — OBS-2026-11-02-001
## Observación de mercado en vivo y auditoría de continuidad

- Fecha/hora de referencia de los tickers Binance: 2026-11-02 00:49:12 UTC (2026-11-01 19:49:12 America/Bogota).
- Tipo: observación puntual, NO backtest, NO entrenamiento de modelo, NO orden ejecutada.
- Modo: solo investigación; no abrir posiciones.
- Repositorio: macabro10000/freqtrade.
- Rama de registro: alfa-omega-rebuild.
- Fuente de precios: Binance USDⓈ-M Futures.
- Instrumentos: BTCUSDT (proxy, no idéntico a BTCUSD) y XAUUSDT TRADIFI_PERPETUAL (no idéntico a XAUUSD spot/CFD).

## 1. Snapshot de precio
| Instrumento | Último precio consultado | Mark price | Index price |
|---|---:|---:|---:|
| BTCUSDT | 78,117.50 | 78,126.08057759 | 78,162.46300000 |
| XAUUSDT TRADIFI_PERPETUAL | 3,908.39 | 3,908.49239032 | 3,904.70848771 |

## 2. Contexto multitemporal — velas cerradas
Los EMA se calcularon sobre las series descargadas en esta observación; son aproximaciones de contexto y no señales autónomas. No se utilizaron velas HTF incompletas como confirmación.

### BTCUSDT
- 15m: último cierre observado 78,081.40; EMA20 78,002.03; EMA50 77,944.86; rango alto/bajo de las últimas 20 velas cerradas: 78,488.80 / 77,561.90.
- 1h: último cierre 78,313.00; EMA20 77,899.77; EMA50 77,928.75.
- 4h: último cierre 78,313.00; EMA20 78,183.43; EMA50 79,214.25.
- 1d: último cierre diario completo 78,313.00; EMA20 80,447.38; EMA50 80,081.18.
- 1w: última semana completa cerró 78,313.00; rango de esa semana 81,953.70 / 76,270.00. La semana nueva estaba en formación.

Lectura: rebote de corto plazo por encima de EMA20/EMA50 en 15m y 1h, pero precio por debajo de EMA50 en 4h y por debajo de ambas EMA diarias. Contexto mixto; el rebote intradía no confirma cambio de tendencia mayor.

### XAUUSDT TRADIFI_PERPETUAL
- 15m: último cierre observado 3,903.38; EMA20 3,899.63; EMA50 3,895.69; rango alto/bajo de las últimas 20 velas cerradas: 3,912.10 / 3,888.16.
- 1h: último cierre 3,906.89; EMA20 3,893.62; EMA50 3,905.40.
- 4h: último cierre 3,906.89; EMA20 3,922.90; EMA50 3,975.90.
- 1d: último cierre diario completo 3,906.89; EMA20 4,041.84; EMA50 4,155.04.
- 1w: última semana completa cerró 3,906.89; rango de esa semana 4,089.05 / 3,881.02. La semana nueva estaba en formación.

Lectura: recuperación intradía por encima de las EMA cortas de 15m y 1h, pero sigue muy por debajo de las medias de 4h y diario. No hay confirmación de reversión de la estructura superior.

## 3. Decisión de la prueba
**BTCUSDT: ESPERAR / NO ENTRAR.**
**XAUUSDT TradFi: ESPERAR / NO ENTRAR.**

Motivos:
- Las temporalidades cortas muestran recuperación, pero las superiores mantienen resistencia/tendencia bajista relativa.
- No se confirmó en esta observación una señal completa del baseline de sweep + cierre de vuelta + rechazo + volumen relativo.
- No se ha calculado aquí una entrada con stop/objetivos que tenga ventaja estadística demostrada.
- No se proporcionan niveles de entrada ficticios ni se fuerza una operación.

## 4. Evidencia positiva
- Se pudo consultar ticker, mark price e index price para ambos instrumentos.
- Se alineó contexto semanal, diario, 4h, 1h y 15m.
- Se evitó usar la vela semanal nueva todavía abierta como confirmación.
- Se detectó divergencia útil entre rebote de corto plazo y estructura de mayor temporalidad.

## 5. Evidencia negativa / limitaciones
- BTCUSDT es proxy de BTCUSD, no el contrato BTCUSD COIN-M ni necesariamente el mercado spot del usuario.
- XAUUSDT TradFi no es XAUUSD spot/CFD; no extrapolar niveles directamente.
- No se consultó XAUUSD auténtico en esta observación.
- No hay aquí cálculo de expectancy, win rate, profit factor, drawdown ni costes; por tanto esto no demuestra edge.
- No se guardaron las velas crudas de esta consulta ni se ejecutó un backtest.
- Las cotizaciones son un snapshot puntual, no streaming tick-a-tick.

## 6. Auditoría de continuidad GitHub
- Se verificó que existen las ramas `develop` y `alfa-omega-rebuild`.
- `alfa_omega/recovery/MASTER_RECOVERY.py` existe en ambas ramas.
- El archivo de recuperación declara el repositorio `macabro10000/freqtrade`, la rama `develop`, mercados `BTCUSD` y `XAUUSD`, temporalidades 1m/5m/15m/1h/4h/1d/1w, y referencias a Hugging Face Dataset `Macabro10000/trading-data`, MongoDB `trading_system.system_status` y servicio Render.
- La búsqueda de commits mostró como último commit visible `fe62845828e4c4c14bc7f69889253b43b5d30863` con mensaje `test: cover research status endpoint`, fechado 2026-10-04T11:34:30Z.
- Esta inspección NO demuestra que las credenciales externas estén disponibles ni que el dataset/MongoDB/Render estén conectados actualmente.
- Tampoco se confirmó en esta revisión un registro consolidado previo de resultados buenos/malos de cada experimento. Este archivo crea un registro puntual en la rama de trabajo; no reemplaza ni modifica el sistema de recuperación.

## 7. Próximas mejoras
1. Auditar la estructura completa de `alfa-omega-rebuild` antes de crear nuevos módulos o duplicar componentes.
2. Identificar el registro central de experimentos y enlazar cada resultado a datos, parámetros, commit y código exacto.
3. Persistir datasets versionados con fuente, símbolo, contrato, temporalidad, rango UTC, checksum y validación de huecos/duplicados.
4. Repetir la prueba con XAUUSD auténtico y BTCUSD del contrato exacto, sin mezclar proxies.
5. Ejecutar backtest multitemporal fuera de muestra, con comisiones, slippage, funding y reglas de sesión.
6. Mantener la decisión NO ENTRAR como resultado válido cuando no haya confirmación.

---
Registro de investigación. No constituye asesoramiento financiero ni una orden de trading.
