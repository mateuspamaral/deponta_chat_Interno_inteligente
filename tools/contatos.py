"""
Tool de contatos — busca de clientes e fornecedores.
"""

import json
import logging

from tools.base import BlingClient

logger = logging.getLogger(__name__)


def buscar_contatos(client: BlingClient, nome: str = None, documento: str = None, limite: int = 50) -> str:
    """
    Busca contatos (clientes) no Bling.
    
    Args:
        client: instância do BlingClient
        nome: nome do contato para filtro (busca parcial)
        documento: CPF ou CNPJ
        limite: limite de registros retornados (padrão 50)
    
    Returns:
        JSON string com lista de contatos
    """
    params = {"limite": limite}
    if nome:
        params["pesquisa"] = nome
    if documento:
        params["numeroDocumento"] = documento

    contatos_raw = client.get_all_pages("contatos", params=params)

    contatos = []
    for c in contatos_raw:
        # A API pode retornar listas de contatos com dados incompletos dependendo do endpoint,
        # portanto validamos os campos principais
        if not c.get("id"):
            continue

        contatos.append({
            "id": c.get("id"),
            "nome": c.get("nome", ""),
            "codigo": c.get("codigo", ""),
            "situacao": c.get("situacao", ""),
            "numeroDocumento": c.get("numeroDocumento", ""),
            "telefone": c.get("telefone", ""),
            "celular": c.get("celular", ""),
        })

    return json.dumps({
        "total_contatos": len(contatos),
        "filtro_nome": nome or "Nenhum",
        "filtro_documento": documento or "Nenhum",
        "contatos": contatos[:limite],
    }, ensure_ascii=False)
