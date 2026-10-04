# ALFA OMEGA — CONTINUIDAD MAESTRA

> **Propósito:** este archivo es el punto único de continuidad para cualquier chat, agente o sesión que continúe ALFA OMEGA. Debe leerse **antes de modificar código**. Su objetivo es permitir retomar el proyecto como si la sesión anterior siguiera abierta, sin reiniciar el análisis ni inventar estado.

## 0. REGLA PRINCIPAL DE CONTINUIDAD

1. Leer este archivo completo antes de trabajar.
2. Verificar el estado real de GitHub, Actions y Render antes de afirmar que algo funciona.
3. **Nunca inventar** ejecuciones, resultados, secretos, credenciales, despliegues, operaciones de broker ni pruebas físicas.
4. Trabajar sobre el repositorio y rama indicados aquí; no crear otro proyecto/backend/repositorio sin justificación explícita.
5. Después de cada proceso relevante:
   - registrar qué se investigó;
   - qué se encontró;
   - qué se cambió;
   - qué pruebas se ejecutaron;
   - resultado real;
   - commit;
   - siguiente paso.
6. Actualizar este archivo en el mismo repositorio después de cada avance significativo para que el siguiente chat pueda continuar sin perder contexto.
7. Si una ejecución está pendiente, **esperar/verificar** antes de declarar éxito.
8. Si un test falla, investigar la causa raíz y corregirla; no ocultar el fallo ni saltarse la prueba.
9. No hacer cambios destructivos sin advertencia y justificación.
10. Mantener la investigación separada de la ejecución.

---

# 1. IDENTIDAD DEL PROYECTO

- Nombre: **ALFA OMEGA TRADING**
- Repositorio: **macabro10000/freqtrade**
- Rama activa: **alfa-omega-rebuild**
- Objetivo: plataforma de investigación, validación, aprendizaje y ejecución controlada de trading.
- Mercados permitidos actualmente:
  - BTC/USD
  - XAU/USD
- EUR/USD: **excluido** hasta nueva autorización explícita.
- Ejecución: **PAPER únicamente**.
- LIVE: **bloqueado**.
- No se debe convertir el sistema en un robot de trading autónomo sin controles y validaciones.
- La investigación puede funcionar aunque la ejecución esté detenida.

---

# 2. REGLAS DEL USUARIO

## Seguridad y ejecución

- No activar LIVE.
- No ejecutar operaciones reales.
- No automatizar `Robot.ipynb`.
- No realizar BUY/SELL reales.
- Paper Trading debe permanecer separado y protegido.
- "CONECTAR ROBOT" significa autorizar el proceso de evaluación/ejecución, **no comprar inmediatamente**.
- "DETENER EJECUCIÓN" debe detener nuevas entradas, pero la investigación debe continuar.
- Emergency Stop debe ser independiente de la lógica de mercado.
- Una decisión de mercado nunca puede saltarse los controles de seguridad/riesgo.
- No asumir capacidades del broker que no hayan sido comprobadas.
- Nunca guardar secretos en GitHub ni pedir al usuario que publique credenciales.

## Forma de trabajo

- El usuario trabaja principalmente desde Android/Colab y prefiere trabajar directamente sobre GitHub cuando sea posible.
- Una tarea principal a la vez.
- Si el usuario dice **"Siguiente"**, continuar exactamente desde el siguiente paso pendiente.
- Para código solicitado, preferir archivo completo o bloque completo, no parches ambiguos.
- No repetir preguntas cuya respuesta ya está en este archivo.
- No afirmar "hecho" sin evidencia.
- Antes de modificar, inspeccionar el estado real.
- Antes de desplegar, probar.
- Después de desplegar, verificar salud y logs.
- Toda decisión importante debe quedar documentada aquí.

---

# 3. OBJETIVO FUNCIONAL DEL PANEL

El panel debe permitir:

### Investigación
- Investigación continua 24/7.
- Investigación independiente de ejecución.
- Ver estado del investigador.
- Ver ciclos, errores, tareas y última actividad.
- Mantener memoria de experimentos y resultados.

### Ejecución
Selector de temporalidad:
- 1m
- 5m
- 15m
- 1h
- 4h
- 1d

Controles:
- **CONECTAR ROBOT**
- **DETENER EJECUCIÓN**
- Emergency Stop

