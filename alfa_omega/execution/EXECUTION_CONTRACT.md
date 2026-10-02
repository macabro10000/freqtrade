# EXECUTION CONTRACT

## Objetivo

Definir el contrato entre el motor de decisión y cualquier broker/exchange sin permitir que el modelo tenga acceso directo a credenciales u órdenes.

## OrderIntent

Una señal aprobada produce una intención de orden con:

- intent_id
- timestamp
- market
- timeframe
- side: LONG | SHORT
- order_type
- entry_reference
- stop_loss
- take_profits
- quantity
- risk_fraction
- signal_id
- model_id
- model_version
- feature_version
- regime
- reason
- confidence
- expected_return
- expected_risk
- expected_horizon

## ExecutionResult

Toda orden produce:

- execution_id
- intent_id
- provider
- mode
- status
- provider_order_id
- requested_quantity
- filled_quantity
- average_fill_price
- fees
- slippage
- latency_ms
- rejection_reason
- timestamps

## Seguridad

El modelo no recibe API keys.
El Signal Engine no llama al broker.
El Risk Engine no llama directamente al broker.
Solamente el Broker Adapter autorizado puede comunicarse con el proveedor.

## Estados

CREATED
→ RISK_APPROVED
→ SAFETY_APPROVED
→ SUBMITTED
→ PARTIALLY_FILLED
→ FILLED
→ CANCELLED | REJECTED | FAILED

## Aprendizaje

ExecutionResult puede convertirse en datos de investigación después de validación y etiquetado.

Nunca se debe modificar retrospectivamente una operación para mejorar artificialmente un dataset.
