# De Ponta Chat Intelligence — Contexto Completo do Projeto
**Documento gerado em 23/04/2026 para iniciar nova conversa com IA**

---

## 1. Quem é o usuário

**Mateus Pessoa Amaral** — profissional de TI sênior, 15+ anos de experiência, cofundador e Head de Tecnologia da De Ponta Hemp Shop. Está em transição estruturada para AI Engineer com prazo de 3 meses. Bilíngue PT/EN, baseado em Belo Horizonte/MG.

Stack atual de IA: n8n (em produção), Evolution API, Prompt Engineering, Google Apps Script, Python (em evolução), Agno, LangChain, MCP.

**Postura esperada da IA:** direta, orientada a execução, sem explicar conceitos básicos, sem elogios genéricos. O usuário é técnico sênior.

---

## 2. O que é o projeto

**De Ponta Chat Intelligence** — um ambiente de chat inteligente, inspirado na interface do Claude, que interpreta perguntas em linguagem natural e responde com dados em tempo real extraídos diretamente da API do ERP Bling. O objetivo é substituir a navegação manual por múltiplas telas do Bling por um único ponto de consulta inteligente e contextualizado.

### Por que este projeto existe

O Bling já resolve gestão operacional padrão. O que ele não entrega é inteligência interpretativa: você consegue ver o que aconteceu, mas não recebe leitura contextualizada, cruzamento de métricas por intenção de negócio, ou análise narrativa. Este projeto cria essa camada.

### Posição no portfólio

Este é o **Case 1** do portfólio de AI Engineer do Mateus. Precisa ser:
- Real e útil para a operação da De Ponta
- Mensurável com antes/depois documentado
- Forte o suficiente para LinkedIn, GitHub e currículo
- Alinhado com o que vagas de AI Engineer, Conversational AI e AI Automation exigem

---

## 3. Decisões de arquitetura já tomadas

| Decisão | Escolha | Motivo |
|---|---|---|
| Fonte de dados | API do Bling em tempo real | Dado sempre atualizado, sem cache local |
| LLM | Gratuito (Groq com Llama 3 ou Gemini free tier) | Sem custo operacional no v1 |
| Interface inicial | Local (localhost) | Simplicidade para começar, preparado para deploy |
| Escopo inicial | Somente consulta (read-only) | Segurança, testes primeiro |
| Arquitetura | Modular | Começa com Bling, depois adiciona Bagy, Google Drive, etc. |
| Evolução planejada | Local → servidor próprio → mobile | Progressivo |

### Sobre o LLM gratuito — recomendação técnica

**Groq API (recomendado para v1):**
- Gratuito no free tier com rate limits generosos
- Modelos: Llama 3.1 70B e Llama 3.3 70B
- Extremamente rápido (especializado em inferência rápida)
- API compatível com o padrão OpenAI (facilita migração futura)
- Cadastro em: https://console.groq.com

**Google Gemini (alternativa):**
- Gemini 1.5 Flash gratuito com limites generosos
- Google AI Studio: https://aistudio.google.com

**Ollama (fallback totalmente local):**
- Sem custo algum, sem internet, sem limite de chamadas
- Modelos rodam localmente (requer hardware razoável)
- Ideal como backup ou para dados sensíveis

---

## 4. Contexto técnico do Bling — já mapeado

### Credenciais e acesso
- **ERP:** Bling (plano Titânio Faixa 2)
- **API:** REST, autenticação OAuth 2.0 com refresh token
- **Documentação:** https://developer.bling.com.br/referencia
- **Autenticação:** https://developer.bling.com.br/autenticacao
- **App criado:** "dePONTA Hemp Shop" no Cadastro de Aplicativos do Bling
- **Credenciais:** client_id e client_secret já obtidos pelo usuário
- **Token expira em:** 21600 segundos (6 horas) — refresh token automático necessário

### Escopos configurados (todos ativos)
- ✅ Anúncios de Marketplaces
- ✅ Clientes e Fornecedores
- ✅ Controle de Estoque
- ✅ Depósitos de Estoque
- ✅ Integrações e Lojas Virtuais
- ✅ Nota fiscal de consumidor eletrônica (NFC-e)
- ✅ Notas Fiscais
- ✅ Pedidos de Venda
- ✅ Produtos

