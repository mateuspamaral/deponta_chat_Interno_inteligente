"""
Tool de pedidos de venda — busca e processamento de pedidos do Bling.
Funções chamáveis pelo LLM via tool calling.
"""

import json
import logging

from tools.base import BlingClient
from utils.constants import LOJAS, LOJAS_POR_NOME, SITUACOES_PEDIDO, SITUACOES_EXCLUIDAS

logger = logging.getLogger(__name__)


def buscar_pedidos(
    client: BlingClient,
    data_inicio: str,
    data_fim: str,
    canal: str = None,
    situacao: str = None,
) -> str:
    """
    Busca pedidos de venda no período especificado.
    
    Args:
        client: instância do BlingClient
        data_inicio: data inicial no formato YYYY-MM-DD
        data_fim: data final no formato YYYY-MM-DD
        canal: 'PDV', 'E-commerce' ou None (todos)
        situacao: nome da situação (ex: 'Atendido') ou None (todas)
    
    Returns:
        JSON string com lista de pedidos resumidos
    """
    params = {
        "dataInicial": data_inicio,
        "dataFinal": data_fim,
    }

    # Filtro de situação por ID
    if situacao:
        sit_id = next(
            (k for k, v in SITUACOES_PEDIDO.items() if v.lower() == situacao.lower()),
            None
        )
        if sit_id:
            params["idsSituacoes[]"] = sit_id

    # Busca paginada
    pedidos_raw = client.get_all_pages("pedidos/vendas", params=params)

    # Filtro de canal (pós-fetch, já que a API não filtra por loja diretamente)
    if canal:
        loja_id = LOJAS_POR_NOME.get(canal)
        if loja_id:
            pedidos_raw = [p for p in pedidos_raw if p.get("loja", {}).get("id") == loja_id]

    # Monta resumo
    pedidos = []
    for p in pedidos_raw:
        loja_id = p.get("loja", {}).get("id")
        pedidos.append({
            "id": p.get("id"),
            "numero": p.get("numero"),
            "data": p.get("data"),
            "canal": LOJAS.get(loja_id, "Desconhecido"),
            "totalProdutos": p.get("totalProdutos", 0),
            "frete": p.get("transporte", {}).get("frete", 0),
            "total": p.get("total", 0),
            "situacao": SITUACOES_PEDIDO.get(
                p.get("situacao", {}).get("id"), 
                p.get("situacao", {}).get("valor", "Desconhecida")
            ),
            "contato": p.get("contato", {}).get("nome", ""),
            "numeroLoja": p.get("numeroLoja", ""),
        })

    resultado = {
        "total_pedidos": len(pedidos),
        "periodo": f"{data_inicio} a {data_fim}",
        "canal_filtro": canal or "Todos",
        "pedidos": pedidos,
    }

    return json.dumps(resultado, ensure_ascii=False)


def buscar_detalhe_pedido(client: BlingClient, pedido_id: int) -> str:
    """
    Busca detalhe completo de um pedido incluindo itens.
    
    Args:
        client: instância do BlingClient
        pedido_id: ID do pedido no Bling
    
    Returns:
        JSON string com detalhe completo do pedido
    """
    response = client.get(f"pedidos/vendas/{pedido_id}")
    p = response.get("data", {})

    loja_id = p.get("loja", {}).get("id")

    # Extrair itens
    itens = []
    for item in p.get("itens", []):
        itens.append({
            "produto_id": item.get("produto", {}).get("id"),
            "codigo": item.get("codigo", ""),
            "descricao": item.get("descricao", ""),
            "quantidade": item.get("quantidade", 0),
            "valor_unitario": item.get("valor", 0),
            "desconto": item.get("desconto", 0),
        })

    detalhe = {
        "id": p.get("id"),
        "numero": p.get("numero"),
        "data": p.get("data"),
        "canal": LOJAS.get(loja_id, "Desconhecido"),
        "totalProdutos": p.get("totalProdutos", 0),
        "frete": p.get("transporte", {}).get("frete", 0),
        "total": p.get("total", 0),
        "situacao": SITUACOES_PEDIDO.get(
            p.get("situacao", {}).get("id"),
            p.get("situacao", {}).get("valor", "Desconhecida")
        ),
        "contato": p.get("contato", {}).get("nome", ""),
        "itens": itens,
        "observacoes": p.get("observacoes", ""),
    }

    return json.dumps(detalhe, ensure_ascii=False)
