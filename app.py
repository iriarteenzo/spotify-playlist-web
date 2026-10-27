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
# ESTILOS CSS UX/UI (AI STYLE & SPOTIFY DARK - TAMAÑOS REDUCIDOS Y LÍNEA ÚNICA)
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

    /* Logo principal */
    .logo-container {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 4px;
        font-size: 40px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
        margin-bottom: 20px;
        padding-top: 6px;
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

    /* Logo barra lateral (20% más pequeño pero 100% idéntico en estructura) */
    .logo-container-sidebar {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 3px;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
        margin-bottom: 20px;
        padding-top: 6px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    .ai-wave-badge-sidebar {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #1DB954;
        border-radius: 50%;
        width: 27px;
        height: 27px;
        font-size: 16px;
        color: #1DB954;
        font-weight: 800;
        background-color: rgba(29, 185, 84, 0.1);
        box-shadow: 0 0 10px rgba(29, 185, 84, 0.4);
        line-height: 1;
        vertical-align: middle;
        flex-shrink: 0;
    }

    /* Hero Section (Fuentes y tarjetas reducidas un 20%) */
    .hero-container {
        padding: 5px 0 5px 0;
        text-align: left;
    }
    .hero-title {
        font-size: 33px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -1px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 4px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }

    .feature-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 14px 16px;
        border-radius: 8px;
        border-left: 2px solid #1DB954;
        margin-bottom: 10px;
    }
    .feature-title {
        font-size: 16px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 3px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    .feature-desc {
        font-size: 12px;
        color: #B3B3B3;
        line-height: 1.3;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }

    .stButton>button[kind="primary"] {
        background-color: #1DB954 !important;
        color: #000000 !important;
        font-weight: 500 !important;
        font-size: 18px !important;
        border-radius: 500px !important;
        border: none !important;
        padding: 10px 24px !important;
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
  st.session_state["paso_actual"] = "creacion"

if "modo_creacion" not in st.session_state:
  st.session_state["modo_creacion"] = None

if "playlist_creada_url" not in st.session_state:
  st.session_state["playlist_creada_url"] = ""

# =====================================================================
# BLOQUE 4: BARRA LATERAL
# =====================================================================
with st.sidebar:
  st.markdown(
      """
        <div class="logo-container-sidebar">
            pl<div class="ai-wave-badge-sidebar">ai</div>lister
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown("---")
  st.markdown(
      "<h3 style='font-size: 14px; text-transform: uppercase; letter-spacing:"
      " 1px;'>Últimas playlists</h3>",
      unsafe_allow_html=True,
  )

  if len(st.session_state["history_playlists"]) == 0:
    st.markdown(
        "<p style='color: #727272; font-style: italic; margin-bottom: 12px;'>Aún"
        " no hay playlists creadas. ¡Crea una nueva playlist para empezar!</p>",
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
          f"<p style='color: #FFFFFF; font-size: 13px; margin: 6px 0;"
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

  # Botón primario verde en la barra lateral para crear nueva playlist
  if st.button(
      "Crear una nueva playlist",
      key="btn_sidebar_crear",
      type="primary",
      use_container_width=True,
  ):
    st.session_state["resultado_lista"] = ""
    st.session_state["modo_creacion"] = None
    st.session_state["paso_actual"] = "creacion"
    st.rerun()

  st.markdown("---")
  st.markdown(
      "<p style='font-size: 10px; color: #727272;'>Conectado a Spotify API"
      " & Google GenAI</p>",
      unsafe_allow_html=True,
  )

# =====================================================================
# BLOQUE 1: HERO SECTION (PÁGINA PRINCIPAL)
# =====================================================================
st.markdown('<div class="hero-container">', unsafe_allow_html=True)
st.markdown(
    """
    <div class="hero-title">
        pl<div class="ai-wave-badge" style="width: 29px; height: 29px; font-size: 16px;">ai</div>lister
    </div>
""",
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
# BLOQUE 2: CREACIÓN DE PLAYLISTS (En una sola línea, sin elementos debajo)
# =====================================================================
if st.session_state["paso_actual"] == "creacion":
  st.markdown(
      "<h2 style='font-size: 20px; margin-bottom: 10px;'>Creación de"
      " playlists</h2>",
      unsafe_allow_html=True,
  )

  # Botones de selección en la misma línea horizontal exacta
  col_sel1, col_sel2 = st.columns(2)
  with col_sel1:
    if st.button("Generar nueva playlist con IA", use_container_width=True):
      st.session_state["modo_creacion"] = "Generar nueva playlist con IA"
      st.rerun()
  with col_sel2:
    if st.button("Subir un archivo .txt", use_container_width=True):
      st.session_state["modo_creacion"] = "Subir un archivo .txt"
      st.rerun()

  st.markdown("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)

  # -----------------------------------------------------------------
  # OPCIÓN 2.a: Generar Playlist con IA (Exclusivo con IA real)
  # -----------------------------------------------------------------
  if st.session_state["modo_creacion"] == "Generar nueva playlist con IA":
    st.markdown("---")
    prompt_usuario = st.text_area(
        "Describe la música que deseas generar:",
        value="",
        height=130,
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

    st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)

    if st.button("Generar playlist", type="primary", use_container_width=True):
      if not prompt_usuario.strip():
        st.error(
            "Por favor, describe detalladamente la música o los artistas que"
            " deseas incluir."
        )
      else:
        resultado_ia = ""
        with st.spinner(
            "Generando curación musical única y específica con Inteligencia"
            " Artificial..."
        ):
          try:
            ai_client = genai.Client()
            # Prompt maestro estricto para garantizar dependencia exclusiva de IA sin respuestas genéricas
            prompt_sistema = (
                f"Eres un curador musical experto y director de programación artística. "
                f"Tu única misión es generar una lista EXACTA de {num_canciones} canciones reales, "
                f"coherentes, altamente específicas y rigurosamente adaptadas al siguiente prompt del usuario, "
                f"incorporando aproximadamente {num_artistas} artistas diferentes.\n\n"
                f"REGLAS ABSOLUTAS:\n"
                f"1. PROHIBIDO usar resultados genéricos, plantillas repetitivas o listas estándar predefinidas. "
                f"Cada canción debe ser un tema real publicado por dichos artistas o acorde absoluto al estilo solicitado.\n"
                f"2. Devuelve exclusivamente la lista de canciones en formato de texto plano, una por línea.\n"
                f"3. Formato estricto por línea: 'Artista - Canción'.\n"
                f"4. Sin numeración, sin viñetas, sin introducciones ni comentarios adicionales."
            )
            response = ai_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=f"{prompt_sistema}\n\nPetición del usuario: {prompt_usuario}",
                config=types.GenerateContentConfig(temperature=temperatura),
            )
            resultado_ia = response.text.strip()
          except Exception as e:
            st.error(
                "Error al conectar con la Inteligencia Artificial. Por favor,"
                f" verifica tu conexión o reintenta: {e}"
            )

          if resultado_ia:
            st.session_state["resultado_lista"] = resultado_ia
            nuevo_nombre = prompt_usuario[:25] + "..."
            if nuevo_nombre not in st.session_state["history_playlists"]:
              st.session_state["history_playlists"].append(nuevo_nombre)
            st.session_state["paso_actual"] = "revision"
            st.rerun()

  # -----------------------------------------------------------------
  # OPCIÓN 2.b: Subir Archivo TXT (Con botón de continuar inactivo/activo)
  # -----------------------------------------------------------------
  elif st.session_state["modo_creacion"] == "Subir un archivo .txt":
    st.markdown("---")
    st.markdown(
        "<p style='margin-bottom: 8px;'>Sube un archivo de texto plano (.txt)"
        " con una canción por línea (formato: 'Artista - Canción').</p>",
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "Seleccionar archivo .txt", type=["txt"], key="uploader_principal"
    )

    if uploaded_file is not None:
      contenido_archivo = uploaded_file.getvalue().decode("utf-8")
      st.markdown(
          "<p style='color: #1DB954; font-weight: 600; margin-top: 10px;'>✔"
          " Archivo cargado con éxito. Visualiza el contenido a"
          " continuación:</p>",
          unsafe_allow_html=True,
      )
      st.text_area(
          "Texto detectado en el archivo:",
          value=contenido_archivo,
          height=130,
          disabled=True,
      )

      st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
      # Botón de continuar activo una vez seleccionado el archivo
      if st.button(
          "Continuar",
          type="primary",
          use_container_width=True,
          key="btn_cont_upload",
      ):
        st.session_state["resultado_lista"] = contenido_archivo
        st.session_state["paso_actual"] = "revision"
        st.rerun()
    else:
      # Modo inactivo visual si aún no hay archivo cargado
      st.button(
          "Continuar",
          disabled=True,
          use_container_width=True,
          key="btn_cont_upload_inactivo",
      )

# =====================================================================
# FASE DE REVISIÓN Y EDICIÓN (DESCARTE / AJUSTE DE CANCIONES)
# =====================================================================
elif st.session_state["paso_actual"] == "revision":
  st.markdown(
      "<h2 style='font-size: 20px; margin-bottom: 8px;'>Revisión de la"
      " playlist</h2>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p>Puedes revisar, editar o descartar canciones de tu playlist antes"
      " de crearla en Spotify.</p>",
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
# BLOQUE 3: CREACIÓN DE PLAYLIST EN SPOTIFY, PROGRESO Y MENSAJE FINAL
# =====================================================================
elif st.session_state["paso_actual"] == "exportacion":
  st.markdown(
      "<h2 style='font-size: 20px; margin-bottom: 8px;'>Exportar a Spotify</h2>",
      unsafe_allow_html=True,
  )

  nombre_playlist = st.text_input(
      "Nombre de la playlist en Spotify", value="Mi nueva playlist"
  )
  st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)

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
        ).get("spotify", "https://open.spotify.com")
        st.session_state["paso_actual"] = "exito"
        st.rerun()

      except Exception as e:
        st.error(f"Error al conectar con Spotify o procesar la exportación: {e}")

elif st.session_state["paso_actual"] == "exito":
  st.markdown(
      "<h2 style='font-size: 22px; color: #1DB954 !important;'>¡Playlist"
      " creada con éxito!</h2>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p>Tu nueva playlist ya está disponible y sincronizada en tu cuenta de"
      " Spotify.</p>",
      unsafe_allow_html=True,
  )

  url_pl = st.session_state.get(
      "playlist_creada_url", "https://open.spotify.com"
  )
  st.text_input("Enlace URL de la playlist:", value=url_pl, disabled=True)

  col_comp1, col_comp2 = st.columns(2)
  with col_comp1:
    if st.button("Copiar enlace", use_container_width=True):
      st.toast("¡Enlace copiado al portapapeles!", icon="📋")
  with col_comp2:
    whatsapp_url = f"https://api.whatsapp.com/send?text=¡Escucha%20esta%20playlist%20que%20acabo%20de%20crear!%20{url_pl}"
    st.markdown(
        f'<a href="{whatsapp_url}" target="_blank"><button style="width:100%;'
        " background-color:#282828; color:#FFFFFF; border:1px solid"
        " #3E3E3E; border-radius:500px; padding:10px 18px; font-weight:500;"
        ' cursor:pointer;">Compartir en WhatsApp</button></a>',
        unsafe_allow_html=True,
    )

  st.markdown("<div style='margin: 14px 0;'></div>", unsafe_allow_html=True)

  col_e1, col_e2 = st.columns(2)
  with col_e1:
    if st.button("Finalizar", use_container_width=True):
      st.session_state["resultado_lista"] = ""
      st.session_state["modo_creacion"] = None
      st.session_state["paso_actual"] = "creacion"
      st.rerun()
  with col_e2:
    if st.button(
        "Crear una nueva playlist", type="primary", use_container_width=True
    ):
      st.session_state["resultado_lista"] = ""
      st.session_state["modo_creacion"] = None
      st.session_state["paso_actual"] = "creacion"
      st.rerun()