### Contexto operacional da De Ponta
- **Canais de venda:** balcão físico (PDV do Bling) e e-commerce (plataforma Bagy)
- **Integração Bagy→Bling:** pedidos aprovados na Bagy chegam automaticamente ao Bling
- **Volume:** ~618 pedidos/mês
- **Dados históricos confiáveis desde:** janeiro de 2025
- **Custo de produto:** cadastrado no Bling (viabiliza análise de margem)
- **Categorias:** todos os produtos têm categoria cadastrada
- **Variantes:** existem produtos com variantes (modelo pai/filho) — estrutura mapeada
- **iFood:** operação encerrada, dados históricos existem no Bling mas não são foco

---

## 5. Mapeamento completo da API do Bling — resultado do discovery

### 5.1 Identificação de canal (PDV vs. e-commerce)

A distinção é feita pelo campo `loja.id` no objeto do pedido:

```python
LOJAS = {
    203925713: "PDV",       # Stop Gallery — loja física
    205259157: "E-commerce" # Bagy
}
```

**Sinais secundários de confirmação:**
- Pedido PDV: `intermediador.cnpj == ""`, `transporte.frete == 0`, `numeroLoja == ""`
- Pedido Bagy: `intermediador.cnpj == "21.345.139/0001-47"`, `transporte.frete > 0` (quando tem frete), `numeroLoja` preenchido com número do pedido Bagy

### 5.2 Campos de valor nos pedidos

```
ATENÇÃO: não confundir totalProdutos com total

totalProdutos = receita de produto (sem frete)  ← usar este para análise de receita
frete         = transporte.frete
total         = totalProdutos + frete            ← valor pago pelo cliente, inclui frete
```

**Exemplo real:**
```
Pedido Bagy #34636:
  totalProdutos = 35.00   (produto)
  frete         = 32.14   (PAC)
  total         = 67.14   (o que o cliente pagou)
```

### 5.3 Itens do pedido

Os itens já vêm no endpoint de detalhe — sem chamada adicional:

```
GET /Api/v3/pedidos/vendas/{id}

Campos relevantes por item:
  item.produto.id      → id do produto (pode ser variante)
  item.codigo          → código interno do produto
  item.descricao       → nome do produto
  item.quantidade      → quantidade vendida
  item.valor           → preço unitário no pedido
  item.desconto        → desconto em valor absoluto
```

### 5.4 Estrutura de variantes (pai/filho)

```
PRODUTO PAI:  formato = "V"  (tem variações)
VARIANTE:     formato = "S"  (produto simples, filho)

Para resolver variante → pai:
  variante["variacao"]["produtoPai"]["id"]  → id do produto pai

Para nome e categoria de exibição:
  Buscar produto pai → usar nome, categoria, marca do pai

Na listagem GET /produtos?tipo=V:
  item["idProdutoPai"]  → disponível diretamente sem chamar detalhe
```

**Atenção:** algumas variantes antigas têm `precoCusto: 0` — tratar como dado ausente.

### 5.5 Custo do produto

O campo `precoCusto` está disponível na **listagem** paginada mas não aparece no endpoint de detalhe individual. No detalhe, o custo está em:

```python
# Fonte correta no endpoint de detalhe:
custo = produto["fornecedor"]["precoCusto"]

# Na listagem paginada:
custo = item["precoCusto"]  # disponível diretamente
```

### 5.6 Estoque — atenção para negativo

```python
# Algumas variantes têm saldoVirtualTotal negativo (venda sem reposição)
# Tratar assim:
estoque_efetivo = max(0, produto["estoque"]["saldoVirtualTotal"])
```

### 5.7 Endpoints principais

```
GET /Api/v3/pedidos/vendas           → listagem de pedidos (paginado, limite 100/página)
GET /Api/v3/pedidos/vendas/{id}      → detalhe do pedido com itens
GET /Api/v3/produtos                 → listagem de produtos
GET /Api/v3/produtos?tipo=V          → apenas variantes
GET /Api/v3/produtos/{id}            → detalhe do produto
GET /Api/v3/estoques                 → posição de estoque
GET /Api/v3/contatos                 → base de clientes
GET /Api/v3/categorias               → hierarquia de categorias
```

### 5.8 Autenticação OAuth 2.0

