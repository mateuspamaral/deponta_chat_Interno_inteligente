"""
Tool de estoque — posição atual, cobertura em dias, risco de ruptura.
"""

import json
import logging
from datetime import datetime, timedelta

from tools.base import BlingClient
from utils.constants import SITUACOES_EXCLUIDAS

logger = logging.getLogger(__name__)


def buscar_estoque_critico(client: BlingClient, limite_minimo: int = 5) -> str:
    """
    Produtos com estoque <= limite_minimo. Identifica risco de ruptura.
    """
    produtos_raw = client.get_all_pages("produtos", params={})
    criticos = []

    for p in produtos_raw:
        estoque = max(0, p.get("estoque", {}).get("saldoVirtualTotal", 0))
        if p.get("formato", "") == "V":
            continue  # pular produto pai, estoque está nas variantes
        if estoque <= limite_minimo:
            criticos.append({
                "id": p.get("id"),
                "nome": p.get("nome", ""),
                "codigo": p.get("codigo", ""),
                "estoque": estoque,
                "preco": p.get("preco", 0),
                "categoria": p.get("categoria", {}).get("descricao", ""),
            })

    criticos.sort(key=lambda x: x["estoque"])
    return json.dumps({
        "total_criticos": len(criticos),
        "limite_minimo": limite_minimo,
        "produtos": criticos,
    }, ensure_ascii=False)


def calcular_cobertura_estoque(client: BlingClient, produto_id: int, dias_analise: int = 30) -> str:
    """
    Cobertura de estoque em dias: estoque_atual / (vendas_periodo / dias).
    """
    prod = client.get(f"produtos/{produto_id}").get("data", {})
    estoque = max(0, prod.get("estoque", {}).get("saldoVirtualTotal", 0))

    data_fim = datetime.now().strftime("%Y-%m-%d")
    data_inicio = (datetime.now() - timedelta(days=dias_analise)).strftime("%Y-%m-%d")
    pedidos = client.get_all_pages("pedidos/vendas", params={
        "dataInicial": data_inicio, "dataFinal": data_fim,
    })

    qtd_vendida = 0
    for pedido in pedidos:
        if pedido.get("situacao", {}).get("id") in SITUACOES_EXCLUIDAS:
            continue
        try:
            detalhe = client.get(f"pedidos/vendas/{pedido['id']}")
            for item in detalhe.get("data", {}).get("itens", []):
                if item.get("produto", {}).get("id") == produto_id:
                    qtd_vendida += item.get("quantidade", 0)
        except Exception as e:
            logger.warning("Erro detalhe pedido %s: %s", pedido.get("id"), e)

    media = qtd_vendida / dias_analise if dias_analise > 0 else 0
    cobertura = (estoque / media) if media > 0 else float("inf")
    risco = "ALTO" if cobertura < 7 else "MÉDIO" if cobertura < 14 else "OK"

    return json.dumps({
        "produto_id": produto_id,
        "nome": prod.get("nome", ""),
        "estoque_atual": estoque,
        "vendas_periodo": qtd_vendida,
        "media_diaria": round(media, 2),
        "cobertura_dias": round(cobertura, 1) if cobertura != float("inf") else "Sem vendas",
        "risco_ruptura": risco,
        "periodo_analise": f"{data_inicio} a {data_fim}",
    }, ensure_ascii=False)
