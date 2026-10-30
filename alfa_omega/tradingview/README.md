# TradingView — ALFA OMEGA BTCUSD

## Estado del indicador

Archivo: `ALFA_OMEGA_BTCUSD_SMC_Experimental.pine`

- Pine Script v6.
- Indicador visual; no envía órdenes ni conecta una cuenta de exchange.
- Señales evaluadas al cierre de vela.
- Componentes: swings confirmados, BOS/CHOCH, barridos de liquidez, FVG, desplazamiento, filtro de volumen, SL y TP1/TP2/TP3.
- El FVG debe aparecer después del barrido y dentro de la ventana de confirmación configurada.

## Validación pendiente

Este repositorio no ejecuta el compilador de TradingView. Por tanto, el archivo está guardado en GitHub, pero **no se declara compilado ni validado** hasta abrirlo en Pine Editor y añadirlo a un gráfico.

Protocolo mínimo, sin coste:

1. Abrir TradingView y seleccionar el gráfico BTCUSD del proveedor que se vaya a evaluar.
2. Abrir Pine Editor, pegar el contenido del archivo y pulsar Add to chart.
3. Registrar cualquier error de compilación exactamente como aparece.
4. Revisar señales en BTCUSD 15m y 1h; confirmar que solo aparecen al cierre de vela.
5. Crear alertas LONG y SHORT y comprobarlas en modo simulado.
6. Exportar/registrar resultados de backtest independientes antes de considerar cualquier uso operativo.

## Limitaciones conocidas

- No hay todavía backtest validado de este Pine Script.
- El filtro de volumen puede no ser comparable entre proveedores de BTCUSD.
- Los niveles SL/TP muestran los del último setup; no representan una posición abierta ni gestionan salidas.
- El indicador no incluye todavía un motor de sizing, comisiones, slippage ni gestión de posiciones.
- Las cifras preliminares de otras pruebas no deben atribuirse a este indicador.

## Seguridad

Investigación y alertas visuales solamente. No conectar claves API ni activar ejecución automática. No usar con dinero real hasta completar pruebas, costes y validación fuera de muestra.
