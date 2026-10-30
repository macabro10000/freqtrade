# 04 — Plan de trabajo y auditoría

## Principio

Seguir desde el estado real del repositorio. Primero inspección de solo lectura; después propuesta de cambios; finalmente modificación pequeña y verificable. No construir un componente nuevo si ya existe uno equivalente.

## Fase 1 — Auditoría de repositorios y código existente

Estado: PENDIENTE.

1. Confirmar rama actual y SHA HEAD de `macabro10000/freqtrade`.
2. Obtener inventario del árbol del repositorio y localizar:
   - conectores y lectores de mercado;
   - scripts de descarga y normalización;
   - catálogos/manifiestos de datasets;
   - adaptadores Alpaca, Kraken, Binance y Hugging Face;
   - tareas de Colab;
   - pruebas y documentación;
   - configuraciones de paper/live.
3. Identificar duplicados y dependencias antes de proponer cambios.
4. Revisar secretos y evitar exponer valores sensibles.

**Salida exigida:** inventario con ruta, propósito, estado, evidencia y reutilización recomendada.

## Fase 2 — Verificar almacenamiento BTCUSD

Estado: PENDIENTE.

1. Localizar y confirmar el nombre exacto del repositorio privado de datos.
2. Comprobar permiso de lectura real; no confundir instalación del conector con acceso a un repositorio específico.
3. Inventariar archivos sin modificarlos.
4. Determinar formato (CSV, Parquet, SQLite u otro), tamaño, símbolo, mercado, proveedor y temporalidad.
5. Leer muestras y calcular:
   - filas y rango temporal;
   - timestamps duplicados;
   - velas ausentes;
   - valores nulos/no numéricos;
   - OHLC inválido;
   - volumen negativo o anómalo;
   - frecuencia y zona horaria.
6. Separar BTC/USD de BTC/USDT y spot de derivados.

**Salida exigida:** catálogo de datasets con hashes o identificadores, cobertura temporal y reporte de calidad.

## Fase 3 — Conexión de consulta de solo lectura

Estado: PENDIENTE.

1. Revisar si ya hay lector reutilizable.
2. Definir una interfaz de consulta pequeña y documentada.
3. Consultar rango temporal y temporalidad sin alterar archivos.
4. Verificar paginación, límites, errores y consistencia.
5. Probar que el acceso funciona desde el entorno real del proyecto.
6. Documentar actualización de datos y límites gratuitos.

**Salida exigida:** prueba reproducible de lectura y ejemplo de consulta con conteos/rango. No declarar conexión por una consulta aislada a una API pública.

## Fase 4 — Investigación y backtesting

Estado: PENDIENTE.

1. Definir formalmente las reglas de cada estrategia.
2. Construir baseline simple.
3. Evitar look-ahead, repainting y leakage.
4. Incluir comisiones, spread y slippage.
5. Separar muestras por tiempo y realizar pruebas fuera de muestra.
6. Medir expectancy, profit factor, drawdown, retorno, tasa de acierto, número de operaciones y exposición.
7. Comparar SMC con momentum, tendencia, ruptura, reversión a la media, VWAP y otras hipótesis.
8. Guardar configuración, dataset, commit, logs y resultados de cada experimento.

**Salida exigida:** informe reproducible por estrategia. Ningún resultado aislado constituye garantía de rentabilidad.

## Fase 5 — Simulación y controles de riesgo

Estado: PENDIENTE DE AUDITORÍA.

- Confirmar configuración paper y bloqueo LIVE en código y entorno.
- Confirmar límites de posición, pérdida diaria y exposición.
- Simular fallos de datos, reconexión, órdenes rechazadas y límites de API.
- No activar dinero real.

## Fase 6 — TradingView auxiliar

Estado: PENDIENTE DE VALIDACIÓN MANUAL.

El Pine experimental solo se revisa después de resolver la prioridad de datos y el motor de investigación, salvo que una prueba concreta requiera contrastar una señal visual.

## Protocolo de cada sesión

Al empezar:
1. Leer `00_LEER_PRIMERO.md` y los otros documentos.
2. Verificar rama y HEAD actual.
3. Revisar los últimos commits y cambios.
4. Identificar el último hito demostrado.
5. Continuar una sola tarea principal.

Al terminar:
1. Ejecutar pruebas pertinentes y registrar comandos/salidas reales.
2. Revisar diff y archivos afectados.
3. Actualizar estado e historial.
4. Registrar SHA del commit y enlaces.
5. Indicar con claridad si se necesita intervención manual del propietario.

## Condiciones de aceptación

Una tarea solo se marca VERIFICADA cuando existe evidencia repetible. Si falta acceso, datos, permisos o ejecución, marcar BLOQUEADO o PENDIENTE y explicar exactamente qué falta. No fabricar porcentajes de avance.

## Próxima acción

**Auditoría de solo lectura de todo el código de datos en `alfa-omega-rebuild` y verificación del repositorio de datos histórico.** No crear otro downloader ni otro indicador antes de completar ese inventario.
