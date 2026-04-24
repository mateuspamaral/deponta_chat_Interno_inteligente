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

    /* Base */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Header area */
    header[data-testid="stHeader"] {
        background-color: rgba(14, 14, 26, 0.95);
        backdrop-filter: blur(10px);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #12121f;
        border-right: 1px solid rgba(76, 175, 80, 0.15);
    }

    section[data-testid="stSidebar"] .stMarkdown h1 {
        font-size: 1.3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #4CAF50, #81C784);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* Chat messages */
    .stChatMessage {
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 1rem;
        margin-bottom: 0.5rem;
    }

    /* User message */
    .stChatMessage[data-testid="stChatMessage-user"] {
        background-color: rgba(76, 175, 80, 0.08);
        border-color: rgba(76, 175, 80, 0.15);
    }

    /* Assistant message */
    .stChatMessage[data-testid="stChatMessage-assistant"] {
        background-color: rgba(26, 26, 46, 0.6);
    }

    /* Chat input */
    .stChatInput {
        border-color: rgba(76, 175, 80, 0.3);
    }
    .stChatInput:focus-within {
        border-color: #4CAF50;
        box-shadow: 0 0 0 1px rgba(76, 175, 80, 0.3);
    }

    /* Status indicator */
    .status-connected {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .status-connected.online {
        background: rgba(76, 175, 80, 0.15);
        color: #81C784;
        border: 1px solid rgba(76, 175, 80, 0.3);
    }
    .status-connected.offline {
        background: rgba(244, 67, 54, 0.15);
        color: #ef9a9a;
        border: 1px solid rgba(244, 67, 54, 0.3);
    }

    /* Suggestion chips */
    .suggestion-chip {
        display: inline-block;
        padding: 8px 16px;
        margin: 4px;
        border-radius: 20px;
        background: rgba(76, 175, 80, 0.1);
        border: 1px solid rgba(76, 175, 80, 0.25);
        color: #a5d6a7;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s;
    }

    /* Divider */
    .sidebar-divider {
        border: none;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        margin: 1rem 0;
    }

    /* Tables in chat */
    .stChatMessage table {
        border-collapse: collapse;
        width: 100%;
        margin: 0.5rem 0;
    }
    .stChatMessage th {
        background: rgba(76, 175, 80, 0.15);
        padding: 8px 12px;
        text-align: left;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .stChatMessage td {
        padding: 6px 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        font-size: 0.85rem;
    }

    /* Welcome message */
    .welcome-title {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #4CAF50, #81C784, #C8E6C9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    .welcome-subtitle {
        color: #9e9e9e;
        font-size: 1rem;
        margin-bottom: 2rem;
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
        '<div class="welcome-title">De Ponta Chat Intelligence</div>',
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