```python
# Fluxo de renovação — token expira em 6h, renovar automaticamente

POST https://www.bling.com.br/Api/v3/oauth/token
Headers: Authorization: Basic base64(client_id:client_secret)
Body: grant_type=refresh_token&refresh_token={refresh_token}

Resposta:
{
  "access_token": "...",
  "expires_in": 21600,
  "token_type": "Bearer",
  "refresh_token": "..."  ← salvar o novo refresh_token para próxima renovação
}
```

---

## 6. O que construir — visão do produto

### 6.1 Conceito

Uma interface de chat em Python (Streamlit) onde o usuário digita perguntas em português natural e recebe respostas contextualizadas baseadas em dados em tempo real do Bling. Inspiração visual: Claude.ai.

**Exemplos de perguntas que o sistema deve responder:**
- "Qual foi o faturamento dessa semana comparado com a semana passada?"
- "Quais produtos estão com risco de ruptura de estoque?"
- "Como foram as vendas do balcão hoje?"
- "Qual produto tem a maior margem?"
- "Me mostra os 10 produtos mais vendidos no último mês"
- "Tem algum pedido da Bagy pendente de envio?"
- "Qual a margem média do e-commerce vs. balcão?"
- "Quais produtos não venderam nada nos últimos 30 dias?"

### 6.2 Fluxo de uma conversa

```
1. Usuário digita pergunta em linguagem natural
2. Sistema envia pergunta para o LLM com contexto sobre os dados disponíveis
3. LLM decide quais endpoints do Bling precisam ser chamados
4. Sistema chama a API do Bling em tempo real
5. Dados brutos são processados e formatados
6. LLM interpreta os dados e gera resposta em português natural
7. Resposta aparece no chat com dados, números e interpretação
```

### 6.3 Diferenciais que fazem este ser um case de AI Engineer

- LLM interpreta a intenção da pergunta e decide quais dados buscar (não é só uma busca fixa)
- Resposta contextualizada com leitura operacional, não só números brutos
- Arquitetura modular com tool calling — cada fonte de dados é uma "ferramenta" que o LLM pode chamar
- Pronto para escalar: adicionar Bagy, Google Drive, ou qualquer outra fonte é adicionar um novo tool

---

## 7. Arquitetura técnica recomendada

### 7.1 Stack

```
Interface:      Streamlit  (chat UI inspirado no Claude)
LLM:            Groq API   (Llama 3.1 70B ou 3.3 70B — gratuito)
Tool Calling:   Implementação manual com function calling do LLM
API do Bling:   requests + OAuth 2.0 com refresh automático
Sem banco:      Todas as consultas em tempo real na API do Bling
Versionamento:  Git + GitHub
```

### 7.2 Padrão de arquitetura — Tool Calling

O LLM não vai ter acesso direto à API do Bling. Ele vai ter acesso a **ferramentas** (tools/functions) que encapsulam chamadas específicas:

```
Tool: buscar_pedidos(data_inicio, data_fim, canal=None, status=None)
Tool: buscar_produtos(categoria=None, com_estoque=None)
Tool: buscar_estoque_produto(produto_id)
Tool: calcular_faturamento(data_inicio, data_fim, canal=None)
Tool: buscar_produtos_sem_giro(dias=30)
Tool: calcular_margem_produtos(top_n=10)
```

O LLM recebe a pergunta do usuário, decide quais tools usar e com quais parâmetros, o sistema executa as tools (chamadas reais à API), e o LLM recebe os dados e gera a resposta final.

### 7.3 Estrutura de diretórios

```
deponta-chat/
├── README.md
├── .env                    # CLIENT_ID, CLIENT_SECRET, GROQ_API_KEY (nunca commitar)
├── .env.example            # template sem dados sensíveis
├── requirements.txt
├── app.py                  # ponto de entrada — Streamlit
├── auth/
│   └── bling_auth.py       # OAuth 2.0 + refresh token automático
├── tools/                  # cada arquivo = uma ferramenta do LLM
│   ├── __init__.py
│   ├── pedidos.py          # buscar e processar pedidos
│   ├── produtos.py         # buscar produtos, variantes, custo
│   ├── estoque.py          # posição e cobertura de estoque
│   ├── financeiro.py       # faturamento, margem, receita
│   └── base.py             # cliente HTTP compartilhado, rate limiting
├── llm/
│   ├── client.py           # cliente Groq
│   ├── system_prompt.py    # prompt de sistema do chat
│   └── tool_definitions.py # definição das tools para o LLM
├── utils/
│   ├── formatters.py       # formatação de datas, moedas, tabelas
│   └── constants.py        # LOJAS map, situações de pedido, etc.
└── docs/
    ├── baseline.md         # métricas antes — já documentado
    └── arquitetura.md      # diagrama e decisões
```

