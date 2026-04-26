"""
Tool financeiro — faturamento, ticket médio, margem, comparativos.
"""

import json
import logging
from datetime import datetime, timedelta

from tools.base import BlingClient
from utils.constants import LOJAS, LOJAS_POR_NOME, SITUACOES_EXCLUIDAS

logger = logging.getLogger(__name__)

from concurrent.futures import ThreadPoolExecutor, as_completed

# Concorrência máxima para chamadas paralelas à API do Bling.
# Valor conservador para respeitar rate limiting (API permite ~10 req/s).
# Com 618 pedidos e 8 workers: ~77 batches × ~0.2s = ~15s estimado.
_MAX_WORKERS_DETALHES = 8


def _buscar_detalhes_paralelo(
    client: BlingClient,
    pedidos: list[dict],
) -> dict[int, dict]:
    """
    Busca detalhes de múltiplos pedidos em paralelo via ThreadPoolExecutor.

    Substitui o padrão N+1 sequencial. Usa cache TTL=2min do BlingClient,
    então pedidos já consultados nesta sessão retornam imediatamente do cache
    sem chamada à API.

    Args:
        client: instância do BlingClient
        pedidos: lista de dicts de pedido com campo 'id'

    Returns:
        dict mapeando pedido_id → dict com o conteúdo de 'data' do response.
        Pedidos com erro são omitidos do resultado.
    """
    resultados: dict[int, dict] = {}

    def _fetch(pedido: dict) -> tuple[int, dict | None]:
        pid = pedido["id"]
        try:
            resp = client.get(f"pedidos/vendas/{pid}")
            return pid, resp.get("data", {})
        except Exception as e:
            logger.warning("Erro ao buscar detalhe do pedido %s: %s", pid, e)
            return pid, None

    logger.info(
        "_buscar_detalhes_paralelo: %d pedidos com %d workers",
        len(pedidos), _MAX_WORKERS_DETALHES,
    )

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS_DETALHES) as executor:
        futures = {executor.submit(_fetch, p): p["id"] for p in pedidos}
        for future in as_completed(futures):
            pid, detalhe = future.result()
            if detalhe is not None:
                resultados[pid] = detalhe

    logger.info(
        "_buscar_detalhes_paralelo: %d/%d pedidos retornados com sucesso",
        len(resultados), len(pedidos),
    )
    return resultados
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

    # Taxas de marketplace: disponíveis apenas via detalhe de pedido.
    # Na listagem de /pedidos/vendas, o campo taxas não está disponível.
    # Reportamos 0 aqui por consistência — o valor real está em calcular_margem_produtos.
    # Para obter taxas reais, cruzar com extrato /caixas (tool futura Fase 2).
    taxas_nota = (
        "Taxas de gateway/marketplace não incluídas neste total. "
        "Use calcular_margem_produtos para análise com taxas por produto."
    )

    return json.dumps({
        "faturamento": round(faturamento, 2),
        "quantidade_pedidos": qtd,
        "ticket_medio": round(ticket, 2),
        "frete_total": round(frete_total, 2),
        "total_com_frete": round(faturamento + frete_total, 2),
        "periodo": f"{data_inicio} a {data_fim}",
        "canal": canal or "Todos",
        "nota_taxas": taxas_nota,
    }, ensure_ascii=False)


