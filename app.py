from google import genai
from google.genai import types
import re
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st

# =====================================================================
# CONFIGURACIÓN DE CREDENCIALES DE SPOTIFY
# =====================================================================
CLIENT_ID = "ce6c0302d9b147aabdcd3f8f4a62bab0"
CLIENT_SECRET = "ce6c0302d9b147aabdcd3f8f4a62bab0"
REDIRECT_URI = "https://spotify-playlist-web-ktnmkfkhdjehk7qzx4eoxq.streamlit.app/"  # O pon http://localhost:8888 si lo pruebas en local
# =====================================================================

st.set_page_config(
    page_title="plAIlister", page_icon="P", layout="centered"
)

# =====================================================================
# ESTILOS CSS UX/UI (AI STYLE & SPOTIFY DARK - CORREGIDO DEFINITIVO)
# =====================================================================
st.markdown(
    """
    <style>
    /* Fondo general de la aplicación */
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Barra lateral en negro absoluto */
    section[data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #282828;
    }
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h3 {
        color: #B3B3B3 !important;
    }
    section[data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
    }

    /* Logo con ondas AI */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
        margin-bottom: 24px;
        padding-top: 10px;
    }
    .ai-wave-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #1DB954;
        border-radius: 50%;
        width: 38px;
        height: 38px;
        font-size: 20px;
        color: #1DB954;
        font-weight: 900;
        background-color: rgba(29, 185, 84, 0.1);
        box-shadow: 0 0 12px rgba(29, 185, 84, 0.4);
    }

    /* Hero Section Minimalista */
    .hero-container {
        padding: 10px 0 20px 0;
        text-align: left;
    }
    .hero-title {
        font-size: 40px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -1px;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        font-size: 20px;
        color: #1DB954;
        font-weight: 600;
        margin-bottom: 24px;
    }

    /* Tarjetas estáticas visibles */
    .feature-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 18px 20px;
        border-radius: 10px;
        border-left: 3px solid #1DB954;
        margin-bottom: 12px;
    }
    .feature-title {
        font-size: 15px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 4px;
    }
    .feature-desc {
        font-size: 13px;
        color: #B3B3B3;
        line-height: 1.4;
    }

    /* BOTONES PRIMARIOS: Verde Spotify con TEXTO NEGRO PURO */
    .stButton>button[kind="primary"] {
        background-color: #1DB954 !important;
        color: #000000 !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        border-radius: 500px !important;
        border: none !important;
        padding: 12px 28px !important;
        box-shadow: 0 4px 14px rgba(29, 185, 84, 0.4);
    }
    .stButton>button[kind="primary"] p,
    .stButton>button[kind="primary"] span {
        color: #000000 !important;
        font-weight: 800 !important;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #1ed760 !important;
    }

    /* Botones secundarios oscuros */
    .stButton>button {
        background-color: #282828;
        color: #FFFFFF !important;
        border: 1px solid #3E3E3E;
        border-radius: 500px;
        font-weight: 600;
        padding: 8px 18px;
    }
    .stButton>button:hover {
        border-color: #FFFFFF;
        background-color: #3E3E3E;
    }

    /* FORZADO ABSOLUTO DE INPUTS Y TEXTAREAS: Fondo #d6d6d6 y Texto #000000 */
    .stTextInput input, 
    .stTextArea textarea,
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input,
    textarea.stTextArea {
        background-color: #d6d6d6 !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border: 1px solid #3E3E3E !important;
        border-radius: 8px;
        padding: 12px;
        font-size: 14px;
        font-weight: 700 !important;
    }
    .stTextInput input:focus, 
    .stTextArea textarea:focus {
        border-color: #1DB954 !important;
        box-shadow: 0 0 0 1px #1DB954 !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* Sliders con acento en verde Spotify */
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: #1DB954 !important;
    }

    /* File Uploader estilizado y texto de botón upload en #3e3e3e */
    div[data-testid="stFileUploader"] {
        background-color: #181818;
        border: 1px dashed #3E3E3E;
        border-radius: 12px;
        padding: 20px;
    }
    div[data-testid="stFileUploader"] section {
        background-color: #d6d6d6 !important;
        border: none !important;
    }
    div[data-testid="stFileUploader"] button {
        color: #3e3e3e !important;
        font-weight: 700 !important;
    }
    div[data-testid="stFileUploader"] span, 
    div[data-testid="stFileUploader"] small {
        color: #555555 !important;
    }

    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    p, label {
        color: #B3B3B3 !important;
        font-size: 14px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# =====================================================================
# INICIALIZACIÓN DE ESTADOS DE SESIÓN
# =====================================================================
if "history_playlists" not in st.session_state:
  st.session_state["history_playlists"] = [
      "Indie Rock Essentials",
      "Latte & Lofi Beats",
      "Tech House Underground",
      "80s Synthwave Drive",
      "Acoustic Coffee Morning",
  ]

if "show_all_history" not in st.session_state:
  st.session_state["show_all_history"] = False

if "resultado_lista" not in st.session_state:
  st.session_state["resultado_lista"] = ""

# =====================================================================
# BARRA LATERAL (SIDEBAR)
# =====================================================================
with st.sidebar:
  st.markdown(
      """
        <div class="logo-container">
            pl<span><div class="ai-wave-badge">AI</div></span>lister
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown("---")
  st.markdown(
      "<h3 style='font-size: 15px; text-transform: uppercase; letter-spacing:"
      " 1px;'>Últimas playlists</h3>",
      unsafe_allow_html=True,
  )

  limit_display = (
      len(st.session_state["history_playlists"])
      if st.session_state["show_all_history"]
      else min(5, len(st.session_state["history_playlists"]))
  )
  recent_playlists = st.session_state["history_playlists"][::-1][
      :limit_display
  ]

  for pl in recent_playlists:
    st.markdown(
        f"<p style='color: #FFFFFF; font-size: 14px; margin: 8px 0; font-weight:"
        f" 500;'>• {pl}</p>",
        unsafe_allow_html=True,
    )

  if len(st.session_state["history_playlists"]) > 5:
    if st.button(
        "Ver más" if not st.session_state["show_all_history"] else "Ver menos",
        key="btn_ver_mas",
        use_container_width=True,
    ):
      st.session_state["show_all_history"] = not st.session_state[
          "show_all_history"
      ]
      st.rerun()

  st.markdown("---")
  st.markdown(
      "<p style='font-size: 12px; color: #727272;'>Conectado a Spotify API"
      " & Google GenAI</p>",
      unsafe_allow_html=True,
  )

# =====================================================================
# PANTALLA PRINCIPAL
# =====================================================================

# HERO SECTION ESTÁTICO
st.markdown('<div class="hero-container">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="hero-title">
        pl<span><div class="ai-wave-badge" style="width: 32px; height: 32px; font-size: 16px;">AI</div></span>lister
    </div>
""",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hero-subtitle">Genera playlists con IA y subelas a Spotify'"</div>",
    unsafe_allow_html=True,
)

st.markdown(
    "<div style='font-size: 15px; color: #FFFFFF; font-weight: 700; margin-top:"
    " 16px; margin-bottom: 12px;'>Usa plAIlister para:</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="feature-card">
        <div class="feature-title">Generar nuevas playlists con IA</div>
        <div class="feature-desc">Crea colecciones musicales personalizadas al instante describiendo cualquier concepto, género o atmósfera.</div>
    </div>
    <div class="feature-card">
        <div class="feature-title">Descubrir nuevos artistas</div>
        <div class="feature-desc">Explora recomendaciones expertas basadas en algoritmos de inteligencia artificial que cruzan estilos musicales afines.</div>
    </div>
    <div class="feature-card">
        <div class="feature-title">Ampliar tus gustos musicales</div>
        <div class="feature-desc">Evoluciona tu biblioteca con selecciones inteligentes conectadas directamente a tu cuenta de Spotify.</div>
    </div>
""",
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")

# =====================================================================
# BLOQUE DEL GENERADOR DE PLAYLISTS CON IA
# =====================================================================
st.markdown(
    "<h2 style='font-size: 22px; margin-bottom: 16px;'>Generador de listas"
    " inteligente</h2>",
    unsafe_allow_html=True,
)

# Campo de texto principal
prompt_usuario = st.text_area(
    "Describe la música que deseas generar:",
    value="",
    height=100,
    key="main_prompt_box",
)

# Parámetros avanzados
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
  num_canciones = st.slider(
      "Cantidad de canciones", min_value=5, max_value=40, value=15
  )
with col_p2:
  num_artistas = st.slider("Artistas distintos", min_value=1, max_value=12, value=5)
with col_p3:
  temperatura = st.slider(
      "Creatividad", min_value=0.0, max_value=1.0, value=0.7
  )

st.markdown("<div style='margin: 16px 0;'></div>", unsafe_allow_html=True)

# Botón de Generación Directa actualizado al modelo gemini-3.8-flash
if st.button("Generar playlist", type="primary", use_container_width=True):
  if not prompt_usuario.strip():
    st.error(
        "Por favor, describe la música o los artistas que deseas incluir."
    )
  else:
    with st.spinner("Gemini está curando tu selección musical..."):
      try:
        ai_client = genai.Client()
        prompt_sistema = (
            f"Actúa como un curador musical profesional. Genera una lista"
            f" exacta de {num_canciones} canciones basada en la solicitud. Debe"
            f" incluir aproximadamente {num_artistas} artistas diferentes.\n\n"
            f"REQUISITO: Devuelve exclusivamente la lista de canciones en"
            f" formato de texto plano, una por línea, con el formato exacto:"
            f" 'Artista - Canción'. Sin números, sin viñetas, sin introducciones."
        )

        response = ai_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=f"{prompt_sistema}\n\nSolicitud: {prompt_usuario}",
            config=types.GenerateContentConfig(temperature=temperatura),
        )

        resultado_ia = response.text.strip()

        if resultado_ia:
          st.success("¡Lista generada con éxito!")
          st.session_state["resultado_lista"] = resultado_ia

          nuevo_nombre = prompt_usuario[:25] + "..."
          if nuevo_nombre not in st.session_state["history_playlists"]:
            st.session_state["history_playlists"].append(nuevo_nombre)
        else:
          st.error("La IA no devolvió resultados. Inténtalo de nuevo.")

      except Exception as e:
        st.error(f"Error al conectar con la inteligencia artificial: {e}")

# Visualización y edición de la playlist generada por IA
if st.session_state["resultado_lista"]:
  st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
  st.markdown(
      "<h3>Vista previa de la playlist generada (Puedes editarla antes de"
      " enviarla):</h3>",
      unsafe_allow_html=True,
  )
  st.session_state["resultado_lista"] = st.text_area(
      "Canciones (Artista - Canción):",
      value=st.session_state["resultado_lista"],
      height=180,
      key="editable_result_box",
  )

  st.download_button(
      label="Descargar lista como archivo .txt",
      data=st.session_state["resultado_lista"],
      file_name="playlist_ia.txt",
      mime="text/plain",
      use_container_width=True,
  )

st.markdown("<div style='margin: 36px 0;'></div>", unsafe_allow_html=True)

# =====================================================================
# OPCIÓN ALTERNATIVA: SUBIR TXT Y ENVIAR A SPOTIFY
# =====================================================================
st.markdown(
    "<h2 style='font-size: 22px; margin-bottom: 6px;'>Exportar a Spotify</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='margin-bottom: 16px;'>Puedes usar el resultado generado arriba"
    " o subir un archivo de texto externo (.txt) para pasarlo a tu"
    " cuenta.</p>",
    unsafe_allow_html=True,
)

tipo_origen = st.radio(
    "Origen de las canciones:",
    [
        "Usar la lista generada por IA de arriba",
        "Subir un archivo .txt externo",
    ],
)

uploaded_file = None
if tipo_origen == "Subir un archivo .txt externo":
  uploaded_file = st.file_uploader(
      "Sube tu archivo de canciones (.txt)", type=["txt"]
  )

nombre_playlist = st.text_input(
    "Nombre de la playlist en Spotify", value="Mi nueva playlist"
)

texto_a_procesar = ""
if tipo_origen == "Usar la lista generada por IA de arriba":
  texto_a_procesar = st.session_state.get("resultado_lista", "")
else:
  if uploaded_file:
    texto_a_procesar = uploaded_file.getvalue().decode("utf-8")

st.markdown("<div style='margin: 16px 0;'></div>", unsafe_allow_html=True)

if st.button("Crear playlist en Spotify", type="primary", use_container_width=True):
  if not texto_a_procesar.strip():
    st.error(
        "No hay canciones disponibles para procesar. Genera una lista con IA o"
        " sube un archivo."
    )
  elif not CLIENT_ID or CLIENT_ID == "TU_CLIENT_ID_REAL":
    st.error("Configura tus credenciales reales de Spotify en el código.")
  else:
    lines = [
        line.strip() for line in texto_a_procesar.splitlines() if line.strip()
    ]
    with st.spinner(f"Conectando con Spotify y procesando {len(lines)} temas..."):
      try:
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope="playlist-modify-public playlist-modify-private",
            cache_path=None,
            show_dialog=True,
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)

        user_id = sp.me()["id"]
        playlist = sp.user_playlist_create(
            user=user_id,
            name=nombre_playlist,
            public=True,
            description="Creada automáticamente con plAIlister",
        )
        playlist_id = playlist["id"]

        track_uris = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, line in enumerate(lines):
          raw_query = line.strip()
          result = sp.search(q=raw_query, type="track", limit=1)
          tracks = result["tracks"]["items"]

          if not tracks and "-" in raw_query:
            clean_query = re.sub(r"[\(\[\{].*?[\)\]\}]", "", raw_query).strip()
            result = sp.search(q=clean_query, type="track", limit=1)
            tracks = result["tracks"]["items"]

          if tracks:
            track_uris.append(tracks[0]["uri"])
            status_text.text(
                f"Encontrada: {tracks[0]['name']} -"
                f" {tracks[0]['artists'][0]['name']}"
            )
          else:
            status_text.text(f"No encontrada: {raw_query}")

          progress_bar.progress((i + 1) / len(lines))
          time.sleep(0.1)

          if len(track_uris) >= 50:
            sp.playlist_add_items(playlist_id, track_uris)
            track_uris = []

        if track_uris:
          sp.playlist_add_items(playlist_id, track_uris)

        st.success("¡Playlist creada con éxito en tu cuenta de Spotify!")

      except Exception as e:
        st.error(f"Error al conectar con Spotify: {e}")
