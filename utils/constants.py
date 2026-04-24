"""
Constantes do projeto De Ponta Chat Intelligence.
"""

# ============================================================
# Bling API
# ============================================================

BLING_BASE_URL = "https://www.bling.com.br/Api/v3"

TOKEN_EXPIRY_SECONDS = 21600  # 6 horas

# Limite máximo de itens por página na API do Bling
BLING_PAGE_LIMIT = 100

# ============================================================
# Mapeamento de lojas (canal de venda)
# ============================================================

LOJAS = {
    203925713: "PDV",        # Stop Gallery — loja física
    205259157: "E-commerce",  # Bagy
}

# Inverso para lookup por nome
LOJAS_POR_NOME = {v: k for k, v in LOJAS.items()}

# ============================================================
# Situações de pedido
# ============================================================

SITUACOES_PEDIDO = {
    6: "Em aberto",
    9: "Atendido",
    12: "Cancelado",
    15: "Em andamento",
    18: "Venda Agenciada",
    21: "Em digitação",
    24: "Verificado",
    410580: "Consig. Aberta",
    410581: "Consig. Finalizada",
    422511: "Devolução",
    735798: "Pagamento aprovado",
    735799: "Em devolução",
}

# Situações que representam vendas efetivas (não canceladas/devolvidas)
SITUACOES_VENDA_EFETIVA = {6, 9, 15, 18, 24, 410580, 735798}

# Situações excluídas de cálculos de faturamento
SITUACOES_EXCLUIDAS = {12, 422511, 735799}

# ============================================================
# Intermediador (para confirmação de canal)
# ============================================================

CNPJ_BAGY = "21.345.139/0001-47"
