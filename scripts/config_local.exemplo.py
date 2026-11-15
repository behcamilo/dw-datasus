"""Modelo do config_local.py (fora do git). Copie para config_local.py e troque o sal.

Gerar um sal: python -c "import secrets; print(secrets.token_hex(16))"
O sal não pode mudar depois de gerar a origem: ele define o hash dos documentos de pessoas.
"""

SAL_HASH_PII = "troque-por-um-valor-aleatorio-e-fixo"
