from google import genai
from google.genai import types
import random
import re
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st

# ================= CONFIGURACIÓN DE TUS CREDENCIALES =================
# (Sustituye los asteriscos por tus credenciales reales de Spotify Developer)
CLIENT_ID = "ce6c0302d9b147aabdcd3f8f4a62bab0"
CLIENT_SECRET = "ce6c0302d9b147aabdcd3f8f4a62bab0"
REDIRECT_URI = "https://spotify-playlist-web-ktnmkfkhdjehk7qzx4eoxq.streamlit.app/"  # O pon http://localhost:8888 si lo pruebas en local
# ======================================================================

st.set_page_config(
    page_title="PlAIlister", page_icon="P", layout="centered"
)

# =====================================================================
# ESTILOS CSS DE NIVEL UX/UI (DISEÑO OBSESIVO ESTILO SPOTIFY)
# =====================================================================
st.markdown(
    """
    <style>
    /* Fondo general de toda la aplicación */
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Forzar fondo oscuro absoluto en la barra lateral */
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

    /* Logo con estilo de ondas en la AI */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 26px;
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
        font-size: 13px;
        color: #1DB954;
        font-weight: 700;
        background-color: rgba(29, 185, 84, 0.1);
        box-shadow: 0 0 12px rgba(29, 185, 84, 0.4);
    }

    /* Contenedores tipo tarjeta Spotify */
    .spotify-card {
        background-color: #181818;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #282828;
        margin-bottom: 20px;
        transition: background-color 0.3s ease;
    }
    .spotify-card:hover {
        background-color: #202020;
        border-color: #3E3E3E;
    }

    /* Banner superior con gradiente inmersivo */
    .banner-box {
        background: linear-gradient(135deg, rgba(29, 185, 84, 0.15) 0%, #181818 100%);
        border: 1px solid #282828;
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 32px;
    }

    /* Botones primarios (Verde Spotify con texto negro de alto contraste) */
    .stButton>button[kind="primary"] {
        background-color: #1DB954 !important;
        color: #000000 !important;
        font-weight: 700;
        border-radius: 500px;
        border: none;
        padding: 12px 28px;
        transition: transform 0.1s ease, background-color 0.2s;
        box-shadow: 0 4px 12px rgba(29, 185, 84, 0.3);
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #1ed760 !important;
        transform: scale(1.02);
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

    /* Corrección radical de Inputs y TextAreas para máxima legibilidad */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea {
        background-color: #242424 !important;
        color: #FFFFFF !important;
        border: 1px solid #3E3E3E !important;
        border-radius: 8px;
        padding: 12px;
        font-size: 14px;
    }
    .stTextInput>div>div>input:focus, 
    .stTextArea>div>div>textarea:focus {
        border-color: #1DB954 !important;
        box-shadow: 0 0 0 1px #1DB954 !important;
    }

    /* File Uploader personalizado a modo oscuro */
    div[data-testid="stFileUploader"] {
        background-color: #181818;
        border: 1px dashed #3E3E3E;
        border-radius: 12px;
        padding: 20px;
    }
    div[data-testid="stFileUploader"] section {
        background-color: #242424 !important;
        border: none !important;
    }
    div[data-testid="stFileUploader"] span, 
    div[data-testid="stFileUploader"] small {
        color: #B3B3B3 !important;
    }

    /* Tipografía y jerarquía */
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

if "carousel_index" not in st.session_state:
  st.session_state["carousel_index"] = 0

if "prompt_input_field" not in st.session_state:
  st.session_state["prompt_input_field"] = ""

if "is_generating" not in st.session_state:
  st.session_state["is_generating"] = False

if "show_all_history" not in st.session_state:
  st.session_state["show_all_history"] = False

# =====================================================================
# BARRA LATERAL (SIDEBAR - OSCURA RIGUROSA)
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

# 1. Banner superior
st.markdown(
    """
    <div class="banner-box">
        <h1 style="margin: 0; font-size: 34px; color: #FFFFFF;">plAIlister Studio</h1>
        <p style="margin: 8px 0 0 0; font-size: 15px; color: #1DB954; font-weight: 600;">Inteligencia artificial aplicada a la curación musical conectada con Spotify</p>
    </div>
""",
    unsafe_allow_html=True,
)

# 2. Textos explicativos y tarjetas de soluciones ("Usa plAIlister para:")
st.markdown(
    "<h2 style='font-size: 22px; margin-bottom: 16px;'>Usa plAIlister"
    " para:</h2>",
    unsafe_allow_html=True,
)
soluciones_cols = st.columns(3)
with soluciones_cols[0]:
  st.markdown(
      """
        <div class="spotify-card">
            <h3 style="font-size: 16px; color: #FFFFFF; margin-bottom: 8px;">Generar nuevas playlists con IA</h3>
            <p style="font-size: 13px; line-height: 1.5; margin: 0;">Crea colecciones musicales personalizadas al instante describiendo cualquier concepto o atmósfera.</p>
        </div>
    """,
      unsafe_allow_html=True,
  )
with soluciones_cols[1]:
  st.markdown(
      """
        <div class="spotify-card">
            <h3 style="font-size: 16px; color: #FFFFFF; margin-bottom: 8px;">Descubrir nuevos artistas</h3>
            <p style="font-size: 13px; line-height: 1.5; margin: 0;">Explora recomendaciones expertas que cruzan géneros y estilos afines a tus preferencias.</p>
        </div>
    """,
      unsafe_allow_html=True,
  )
with soluciones_cols[2]:
  st.markdown(
      """
        <div class="spotify-card">
            <h3 style="font-size: 16px; color: #FFFFFF; margin-bottom: 8px;">Ampliar tus gustos musicales</h3>
            <p style="font-size: 13px; line-height: 1.5; margin: 0;">Evoluciona tu biblioteca con selecciones curadas conectadas directamente a tu cuenta de Spotify.</p>
        </div>
    """,
      unsafe_allow_html=True,
  )

st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

# =====================================================================
# 3. BLOQUE DEL GENERADOR DE PLAYLISTS CON IA
# =====================================================================
st.markdown(
    "<h2 style='font-size: 22px; margin-bottom: 6px;'>Generador de listas"
    " inteligente</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='margin-bottom: 16px;'>Explora los ejemplos sugeridos o escribe tu"
    " propia descripción detallada.</p>",
    unsafe_allow_html=True,
)

# 10 ejemplos de prompts en tarjeta carrusel
ejemplos_prompts = [
    "Playlist navideña incluyendo a John Mayer, Mariah Carey y Ed Sheeran",
    "Rock clásico de los 80s ideal para correr por la mañana con alta energía",
    "Indie pop y bedroom pop suave para trabajar o concentrarse por la tarde",
    "Tech house y minimal para una sesión de fiesta nocturna con amigos",
    "Jazz instrumental y lo-fi relajante para acompañar una cena tranquila",
    "Rock en español alternativo de los 90s y 2000s con Soda Stereo y Café Tacvba",
    "Liquid drum and bass melódico para un viaje largo en carretera",
    "Pop comercial bailable de los 2010s para actividades del hogar",
    "Blues y soul profundo para un domingo de descanso",
    "Reggaeton clásico del género urbano antiguo",
]

st.markdown('<div class="spotify-card">', unsafe_allow_html=True)
st.markdown(
    "<p style='font-weight: 600; color: #FFFFFF !important; margin-bottom:"
    " 12px;'>Sugerencias de consultas:</p>",
    unsafe_allow_html=True,
)

col_prev, col_text, col_copy, col_next = st.columns([1, 6, 2, 1])

with col_prev:
  if st.button("<", key="prev_prompt", use_container_width=True):
    st.session_state["carousel_index"] = (
        st.session_state["carousel_index"] - 1
    ) % len(ejemplos_prompts)
    st.rerun()

with col_text:
  prompt_actual = ejemplos_prompts[st.session_state["carousel_index"]]
  st.markdown(
      f"<div style='font-size: 14px; color: #FFFFFF; padding-top:"
      f" 8px;'>{prompt_actual}</div>",
      unsafe_allow_html=True,
  )

with col_copy:
  if st.button("Copiar prompt", key="btn_copiar_prompt", use_container_width=True):
    st.session_state["prompt_input_field"] = prompt_actual
    st.success("Prompt copiado al campo.")
    st.rerun()

with col_next:
  if st.button(">", key="next_prompt", use_container_width=True):
    st.session_state["carousel_index"] = (
        st.session_state["carousel_index"] + 1
    ) % len(ejemplos_prompts)
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# Campo de texto principal
prompt_usuario = st.text_area(
    "Describe la música que deseas generar:",
    value=st.session_state.get("prompt_input_field", ""),
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

st.markdown("<div style='margin: 12px 0;'></div>", unsafe_allow_html=True)

# Botón dinámico Generar / Detener
btn_label = "Detener" if st.session_state["is_generating"] else "Generar playlist"

if st.button(btn_label, type="primary", use_container_width=True):
  if not st.session_state["is_generating"]:
    if not prompt_usuario.strip():
      st.error("Por favor, introduce o copia una consulta válida.")
    else:
      st.session_state["is_generating"] = True
      st.rerun()
  else:
    st.session_state["is_generating"] = False
    st.warning("Generación detenida por el usuario.")
    st.rerun()

# Lógica de ejecución Gemini
if st.session_state["is_generating"]:
  with st.spinner("Procesando consulta con Gemini..."):
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
          model="gemini-2.5-flash",
          contents=f"{prompt_sistema}\n\nSolicitud: {prompt_usuario}",
          config=types.GenerateContentConfig(temperature=temperatura),
      )

      resultado_ia = response.text.strip()
      st.session_state["is_generating"] = False

      if resultado_ia:
        st.success("Lista generada con éxito.")
        st.text_area(
            "Resultado de IA:",
            resultado_ia,
            height=160,
            key="resultado_ia_box",
        )
        st.session_state["resultado_lista"] = resultado_ia

        nuevo_nombre = prompt_usuario[:25] + "..."
        if nuevo_nombre not in st.session_state["history_playlists"]:
          st.session_state["history_playlists"].append(nuevo_nombre)

        st.download_button(
            label="Descargar archivo .txt",
            data=resultado_ia,
            file_name="playlist_generada.txt",
            mime="text/plain",
            use_container_width=True,
        )
      else:
        st.error("La IA no devolvió resultados.")
        st.rerun()

    except Exception as e:
      st.session_state["is_generating"] = False
      st.error(f"Error al conectar con la inteligencia artificial: {e}")
      st.rerun()

st.markdown("<div style='margin: 32px 0;'></div>", unsafe_allow_html=True)

# =====================================================================
# 4. OPCIÓN ALTERNATIVA: SUBIR TXT Y ENVIAR A SPOTIFY
# =====================================================================
st.markdown(
    "<h2 style='font-size: 22px; margin-bottom: 6px;'>Opción alternativa: Subir"
    " archivo .txt</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='margin-bottom: 16px;'>También puedes cargar un archivo de texto"
    " con tus canciones para transferirlas directamente a Spotify.</p>",
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Sube tu archivo de canciones (.txt)", type=["txt"]
)
nombre_playlist = st.text_input(
    "Nombre de la playlist en Spotify", value="Mi nueva playlist"
)

texto_a_procesar = ""
if uploaded_file:
  texto_a_procesar = uploaded_file.getvalue().decode("utf-8")
elif "resultado_lista" in st.session_state:
  if st.checkbox("Usar la lista generada por IA en su lugar"):
    texto_a_procesar = st.session_state["resultado_lista"]

st.markdown("<div style='margin: 12px 0;'></div>", unsafe_allow_html=True)

if st.button("Crear playlist en Spotify", type="primary", use_container_width=True):
  if not texto_a_procesar.strip():
    st.error(
        "No hay canciones disponibles. Genera con IA o sube un archivo .txt."
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

        st.success("Playlist creada con éxito en tu cuenta de Spotify.")

      except Exception as e:
        st.error(f"Error al conectar con Spotify: {e}")