Estados:
- Research ON/OFF.
- Execution ON/OFF.
- PAPER.
- LIVE siempre bloqueado.

La selección de timeframe de ejecución no debe alterar la jerarquía de contexto MTF.

---

# 4. JERARQUÍA MTF

Jerarquía obligatoria:

**1W → 1D → 4H → 1H → 15M → 5M → 1M**

Reglas:

- Solo usar velas cerradas para contexto superior.
- No lookahead.
- Una vela HTF no puede influir en una decisión LTF antes de estar cerrada.
- Los joins temporales deben ser exactos/causalmente válidos.
- No mezclar información futura durante labels, features, entrenamiento o validación.

Temporalidades primarias:
- 5m
- 15m
- 1h
- 4h
- 1d

Temporalidades disponibles para ejecución:
- 1m
- 5m
- 15m
- 1h
- 4h
- 1d

---

# 5. CICLO DE INVESTIGACIÓN ALFA OMEGA

El proceso conceptual completo es:

OBSERVAR
→ ENTENDER ESTRUCTURA
→ RECONOCER CONTEXTO
→ ANALIZAR LIQUIDEZ
→ BUSCAR PATRONES
→ GENERAR HIPÓTESIS
→ INVESTIGAR
→ BACKTEST
→ OOS
→ WALK-FORWARD
→ COSTOS/SLIPPAGE
→ ESTRÉS DE REGÍMENES
→ VALIDAR
→ MODELOS/ENSEMBLE
→ ¿VENTAJA?
→ NO_TRADE / TRADE
→ RIESGO
→ PAPER
→ RESULTADO
→ ANALIZAR POR QUÉ GANÓ/PERDIÓ
→ MEMORIA
→ APRENDIZAJE
→ REENTRENAMIENTO
→ VALIDACIÓN NUEVA
→ NUEVA VERSIÓN

Importante:

- Una hipótesis no es una verdad.
- Web research es evidencia, no verdad.
- Un backtest favorable no implica ventaja real.
- OOS y walk-forward son obligatorios antes de considerar una hipótesis candidata.
- Los costos, comisiones y slippage deben formar parte de la evaluación.
- Los regímenes adversos deben estresarse.
- Los fallos pueden convertirse en conocimiento negativo y restricciones de regresión.
- La memoria de observaciones no debe convertirse automáticamente en entrenamiento.

---

# 6. COMPONENTES EXISTENTES

Arquitectura relevante ya existente:

- `alfa_omega/features/feature_engine.py`
- `alfa_omega/smc/structure_engine.py`
- `alfa_omega/features/proprietary_engine.py`
- `alfa_omega/intelligence/market_intelligence.py`
- `alfa_omega/intelligence/trade_decision.py`
- `alfa_omega/execution/risk_engine.py`
- `alfa_omega/execution/safety_gate.py`
- `alfa_omega/execution/trade_cycle.py`
- `alfa_omega/intelligence/trade_lifecycle.py`
- `alfa_omega/memory/trade_memory.py`
- `alfa_omega/research/web_research.py`
- `alfa_omega/research/research_orchestrator.py`
- `alfa_omega/research/learning_loop.py`
- `alfa_omega/research/experiment_runner.py`
- módulos de hipótesis/descubrimiento/evaluación
- Triple Barrier
- validación
- walk-forward
- regime stress
- pattern engine

---

# 7. TRIPLE BARRIER Y ANTI-LEAKAGE

Reglas ya establecidas:

- Los labels se calculan sobre la línea temporal completa.
- No recalcular labels después de filtrar de forma que se introduzca información futura.
- No lookahead.
- Joins por timestamp deben respetar causalidad.
- Si TP y SL ocurren en la misma vela, resolver de forma conservadora.
- Horizonte incompleto: tratar como UNRESOLVED/excluir según configuración, no inventar resultado.
- Usar un artefacto común de labels cuando corresponda.
- No permitir que entrenamiento, selección o validación vea información del futuro.

---

# 8. VALIDACIÓN

La validación debe contemplar:

- split temporal;
- purging;
- embargo;
- OOS;
- walk-forward;
- costos;
- slippage;
- estrés por régimen;
- holdout final;
- control de selección múltiple/selection bias;
- evitar que el conjunto de prueba final sea usado para ajustar el modelo.

Un modelo no se considera validado simplemente porque:
- gane en backtest;
- tenga buen Sharpe;
- tenga buen win rate;
- funcione en una muestra histórica.

