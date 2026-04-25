"""
Tool financeiro contas — contas a receber, contas a pagar e fluxo de caixa.
"""

import json
import logging

from tools.base import BlingClient

logger = logging.getLogger(__name__)


def buscar_contas_receber(
    client: BlingClient,
    situacao: int = None,
    data_inicio: str = None,
    data_fim: str = None
) -> str:
    """
    Busca contas a receber.
    """
    params = {}
    if data_inicio and data_fim:
        params["dataInicial"] = data_inicio
        params["dataFinal"] = data_fim
    if situacao is not None:
        params["situacoes[]"] = situacao

    contas_raw = client.get_all_pages("contas/receber", params=params)

    contas = []
    total_valor = 0.0

    for c in contas_raw:
        valor = c.get("valor", 0)
        total_valor += valor
        contas.append({
            "id": c.get("id"),
            "situacao": c.get("situacao", ""),
            "vencimento": c.get("vencimento", ""),
            "valor": valor,
            "dataEmissao": c.get("dataEmissao", ""),
            "contato": c.get("contato", {}).get("nome", ""),
            "formaPagamento": c.get("formaPagamento", {}).get("descricao", ""),
            "linkBoleto": c.get("linkBoleto", ""),
            "linkQRCodePix": c.get("linkQRCodePix", ""),
        })

    return json.dumps({
        "total_contas": len(contas),
        "valor_total": round(total_valor, 2),
        "periodo": f"{data_inicio or 'Sempre'} a {data_fim or 'Hoje'}",
        "contas": contas,
    }, ensure_ascii=False)


def buscar_contas_pagar(
    client: BlingClient,
    situacao: int = None,
    data_inicio: str = None,
    data_fim: str = None
) -> str:
    """
    Busca contas a pagar.
    """
    params = {}
    if data_inicio and data_fim:
        params["dataInicial"] = data_inicio
        params["dataFinal"] = data_fim
    if situacao is not None:
        params["situacoes[]"] = situacao

    contas_raw = client.get_all_pages("contas/pagar", params=params)

    contas = []
    total_valor = 0.0

    for c in contas_raw:
        valor = c.get("valor", 0)
        total_valor += valor
        contas.append({
            "id": c.get("id"),
            "situacao": c.get("situacao", ""),
            "vencimento": c.get("vencimento", ""),
            "valor": valor,
            "contato": c.get("contato", {}).get("nome", ""),
            "formaPagamento": c.get("formaPagamento", {}).get("descricao", ""),
        })

    return json.dumps({
        "total_contas": len(contas),
        "valor_total": round(total_valor, 2),
        "periodo": f"{data_inicio or 'Sempre'} a {data_fim or 'Hoje'}",
        "contas": contas,
    }, ensure_ascii=False)


def calcular_fluxo_caixa(client: BlingClient, data_inicio: str, data_fim: str) -> str:
    """
    Calcula fluxo de caixa considerando contas a receber e contas a pagar.
    Considera situação de baixa (pago/recebido)
    """
    receber_res = json.loads(buscar_contas_receber(client, situacao=3, data_inicio=data_inicio, data_fim=data_fim))  # 3 = recebido
    pagar_res = json.loads(buscar_contas_pagar(client, situacao=3, data_inicio=data_inicio, data_fim=data_fim))  # 3 = pago

    total_recebido = receber_res.get("valor_total", 0)
    total_pago = pagar_res.get("valor_total", 0)
    saldo_liquido = total_recebido - total_pago

    return json.dumps({
        "periodo": f"{data_inicio} a {data_fim}",
        "total_recebido": round(total_recebido, 2),
        "total_pago": round(total_pago, 2),
        "saldo_liquido": round(saldo_liquido, 2),
    }, ensure_ascii=False)
