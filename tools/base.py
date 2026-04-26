"""
Cliente HTTP base para a API do Bling.
Gerencia autenticação, rate limiting, paginação e logging.
"""

import logging
import time

import requests

from auth.bling_auth import BlingAuth
from utils.constants import BLING_BASE_URL, BLING_PAGE_LIMIT

logger = logging.getLogger(__name__)

# TTL em segundos por prefixo de endpoint.
# Dados de catálogo (produtos, categorias) → cache longo.
# Dados transacionais (pedidos, contas, estoques) → cache curto ou sem cache.
ENDPOINT_CACHE_TTL: dict[str, int] = {
    "produtos":           1800,  # 30 min — catálogo muda pouco
    "categorias":         1800,
    "formas-pagamentos":  1800,
    "canais-venda":       1800,
    "depositos":          1800,
    "vendedores":         1800,
    "contatos":            600,  # 10 min
    "pedidos/vendas":      120,  # 2 min — transacional
    "contas/receber":      120,
    "contas/pagar":        120,
    "estoques":            120,
    "nfe":                 300,
    "nfce":                300,
    "nfse":                300,
    "anuncios":            300,
    "caixas":               60,  # 1 min — extrato financeiro
    "_default":            300,  # 5 min para qualquer outro
}


class BlingAPIError(Exception):
    """Erro na chamada à API do Bling."""
    pass


class BlingClient:
    """
    Cliente HTTP para API do Bling v3.
    
    - Injeta Bearer token automaticamente
    - Retry com backoff exponencial em rate limiting (429)
    - Paginação automática
    - Timeout de 30s por request
    """

    MAX_RETRIES = 3
    BASE_BACKOFF = 1.0  # segundos

    def __init__(self, auth: BlingAuth):
        self.auth = auth
        self.session = requests.Session()
        self.session.timeout = 30
        # Cache com TTL: {cache_key: {"data": dict, "expires_at": float}}
        self._cache: dict[str, dict] = {}

    def _request(self, method: str, endpoint: str, params: dict = None, **kwargs) -> dict:
        """
        Faz request com retry em caso de rate limiting.
        Retorna o JSON parseado da resposta.
        """
        url = f"{BLING_BASE_URL}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.MAX_RETRIES):
            headers = self.auth.get_auth_header()
            headers["Accept"] = "application/json"

            try:
                start = time.time()
                response = self.session.request(
                    method, url, headers=headers, params=params, **kwargs
                )
                elapsed = time.time() - start
                
                logger.debug(
                    "Bling %s %s [%d] %.2fs",
                    method, endpoint, response.status_code, elapsed
                )

            except requests.RequestException as e:
                logger.error("Erro de conexão com Bling: %s", e)
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.BASE_BACKOFF * (2 ** attempt))
                    continue
                raise BlingAPIError(f"Falha de conexão após {self.MAX_RETRIES} tentativas: {e}")

            # Rate limiting — espera e retenta
            if response.status_code == 429:
                wait = self.BASE_BACKOFF * (2 ** attempt)
                logger.warning("Rate limit Bling. Aguardando %.1fs...", wait)
                time.sleep(wait)
                continue

            # Token expirado — força refresh e retenta
            if response.status_code == 401:
                logger.warning("Token Bling expirado. Renovando...")
                self.auth._access_token = None  # força refresh
                continue

            # Erros do servidor
            if response.status_code >= 500:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.BASE_BACKOFF * (2 ** attempt))
                    continue
                raise BlingAPIError(f"Erro do servidor Bling: HTTP {response.status_code}")

            # Erros do cliente (exceto 401 e 429 já tratados)
            if response.status_code >= 400:
                raise BlingAPIError(
                    f"Erro na API Bling: HTTP {response.status_code} — {response.text[:500]}"
                )

            return response.json()

        raise BlingAPIError("Número máximo de retentativas excedido.")

    def _get_cache_ttl(self, endpoint: str) -> int:
        """Retorna TTL em segundos baseado no prefixo do endpoint."""
        endpoint_clean = endpoint.lstrip("/")
        for prefix, ttl in ENDPOINT_CACHE_TTL.items():
            if endpoint_clean.startswith(prefix):
                return ttl
        return ENDPOINT_CACHE_TTL["_default"]

    def get(self, endpoint: str, params: dict = None, use_cache: bool = True) -> dict:
        """
        GET request para a API do Bling com cache TTL em memória.

        O TTL é definido por tipo de endpoint em ENDPOINT_CACHE_TTL:
        - Dados de catálogo (produtos, categorias): 30 min
        - Dados transacionais (pedidos, contas): 2 min
        - Padrão: 5 min

        Args:
            endpoint: caminho do endpoint sem a base URL
            params: parâmetros de query string
            use_cache: False força request mesmo com cache válido
        """
        if not use_cache:
            return self._request("GET", endpoint, params=params)

        cache_key = f"{endpoint}_{str(params or {})}"
        entry = self._cache.get(cache_key)

        if entry and time.time() < entry["expires_at"]:
            logger.debug("Cache hit: %s (expira em %.0fs)", endpoint,
                         entry["expires_at"] - time.time())
            return entry["data"]

        result = self._request("GET", endpoint, params=params)
        ttl = self._get_cache_ttl(endpoint)
        self._cache[cache_key] = {
            "data": result,
            "expires_at": time.time() + ttl,
        }
        logger.debug("Cache set: %s (TTL=%ds)", endpoint, ttl)
        return result

    def clear_cache(self, endpoint_prefix: str = None) -> int:
        """
        Limpa o cache em memória.

        Args:
            endpoint_prefix: se informado, remove apenas entradas cujo
                             cache_key começa com este prefixo.
                             Se None, limpa todo o cache.

        Returns:
            Número de entradas removidas.
        """
        if endpoint_prefix is None:
            count = len(self._cache)
            self._cache.clear()
            logger.info("Cache limpo: %d entradas removidas", count)
            return count

        keys_to_remove = [k for k in self._cache if k.startswith(endpoint_prefix)]
        for k in keys_to_remove:
            del self._cache[k]
        logger.info("Cache parcial limpo: %d entradas removidas (prefix='%s')",
                    len(keys_to_remove), endpoint_prefix)
        return len(keys_to_remove)

    def get_all_pages(self, endpoint: str, params: dict = None) -> list:
        """
        GET com paginação automática. 
        Retorna lista consolidada de todos os itens (campo 'data').
        Percorre todas as páginas até não haver mais dados.
        """
        if params is None:
            params = {}
        
        params["limite"] = BLING_PAGE_LIMIT
        all_items = []
        page = 1

        while True:
            params["pagina"] = page
            response = self.get(endpoint, params=params)
            
            data = response.get("data", [])
            if not data:
                break
            
            all_items.extend(data)
            
            # Se retornou menos que o limite, é a última página
            if len(data) < BLING_PAGE_LIMIT:
                break
            
            page += 1
            logger.debug("Paginação: página %d carregada (%d itens)", page - 1, len(data))

        logger.info(
            "GET %s — %d itens em %d páginas",
            endpoint, len(all_items), page
        )
        return all_items