---

# 9. RIESGO

Configuración de riesgo conocida:

- Riesgo máximo por posición: **0.5%**
- Pérdida diaria máxima: **2%**
- Máximo de posiciones abiertas: **1**
- Máximo notional: **10%**

Principios:

- Dynamic Risk Stop puede gestionar dentro del riesgo permitido, nunca ampliarlo.
- Intelligent Exit puede invalidar la tesis.
- Profit Target es una referencia de salida.
- Emergency Stop tiene prioridad.
- No aumentar riesgo porque un modelo tenga alta confianza.
- No abrir otra posición para recuperar una pérdida automáticamente.

---

# 10. PAPER EXECUTION

Adaptador:

`alfa_omega/execution/alpaca_paper.py`

Características conocidas:

- Paper-only.
- BTC/USD controlado.
- Entry LIMIT.
- Exit MARKET.
- Espera fills.
- Reconciliación.
- Smoke controlado BUY → SELL.
- No asumir bracket/OCO atómico para crypto.
- No LIVE.

Variables conocidas de Render:
- `ALFA_OMEGA_PAPER_EXECUTION_ENABLE=true`
- `ALFA_OMEGA_PAPER_SMOKE_TEST_ENABLE=true`
- LIVE permanece bloqueado.

El smoke test no debe declararse ejecutado sin evidencia real.

---

# 11. CONTROL PLANE IMPLEMENTADO

Archivos:

- `alfa_omega/control/__init__.py`
- `alfa_omega/control/control_state.py`
- `alfa_omega/control/control_service.py`
- `alfa_omega/control/control_store.py`
- `tests/alfa_omega/test_control_plane.py`
- `tests/alfa_omega/test_control_store.py`

Estado permitido:

- Markets: BTC/USD, XAU/USD.
- Timeframes: 1m, 5m, 15m, 1h, 4h, 1d.
- Mode: PAPER.

Defaults:

- research_enabled=True
- execution_enabled=False
- selected_market=BTC/USD
- execution_timeframe=5m
- mode=PAPER
- kill_switch=True
- live_execution_enabled=False

**Nota importante:** el campo `kill_switch` tiene una semántica histórica particular en esta implementación: el estado normal permitido usa `True`; activar el kill switch cambia el valor a `False` y desactiva ejecución. No renombrar/reinterpretar sin revisar todos los tests y consumidores.

ControlService:

- get_state
- snapshot
- set_market
- set_timeframe
- connect_execution
- stop_execution
- set_research
- activate_kill_switch

Concurrencia:
- RLock.

Persistencia:
- MongoDB si está configurado.
- process-local como fallback controlado.

---

# 12. CONTROL STATE PERSISTENTE

Archivo:

`alfa_omega/control/control_store.py`

Incluye:

- `ControlStateConflict`
- `ControlStateStore` Protocol
- `InMemoryControlStateStore`
- `MongoControlStateStore`

Variables:

- `ALFA_OMEGA_CONTROL_MONGODB_URI`
- fallback `MONGODB_URI`
- DB default: `trading_system`
- collection: `control_state`

Usa versionado/optimistic concurrency.

Dependencia agregada:
- `pymongo>=4.15,<5.0`

---

# 13. API DEL CONTROL PLANE

En `alfa_omega/render_service.py`:

- GET `/api/v1/control/state`
- POST `/api/v1/control/market`
- POST `/api/v1/control/timeframe`
- POST `/api/v1/control/execution/connect`
- POST `/api/v1/control/execution/stop`

También:

- `/api/v1/status` incluye snapshot de control.

Mutaciones requieren:
- `ALFA_OMEGA_CONTROL_TOKEN`
- comparación segura con `hmac.compare_digest`.

Las mutaciones del control plane **no llaman al broker**.

No convertir `/api/v1/status` en un endpoint gigante de control.

---

# 14. RESEARCH RUNTIME 24/7

Archivos:

- `alfa_omega/research/runtime.py`
- `alfa_omega/research/runtime_store.py`
- `alfa_omega/research/worker.py`
- `tests/alfa_omega/test_research_runtime.py`
- `tests/alfa_omega/test_research_runtime_store.py`

El runtime actual:

