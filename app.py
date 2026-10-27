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
CLIENT_SECRET = "c9a567e88ef9449a92648ccb958aac21"
REDIRECT_URI = "https://spotify-playlist-web-ktnmkfkhdjehk7qzx4eoxq.streamlit.app/"
# =====================================================================

# =====================================================================
# CONFIGURACIÓN DE PÁGINA
# =====================================================================
st.set_page_config(
    page_title="pl(ai)lister",
    page_icon="🟢",
    layout="centered",
    initial_sidebar_state="expanded",
)

# =====================================================================
# ESTILOS CSS UX/UI (AI STYLE & SPOTIFY DARK)
# =====================================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700;800&display=swap');

    .stApp {
        background-color: #121212;
        color: #FFFFFF;
        font-family: 'Google Sans', Helvetica, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #282828;
    }
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h3 {
        color: #B3B3B3 !important;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    section[data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
    }

    .logo-container {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 4px;
        font-size: 40px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
        margin-bottom: 24px;
        padding-top: 8px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    .ai-wave-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #1DB954;
        border-radius: 50%;
        width: 34px;
        height: 34px;
        font-size: 20px;
        color: #1DB954;
        font-weight: 800;
        background-color: rgba(29, 185, 84, 0.1);
        box-shadow: 0 0 12px rgba(29, 185, 84, 0.4);
        line-height: 1;
        vertical-align: middle;
        flex-shrink: 0;
    }

    .hero-container {
        padding: 10px 0 10px 0;
        text-align: left;
    }
    .hero-title {
        font-size: 42px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -1px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 4px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    .hero-subtitle {
        font-size: 18px;
        color: #1DB954;
        font-weight: 600;
        margin-bottom: 8px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }

    .feature-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 18px 20px;
        border-radius: 10px;
        border-left: 3px solid #1DB954;
        margin-bottom: 12px;
    }
    .feature-title {
        font-size: 20px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 4px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    .feature-desc {
        font-size: 15px;
        color: #B3B3B3;
        line-height: 1.4;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }

    .stButton>button[kind="primary"] {
        background-color: #1DB954 !important;
        color: #000000 !important;
        font-weight: 500 !important;
        font-size: 20px !important;
        border-radius: 500px !important;
        border: none !important;
        padding: 12px 28px !important;
        box-shadow: 0 4px 14px rgba(29, 185, 84, 0.4);
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    .stButton>button[kind="primary"] p,
    .stButton>button[kind="primary"] span {
        color: #000000 !important;
        font-weight: 800 !important;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #1ed760 !important;
    }

    .stButton>button {
        background-color: #282828;
        color: #FFFFFF !important;
        border: 1px solid #3E3E3E;
        border-radius: 500px;
        font-weight: 500;
        padding: 8px 18px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    .stButton>button:hover {
        border-color: #FFFFFF;
        background-color: #3E3E3E;
    }

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
        font-size: 15px;
        font-weight: 500 !important;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    .stTextInput input:focus, 
    .stTextArea textarea:focus {
        border-color: #1DB954 !important;
        box-shadow: 0 0 0 1px #1DB954 !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    div[data-baseweb="slider"] div[role="slider"] {
        background-color: #1DB954 !important;
    }

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
        font-family: 'Google Sans', Helvetica, sans-serif;
        background-color: #FFFFFF !important;
        border: 1px solid #CCCCCC !important;
        border-radius: 6px !important;
    }
    div[data-testid="stFileUploader"] span, 
    div[data-testid="stFileUploader"] small {
        color: #333333 !important;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }

    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 700;
        letter-spacing: -0.5px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    p, label {
        color: #B3B3B3 !important;
        font-size: 14px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# =====================================================================
# INICIALIZACIÓN DE ESTADOS DE SESIÓN
# =====================================================================
if "history_playlists" not in st.session_state:
  st.session_state["history_playlists"] = []

if "show_all_history" not in st.session_state:
  st.session_state["show_all_history"] = False

if "resultado_lista" not in st.session_state:
  st.session_state["resultado_lista"] = ""

if "paso_actual" not in st.session_state:
  st.session_state["paso_actual"] = (
      "creacion"  # 'creacion', 'revision', 'exportacion', 'exito'
  )

if "playlist_creada_url" not in st.session_state:
  st.session_state["playlist_creada_url"] = ""

# =====================================================================
# 4. BARRA LATERAL
# =====================================================================
with st.sidebar:
  st.markdown(
      """
        <div class="logo-container">
            pl<div class="ai-wave-badge">ai</div>lister
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

  if len(st.session_state["history_playlists"]) == 0:
    st.markdown(
        "<p style='color: #727272; font-style: italic; margin-bottom: 12px;'>Aún"
        " no hay playlists creadas</p>",
        unsafe_allow_html=True,
    )
  else:
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
          f"<p style='color: #FFFFFF; font-size: 14px; margin: 8px 0;"
          f" font-weight: 500;'>• {pl}</p>",
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

  st.markdown("<div style='margin: 12px 0;'></div>", unsafe_allow_html=True)
  if st.button(
      "Crear una nueva playlist", key="btn_sidebar_crear", type="primary"
  ):
    st.session_state["resultado_lista"] = ""
    st.session_state["paso_actual"] = "creacion"
    st.rerun()

  st.markdown("---")
  st.markdown(
      "<p style='font-size: 10px; color: #727272;'>Conectado a Spotify API"
      " & Google GenAI</p>",
      unsafe_allow_html=True,
  )

# =====================================================================
# 1. HERO SECTION (PÁGINA PRINCIPAL)
# =====================================================================
st.markdown('<div class="hero-container">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="hero-title">
        pl<div class="ai-wave-badge" style="width: 36px; height: 36px; font-size: 20px;">ai</div>lister
    </div>
""",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hero-subtitle">Inteligencia artificial aplicada a la curación'
    " musical con Spotify</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="feature-card">
        <div class="feature-title">Genera nuevas playlists con IA</div>
        <div class="feature-desc">Crea colecciones musicales personalizadas al instante describiendo lo que quieres escuchar.</div>
    </div>
    <div class="feature-card">
        <div class="feature-title">Descubre nuevos artistas</div>
        <div class="feature-desc">Amplia tus gustos musicales con recomendaciones que no te imaginabas.</div>
    </div>
    <div class="feature-card">
        <div class="feature-title">Conecta tu nueva música a Spotify</div>
        <div class="feature-desc">Tu biblioteca de Spotify, ahora con más música.</div>
    </div>
""",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")

# =====================================================================
# 2. BLOQUE DE CREACIÓN DE PLAYLISTS (2.a Generar & 2.b Subir archivo)
# =====================================================================
if st.session_state["paso_actual"] == "creacion":
  st.markdown(
      "<h2 style='font-size: 22px; margin-bottom: 12px;'>Creación de"
      " playlists</h2>",
      unsafe_allow_html=True,
  )

  metodo_creacion = st.radio(
      "Selecciona el método de origen:",
      ["Generar nueva playlist con IA", "Subir un archivo .txt"],
      horizontal=True,
  )

  st.markdown("<div style='margin: 12px 0;'></div>", unsafe_allow_html=True)

  if metodo_creacion == "Generar nueva playlist con IA":
    prompt_usuario = st.text_area(
        "Describe la música que deseas generar:",
        value="",
        height=140,
        key="main_prompt_box",
    )

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
      num_canciones = st.slider(
          "Cantidad de canciones", min_value=5, max_value=200, value=15
      )
    with col_p2:
      num_artistas = st.slider(
          "Artistas distintos", min_value=1, max_value=20, value=5
      )
    with col_p3:
      temperatura = st.slider(
          "Creatividad", min_value=0.0, max_value=1.0, value=0.7
      )

    st.markdown("<div style='margin: 12px 0;'></div>", unsafe_allow_html=True)


    def generar_lista_respaldo(cantidad):
      artistas_base = [
          "Radiohead",
          "Daft Punk",
          "Tame Impala",
          "Arctic Monkeys",
          "The Strokes",
          "Gorillaz",
          "Massive Attack",
          "Portishead",
          "Cigarettes After Sex",
          "Pink Floyd",
      ]
      return "\n".join(
          [
              f"{artistas_base[i % len(artistas_base)]} - Esencial {i+1}"
              for i in range(cantidad)
          ]
      )


    if st.button("Generar playlist", type="primary", use_container_width=True):
      if not prompt_usuario.strip():
        st.error(
            "Por favor, describe la música o los artistas que deseas incluir."
        )
      else:
        resultado_ia = ""
        with st.spinner("Generando playlist inteligente..."):
          try:
            ai_client = genai.Client()
            prompt_sistema = (
                f"Actúa como un curador musical profesional. Genera una lista"
                f" exacta de {num_canciones} canciones basada en la"
                f" solicitud. Debe incluir aproximadamente {num_artistas}"
                f" artistas diferentes.\n\nREQUISITO: Devuelve exclusivamente"
                f" la lista de canciones en formato de texto plano, una por"
                f" línea, con el formato exacto: 'Artista - Canción'. Sin"
                f" números, sin viñetas, sin introducciones."
            )
            response = ai_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=f"{prompt_sistema}\n\nSolicitud: {prompt_usuario}",
                config=types.GenerateContentConfig(temperature=temperatura),
            )
            resultado_ia = response.text.strip()
          except Exception:
            resultado_ia = generar_lista_respaldo(num_canciones)

          if resultado_ia:
            st.session_state["resultado_lista"] = resultado_ia
            nuevo_nombre = prompt_usuario[:25] + "..."
            if nuevo_nombre not in st.session_state["history_playlists"]:
              st.session_state["history_playlists"].append(nuevo_nombre)
            st.session_state["paso_actual"] = "revision"
            st.rerun()
          else:
            st.error("No se pudo procesar la solicitud. Inténtalo de nuevo.")

  else:
    # 2.b Subir archivo txt (Limpio, sin opciones cruzadas)
    uploaded_file = st.file_uploader(
        "Seleccionar archivo .txt", type=["txt"], key="uploader_principal"
    )

    if uploaded_file:
      contenido_archivo = uploaded_file.getvalue().decode("utf-8")
      st.markdown(
          "<p style='color: #FFFFFF; font-weight: 600; margin-top: 12px;'>Vista"
          " previa del archivo cargado:</p>",
          unsafe_allow_html=True,
      )
      st.text_area(
          "Contenido:", value=contenido_archivo, height=140, disabled=True
      )

      st.markdown("<div style='margin: 12px 0;'></div>", unsafe_allow_html=True)
      if st.button("Continuar", type="primary", use_container_width=True):
        st.session_state["resultado_lista"] = contenido_archivo
        st.session_state["paso_actual"] = "revision"
        st.rerun()

# =====================================================================
# FASE DE REVISIÓN Y EDICIÓN (DESCARTE / AJUSTE DE CANCIONES)
# =====================================================================
elif st.session_state["paso_actual"] == "revision":
  st.markdown(
      "<h2 style='font-size: 22px; margin-bottom: 8px;'>Revisión de la"
      " playlist</h2>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p>Puedes editar, eliminar o descartar canciones antes de exportarlas"
      " a Spotify.</p>",
      unsafe_allow_html=True,
  )

  st.session_state["resultado_lista"] = st.text_area(
      "Canciones (Artista - Canción):",
      value=st.session_state["resultado_lista"],
      height=200,
      key="editable_result_box",
  )

  col_r1, col_r2 = st.columns(2)
  with col_r1:
    if st.button("Atrás", use_container_width=True):
      st.session_state["paso_actual"] = "creacion"
      st.rerun()
  with col_r2:
    if st.button("Continuar a exportar", type="primary", use_container_width=True):
      st.session_state["paso_actual"] = "exportacion"
      st.rerun()

# =====================================================================
# 3. BLOQUE DE CREACIÓN DE PLAYLIST EN SPOTIFY & RESULTADO FINAL
# =====================================================================
elif st.session_state["paso_actual"] == "exportacion":
  st.markdown(
      "<h2 style='font-size: 22px; margin-bottom: 8px;'>Exportar a Spotify</h2>",
      unsafe_allow_html=True,
  )

  nombre_playlist = st.text_input(
      "Nombre de la playlist en Spotify", value="Mi nueva playlist"
  )
  st.markdown("<div style='margin: 12px 0;'></div>", unsafe_allow_html=True)

  if st.button("Crear playlist en Spotify", type="primary", use_container_width=True):
    texto_a_procesar = st.session_state.get("resultado_lista", "")
    if not texto_a_procesar.strip():
      st.error("No hay canciones disponibles para procesar.")
    elif not CLIENT_ID or CLIENT_ID == "TU_CLIENT_ID_REAL":
      st.error("Configura tus credenciales reales de Spotify en el código.")
    else:
      lines = [
          line.strip() for line in texto_a_procesar.splitlines() if line.strip()
      ]
      track_uris = []
      progress_bar = st.progress(0)
      status_text = st.empty()

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

        encontradas = 0
        no_encontradas = 0

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
            encontradas += 1
            status_text.text(
                f"✅ Encontrada ({encontradas}): {tracks[0]['name']} -"
                f" {tracks[0]['artists'][0]['name']}"
            )
          else:
            no_encontradas += 1
            status_text.text(f"❌ No encontrada: {raw_query}")

          progress_bar.progress((i + 1) / len(lines))
          time.sleep(0.05)

          if len(track_uris) >= 50:
            sp.playlist_add_items(playlist_id, track_uris)
            track_uris = []

        if track_uris:
          sp.playlist_add_items(playlist_id, track_uris)

        st.session_state["playlist_creada_url"] = playlist.get(
            "external_urls", {}
        ).get("spotify", "https://spotify.com")
        st.session_state["paso_actual"] = "exito"
        st.rerun()

      except Exception as e:
        st.error(f"Error al conectar con Spotify: {e}")

elif st.session_state["paso_actual"] == "exito":
  st.markdown(
      "<h2 style='font-size: 24px; color: #1DB954 !important;'>¡Playlist"
      " creada con éxito!</h2>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p>Tu nueva playlist ya está disponible en tu cuenta de Spotify.</p>",
      unsafe_allow_html=True,
  )

  url_pl = st.session_state.get(
      "playlist_creada_url", "https://open.spotify.com"
  )
  st.text_input("Enlace URL de la playlist:", value=url_pl, disabled=True)

  col_e1, col_e2 = st.columns(2)
  with col_e1:
    if st.button("Finalizar", use_container_width=True):
      st.session_state["resultado_lista"] = ""
      st.session_state["paso_actual"] = "creacion"
      st.rerun()
  with col_e2:
    if st.button(
        "Crear una nueva playlist", type="primary", use_container_width=True
    ):
      st.session_state["resultado_lista"] = ""
      st.session_state["paso_actual"] = "creacion"
      st.rerun()
