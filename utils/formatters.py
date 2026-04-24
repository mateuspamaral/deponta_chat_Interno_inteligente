"""
Formatadores de dados para o De Ponta Chat Intelligence.
Moeda brasileira, datas, percentuais.
"""

from datetime import datetime


def formatar_moeda(valor: float) -> str:
    """Formata valor como moeda brasileira: R$ 1.234,56"""
    if valor < 0:
        return f"-R$ {abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_data(data_str: str) -> str:
    """
    Converte data ISO (2026-04-24 ou 2026-04-24T10:30:00) para formato BR (24/04/2026).
    Retorna a string original se não conseguir parsear.
    """
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            dt = datetime.strptime(data_str[:19], fmt[:len(data_str[:19])])
            return dt.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            continue
    return data_str


def formatar_percentual(valor: float) -> str:
    """Formata percentual com sinal: +12,3% ou -5,7%"""
    sinal = "+" if valor > 0 else ""
    return f"{sinal}{valor:.1f}%".replace(".", ",")


def calcular_variacao(atual: float, anterior: float) -> float:
    """
    Calcula variação percentual entre dois valores.
    Retorna 0 se anterior for 0 (evita divisão por zero).
    """
    if anterior == 0:
        return 0.0 if atual == 0 else 100.0
    return ((atual - anterior) / abs(anterior)) * 100


def data_hoje() -> str:
    """Retorna data de hoje no formato YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def inicio_semana() -> str:
    """Retorna segunda-feira da semana atual no formato YYYY-MM-DD."""
    hoje = datetime.now()
    inicio = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
    inicio -= __import__("datetime").timedelta(days=hoje.weekday())
    return inicio.strftime("%Y-%m-%d")


def inicio_mes() -> str:
    """Retorna primeiro dia do mês atual no formato YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-01")