### 7.4 Constantes já mapeadas

```python
# utils/constants.py

LOJAS = {
    203925713: "PDV",
    205259157: "E-commerce"
}

SITUACOES_PEDIDO = {
    # mapear ids de situação para textos legíveis
    # verificar na API quais situações existem
}

BLING_BASE_URL = "https://api.bling.com.br/Api/v3"
TOKEN_EXPIRY_SECONDS = 21600  # 6 horas
```

### 7.5 Interface Streamlit — inspiração Claude

A interface deve ter:
- Área de chat com histórico de mensagens
- Campo de input fixo na parte inferior
- Mensagens do usuário alinhadas à direita
- Respostas do assistente à esquerda, com nome "De Ponta AI"
- Indicador de "digitando..." durante chamadas à API
- Sidebar com informações de contexto (última atualização, status da conexão com Bling)
- Suporte a markdown nas respostas (tabelas, listas, negrito)

---

## 8. Métricas de negócio que o sistema deve saber calcular

### Métricas prioritárias (v1)

| Métrica | Como calcular | Fonte |
|---|---|---|
| Faturamento por período | soma de `totalProdutos` dos pedidos | `/pedidos/vendas` |
| Ticket médio | faturamento ÷ número de pedidos | `/pedidos/vendas` |
| Faturamento por canal | agrupar por `loja.id` | `/pedidos/vendas` |
| Margem bruta por produto | `valor_venda - fornecedor.precoCusto` | `/pedidos/vendas` + `/produtos` |
| Cobertura em dias | `estoque_atual ÷ (vendas_30d ÷ 30)` | `/estoques` + `/pedidos/vendas` |
| Produtos sem giro | produtos sem venda nos últimos N dias | `/pedidos/vendas` + `/produtos` |
| Receita por categoria | agrupar por `categoria.id` do produto pai | `/pedidos/vendas` + `/produtos` |
| Top N produtos | por volume ou por receita | `/pedidos/vendas` |

### Campos de atenção no cálculo

- **Receita de produto:** usar `totalProdutos`, não `total` (que inclui frete)
- **Custo:** usar `fornecedor.precoCusto` no detalhe do produto
- **Variantes:** resolver variante→pai para agrupamentos por produto
- **Estoque negativo:** tratar como zero no cálculo de cobertura

---

## 9. Prompt de sistema sugerido para o LLM

```
Você é o assistente de inteligência operacional da De Ponta Hemp Shop, uma loja multicanal com balcão físico e e-commerce.

Você tem acesso a ferramentas que consultam em tempo real o ERP Bling da empresa.

Canais de venda:
- PDV: vendas no balcão físico da loja Stop Gallery
- E-commerce: vendas pelo site (plataforma Bagy)

Ao receber uma pergunta:
1. Identifique quais dados são necessários para responder
2. Use as ferramentas disponíveis para buscar esses dados
3. Interprete os números e responda com contexto operacional, não apenas com dados brutos
4. Se algo indicar uma situação de atenção (estoque baixo, queda de vendas, margem negativa), aponte explicitamente

Responda sempre em português brasileiro. Seja direto e objetivo.
Use tabelas quando apresentar listas de produtos ou comparativos.
Mostre variações percentuais quando comparar períodos.
```

---

## 10. O que NÃO construir no v1 (escopo fora)

```
❌ Banco de dados local (SQLite, PostgreSQL) — tudo em tempo real
❌ Ações de escrita (criar pedido, alterar estoque, etc.)
❌ Integração com Bagy, Google Drive, WhatsApp — módulos futuros
❌ Autenticação de usuário — uso pessoal local por enquanto
❌ Deploy em servidor — fase 2
❌ Mobile — fase 3
❌ Análise de ML ou previsão de demanda — v2+
```

