# ALFA OMEGA — EXECUTION LAYER

La ejecución forma parte de la arquitectura desde el diseño, pero permanece DESACTIVADA por defecto.

## Modos

### RESEARCH
No envía órdenes a ningún broker/exchange. Se utiliza para backtesting, simulación y descubrimiento.

### PAPER
Puede comunicarse con una cuenta o entorno de práctica compatible con API. Las órdenes son simuladas por el proveedor o por el entorno de paper trading.

### LIVE
Puede enviar órdenes reales. Este modo no está habilitado actualmente.

## Flujo obligatorio

SIGNAL ENGINE
→ RISK ENGINE
→ EXECUTION INTELLIGENCE
→ SAFETY GATE
→ BROKER ADAPTER
→ ORDER
→ EXECUTION LOG
→ RESULT ANALYSIS
→ LEARNING LOOP

## Reglas

1. Ningún modelo envía órdenes directamente.
2. Ningún indicador propietario envía órdenes directamente.
3. El Risk Engine debe aprobar tamaño y riesgo.
4. El Safety Gate debe aprobar la operación antes de LIVE.
5. Las credenciales PAPER y LIVE deben estar separadas.
6. El modo predeterminado es RESEARCH.
7. LIVE requiere activación explícita y controles adicionales.
8. Los resultados PAPER/LIVE pueden alimentar investigación, pero no producen promoción automática de modelos.
9. Toda orden debe ser trazable hasta señal, modelo, versión, mercado y timeframe.
10. Debe existir kill switch.

## Adaptadores

La capa usa un contrato BrokerAdapter para evitar que el núcleo de ALFA OMEGA dependa de un proveedor concreto.

Un adaptador futuro deberá implementar, como mínimo:

- obtener balance;
- obtener posiciones;
- obtener mercado/quotes;
- crear orden;
- cancelar orden;
- consultar orden;
- consultar fills;
- health check;
- normalizar errores;
- registrar latencia y estado.

La implementación concreta del broker/exchange se hará después de seleccionar y validar el entorno PAPER adecuado para BTC/USD y XAU/USD.

## Estado actual

Arquitectura preparada.
RESEARCH: disponible conceptualmente.
PAPER: pendiente de proveedor/adaptador.
LIVE: bloqueado.
