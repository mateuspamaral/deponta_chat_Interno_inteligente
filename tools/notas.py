"""
Tool de notas fiscais — busca NF-e e NFC-e.
"""

import json
import logging

from tools.base import BlingClient
from utils.constants import LOJAS

logger = logging.getLogger(__name__)


def buscar_notas_fiscais(
    client: BlingClient,
    tipo: str = "todos",
    data_inicio: str = None,
    data_fim: str = None,
    limite: int = 20
) -> str:
    """
    Busca notas fiscais emitidas.
    
    Args:
        client: instância do BlingClient
        tipo: 'nfe', 'nfce' ou 'todos'
        data_inicio: data inicial no formato YYYY-MM-DD
        data_fim: data final no formato YYYY-MM-DD
        limite: número máximo de notas por tipo a retornar
    
    Returns:
        JSON string com lista de notas
    """
    params = {}
    if data_inicio:
        params["dataInicial"] = f"{data_inicio} 00:00:00"
    if data_fim:
        params["dataFinal"] = f"{data_fim} 23:59:59"

    notas = []

    def fetch_notas(endpoint, tipo_label):
        raw = client.get_all_pages(endpoint, params=params)
        for n in raw[:limite]:
            loja_id = n.get("loja", {}).get("id")
            notas.append({
                "id": n.get("id"),
                "tipo_nota": tipo_label,
                "tipo": n.get("tipo", ""),
                "situacao": n.get("situacao", ""),
                "numero": n.get("numero", ""),
                "dataEmissao": n.get("dataEmissao", ""),
                "chaveAcesso": n.get("chaveAcesso", ""),
                "contato": n.get("contato", {}).get("nome", ""),
                "naturezaOperacao": n.get("naturezaOperacao", {}).get("descricao", ""),
                "canal": LOJAS.get(loja_id, "Desconhecido"),
            })

    if tipo.lower() in ["nfe", "todos"]:
        fetch_notas("nfe", "NF-e")
    
    if tipo.lower() in ["nfce", "todos"]:
        fetch_notas("nfce", "NFC-e")

    return json.dumps({
        "total_notas": len(notas),
        "tipo_filtro": tipo,
        "periodo": f"{data_inicio or 'Sempre'} a {data_fim or 'Hoje'}",
        "notas": notas,
    }, ensure_ascii=False)
