"""
Tool de estoque — posição atual, cobertura em dias, risco de ruptura.
"""

import json
import logging
from datetime import datetime, timedelta

from tools.base import BlingClient
from utils.constants import SITUACOES_EXCLUIDAS

logger = logging.getLogger(__name__)

# IDs de depósitos confirmados no ambiente De Ponta
DEPOSITO_LOJA_FISICA = 14887895820    # Loja Física - Stop Gallery (padrão)
DEPOSITO_DISTRIBUICAO = 14887895821   # Distribuição - Stop Gallery

# Tamanho do batch para /estoques/saldos
# A API do Bling processa um ID por chamada — iteramos produto a produto
# usando o cache TTL=2min para amortizar o custo em consultas repetidas.
ESTOQUE_SALDOS_BATCH_SIZE = 1


def _buscar_saldo_produto(client: BlingClient, produto_id: int) -> dict:
    """
    Busca saldo de estoque detalhado para um produto via /estoques/saldos.

    Retorna breakdown por depósito além dos totais virtuais e físicos.
    Usa cache TTL=2min (herda do BlingClient).

    Args:
        client: instância do BlingClient
        produto_id: ID do produto no Bling

    Returns:
        dict com saldoFisicoTotal, saldoVirtualTotal, depositos[].
        Em caso de erro, retorna valores zerados.
    """
    try:
        resp = client.get(
            "estoques/saldos",
            params={"idsProdutos[]": produto_id},
        )
        saldos = resp.get("data", [])
        if saldos:
            return saldos[0]
        return {"saldoFisicoTotal": 0, "saldoVirtualTotal": 0, "depositos": []}
    except Exception as e:
        logger.warning("Erro /estoques/saldos produto %s: %s", produto_id, e)
        return {"saldoFisicoTotal": 0, "saldoVirtualTotal": 0, "depositos": []}


def buscar_estoque_critico(
    client: BlingClient,
    limite_minimo: int = 5,
    id_deposito: int = None,
) -> str:
    """
    Busca produtos com estoque crítico (abaixo do limite mínimo).

    Usa /estoques/saldos para obter dados precisos com breakdown por depósito,
    permitindo identificar se a ruptura é na loja física ou no armazém.

    Fluxo:
    1. Lista produtos ativos (formato "S" = simples, exclui produtos-pai "V")
    2. Para cada produto, busca saldo detalhado via /estoques/saldos
    3. Filtra produtos com saldo virtual <= limite_minimo
    4. Retorna com breakdown de estoque por depósito

    Args:
        client: instância do BlingClient
        limite_minimo: estoque virtual mínimo para considerar crítico (default: 5)
        id_deposito: se informado, filtra pelo saldo do depósito específico.
                     Use DEPOSITO_LOJA_FISICA ou DEPOSITO_DISTRIBUICAO.
                     Se None, usa saldoVirtualTotal (soma de todos depósitos).

    Returns:
        JSON string com lista de produtos críticos e breakdown por depósito.
    """
    # 1. Buscar produtos ativos (sem variantes-pai)
    produtos_raw = client.get_all_pages("produtos", params={"situacao": "A"})
    produtos_simples = [
        p for p in produtos_raw
        if p.get("formato", "") != "V" and p.get("id")
    ]

    logger.info(
        "buscar_estoque_critico: %d produtos simples ativos para verificar",
        len(produtos_simples),
    )

    criticos = []
    erros = 0

    for produto in produtos_simples:
        pid = produto.get("id")

        # Buscar saldo via endpoint dedicado (cache TTL=2min)
        saldo = _buscar_saldo_produto(client, pid)

        # Determinar o estoque relevante conforme o depósito solicitado
        if id_deposito:
            deposito_data = next(
                (d for d in saldo.get("depositos", [])
                 if d.get("deposito", {}).get("id") == id_deposito),
                None,
            )
            if deposito_data:
                estoque_virtual = max(0, deposito_data.get("saldoVirtualTotal", 0) or 0)
                estoque_fisico = max(0, deposito_data.get("saldoFisicoTotal", 0) or 0)
            else:
                estoque_virtual = 0
                estoque_fisico = 0
        else:
            estoque_virtual = max(0, saldo.get("saldoVirtualTotal", 0) or 0)
            estoque_fisico = max(0, saldo.get("saldoFisicoTotal", 0) or 0)

        if estoque_virtual <= limite_minimo:
            # Montar breakdown por depósito para diagnóstico
            depositos_detalhados = []
            for dep in saldo.get("depositos", []):
                depositos_detalhados.append({
                    "deposito_id": dep.get("deposito", {}).get("id"),
                    "deposito_nome": dep.get("deposito", {}).get("descricao", ""),
                    "saldo_fisico": max(0, dep.get("saldoFisicoTotal", 0) or 0),
                    "saldo_virtual": max(0, dep.get("saldoVirtualTotal", 0) or 0),
                })

            criticos.append({
                "id": pid,
                "nome": produto.get("nome", ""),
                "codigo": produto.get("codigo", ""),
                "estoque_virtual": estoque_virtual,
                "estoque_fisico": estoque_fisico,
                "preco": produto.get("preco", 0),
                "categoria": produto.get("categoria", {}).get("descricao", ""),
                "depositos": depositos_detalhados,
            })

    criticos.sort(key=lambda x: x["estoque_virtual"])

    return json.dumps({
        "total_criticos": len(criticos),
        "limite_minimo": limite_minimo,
        "filtro_deposito": id_deposito,
        "produtos": criticos,
        "meta": {
            "total_produtos_verificados": len(produtos_simples),
            "fonte": "/estoques/saldos",
        },
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
