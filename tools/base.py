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

    def get(self, endpoint: str, params: dict = None) -> dict:
        """GET request para a API do Bling."""
        return self._request("GET", endpoint, params=params)

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