def calcular_margem_produtos(
    client: BlingClient,
    top_n: int = 10,
    data_inicio: str = None,
    data_fim: str = None,
) -> str:
    """
    Calcula e rankeia produtos por margem bruta no período.

    Margem bruta = receita_produto - custo_produto - taxas_marketplace

    As taxas de marketplace (gateway de pagamento, plataforma) são extraídas
    do campo `taxas` do detalhe do pedido e distribuídas proporcionalmente
    entre os itens do pedido pela receita gerada por cada um.

    Todos os pedidos do período são analisados via busca paralela
    (ThreadPoolExecutor), eliminando o gargalo N+1 sequencial.

    Args:
        client: instância do BlingClient
        top_n: quantidade de produtos no ranking (default: 10)
        data_inicio: data inicial YYYY-MM-DD (default: 30 dias atrás)
        data_fim: data final YYYY-MM-DD (default: hoje)

    Returns:
        JSON string com ranking de margem e metadados de cobertura
    """
    if not data_inicio:
        data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not data_fim:
        data_fim = datetime.now().strftime("%Y-%m-%d")

    # 1. Buscar pedidos do período (paginado, com cache de 2min)
    pedidos = client.get_all_pages("pedidos/vendas", params={
        "dataInicial": data_inicio,
        "dataFinal": data_fim,
    })
    pedidos = [p for p in pedidos if p.get("situacao", {}).get("id") not in SITUACOES_EXCLUIDAS]
    total_pedidos_periodo = len(pedidos)

    # 2. Buscar custo de todos os produtos (cache 30min — catálogo não muda frequentemente)
    produtos_raw = client.get_all_pages("produtos", params={})
    custo_map: dict[int, float] = {}
    nome_map: dict[int, str] = {}
    for p in produtos_raw:
        pid = p.get("id")
        if pid:
            custo_map[pid] = p.get("precoCusto", 0) or 0
            nome_map[pid] = p.get("nome", "")

    # 3. Buscar detalhes de todos os pedidos em paralelo
    detalhes_map = _buscar_detalhes_paralelo(client, pedidos)

    # 4. Agregar receita, quantidade e taxas por produto
    vendas_produto: dict[int, dict] = {}

    for pedido in pedidos:
        detalhe = detalhes_map.get(pedido["id"])
        if not detalhe:
            continue

        itens = detalhe.get("itens", [])
        if not itens:
            continue

        taxa_pedido = _extrair_taxa_pedido(detalhe)

        receita_total_pedido = sum(
            (item.get("valor", 0) or 0) * (item.get("quantidade", 0) or 0)
            for item in itens
        )

        for item in itens:
            pid = item.get("produto", {}).get("id")
            if not pid:
                continue

            quantidade = item.get("quantidade", 0) or 0
            valor_unit = item.get("valor", 0) or 0
            receita_item = valor_unit * quantidade

            if pid not in vendas_produto:
                vendas_produto[pid] = {
                    "receita": 0.0,
                    "quantidade": 0,
                    "taxas": 0.0,
                    "descricao": item.get("descricao", ""),
                }

            vendas_produto[pid]["receita"] += receita_item
            vendas_produto[pid]["quantidade"] += quantidade

            if taxa_pedido > 0 and receita_total_pedido > 0:
                proporcao = receita_item / receita_total_pedido
                vendas_produto[pid]["taxas"] += taxa_pedido * proporcao

    # 5. Calcular margem por produto
    margens = []
    for pid, dados in vendas_produto.items():
        custo_unit = custo_map.get(pid, 0) or 0
        receita = dados["receita"]
        custo_total = custo_unit * dados["quantidade"]
        taxas_total = round(dados["taxas"], 4)
        margem = receita - custo_total - taxas_total
        margem_pct = (margem / receita * 100) if receita > 0 else 0

        margens.append({
            "produto_id": pid,
            "nome": nome_map.get(pid, dados["descricao"]),
            "receita": round(receita, 2),
            "custo_total": round(custo_total, 2),
            "taxas_marketplace": round(taxas_total, 2),
            "margem_bruta": round(margem, 2),
            "margem_percentual": round(margem_pct, 1),
            "quantidade": dados["quantidade"],
        })

    margens.sort(key=lambda x: x["margem_bruta"], reverse=True)

    return json.dumps({
        "top_n": top_n,
        "periodo": f"{data_inicio} a {data_fim}",
        "produtos": margens[:top_n],
        "meta": {
            "total_pedidos_periodo": total_pedidos_periodo,
            "pedidos_analisados": len(detalhes_map),
            "cobertura_parcial": False,
            "aviso": None,
        },
    }, ensure_ascii=False)


def _extrair_taxa_pedido(detalhe: dict) -> float:
    """
    Extrai o valor total de taxas de marketplace/gateway de um pedido.

    O campo `taxas` no response do Bling pode ser:
    - dict com chave "valor": {"valor": 0.29, "taxa": 1.0, ...}
    - list de dicts: [{"valor": 0.15}, {"valor": 0.14}]
    - None ou ausente

    Args:
        detalhe: dict com o conteúdo de data do /pedidos/vendas/{id}

    Returns:
        Valor total das taxas em reais (float). Zero se não houver taxas.
    """
    taxas_raw = detalhe.get("taxas")

    if not taxas_raw:
        return 0.0

    if isinstance(taxas_raw, dict):
        return float(taxas_raw.get("valor", 0) or 0)

    if isinstance(taxas_raw, list):
        return sum(float(t.get("valor", 0) or 0) for t in taxas_raw if isinstance(t, dict))

    return 0.0


def buscar_produtos_sem_giro(client: BlingClient, dias: int = 30) -> str:
    """
    Produtos que não venderam nada nos últimos N dias.

    Usa busca paralela de detalhes de pedidos para eliminar latência N+1.
    """
    data_fim = datetime.now().strftime("%Y-%m-%d")
    data_inicio = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d")

    pedidos = client.get_all_pages("pedidos/vendas", params={
        "dataInicial": data_inicio, "dataFinal": data_fim,
    })
    pedidos = [p for p in pedidos if p.get("situacao", {}).get("id") not in SITUACOES_EXCLUIDAS]

    # Buscar detalhes em paralelo
    detalhes_map = _buscar_detalhes_paralelo(client, pedidos)

    # Coletar IDs de produtos vendidos
    ids_vendidos = set()
    for detalhe in detalhes_map.values():
        for item in detalhe.get("itens", []):
            pid = item.get("produto", {}).get("id")
            if pid:
                ids_vendidos.add(pid)

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
