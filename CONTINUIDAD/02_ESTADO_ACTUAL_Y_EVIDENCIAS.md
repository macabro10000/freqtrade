# 02 — Estado actual y evidencias

**Última actualización documental:** 2026-10-30  
**Repositorio:** `macabro10000/freqtrade`  
**Rama objetivo:** `alfa-omega-rebuild`

> Esta ficha distingue hechos verificados en GitHub de antecedentes de conversaciones que requieren repetición. No equivale a una auditoría completa del repositorio.

## 1. Evidencia comprobada en esta revisión

| Elemento | Estado | Evidencia |
|---|---|---|
| Rama `alfa-omega-rebuild` | VERIFICADO | La búsqueda de ramas de GitHub devolvió esa rama. |
| Pine experimental | VERIFICADO | Se pudo leer `alfa_omega/tradingview/ALFA_OMEGA_BTCUSD_SMC_Experimental.pine`. |
| SHA del blob Pine | VERIFICADO | `2ba29f076709b0ffb4c1b1c75481e7600484e311`. |
| README de TradingView | VERIFICADO | Se pudo leer `alfa_omega/tradingview/README.md`. |
| SHA del blob README | VERIFICADO | `00f06438021804ee3a2c6189de6bec9aa6a78d76`. |
| Validación del Pine en TradingView | PENDIENTE | No se ejecutó Pine Editor ni se recibió resultado de compilación. |
| Conexión persistente al repositorio de datos | NO COMPROBADO | No se confirmó acceso/lectura del repositorio privado de datos. |
| Histórico BTCUSD almacenado y catalogado | NO COMPROBADO | No se inspeccionó el almacenamiento persistente. |
| Consulta Binance BTCUSDT 15m | PARCIAL | Se ejecutó una consulta de 1.000 velas en esta conversación; no equivale a persistencia ni a BTC/USD. |

## 2. Antecedentes de conversaciones que deben revalidarse

Se había informado anteriormente:
- Un repositorio privado llamado `Macabro10000/trading-data`.
- Lectores existentes para Alpaca BTC/USD, Hugging Face, datasets y catálogos.
- Una descarga histórica de Kraken BTCUSD en Google Colab, descrita como temporal.
- Consultas anteriores de aproximadamente 8.701 velas de 15m y 1.500 velas de 1h.
- Consultas de métricas de derivados: open interest, taker, funding y basis.

Estos puntos son **ANTECEDENTES NO REVALIDADOS** en esta revisión. No afirmar que los archivos siguen disponibles, que el repositorio es accesible o que los conteos son actuales.

La búsqueda de repositorios instalados por el término `trading-data` no devolvió resultados. Esto no demuestra que el repositorio no exista; solo que no fue localizado por esa búsqueda. Comprobar acceso y nombre exacto mediante el propietario antes de concluir.

## 3. TradingView — estado del artefacto secundario

Archivo: `alfa_omega/tradingview/ALFA_OMEGA_BTCUSD_SMC_Experimental.pine`

El código leído declara Pine Script v6 y un indicador visual. Incluye lógica experimental relacionada con swings, BOS/CHOCH, barridos de liquidez, FVG, desplazamiento, volumen y niveles SL/TP.

Limitaciones documentadas:
- No se ha demostrado que compile.
- No hay backtest validado de este archivo.
- No ejecuta órdenes ni conecta una cuenta de exchange.
- SL/TP representan niveles del último setup, no una gestión real de posición.
- No incorpora motor de sizing, comisiones, slippage ni gestión completa de operaciones.

El README de ese directorio ya establece un protocolo de validación manual. No crear otro indicador ni reescribirlo sin auditoría y necesidad demostrada.

## 4. Trading y riesgo

Contexto histórico del proyecto:
- BTC/USD y XAU/USD.
- Entorno paper-only.
- LIVE bloqueado.
- Parámetros históricos mencionados: riesgo de posición 0,5%, límite diario 2%, una posición y notional máximo 10%.

Estos parámetros deben verificarse en la configuración real antes de tratarlos como controles activos. No son autorización para operar.

## 5. Qué no se puede afirmar

A la fecha de esta ficha no se puede afirmar:
- que la base de datos BTCUSD esté conectada;
- que todos los datos históricos estén persistidos;
- que los datos de BTCUSDT sean intercambiables con BTCUSD;
- que el Pine Script esté compilado o sea rentable;
- que exista una estrategia ganadora validada;
- que el trading real esté habilitado o deba habilitarse.

## 6. Evidencias y enlaces

- Rama: https://github.com/macabro10000/freqtrade/tree/alfa-omega-rebuild
- Directorio TradingView: https://github.com/macabro10000/freqtrade/tree/alfa-omega-rebuild/alfa_omega/tradingview
- Pine experimental: https://github.com/macabro10000/freqtrade/blob/alfa-omega-rebuild/alfa_omega/tradingview/ALFA_OMEGA_BTCUSD_SMC_Experimental.pine
- README TradingView: https://github.com/macabro10000/freqtrade/blob/alfa-omega-rebuild/alfa_omega/tradingview/README.md

Actualizar esta ficha únicamente con resultados repetibles y evidencia (comando, fecha, salida, archivo/commit).