- es independiente de FastAPI;
- no envía órdenes;
- no activa ejecución;
- consulta el ControlService;
- planifica tareas de investigación;
- registra heartbeat;
- registra ciclos;
- registra errores;
- puede detenerse limpiamente.

**Estado actual importante:** todavía NO es aprendizaje autónomo completo. El runtime actual planifica tareas y registra actividad; aún falta conectar de forma real el ciclo con experimentos, backtests, OOS, walk-forward, costos, validación, resultados y aprendizaje persistente.

---

# 15. DURABLE RESEARCH STORE

`MongoResearchRuntimeStore`:

- URI: `ALFA_OMEGA_CONTROL_MONGODB_URI` o `MONGODB_URI`
- DB: `ALFA_OMEGA_RESEARCH_DB`, default `trading_system`
- Collection: `ALFA_OMEGA_RESEARCH_COLLECTION`, default `research_runtime`
- lease: `RESEARCH_LEASE`
- status: `RESEARCH_STATUS`

Tiene:
- acquire_lease
- renew_lease
- release_lease
- save_status
- load_status

Pendiente de endurecimiento:
- carrera entre dos workers nuevos puede producir DuplicateKeyError en adquisición inicial;
- worker usa actualmente algunos métodos/atributos privados de ResearchRuntime;
- conviene usar `asdict()` para persistencia del dataclass;
- validar explícitamente intervalos y TTL.

---

# 16. RESEARCH WORKER

Archivo:

`alfa_omega/research/worker.py`

Es el entrypoint pensado para un proceso persistente de investigación.

Variables:
- `ALFA_OMEGA_RESEARCH_WORKER_ID`
- `ALFA_OMEGA_RESEARCH_INTERVAL_SECONDS`
- `ALFA_OMEGA_RESEARCH_LEASE_TTL_SECONDS`

El worker:
- adquiere lease;
- ejecuta ciclos;
- guarda estado;
- renueva lease;
- libera lease al salir.

Pendiente:
- refactorizar acceso a privados del runtime;
- endurecer validaciones;
- endurecer adquisición de lease;
- añadir endpoint de estado de research;
- tests adicionales;
- conectar con investigación real.

---

# 17. RENDER

Servicio web actual:

- Nombre: `alfa-omega-trading`
- URL: `https://alfa-omega-trading.onrender.com`
- Service ID: `srv-dasi2d942hec73812jpg`
- Start:
  `uvicorn alfa_omega.render_service:app --host 0.0.0.0 --port $PORT`
- Build:
  `pip install --upgrade pip && pip install -r requirements.txt`

Endpoints existentes conocidos:

- `/`
- `/health`
- `/api/v1/status`
- `/api/v1/account`
- `/api/v1/positions`
- `/api/v1/market/btc-usd`
- `/api/v1/data/btc-usd`
- `/api/v1/data/btc-usd/multi-timeframe`
- `/api/v1/execution`
- `/api/v1/execution/paper-smoke`
- `/ready`

Arquitectura deseada:
- FastAPI/web = panel/API.
- Research worker = proceso separado.
- No poner un while-loop 24/7 dentro de FastAPI.

IMPORTANTE:
- El usuario no tiene tarjeta de crédito.
- No crear ni asumir recursos Render de pago.
- Antes de desplegar un worker persistente, verificar las capacidades/precios actuales de Render.
- Se puede construir y probar el worker en GitHub antes de desplegarlo.

---

# 18. GITHUB ACTIONS — ESTADO REAL DOCUMENTADO

Workflow:

`.github/workflows/alfa-omega-research.yml`

Historial reciente relevante:

- Run #188 — tests 121/121 pasaron; Ruff falló.
- Run #189 — tests 121/121 pasaron; Ruff falló.
- Run #190 — tests 121/121 pasaron; Ruff falló por `I001` en `control_state.py`.
- Corrección posterior:
  - commit `4a42d5880852600d3d931247a1412d03f0c7eeab`
  - mensaje: `fix: satisfy control state import formatting`
- Run #191 fue creado para ese commit y al momento de escribir esta actualización estaba **in_progress**.

**NO declarar Run #191 exitoso hasta volver a consultar GitHub.**

Run histórico estable:
- Run #153
- ID `37089522090`
- commit `862b0e73432fbcd232841075c84c7443b076126b`
- tests + Ruff OK
- commit: `chore: add controlled Paper smoke trigger workflow`

---

# 19. QUÉ FALTA

