"""
Autenticação OAuth 2.0 com o Bling.
Gerencia ciclo de vida do token com refresh automático.
"""

import base64
import logging
import os
import threading
import time
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key

logger = logging.getLogger(__name__)

# Caminho do .env na raiz do projeto
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class BlingAuthError(Exception):
    """Erro de autenticação com o Bling."""
    pass


class BlingAuth:
    """
    Gerencia OAuth 2.0 do Bling com refresh automático.
    
    - Token expira em 21600s (6h)
    - Renova automaticamente 5 min antes da expiração
    - Persiste o novo refresh_token no .env (Bling rotaciona tokens)
    - Thread-safe
    """

    TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
    EXPIRY_SECONDS = 21600
    REFRESH_MARGIN = 300  # renova 5 min antes

    def __init__(self):
        load_dotenv(ENV_PATH)

        self.client_id = os.getenv("BLING_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("BLING_CLIENT_SECRET", "").strip()
        self.refresh_token = os.getenv("BLING_REFRESH_TOKEN", "").strip()

        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise BlingAuthError(
                "Credenciais Bling incompletas. Verifique BLING_CLIENT_ID, "
                "BLING_CLIENT_SECRET e BLING_REFRESH_TOKEN no .env"
            )

        self._access_token: str | None = None
        self._token_expires_at: float = 0
        self._lock = threading.Lock()

    @property
    def _basic_auth(self) -> str:
        """Header Authorization: Basic base64(client_id:client_secret)"""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _is_token_valid(self) -> bool:
        """Verifica se o token ainda é válido (com margem de segurança)."""
        if not self._access_token:
            return False
        return time.time() < (self._token_expires_at - self.REFRESH_MARGIN)

    def _do_refresh(self) -> None:
        """Executa refresh do token via API do Bling."""
        logger.info("Renovando token Bling...")

        try:
            response = requests.post(
                self.TOKEN_URL,
                headers={
                    "Authorization": self._basic_auth,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                },
                timeout=30,
            )
        except requests.RequestException as e:
            logger.error("Falha HTTP ao renovar token: %s", e)
            raise BlingAuthError(f"Erro de conexão ao renovar token: {e}")

        if response.status_code == 401 or (response.status_code == 400 and "invalid_grant" in response.text):
            logger.error("Refresh token inválido/expirado (%d). Body: %s", response.status_code, response.text)
            raise BlingAuthError(
                "Refresh token inválido ou expirado. Refaça o fluxo OAuth "
                "no Bling e atualize BLING_REFRESH_TOKEN no .env"
            )

        if response.status_code == 429:
            logger.error("Rate limit (429) no endpoint de token.")
            raise BlingAuthError(
                "Rate limit atingido na renovação de token. Aguarde e tente novamente."
            )

        if response.status_code != 200:
            logger.error("Falha ao renovar token. HTTP %d - %s", response.status_code, response.text)
            raise BlingAuthError(
                f"Erro ao renovar token: HTTP {response.status_code} — {response.text}"
            )

        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", self.EXPIRY_SECONDS)

        # Bling rotaciona refresh tokens — salvar o novo
        new_refresh = data.get("refresh_token")
        if new_refresh:
            self.refresh_token = new_refresh
            self._persist_refresh_token(new_refresh)

        logger.info(
            "Token Bling renovado. Expira em %d segundos.",
            data.get("expires_in", self.EXPIRY_SECONDS),
        )

    def _persist_refresh_token(self, token: str) -> None:
        """Persiste o novo refresh_token no .env para sobreviver a restarts."""
        try:
            set_key(str(ENV_PATH), "BLING_REFRESH_TOKEN", token)
            logger.debug("Novo refresh_token salvo no .env")
        except Exception as e:
            logger.warning("Não foi possível salvar refresh_token no .env: %s", e)

    def get_access_token(self) -> str:
        """
        Retorna access_token válido. Renova automaticamente se necessário.
        Thread-safe.
        """
        with self._lock:
            if not self._is_token_valid():
                self._do_refresh()
            return self._access_token

    def get_auth_header(self) -> dict:
        """Retorna dict com header Authorization pronto para uso."""
        return {"Authorization": f"Bearer {self.get_access_token()}"}

    def is_connected(self) -> bool:
        """Testa se a conexão com o Bling está funcional."""
        try:
            self.get_access_token()
            return True
        except BlingAuthError:
            return False
