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
                "Identifica itens com risco de ruptura de estoque. "
                "Use para perguntas sobre estoque baixo, risco de faltar produto, "
                "sugestão de reposição."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limite_minimo": {
                        "type": "integer",
                        "description": "Estoque mínimo para considerar crítico. Default: 5.",
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
]
