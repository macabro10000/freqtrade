# SMC

Módulo causal de estructura y liquidez.

Produce features:
- HH
- HL
- LH
- LL
- BOS
- CHOCH
- liquidity sweep
- FVG
- Order Block

Cada detección debe conservar su momento de confirmación. Una estructura confirmada después no puede generar una señal antes de esa confirmación.