---

## 11. Baseline documentado (antes da solução)

Medido em 22/04/2026:

| Consulta | Tempo atual | Processo |
|---|---|---|
| Faturamento semana vs. semana passada | 1min 22seg | Relatórios do Bling + montar no Google Sheets |
| Produtos prestes a zerar estoque | 1min 44seg | Dashboard Meu Negócio > Sugestão de Compras |
| Balcão vs. e-commerce no mês | 15seg | Dashboard > Valor por Canal |
| Leitura completa da operação | múltiplas abas | Navegação manual no Bling |

**Meta com o chat:** qualquer uma dessas perguntas respondida em menos de 30 segundos, com interpretação contextualizada junto com o dado.

---

## 12. Roadmap de evolução modular

```
v1 — Chat local com Bling (este projeto)
  ↓
v2 — Adicionar Bagy como fonte de dados
     Tool: buscar_pedidos_bagy(), buscar_produtos_bagy()
  ↓
v3 — Adicionar Google Drive/Sheets
     Tool: buscar_planilha(), buscar_documento()
  ↓
v4 — Ações (write)
     Tool: marcar_produto_reposicao(), criar_nota_operacional()
  ↓
v5 — Deploy em servidor (Render, Railway ou VPS)
  ↓
v6 — Acesso mobile (PWA ou app simples)
```

---

## 13. Primeiras tarefas para a nova conversa de IA

Execute nesta ordem:

```
1. Configurar ambiente Python
   pip install streamlit groq requests python-dotenv

2. Criar .env com as variáveis:
   BLING_CLIENT_ID=...
   BLING_CLIENT_SECRET=...
   BLING_REFRESH_TOKEN=...   ← obter no primeiro fluxo de autorização
   GROQ_API_KEY=...          ← obter em console.groq.com (gratuito)

3. Implementar auth/bling_auth.py
   - Renovação automática do token
   - Salvar novo refresh_token a cada renovação
   - Tratar erros de autenticação

4. Implementar tools/base.py
   - Cliente HTTP com autenticação injetada
   - Tratamento de rate limiting
   - Logs de chamadas

5. Implementar tools/pedidos.py
   - buscar_pedidos(data_inicio, data_fim)
   - Paginação automática (máximo 100 por página)
   - Mapeamento loja_id → canal

6. Implementar tools/financeiro.py
   - calcular_faturamento(data_inicio, data_fim, canal=None)
   - calcular_ticket_medio(data_inicio, data_fim, canal=None)

7. Implementar llm/client.py
   - Conexão com Groq
   - Suporte a tool calling
   - Histórico de conversa

8. Implementar app.py
   - Interface Streamlit com chat
   - Loop de tool calling

9. Testar com perguntas reais
10. Documentar e preparar para o case de portfólio
```

---

## 14. Referências e links úteis

- Documentação API Bling: https://developer.bling.com.br/referencia
- Autenticação OAuth Bling: https://developer.bling.com.br/autenticacao
- Groq Console (LLM gratuito): https://console.groq.com
- Groq Documentação: https://console.groq.com/docs/tool-use
- Streamlit Documentação: https://docs.streamlit.io
- GitHub do usuário: https://github.com/mateuspamaral (verificar)

---

## 15. Nota sobre o case de portfólio

Para transformar este projeto em case publicável, documentar:

**Durante o desenvolvimento:**
- Print do antes (navegando no Bling manualmente)
- Registro de tempo por tipo de consulta (baseline já feito)

**Após funcionando:**
- Vídeo de 2 minutos demonstrando uma conversa real com o chat
- Comparativo de tempo: pergunta no chat vs. navegação manual
- README completo no GitHub com: problema → solução → stack → como rodar
- Post no LinkedIn: problema real → solução com IA → métrica → stack → aprendizado

**Narrativa para entrevistas:**
"Construí um chat inteligente que interpreta perguntas em linguagem natural e consulta em tempo real o ERP da minha empresa, usando tool calling para decidir quais dados buscar e um LLM para transformar dados brutos em leitura operacional contextualizada."

---

*Documento gerado em 23/04/2026 — De Ponta Chat Intelligence v1*
*Total de contexto consolidado: API mapeada, arquitetura definida, stack escolhida, escopo delimitado, baseline documentado.*
