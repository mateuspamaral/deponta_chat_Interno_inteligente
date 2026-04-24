# Arquitetura — De Ponta Chat Intelligence

## Visão geral

O sistema segue o padrão **agentic tool calling**: o LLM recebe a pergunta, decide quais ferramentas usar, o sistema executa as ferramentas (chamadas à API do Bling), e o LLM interpreta os resultados para gerar a resposta.

## Fluxo de uma pergunta

```
1. Usuário digita: "Qual o faturamento dessa semana?"
2. Streamlit envia para ChatEngine
3. ChatEngine monta mensagens com system prompt + histórico + pergunta
4. Groq API (Llama 3.3 70B) analisa e retorna tool_calls:
   → calcular_faturamento(data_inicio="2026-04-21", data_fim="2026-04-24")
5. ChatEngine executa a tool, que chama BlingClient → API Bling
6. Resultado JSON é enviado de volta ao LLM
7. LLM gera resposta contextualizada com os dados
8. Resposta aparece no chat
```

## Decisões de design

| Decisão | Motivo |
|---|---|
| Groq + Llama 3.3 70B | Gratuito, rápido (~500 tps), bom suporte a tool calling |
| Sem banco de dados | Dados sempre atualizados, sem complexidade de sync |
| Tool calling local | Controle total sobre execução e segurança |
| Refresh token automático | Token Bling expira em 6h, sistema renova sem intervenção |
| Estoque negativo → zero | Bling permite estoque negativo, mas para análise é zero |
| totalProdutos para receita | Campo `total` inclui frete, não representa receita real |

## Componentes

- **BlingAuth**: OAuth 2.0 com refresh automático e persistência do token
- **BlingClient**: HTTP client com retry, rate limiting e paginação
- **Tools**: Funções de negócio que encapsulam chamadas à API
- **ChatEngine**: Agentic loop que orquestra LLM ↔ Tools
- **Streamlit**: Interface de chat com dark theme