Prioridad inmediata:

1. Verificar Run #191.
2. Si falla, leer logs exactos y corregir causa raíz.
3. Cuando CI esté verde, endurecer Research Worker:
   - API pública de parada/señales;
   - eliminar acceso a privados;
   - validación interval/TTL;
   - lease race-safe;
   - `asdict(status)`.
4. Añadir GET `/api/v1/research/status`.
5. Añadir tests del endpoint y estados.
6. Verificar integración Mongo.
7. Diseñar/implementar el adaptador que conecte el runtime con el pipeline real de experimentación.
8. Hacer que un ciclo de research produzca resultados verificables:
   - hipótesis;
   - dataset;
   - experimento;
   - backtest;
   - OOS;
   - walk-forward;
   - costos;
   - régimen;
   - métricas;
   - decisión;
   - artefactos;
   - memoria.
9. Implementar aprendizaje real y versionado de modelos, no un simple loop.
10. Construir panel web.
11. Verificar despliegue del worker según plan Render disponible.
12. Integrar Paper de forma controlada.
13. Pruebas end-to-end.
14. Solo después considerar cualquier ampliación de ejecución.

---

# 20. ORDEN DE TRABAJO OBLIGATORIO

Cada nueva sesión debe seguir:

**SELECT → RECOVER → VERIFY → AUDIT → REPAIR/PREPARE → TEST → STATUS → NEXT**

### SELECT
Confirmar:
- repo;
- rama;
- objetivo;
- tarea inmediata.

### RECOVER
Leer este archivo y revisar:
- último commit;
- últimos tests;
- últimos errores;
- pendientes.

### VERIFY
Consultar GitHub/Actions/Render cuando aplique.

### AUDIT
Inspeccionar archivos afectados antes de tocar código.

### REPAIR/PREPARE
Hacer el cambio mínimo correcto, preferiblemente completo y coherente.

### TEST
Ejecutar/consultar pruebas reales.

### STATUS
Registrar resultado real.

### NEXT
Solo entonces avanzar.

---

# 21. REGISTRO DE ACTUALIZACIONES

## 2026-10-04 — Continuidad maestra creada

Se estableció este archivo como fuente de continuidad para futuros chats.

Se documentó:
- reglas del usuario;
- arquitectura;
- mercados;
- temporalidades;
- seguridad;
- control plane;
- persistencia Mongo;
- research runtime;
- worker;
- Render;
- Paper;
- validación;
- anti-leakage;
- riesgo;
- historial de CI;
- pendientes.

Último cambio de código conocido:
- commit `4a42d5880852600d3d931247a1412d03f0c7eeab`
- corrección de formato Ruff en `control_state.py`
- Run #191 creado y pendiente de verificación.

## REGLA PARA FUTURAS ACTUALIZACIONES

Cada chat/agente que modifique ALFA OMEGA debe agregar una nueva entrada aquí con:

- fecha;
- objetivo;
- investigación realizada;
- archivos modificados;
- decisión técnica;
- tests;
- resultado;
- commit;
- estado de CI;
- estado de Render si aplica;
- pendientes;
- siguiente acción.

Nunca borrar el historial anterior salvo que exista una razón explícita de mantenimiento. Preferir agregar información y corregir contradicciones indicando la fecha de corrección.

---

# 22. MENSAJE DE ARRANQUE PARA CUALQUIER CHAT

Al abrir una nueva sesión, leer este archivo y comenzar con:

> "He recuperado ALFA OMEGA desde ALFA_OMEGA_CONTINUITY.md. Primero voy a verificar el estado real de GitHub/CI y el último proceso registrado; no asumiré resultados. Continuaré exactamente desde el siguiente pendiente."

Después:
1. consultar el estado real;
2. comparar con este documento;
3. corregir cualquier divergencia;
4. continuar desde "QUÉ FALTA".

---

# 23. PRINCIPIO FINAL

**ALFA OMEGA no se considera terminado porque el código compile.**

Debe demostrar, progresivamente:

**datos correctos → causalidad → hipótesis → investigación → backtest → OOS → walk-forward → costos → estrés → validación → ventaja → riesgo → paper → resultado → explicación → memoria → aprendizaje validado → nueva versión.**

La prioridad es construir un sistema verificable, reproducible, seguro y capaz de aprender de forma real, no aparentar que aprende.
