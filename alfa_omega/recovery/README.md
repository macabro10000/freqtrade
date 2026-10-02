# RECOVERY

La recuperación de entorno es infraestructura auxiliar, no el motor de trading.

MASTER_RECOVERY.py se conserva por trazabilidad y reconstrucción de Colab, pero no debe generar señales, entrenar modelos ni ejecutar operaciones.

La arquitectura nueva no depende de ejecutar MASTER_RECOVERY.py para analizar datos o hacer backtesting.

Cualquier recuperación futura debe restaurar el estado sin alterar la lógica de investigación.
