# 03 — Historial del proyecto y decisiones

## 1. Visión desde el principio

El proyecto ALFA OMEGA busca construir una capacidad de análisis y trading algorítmico que pueda estudiar el mercado, descubrir y comparar estrategias y mejorar con pruebas. BTCUSD es el foco de datos de esta etapa. La intención no es producir gráficos bonitos ni acumular indicadores sin validación.

La investigación debe apoyarse en datos históricos, datos recientes, análisis multi-temporalidad y pruebas reproducibles. Las estrategias deben competir con criterios medibles y no por impresiones visuales.

## 2. Evolución del trabajo

### Etapa A — Plataforma de trading e investigación
- Repositorio de trabajo: `macabro10000/freqtrade`.
- Rama de trabajo: `alfa-omega-rebuild`.
- Entorno concebido para investigación y paper trading.
- BTC/USD y XAU/USD aparecen en el alcance histórico.
- Se estableció que LIVE debía permanecer bloqueado.

### Etapa B — Datos de mercado
- Se investigó cómo obtener histórico BTCUSD y datos para análisis.
- Se mencionaron fuentes y lectores relacionados con Alpaca, Kraken, Binance y datasets/Hugging Face.
- Se trabajó desde Google Colab y Android, sin asumir ordenador personal.
- Se señaló que un archivo descargado en Colab podía ser temporal.
- Se identificó como posible almacenamiento el repositorio privado `Macabro10000/trading-data`, pendiente de verificación de acceso y contenido.
- Se insistió en poder consultar los datos desde un chat nuevo sin volver a descargarlos manualmente.

### Etapa C — Investigación de estrategias
Se solicitó investigar Smart Money Concepts y otras familias de estrategias, incluyendo entradas/salidas, liquidez, estructura y confirmaciones. La intención es mejorar reglas a partir de evidencia, no declarar que una estrategia está entrenada o es potente sin pruebas.

### Etapa D — Indicador auxiliar TradingView
Se creó/modificó `alfa_omega/tradingview/ALFA_OMEGA_BTCUSD_SMC_Experimental.pine` como indicador visual experimental.
- Se ajustó la lógica para permitir que el FVG direccional aparezca después del sweep y dentro de una ventana de confirmación, en lugar de exigir todos los eventos en la misma vela.
- Se añadió un README con limitaciones y protocolo de validación.
- El indicador no es el objetivo central ni el motor de trading.
- No se ha demostrado compilación ni rentabilidad.

## 3. Decisiones vigentes

1. Prioridad actual: conectar y catalogar los datos BTCUSD/BTCUSDT disponibles.
2. No reiniciar el proyecto ni duplicar lectores existentes.
3. Auditar antes de modificar.
4. TradingView queda como herramienta auxiliar de visualización/contraste.
5. Diferenciar estrictamente BTC/USD, BTC/USDT, spot y derivados.
6. Mantener paper-only; LIVE bloqueado.
7. Trabajar sin coste.
8. Registrar decisiones, resultados y cambios en GitHub para permitir continuidad entre chats.

## 4. Registro de commits conocidos

Los siguientes commits se habían registrado para el indicador en la rama `alfa-omega-rebuild`:
- `1d4ade1beb2f17b4f3ea25fc520fc2439c96b153` — ajuste de lógica del FVG después del sweep.
- `15ac5e7bacd8284774d852cb83259a0bceda5be0` — README de validación del indicador.

Estos SHA son antecedentes de commits conocidos, no una afirmación de que el segundo siga siendo el HEAD actual. Verificar el historial real de la rama antes de cualquier cambio.

## 5. Cambios de objetivo que deben evitarse

No volver a convertir el trabajo principal en:
- crear otro Pine Script;
- diseñar alertas sin resolver la disponibilidad de datos;
- hacer un dashboard que no tenga conexión demostrada;
- afirmar que una consulta puntual a Binance equivale a una base de datos;
- entrenar o declarar ganadora una estrategia sin protocolo y resultados reproducibles.

La documentación de continuidad existe para impedir esos desvíos.
