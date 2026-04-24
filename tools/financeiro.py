"""
Tool financeiro — faturamento, ticket médio, margem, comparativos.
"""

import json
import logging
from datetime import datetime, timedelta

from tools.base import BlingClient
from utils.constants import LOJAS, LOJAS_POR_NOME, SITUACOES_EXCLUIDAS

logger = logging.getLogger(__name__)


def calcular_faturamento(client: BlingClient, data_inicio: str, data_fim: str, canal: str = None) -> str:
    """
    Faturamento do período. Usa totalProdutos (sem frete).
    Retorna faturamento, qtd pedidos, ticket médio, frete total.
    """
    pedidos = client.get_all_pages("pedidos/vendas", params={
        "dataInicial": data_inicio, "dataFinal": data_fim,
    })

    # Filtrar cancelados/devolvidos
    pedidos = [p for p in pedidos if p.get("situacao", {}).get("id") not in SITUACOES_EXCLUIDAS]

    # Filtrar canal
    if canal:
        loja_id = LOJAS_POR_NOME.get(canal)
        if loja_id:
            pedidos = [p for p in pedidos if p.get("loja", {}).get("id") == loja_id]

    faturamento = sum(p.get("totalProdutos", 0) for p in pedidos)
    frete_total = sum(p.get("transporte", {}).get("frete", 0) for p in pedidos)
    qtd = len(pedidos)
    ticket = faturamento / qtd if qtd > 0 else 0

    return json.dumps({
        "faturamento": round(faturamento, 2),
        "quantidade_pedidos": qtd,
        "ticket_medio": round(ticket, 2),
        "frete_total": round(frete_total, 2),
        "total_com_frete": round(faturamento + frete_total, 2),
        "periodo": f"{data_inicio} a {data_fim}",
        "canal": canal or "Todos",
    }, ensure_ascii=False)


def calcular_margem_produtos(client: BlingClient, top_n: int = 10, data_inicio: str = None, data_fim: str = None) -> str:
    """
    Top N produtos por margem bruta. Margem = valor_venda - precoCusto.
    Se data não informada, usa últimos 30 dias.
    """
    if not data_inicio:
        data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not data_fim:
        data_fim = datetime.now().strftime("%Y-%m-%d")

    pedidos = client.get_all_pages("pedidos/vendas", params={
        "dataInicial": data_inicio, "dataFinal": data_fim,
    })
    pedidos = [p for p in pedidos if p.get("situacao", {}).get("id") not in SITUACOES_EXCLUIDAS]

    # Buscar todos os produtos para ter o custo
    produtos_raw = client.get_all_pages("produtos", params={})
    custo_map = {}
    nome_map = {}
    for p in produtos_raw:
        pid = p.get("id")
        custo_map[pid] = p.get("precoCusto", 0)
        nome_map[pid] = p.get("nome", "")

    # Agregar vendas por produto
    vendas_produto = {}
    for pedido in pedidos:
        try:
            detalhe = client.get(f"pedidos/vendas/{pedido['id']}")
            for item in detalhe.get("data", {}).get("itens", []):
                pid = item.get("produto", {}).get("id")
                if not pid:
                    continue
                if pid not in vendas_produto:
                    vendas_produto[pid] = {"receita": 0, "quantidade": 0, "descricao": item.get("descricao", "")}
                vendas_produto[pid]["receita"] += item.get("valor", 0) * item.get("quantidade", 0)
                vendas_produto[pid]["quantidade"] += item.get("quantidade", 0)
        except Exception as e:
            logger.warning("Erro detalhe pedido %s: %s", pedido.get("id"), e)

    # Calcular margem
    margens = []
    for pid, dados in vendas_produto.items():
        custo = custo_map.get(pid, 0)
        receita = dados["receita"]
        custo_total = custo * dados["quantidade"]
        margem = receita - custo_total
        margem_pct = (margem / receita * 100) if receita > 0 else 0

        margens.append({
            "produto_id": pid,
            "nome": nome_map.get(pid, dados["descricao"]),
            "receita": round(receita, 2),
            "custo_total": round(custo_total, 2),
            "margem_bruta": round(margem, 2),
            "margem_percentual": round(margem_pct, 1),
            "quantidade": dados["quantidade"],
        })

    margens.sort(key=lambda x: x["margem_bruta"], reverse=True)

    return json.dumps({
        "top_n": top_n,
        "periodo": f"{data_inicio} a {data_fim}",
        "produtos": margens[:top_n],
    }, ensure_ascii=False)


def buscar_produtos_sem_giro(client: BlingClient, dias: int = 30) -> str:
    """
    Produtos que não venderam nada nos últimos N dias.
    """
    data_fim = datetime.now().strftime("%Y-%m-%d")
    data_inicio = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")

    pedidos = client.get_all_pages("pedidos/vendas", params={
        "dataInicial": data_inicio, "dataFinal": data_fim,
    })
    pedidos = [p for p in pedidos if p.get("situacao", {}).get("id") not in SITUACOES_EXCLUIDAS]

    # Coletar IDs de produtos vendidos
    ids_vendidos = set()
    for pedido in pedidos:
        try:
            detalhe = client.get(f"pedidos/vendas/{pedido['id']}")
            for item in detalhe.get("data", {}).get("itens", []):
                pid = item.get("produto", {}).get("id")
                if pid:
                    ids_vendidos.add(pid)
        except Exception:
            continue

    # Buscar todos os produtos ativos com estoque
    todos = client.get_all_pages("produtos", params={})
    sem_giro = []
    for p in todos:
        if p.get("formato", "") == "V":
            continue
        estoque = max(0, p.get("estoque", {}).get("saldoVirtualTotal", 0))
        if estoque > 0 and p.get("id") not in ids_vendidos:
            sem_giro.append({
                "id": p.get("id"),
                "nome": p.get("nome", ""),
                "codigo": p.get("codigo", ""),
                "estoque": estoque,
                "preco": p.get("preco", 0),
                "categoria": p.get("categoria", {}).get("descricao", ""),
            })

    return json.dumps({
        "total_sem_giro": len(sem_giro),
        "dias_analisados": dias,
        "periodo": f"{data_inicio} a {data_fim}",
        "produtos": sem_giro,
    }, ensure_ascii=False)


def comparar_periodos(client: BlingClient, periodo1_inicio: str, periodo1_fim: str,
                      periodo2_inicio: str, periodo2_fim: str, canal: str = None) -> str:
    """
    Compara faturamento entre dois períodos. Retorna valores e variação %.
    Período 1 = referência (ex: semana passada), Período 2 = comparação (ex: esta semana).
    """
    fat1 = json.loads(calcular_faturamento(client, periodo1_inicio, periodo1_fim, canal))
    fat2 = json.loads(calcular_faturamento(client, periodo2_inicio, periodo2_fim, canal))

    def variacao(atual, anterior):
        if anterior == 0:
            return 0.0 if atual == 0 else 100.0
        return round(((atual - anterior) / abs(anterior)) * 100, 1)

    return json.dumps({
        "periodo_1": {"inicio": periodo1_inicio, "fim": periodo1_fim, **fat1},
        "periodo_2": {"inicio": periodo2_inicio, "fim": periodo2_fim, **fat2},
        "variacao": {
            "faturamento_pct": variacao(fat2["faturamento"], fat1["faturamento"]),
            "pedidos_pct": variacao(fat2["quantidade_pedidos"], fat1["quantidade_pedidos"]),
            "ticket_medio_pct": variacao(fat2["ticket_medio"], fat1["ticket_medio"]),
        },
        "canal": canal or "Todos",
    }, ensure_ascii=False)
