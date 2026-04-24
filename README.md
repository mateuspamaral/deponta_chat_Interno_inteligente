# De Ponta Chat Intelligence 🌿

Chat inteligente que interpreta perguntas em linguagem natural e responde com dados em tempo real do ERP Bling.

## O problema

Consultar dados operacionais no Bling exige navegar por múltiplas telas, filtros e relatórios. Uma pergunta simples como "qual foi o faturamento dessa semana?" demora mais de 1 minuto.

## A solução

Um chat que entende português natural e consulta a API do Bling em tempo real, usando LLM com tool calling para decidir quais dados buscar.

**Antes:** 1min22s para comparar faturamento semanal  
**Depois:** < 30 segundos com interpretação contextualizada

## Stack

| Componente | Tecnologia |
|---|---|
| Interface | Streamlit |
| LLM | Groq API (Llama 3.3 70B) |
| Tool Calling | Local function calling |
| Dados | API Bling v3 (real-time) |
| Auth | OAuth 2.0 + refresh automático |

## Como rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar credenciais
cp .env.example .env
# Editar .env com suas credenciais

# 3. Rodar
streamlit run app.py
```

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `BLING_CLIENT_ID` | Client ID do app no Bling |
| `BLING_CLIENT_SECRET` | Client Secret do app no Bling |
| `BLING_REFRESH_TOKEN` | Refresh token do OAuth (atualizado automaticamente) |
| `GROQ_API_KEY` | API key do Groq (gratuito) |

## Exemplos de perguntas

- "Qual foi o faturamento dessa semana?"
- "Quais produtos estão com risco de ruptura de estoque?"
- "Como foram as vendas do balcão hoje?"
- "Qual produto tem a maior margem?"
- "Top 10 produtos mais vendidos no último mês"
- "Compara o faturamento desta semana com a semana passada"

## Arquitetura

```
Usuário → Streamlit → ChatEngine → Groq LLM
                                      ↓
                                  tool_calls
                                      ↓
                              Tools (pedidos, estoque, financeiro)
                                      ↓
                              BlingClient → API Bling v3
                                      ↓
                              Resultados → LLM → Resposta final
```

## Estrutura

```
├── app.py                  # Interface Streamlit
├── auth/
│   └── bling_auth.py       # OAuth 2.0 + refresh automático
├── tools/
│   ├── base.py             # Cliente HTTP com retry + paginação
│   ├── pedidos.py           # Busca de pedidos
│   ├── produtos.py          # Busca de produtos e variantes
│   ├── estoque.py           # Estoque crítico e cobertura
│   └── financeiro.py        # Faturamento, margem, comparativos
├── llm/
│   ├── client.py            # ChatEngine com agentic loop
│   ├── system_prompt.py     # Prompt de sistema
│   └── tool_definitions.py  # Schemas das tools
├── utils/
│   ├── constants.py         # Constantes de negócio
│   └── formatters.py        # Formatação BR
└── docs/
    ├── arquitetura.md
    └── baseline.md
```

---

*De Ponta Chat Intelligence v1 — Case de AI Engineer*