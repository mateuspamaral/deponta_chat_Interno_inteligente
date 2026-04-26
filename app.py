"""
De Ponta Chat Intelligence — Interface Streamlit.
Chat inteligente com dados em tempo real do Bling.
"""

import logging
import streamlit as st
from dotenv import load_dotenv

# Carregar variáveis de ambiente antes de tudo
load_dotenv()

from auth.bling_auth import BlingAuth, BlingAuthError
from llm.client import ChatEngine

# ============================================================
# Configuração de logging
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ============================================================
# Page config
# ============================================================
st.set_page_config(
    page_title="De Ponta AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS customizado — dark theme inspirado no Claude
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --bg-000: hsl(60, 11%, 97%);
  --bg-100: hsl(60, 11%, 95%);
  --bg-200: hsl(60, 8%, 92%);
  --bg-300: hsl(60, 6%, 88%);
  --text-000: hsl(30, 20%, 12%);
  --text-100: hsl(30, 8%, 18%);
  --text-200: hsl(30, 5%, 32%);
  --text-300: hsl(30, 4%, 48%);
  --text-400: hsl(30, 3%, 58%);
  --text-500: hsl(30, 2%, 68%);
  --accent: #D97757;
  --border-300: hsl(60, 5%, 83%);
  --border-400: hsl(60, 4%, 89%);
}

/* ── Base ── */
.stApp {
  font-family: 'Inter', system-ui, sans-serif;
  background-color: var(--bg-100) !important;
}

.stApp [data-testid="stAppViewContainer"] {
  background-color: var(--bg-100) !important;
}

.stApp > header {
  background-color: var(--bg-100) !important;
  border-bottom: 0.5px solid var(--border-300);
}

/* ── Sidebar — light, not dark ── */
section[data-testid="stSidebar"] {
  background-color: var(--bg-200) !important;
  border-right: 0.5px solid var(--border-300);
}

section[data-testid="stSidebar"] * {
  color: var(--text-200) !important;
}

section[data-testid="stSidebar"] .stMarkdown h1 {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-000) !important;
  letter-spacing: -0.02em;
}

section[data-testid="stSidebar"] .stButton button {
  background: var(--bg-000);
  border: 0.5px solid var(--border-300);
  color: var(--text-200) !important;
  border-radius: 0.6rem;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.12s ease;
  box-shadow: none;
}

section[data-testid="stSidebar"] .stButton button:hover {
  background: var(--bg-100);
  border-color: var(--text-400);
}

/* ── Sidebar divider ── */
.sidebar-divider {
  border: none;
  border-top: 0.5px solid var(--border-300);
  margin: 0.875rem 0;
}

/* ── Chat messages ── */
.stChatMessage {
  background: transparent !important;
  border: none !important;
  padding: 0.625rem 0 !important;
}

/* User bubble — right-aligned feel */
.stChatMessage[data-testid="stChatMessage-user"] .stMarkdown {
  background: var(--bg-200);
  border: 0.5px solid var(--border-300);
  border-radius: 1.2rem 1.2rem 0.25rem 1.2rem;
  padding: 0.875rem 1.125rem;
  margin-left: auto;
  max-width: 85%;
  width: fit-content;
  color: var(--text-100);
  font-size: 0.9375rem;
  line-height: 1.6;
}

/* Assistant bubble */
.stChatMessage[data-testid="stChatMessage-assistant"] .stMarkdown {
  background: var(--bg-000);
  border: 0.5px solid var(--border-400);
  border-radius: 0.25rem 1.2rem 1.2rem 1.2rem;
  padding: 0.875rem 1.125rem;
  max-width: 100%;
  color: var(--text-100);
  font-size: 0.9375rem;
  line-height: 1.65;
  box-shadow: 0 2px 8px 0 hsl(0 0% 0% / 3%);
}

/* ── Tables inside chat ── */
.stChatMessage table {
  border-collapse: collapse;
  width: 100%;
  font-size: 0.875rem;
  margin: 0.75rem 0;
}

