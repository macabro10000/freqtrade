# SAFETY GATE

El Safety Gate es la última barrera antes de enviar una orden.

## Debe comprobar

- modo de ejecución;
- mercado permitido;
- credencial/proveedor permitido para ese modo;
- estado del broker;
- balance disponible;
- exposición actual;
- número de posiciones abiertas;
- riesgo por operación;
- pérdida diaria;
- límites de tamaño;
- stop-loss válido;
- coherencia de dirección;
- frescura de datos;
- latencia;
- ausencia de estado inconsistente;
- kill switch.

## LIVE

LIVE debe permanecer bloqueado mientras:

- no exista adaptador PAPER validado;
- no exista evidencia OOS/walk-forward suficiente;
- no exista control de riesgo probado;
- no exista monitoreo;
- no exista procedimiento de apagado;
- no exista separación de credenciales.

## Principio

Una señal puede ser válida y aun así ser rechazada por el Safety Gate.

Ejemplo:

SIGNAL = LONG
MODEL = aprobado
SETUP = válido
RISK = aceptable

pero:

SPREAD = excesivo

→ NO EXECUTE.

El Safety Gate protege la ejecución; no decide si una estrategia es buena.
