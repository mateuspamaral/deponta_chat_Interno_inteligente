"""
Tool de catálogo — categorias, canais de venda e formas de pagamento.
"""

import json
import logging

from tools.base import BlingClient

logger = logging.getLogger(__name__)


def buscar_categorias(client: BlingClient) -> str:
    """
    Busca categorias de produtos.
    """
    categorias_raw = client.get_all_pages("categorias/produtos")
    
    categorias = []
    for c in categorias_raw:
        categorias.append({
            "id": c.get("id"),
            "descricao": c.get("descricao", ""),
            "categoriaPai_id": c.get("categoriaPai", {}).get("id"),
        })

    return json.dumps({
        "total_categorias": len(categorias),
        "categorias": categorias,
    }, ensure_ascii=False)


def buscar_canais_venda(client: BlingClient) -> str:
    """
    Busca canais de venda.
    """
    canais_raw = client.get_all_pages("canais-venda")
    
    canais = []
    for c in canais_raw:
        canais.append({
            "id": c.get("id"),
            "descricao": c.get("descricao", ""),
            "tipo": c.get("tipo", ""),
            "situacao": c.get("situacao", ""),
        })

    return json.dumps({
        "total_canais": len(canais),
        "canais_venda": canais,
    }, ensure_ascii=False)


def buscar_formas_pagamento(client: BlingClient) -> str:
    """
    Busca formas de pagamento.
    """
    formas_raw = client.get_all_pages("formas-pagamentos")
    
    formas = []
    for f in formas_raw:
        formas.append({
            "id": f.get("id"),
            "descricao": f.get("descricao", ""),
            "tipoPagamento": f.get("tipoPagamento", ""),
            "situacao": f.get("situacao", ""),
            "fixa": f.get("fixa", False),
            "padrao": f.get("padrao", False),
        })

    return json.dumps({
        "total_formas": len(formas),
        "formas_pagamento": formas,
    }, ensure_ascii=False)