.stChatMessage th {
  background: var(--bg-200);
  padding: 7px 12px;
  text-align: left;
  font-weight: 600;
  color: var(--text-200);
  border-bottom: 0.5px solid var(--border-300);
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stChatMessage td {
  padding: 6px 12px;
  border-bottom: 0.5px solid var(--border-400);
  color: var(--text-100);
}

/* ── Chat input ── */
.stChatInput textarea {
  background: var(--bg-000) !important;
  border: 0.5px solid var(--border-300) !important;
  border-radius: 0.75rem !important;
  color: var(--text-100) !important;
  font-family: 'Inter', system-ui, sans-serif !important;
  font-size: 0.9375rem !important;
  line-height: 1.5 !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}

.stChatInput textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px hsl(20 55% 60% / 12%) !important;
  outline: none !important;
}

/* ── Status indicators ── */
.status-connected {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 500;
}

.status-connected.online {
  background: hsl(135, 40%, 93%);
  color: hsl(135, 45%, 30%);
  border: 0.5px solid hsl(135, 35%, 76%);
}

.status-connected.offline {
  background: hsl(0, 40%, 94%);
  color: hsl(0, 55%, 40%);
  border: 0.5px solid hsl(0, 35%, 82%);
}

/* ── Suggestion buttons (welcome screen) ── */
.stButton button {
  background: var(--bg-000);
  border: 0.5px solid var(--border-300);
  color: var(--text-200) !important;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  text-align: left;
  padding: 0.625rem 0.875rem;
  transition: all 0.12s ease;
  box-shadow: 0 1px 3px 0 hsl(0 0% 0% / 4%);
}

.stButton button:hover {
  background: var(--bg-100);
  border-color: var(--text-400);
  box-shadow: 0 2px 6px 0 hsl(0 0% 0% / 6%);
  transform: translateY(-0.5px);
}

/* ── Welcome screen ── */
.welcome-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-000);
  margin-bottom: 0.375rem;
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.welcome-title span {
  color: var(--accent);
}

.welcome-subtitle {
  color: var(--text-300);
  font-size: 0.9375rem;
  margin-bottom: 1.75rem;
  line-height: 1.5;
}

/* ── Spinner ── */
.stSpinner > div {
  border-top-color: var(--accent) !important;
}

/* ── Content area ── */
.block-container {
  max-width: 52rem !important;
  padding-top: 5rem !important;
}

/* ── Code in responses ── */
.stChatMessage code {
  background: var(--bg-200);
  border: 0.5px solid var(--border-300);
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 0.875em;
  color: var(--accent);
}

