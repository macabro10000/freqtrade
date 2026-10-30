# ALFA OMEGA — CONTINUIDAD
## Leer primero al abrir un chat nuevo

Este directorio conserva el contexto operativo del proyecto ALFA OMEGA Trading AI para continuar el trabajo sin reiniciar, duplicar componentes ni confundir prototipos con sistemas validados.

### Instrucciones para el nuevo chat

1. Lee este archivo completo.
2. Lee `01_OBJETIVO_Y_ARQUITECTURA.md`.
3. Lee `02_ESTADO_ACTUAL_Y_EVIDENCIAS.md`.
4. Lee `03_HISTORIAL_DE_DECISIONES.md`.
5. Lee `04_PLAN_DE_TRABAJO_Y_AUDITORIA.md`.
6. Antes de modificar código, inspecciona la rama y los archivos actuales. No asumas que el estado documentado sigue siendo el HEAD actual.
7. Actualiza esta documentación al terminar cada hito verificable.

### Objetivo principal

Conectar de forma fiable datos históricos y recientes de BTCUSD/BTCUSDT con ALFA OMEGA, construir un proceso reproducible de investigación de estrategias, comparar resultados con costes realistas y conservar el sistema en simulación hasta superar validaciones independientes.

**TradingView es una herramienta auxiliar. No es el producto ni el objetivo principal.**

### Estado resumido

- Repositorio principal: `macabro10000/freqtrade`.
- Rama de trabajo documentada: `alfa-omega-rebuild`.
- Área de TradingView: `alfa_omega/tradingview/` (experimental y secundaria).
- La conexión persistente con el repositorio de datos BTCUSD no está certificada.
- Se ha consultado Binance para BTCUSDT 15m; esto no demuestra conexión a una base persistente ni equivalencia exacta con BTCUSD.
- No hay evidencia suficiente para declarar el indicador Pine compilado ni validado.
- No activar trading real. No añadir gastos, servicios de pago ni APIs de pago.

### Reglas obligatorias

- No inventar avances, permisos, pruebas, métricas ni porcentajes.
- No empezar desde cero: auditar primero lo que existe.
- No duplicar lectores, conectores, datasets o pipelines.
- No modificar `main`; trabajar en la rama indicada y revisar el HEAD antes de cada cambio.
- No debilitar ni borrar pruebas para conseguir un resultado verde.
- Separar claramente datos spot BTCUSD, spot BTCUSDT y derivados.
- Registrar proveedor, símbolo, temporalidad, zona horaria, rango temporal y momento de descarga.
- Mantener credenciales y secretos fuera del repositorio.
- Coste objetivo: cero. No contratar ni activar recursos de pago.
- Cualquier paso que requiera intervención manual del propietario debe indicarse de forma explícita.

### Cómo informar el progreso

Usar estados: **VERIFICADO**, **PARCIAL**, **PENDIENTE**, **BLOQUEADO** o **NO COMPROBADO**. No usar porcentajes globales salvo que exista una lista de tareas definida y evidencia para calcularlos.

### Próximo paso exacto

Realizar una auditoría de solo lectura de la rama y del código de datos existente. Localizar el repositorio de datos privado mencionado en conversaciones anteriores, comprobar permisos reales y catalogar el histórico BTCUSD/BTCUSDT antes de construir o modificar otro conector.
