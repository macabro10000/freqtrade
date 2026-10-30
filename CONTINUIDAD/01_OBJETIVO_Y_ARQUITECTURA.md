# 01 — Objetivo y arquitectura prevista

## 1. Qué estamos construyendo

ALFA OMEGA Trading AI es un sistema de investigación y análisis cuantitativo centrado inicialmente en BTCUSD. Debe reunir datos de mercado, comprobar su calidad, ejecutar investigaciones reproducibles, comparar estrategias y producir señales evaluadas bajo riesgo controlado.

No se reduce a un indicador gráfico. El indicador de TradingView es una representación visual experimental y secundaria.

## 2. Flujo lógico previsto

```
Proveedores de mercado / histórico
             |
             v
Ingesta y almacenamiento verificable
             |
             v
Catálogo de datasets y metadatos
             |
             v
Validación de calidad e integridad
             |
             v
Normalización por símbolo y temporalidad
             |
             v
Motor de investigación y backtesting
             |
             v
Comparación de estrategias y validación fuera de muestra
             |
             v
Análisis de riesgo y modo paper
```

Este diagrama expresa la arquitectura objetivo; no afirma que todos los módulos estén implementados.

## 3. Datos que deben distinguirse

- **BTC/USD:** instrumento cotizado directamente contra USD en el proveedor correspondiente.
- **BTC/USDT:** instrumento cotizado contra USDT. No tratarlo como idéntico a BTC/USD sin documentar diferencias de precio, liquidez y proveedor.
- **Spot:** mercado al contado.
- **Futuros/perpetuos:** instrumentos derivados. Funding, open interest, basis y liquidaciones pertenecen a esta categoría y no deben mezclarse con OHLCV spot como si fueran el mismo mercado.

Cada dataset debe declarar como mínimo:
- proveedor y endpoint o método de obtención;
- símbolo exacto y tipo de mercado;
- temporalidad;
- timestamp y zona horaria (preferiblemente UTC);
- columnas y unidades;
- inicio y fin del histórico;
- frecuencia esperada y huecos detectados;
- fecha de descarga y versión del proceso;
- licencia/condiciones de uso cuando corresponda.

## 4. Estrategias a investigar

La investigación puede incluir, sin asumir rentabilidad:
- estructura de mercado: swing highs/lows, BOS y CHOCH;
- liquidez: equal highs/lows, sweeps y zonas de stops;
- Fair Value Gaps y desplazamiento;
- volumen y volumen relativo;
- tendencia, momentum y volatilidad;
- VWAP y medias móviles;
- rupturas, retrocesos y rangos;
- confluencias multi-temporalidad;
- modelos estadísticos y reglas híbridas.

Smart Money Concepts es una familia de hipótesis y reglas; cada regla debe definirse operacionalmente para poder probarla. No aceptar explicaciones visuales subjetivas como evidencia de ventaja estadística.

## 5. Protocolo de validación

- Separar entrenamiento, validación y prueba temporal (sin fuga de información).
- Incluir comisiones, spread y slippage razonables del proveedor/mercado.
- Evitar look-ahead bias y repainting.
- Medir número de operaciones, retorno, drawdown, profit factor, expectancy, tasa de acierto y exposición.
- Comparar contra benchmarks simples.
- Probar distintos periodos y regímenes de mercado.
- Hacer walk-forward o validación fuera de muestra antes de aceptar una estrategia.
- Conservar resultados negativos y parámetros exactos para evitar selección sesgada.

## 6. Seguridad y operación

El proyecto permanece en investigación/paper. No conectar claves con permisos de trading real, no activar ejecución real y no desplegar automatización financiera hasta completar una revisión independiente y autorización expresa. La arquitectura debe permitir modo solo lectura para datos y paper trading aislado.

## 7. Restricción económica

La fase actual debe ejecutarse sin gasto. Priorizar herramientas, cuotas gratuitas y datos públicos que permitan uso legítimo. No proponer una opción de pago como requisito oculto. Si una capacidad no puede lograrse gratuitamente, documentar el límite y detenerse antes de generar cargos.
