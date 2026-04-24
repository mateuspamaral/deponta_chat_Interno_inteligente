"""
Tool de produtos — busca, detalhe e resolução de variantes.
Funções chamáveis pelo LLM via tool calling.
"""

import json
import logging

from tools.base import BlingClient

logger = logging.getLogger(__name__)


def buscar_produtos(
    client: BlingClient,
    categoria: str = None,
    tipo: str = None,
    com_estoque: bool = None,
) -> str:
    """
    Busca produtos cadastrados no Bling.
    
    Args:
        client: instância do BlingClient
        categoria: nome ou ID da categoria (filtro opcional)
        tipo: 'V' (variantes), 'S' (simples), None (todos)
        com_estoque: True para só com estoque > 0, False para sem estoque, None para todos
    
    Returns:
        JSON string com lista de produtos
    """
    params = {}
    if tipo:
        params["tipo"] = tipo

    produtos_raw = client.get_all_pages("produtos", params=params)

    # Filtro de estoque (pós-fetch)
    if com_estoque is True:
        produtos_raw = [
            p for p in produtos_raw
            if p.get("estoque", {}).get("saldoVirtualTotal", 0) > 0
        ]
    elif com_estoque is False:
        produtos_raw = [
            p for p in produtos_raw
            if p.get("estoque", {}).get("saldoVirtualTotal", 0) <= 0
        ]

    # Filtro de categoria (case-insensitive, por nome)
    if categoria:
        cat_lower = categoria.lower()
        produtos_raw = [
            p for p in produtos_raw
            if cat_lower in (p.get("categoria", {}).get("descricao", "") or "").lower()
        ]

    produtos = []
    for p in produtos_raw:
        estoque_raw = p.get("estoque", {}).get("saldoVirtualTotal", 0)
        produtos.append({
            "id": p.get("id"),
            "nome": p.get("nome", ""),
            "codigo": p.get("codigo", ""),
            "preco": p.get("preco", 0),
            "precoCusto": p.get("precoCusto", 0),
            "estoque": max(0, estoque_raw),
            "formato": p.get("formato", ""),
            "categoria": p.get("categoria", {}).get("descricao", ""),
            "idProdutoPai": p.get("idProdutoPai"),
        })

    resultado = {
        "total_produtos": len(produtos),
        "filtros": {
            "categoria": categoria,
            "tipo": tipo,
            "com_estoque": com_estoque,
        },
        "produtos": produtos,
    }

    return json.dumps(resultado, ensure_ascii=False)


def buscar_detalhe_produto(client: BlingClient, produto_id: int) -> str:
    """
    Busca detalhe completo de um produto, incluindo custo e estoque.
    
    O custo está em fornecedor.precoCusto no endpoint de detalhe.
    O estoque negativo é tratado como zero.
    
    Args:
        client: instância do BlingClient
        produto_id: ID do produto no Bling
    
    Returns:
        JSON string com detalhe do produto
    """
    response = client.get(f"produtos/{produto_id}")
    p = response.get("data", {})

    estoque_raw = p.get("estoque", {}).get("saldoVirtualTotal", 0)

    # Custo: no detalhe está em fornecedor.precoCusto
    custo = 0
    fornecedor = p.get("fornecedor", {})
    if isinstance(fornecedor, dict):
        custo = fornecedor.get("precoCusto", 0)

    # Variante → produto pai
    variacao = p.get("variacao", {})
    produto_pai_id = None
    if isinstance(variacao, dict) and variacao.get("produtoPai"):
        produto_pai_id = variacao["produtoPai"].get("id")

    detalhe = {
        "id": p.get("id"),
        "nome": p.get("nome", ""),
        "codigo": p.get("codigo", ""),
        "preco": p.get("preco", 0),
        "precoCusto": custo,
        "estoque": max(0, estoque_raw),
        "formato": p.get("formato", ""),
        "categoria": p.get("categoria", {}).get("descricao", ""),
        "marca": p.get("marca", ""),
        "produtoPaiId": produto_pai_id,
        "situacao": p.get("situacao", ""),
    }

    return json.dumps(detalhe, ensure_ascii=False)