.stChatMessage pre {
  background: var(--bg-300) !important;
  border: 0.5px solid var(--border-300);
  border-radius: 0.6rem;
  padding: 1rem;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# Inicialização de estado
# ============================================================
def init_session_state():
    """Inicializa variáveis de sessão."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "bling_connected" not in st.session_state:
        st.session_state.bling_connected = False
    if "chat_engine" not in st.session_state:
        st.session_state.chat_engine = None
    if "auth" not in st.session_state:
        st.session_state.auth = None


def init_services():
    """Inicializa BlingAuth e ChatEngine."""
    if st.session_state.chat_engine is not None:
        return True

    try:
        auth = BlingAuth()
        st.session_state.auth = auth
        st.session_state.chat_engine = ChatEngine(auth)
        st.session_state.bling_connected = auth.is_connected()
        return True
    except BlingAuthError as e:
        st.error(f"❌ Erro de autenticação Bling: {e}")
        return False
    except ValueError as e:
        st.error(f"❌ Configuração incompleta: {e}")
        return False
    except Exception as e:
        st.error(f"❌ Erro ao inicializar: {e}")
        return False


# ============================================================
# Sidebar
# ============================================================
def render_sidebar():
    """Renderiza sidebar com status e controles."""
    with st.sidebar:
        st.markdown("# 🌿 De Ponta AI")
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

        # Status da conexão
        if st.session_state.bling_connected:
            st.markdown(
                '<div class="status-connected online">● Bling conectado</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-connected offline">● Bling desconectado</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

        # Botão nova conversa
        if st.button("🔄 Nova conversa", use_container_width=True):
            st.session_state.messages = []
            if st.session_state.chat_engine:
                st.session_state.chat_engine.clear_history()
            st.rerun()

        # Reconectar Bling
        if st.button("🔌 Reconectar Bling", use_container_width=True):
            st.session_state.chat_engine = None
            st.session_state.auth = None
            st.rerun()

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

        # Info
        st.markdown(
            """
            **Exemplos de perguntas:**
            - Qual o faturamento de hoje?
            - Produtos com estoque crítico?
            - Top 5 produtos mais vendidos
            - Compara esta semana com a anterior
            - Margem dos produtos no mês
            - Pedidos pendentes do e-commerce
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.caption("De Ponta Chat Intelligence v1")
        st.caption("Dados em tempo real via Bling API")


# ============================================================
# Welcome screen
# ============================================================
def render_welcome():
    """Tela de boas-vindas quando não há mensagens."""
    st.markdown(
        '<div class="welcome-title">De Ponta <span>AI</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="welcome-subtitle">'
        'Pergunte qualquer coisa sobre a operação da De Ponta. '
        'Dados em tempo real do Bling.'
        '</div>',
        unsafe_allow_html=True,
    )

    # Sugestões de perguntas como botões
    cols = st.columns(2)
    suggestions = [
        "📊 Qual o faturamento de hoje?",
        "📦 Produtos com estoque crítico?",
        "🏆 Top 10 produtos mais vendidos no mês",
        "📈 Compara esta semana com a anterior",
        "💰 Margem dos produtos no último mês",
        "🛒 Pedidos pendentes do e-commerce",
    ]

    for i, suggestion in enumerate(suggestions):
        col = cols[i % 2]
        with col:
            if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                # Remove emoji prefix para a pergunta
                clean = suggestion.split(" ", 1)[1] if " " in suggestion else suggestion
                st.session_state.pending_question = clean
                st.rerun()


# ============================================================
# Main
# ============================================================
def main():
    init_session_state()

    # Inicializar serviços
    services_ok = init_services()

    # Sidebar
    render_sidebar()

    # Se serviços não inicializaram, mostrar erro
    if not services_ok:
        st.warning(
            "⚠️ Preencha as credenciais no arquivo `.env` e reinicie o app.\n\n"
            "Variáveis necessárias:\n"
            "- `BLING_CLIENT_ID`\n"
            "- `BLING_CLIENT_SECRET`\n"
            "- `BLING_REFRESH_TOKEN`\n"
            "- `GROQ_API_KEY`"
        )
        return

    # Se não tem mensagens, mostrar welcome
    if not st.session_state.messages:
        render_welcome()

    # Renderizar histórico de chat
    for msg in st.session_state.messages:
        avatar = "🌿" if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Verificar se tem pergunta pendente (de sugestão)
    pending = st.session_state.pop("pending_question", None)

    # Input do usuário
    user_input = st.chat_input("Pergunte sobre a operação da De Ponta...")

    # Usar pergunta pendente ou input direto
    question = pending or user_input

    if question:
        # Mostrar mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Processar com o ChatEngine
        with st.chat_message("assistant", avatar="🌿"):
            with st.spinner("Consultando dados do Bling..."):
                try:
                    response = st.session_state.chat_engine.process_message(question)
                except Exception as e:
                    logger.error("Erro no processamento: %s", e)
                    response = f"❌ Erro ao processar sua pergunta: {str(e)}"

            st.markdown(response)

        # Salvar resposta no histórico
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Atualizar status de conexão
        if st.session_state.auth:
            st.session_state.bling_connected = st.session_state.auth.is_connected()


if __name__ == "__main__":
    main()
