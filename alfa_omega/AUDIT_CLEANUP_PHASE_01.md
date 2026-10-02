# ALFA OMEGA — AUDIT / CLEANUP PHASE 01

## Hallazgos

El repositorio actual es principalmente el núcleo Freqtrade más una estructura ALFA OMEGA todavía incompleta.

Dentro de alfa_omega había:
- README de objetivos.
- configuración de mercados.
- documentación de pipeline/features/SMC/models/backtests.
- MASTER_RECOVERY.py.

No había una implementación operativa de estrategia ALFA OMEGA en user_data/strategies.
Tampoco había modelos FreqAI propios ni módulos reales de features/SMC dentro de alfa_omega.

## Qué se conserva

- Freqtrade como motor de backtesting y futura integración de ejecución.
- MASTER_RECOVERY.py como infraestructura de recuperación, separado del motor.
- estructura alfa_omega.
- documentación y trazabilidad histórica.
- fuentes externas de datos/estado ya existentes.

## Qué se corrige

- EUR/USD queda fuera de la fase actual; el alcance operativo de esta fase es BTC/USD y XAU/USD.
- Se establece alfa_omega/config como fuente de verdad del alcance.
- Se separa recuperación de investigación.
- Se establece el flujo DATA → VALIDATION → FEATURES → SMC/LIQUIDITY → PROPRIETARY → MODEL → SIGNAL → BACKTEST → WALK-FORWARD → EVALUATION.
- Se establece NO_TRADE como salida válida.
- Se exige protección contra look-ahead y validación fuera de muestra.

## Qué NO se hace todavía

- No se inventan los 3 indicadores propietarios.
- No se crean señales artificiales para aparentar que la IA funciona.
- No se entrena un modelo sin datos validados.
- No se activa ejecución real.
- No se elimina código histórico sin trazabilidad.

## Siguiente bloque de construcción

1. incorporar los 3 indicadores reales;
2. definir su contrato de entrada/salida;
3. convertir sus salidas en features causales;
4. implementar validación de datos;
5. implementar SMC/liquidez;
6. construir dataset de entrenamiento;
7. crear baseline de estrategia;
8. conectar FreqAI;
9. backtest y walk-forward.
