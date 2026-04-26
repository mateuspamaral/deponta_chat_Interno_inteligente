"""
Definições de tools no formato JSON Schema para o Groq (OpenAI-compatible).
Cada tool corresponde a uma função em tools/*.py.
"""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "calcular_faturamento",
            "description": (
                "Calcula o faturamento da De Ponta Hemp Shop em um período. "
                "Retorna faturamento (soma de totalProdutos, sem frete), quantidade de pedidos, "
                "ticket médio e frete total. Use para perguntas sobre receita, vendas totais, "
                "faturamento diário/semanal/mensal. "
                "IMPORTANTE: faturamento usa totalProdutos (receita de produto), não o total que inclui frete."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "data_inicio": {
                        "type": "string",
                        "description": "Data inicial no formato YYYY-MM-DD",
                    },
                    "data_fim": {
                        "type": "string",
                        "description": "Data final no formato YYYY-MM-DD",
                    },
                    "canal": {
                        "type": "string",
                        "enum": ["PDV", "E-commerce"],
                        "description": "Filtrar por canal: 'PDV' (balcão físico) ou 'E-commerce' (Bagy). Omitir para todos.",
                    },
                },
                "required": ["data_inicio", "data_fim"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_pedidos",
            "description": (
                "Busca pedidos de venda no período. Retorna lista com id, data, canal, valor, "
                "situação e nome do cliente. Use para listar pedidos, ver pedidos pendentes, "
                "ou buscar pedidos específicos por canal ou situação."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "data_inicio": {
                        "type": "string",
                        "description": "Data inicial no formato YYYY-MM-DD",
                    },
                    "data_fim": {
                        "type": "string",
                        "description": "Data final no formato YYYY-MM-DD",
                    },
                    "canal": {
                        "type": "string",
                        "enum": ["PDV", "E-commerce"],
                        "description": "Filtrar por canal. Omitir para todos.",
                    },
                    "situacao": {
                        "type": "string",
                        "enum": [
                            "Em aberto", "Atendido", "Cancelado", "Em andamento",
                            "Venda Agenciada", "Em digitação", "Verificado",
                            "Pagamento aprovado", "Em devolução",
                        ],
                        "description": "Filtrar por situação do pedido. Omitir para todas.",
                    },
                },
                "required": ["data_inicio", "data_fim"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_estoque_critico",
            "description": (
                "Busca produtos com estoque baixo (igual ou abaixo do limite mínimo). "
                "Identifica itens com risco de ruptura de estoque com breakdown por depósito. "
                "Use para perguntas sobre estoque baixo, risco de faltar produto, "
                "sugestão de reposição. "
                "Depósitos disponíveis: 14887895820 (Loja Física), 14887895821 (Distribuição)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limite_minimo": {
                        "type": "integer",
                        "description": "Estoque mínimo para considerar crítico. Default: 5.",
                    },
                    "id_deposito": {
                        "type": "integer",
                        "enum": [14887895820, 14887895821],
                        "description": (
                            "Filtrar por depósito específico. "
                            "14887895820 = Loja Física (balcão), "
                            "14887895821 = Distribuição (armazém). "
                            "Omitir para considerar todos os depósitos."
                        ),
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_margem_produtos",
            "description": (
                "Calcula e rankeia produtos por margem bruta (receita - custo). "
                "Retorna top N produtos com receita, custo, margem absoluta e percentual. "
                "Use para perguntas sobre rentabilidade, produtos mais lucrativos, margem."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Quantidade de produtos no ranking. Default: 10.",
                    },
                    "data_inicio": {
                        "type": "string",
                        "description": "Data inicial YYYY-MM-DD. Default: últimos 30 dias.",
                    },
                    "data_fim": {
                        "type": "string",
                        "description": "Data final YYYY-MM-DD. Default: hoje.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_produtos_sem_giro",
            "description": (
                "Encontra produtos que têm estoque mas não venderam nada nos últimos N dias. "
                "Útil para identificar capital parado e produtos encalhados."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dias": {
                        "type": "integer",
                        "description": "Período de análise em dias. Default: 30.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comparar_periodos",
            "description": (
                "Compara faturamento, quantidade de pedidos e ticket médio entre dois períodos. "
                "Retorna valores absolutos e variação percentual. "
                "Use para comparativos: semana vs semana anterior, mês vs mês anterior, etc. "
                "Período 1 = período de referência (anterior), Período 2 = período atual."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "periodo1_inicio": {
                        "type": "string",
                        "description": "Início do período de referência (anterior) YYYY-MM-DD",
                    },
                    "periodo1_fim": {
                        "type": "string",
                        "description": "Fim do período de referência YYYY-MM-DD",
                    },
                    "periodo2_inicio": {
                        "type": "string",
                        "description": "Início do período atual YYYY-MM-DD",
                    },
                    "periodo2_fim": {
                        "type": "string",
                        "description": "Fim do período atual YYYY-MM-DD",
                    },
                    "canal": {
                        "type": "string",
                        "enum": ["PDV", "E-commerce"],
                        "description": "Filtrar por canal. Omitir para todos.",
                    },
                },
                "required": ["periodo1_inicio", "periodo1_fim", "periodo2_inicio", "periodo2_fim"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_produtos",
            "description": (
                "Busca produtos cadastrados no Bling com filtros opcionais. "
                "Retorna id, nome, código, preço, custo, estoque e categoria. "
                "Use para listar produtos, buscar por categoria, verificar preços."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {
                        "type": "string",
                        "description": "Nome da categoria para filtrar (busca parcial, case-insensitive).",
                    },
                    "tipo": {
                        "type": "string",
                        "enum": ["V", "S"],
                        "description": "'V' para variantes, 'S' para simples. Omitir para todos.",
                    },
                    "com_estoque": {
                        "type": "boolean",
                        "description": "true para só com estoque > 0, false para sem estoque. Omitir para todos.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_cobertura_estoque",
            "description": (
                "Calcula a cobertura de estoque em dias para um produto específico. "
                "Cobertura = estoque_atual / média de vendas diárias. "
                "Indica se o estoque cobre 7, 14, 30+ dias de venda. "
                "Classifica risco: ALTO (<7 dias), MÉDIO (7-14), OK (>14)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "produto_id": {
                        "type": "integer",
                        "description": "ID do produto no Bling.",
                    },
                    "dias_analise": {
                        "type": "integer",
                        "description": "Período em dias para calcular média de vendas. Default: 30.",
                    },
                },
                "required": ["produto_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_detalhe_pedido",
            "description": (
                "Busca os detalhes completos de um pedido de venda, incluindo os itens comprados. "
                "Use para responder quais produtos compõem um pedido ou o detalhamento dos valores."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pedido_id": {
                        "type": "integer",
                        "description": "ID numérico do pedido no Bling.",
                    },
                },
                "required": ["pedido_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_contatos",
            "description": (
                "Busca contatos (clientes ou fornecedores) cadastrados no Bling. "
                "Use para responder perguntas como 'quem é o cliente X?' ou para buscar dados cadastrais."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome parcial ou completo do contato.",
                    },
                    "documento": {
                        "type": "string",
                        "description": "CPF ou CNPJ do contato (apenas números).",
                    },
                    "limite": {
                        "type": "integer",
                        "description": "Quantidade máxima de registros. Default: 50.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_notas_fiscais",
            "description": (
                "Busca notas fiscais eletrônicas (NF-e ou NFC-e) emitidas. "
                "Use para responder qual nota foi gerada para um pedido, ou listar notas recentes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": ["nfe", "nfce", "todos"],
                        "description": "Tipo de nota fiscal a buscar. Default: todos.",
                    },
                    "data_inicio": {
                        "type": "string",
                        "description": "Data inicial YYYY-MM-DD.",
                    },
                    "data_fim": {
                        "type": "string",
                        "description": "Data final YYYY-MM-DD.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_contas_receber",
            "description": (
                "Busca contas a receber. "
                "Use para responder quanto há para receber, listar recebimentos futuros ou atrasados."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "situacao": {
                        "type": "integer",
                        "description": "ID da situação: 1=Em aberto, 2=Parcial, 3=Baixada/Recebida, 4=Cancelada. Omitir para todas.",
                    },
                    "data_inicio": {
                        "type": "string",
                        "description": "Data inicial de vencimento YYYY-MM-DD.",
                    },
                    "data_fim": {
                        "type": "string",
                        "description": "Data final de vencimento YYYY-MM-DD.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_contas_pagar",
            "description": (
                "Busca contas a pagar (despesas e pagamentos a fornecedores). "
                "Use para responder quanto há para pagar, listar pagamentos futuros ou em aberto."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "situacao": {
                        "type": "integer",
                        "description": "ID da situação: 1=Em aberto, 2=Parcial, 3=Baixada/Paga, 4=Cancelada. Omitir para todas.",
                    },
                    "data_inicio": {
                        "type": "string",
                        "description": "Data inicial de vencimento YYYY-MM-DD.",
                    },
                    "data_fim": {
                        "type": "string",
                        "description": "Data final de vencimento YYYY-MM-DD.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_fluxo_caixa",
            "description": (
                "Calcula o fluxo de caixa consolidando o total recebido (contas a receber baixadas) e total pago (contas a pagar baixadas). "
                "Use para responder sobre o saldo líquido do período ou lucro líquido."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "data_inicio": {
                        "type": "string",
                        "description": "Data inicial YYYY-MM-DD.",
                    },
                    "data_fim": {
                        "type": "string",
                        "description": "Data final YYYY-MM-DD.",
                    },
                },
                "required": ["data_inicio", "data_fim"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_categorias",
            "description": (
                "Busca a estrutura de categorias de produtos cadastradas no sistema."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_canais_venda",
            "description": (
                "Busca as configurações dos canais de venda (lojas físicas e e-commerce) cadastradas no sistema."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_formas_pagamento",
            "description": (
                "Busca as formas e meios de pagamento configurados no sistema."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]
