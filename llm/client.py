"""
Cliente LLM com agentic loop para tool calling.
Usa Groq API com Llama 3.3 70B.
"""

import json
import logging
import os

from groq import Groq

from auth.bling_auth import BlingAuth
from llm.system_prompt import get_system_prompt
from llm.tool_definitions import TOOL_DEFINITIONS
from tools.base import BlingClient
from tools.pedidos import buscar_pedidos, buscar_detalhe_pedido
from tools.produtos import buscar_produtos, buscar_detalhe_produto
from tools.estoque import buscar_estoque_critico, calcular_cobertura_estoque
from tools.financeiro import (
    calcular_faturamento, calcular_margem_produtos,
    buscar_produtos_sem_giro, comparar_periodos,
)

logger = logging.getLogger(__name__)

MODEL = "llama-3.3-70b-versatile"
MAX_TOOL_ITERATIONS = 10
TEMPERATURE = 0.3


class ChatEngine:
    """
    Motor de chat com tool calling agentic loop.
    
    Fluxo:
    1. Usuário envia mensagem
    2. LLM decide se precisa de tools
    3. Se sim: executa tools → envia resultados → LLM gera resposta
    4. Loop continua até LLM dar resposta final ou atingir max_iterations
    """

    def __init__(self, bling_auth: BlingAuth):
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY não encontrada no .env")

        self.groq = Groq(api_key=api_key)
        self.bling_client = BlingClient(bling_auth)
        self.messages: list[dict] = []

        # Registry: nome da tool → função Python
        self._functions = {
            "calcular_faturamento": lambda **kw: calcular_faturamento(self.bling_client, **kw),
            "buscar_pedidos": lambda **kw: buscar_pedidos(self.bling_client, **kw),
            "buscar_estoque_critico": lambda **kw: buscar_estoque_critico(self.bling_client, **kw),
            "calcular_margem_produtos": lambda **kw: calcular_margem_produtos(self.bling_client, **kw),
            "buscar_produtos_sem_giro": lambda **kw: buscar_produtos_sem_giro(self.bling_client, **kw),
            "comparar_periodos": lambda **kw: comparar_periodos(self.bling_client, **kw),
            "buscar_produtos": lambda **kw: buscar_produtos(self.bling_client, **kw),
            "calcular_cobertura_estoque": lambda **kw: calcular_cobertura_estoque(self.bling_client, **kw),
        }

    def _execute_tool(self, tool_call) -> str:
        """Executa uma tool call e retorna resultado como string."""
        func_name = tool_call.function.name
        
        if func_name not in self._functions:
            return json.dumps({"error": f"Tool desconhecida: {func_name}", "is_error": True})

        try:
            args = json.loads(tool_call.function.arguments)
            logger.info("Executando tool: %s(%s)", func_name, args)
            result = self._functions[func_name](**args)
            return result
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Argumentos inválidos: {e}", "is_error": True})
        except Exception as e:
            logger.error("Erro ao executar tool %s: %s", func_name, e)
            return json.dumps({"error": str(e), "is_error": True})

    def process_message(self, user_input: str) -> str:
        """
        Processa mensagem do usuário com agentic loop.
        Retorna a resposta final do LLM.
        """
        # Adicionar system prompt se é a primeira mensagem
        if not self.messages:
            self.messages.append({
                "role": "system",
                "content": get_system_prompt(),
            })

        # Adicionar mensagem do usuário
        self.messages.append({"role": "user", "content": user_input})

        # Agentic loop
        for iteration in range(MAX_TOOL_ITERATIONS):
            try:
                response = self.groq.chat.completions.create(
                    model=MODEL,
                    messages=self.messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=TEMPERATURE,
                    max_completion_tokens=4096,
                )
            except Exception as e:
                logger.error("Erro na chamada Groq: %s", e)
                error_msg = f"Erro ao consultar o modelo de IA: {str(e)}"
                self.messages.append({"role": "assistant", "content": error_msg})
                return error_msg

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # Adicionar resposta do modelo ao histórico
            self.messages.append(response_message)

            # Se não tem tool calls, é a resposta final
            if not tool_calls:
                content = response_message.content or ""
                logger.info("Resposta final do LLM (iteração %d)", iteration + 1)
                return content

            # Executar cada tool call
            logger.info(
                "Iteração %d: modelo chamou %d tool(s)",
                iteration + 1, len(tool_calls)
            )
            for tool_call in tool_calls:
                result = self._execute_tool(tool_call)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": result,
                })

        # Se excedeu iterações, informar
        fallback = "Desculpe, a consulta exigiu muitas chamadas à API. Tente reformular a pergunta de forma mais específica."
        self.messages.append({"role": "assistant", "content": fallback})
        return fallback

    def clear_history(self):
        """Limpa histórico de conversa."""
        self.messages = []
