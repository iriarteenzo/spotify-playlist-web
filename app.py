
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
# ESTILOS CSS UX/UI (ESTILO EXACTO AI STUDIO PLAYGROUND)
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
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 720px;
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

    /* Logo barra lateral */
    .logo-container-sidebar {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 3px;
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
        margin-bottom: 12px;
        padding-top: 8px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    .ai-wave-badge-sidebar {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #1DB954;
        border-radius: 50%;
        width: 23px;
        height: 23px;
        font-size: 13px;
        color: #1DB954;
        font-weight: 800;
        background-color: rgba(29, 185, 84, 0.1);
        box-shadow: 0 0 8px rgba(29, 185, 84, 0.4);
        line-height: 1;
        vertical-align: middle;
        flex-shrink: 0;
    }

    /* Hero Section Minimalista AI Studio */
    .hero-container {
        padding: 0px 0 10px 0;
        text-align: left;
    }
    .hero-title {
        font-size: 34px;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -1px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 6px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    .ai-wave-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #1DB954;
        border-radius: 50%;
        width: 28px;
        height: 28px;
        font-size: 15px;
        color: #1DB954;
        font-weight: 800;
        background-color: rgba(29, 185, 84, 0.1);
        box-shadow: 0 0 10px rgba(29, 185, 84, 0.4);
        line-height: 1;
        vertical-align: middle;
        flex-shrink: 0;
    }

    .feature-card {
        background: transparent;
        padding: 6px 0;
        margin-bottom: 6px;
    }
    .feature-title {
        font-size: 16px;
        font-weight: 600;
        color: #E3E3E3;
        margin-bottom: 2px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    .feature-desc {
        font-size: 13px;
        color: #9AA0A6;
        line-height: 1.4;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }

    /* CONTENEDOR DE TEXTAREA ESTILO AI STUDIO */
    div[data-testid="stTextArea"] textarea {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
        border-radius: 16px 16px 0px 0px !important;
        padding: 16px !important;
        font-size: 15px !important;
        font-family: 'Google Sans', Helvetica, sans-serif;
        resize: none !important;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #444444 !important;
        box-shadow: none !important;
    }

    /* Barra inferior integrada dentro del bloque prompt */
    .prompt-toolbar {
        background-color: #1E1E1E;
        border: 1px solid #333333;
        border-top: none;
        border-radius: 0px 0px 16px 16px;
        padding: 8px 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: -16px;
        margin-bottom: 16px;
    }

    /* Botones de acción principales y secundarios */
    .stButton>button[kind="primary"] {
        background-color: #1DB954 !important;
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        border-radius: 500px !important;
        border: none !important;
        padding: 8px 20px !important;
        box-shadow: 0 2px 10px rgba(29, 185, 84, 0.3);
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
        background-color: #2A2A2A;
        color: #FFFFFF !important;
        border: 1px solid #3E3E3E;
        border-radius: 500px;
        font-weight: 500;
        padding: 6px 14px;
        font-family: 'Google Sans', Helvetica, sans-serif;
        font-size: 13px;
    }
    .stButton>button:hover {
        border-color: #FFFFFF;
        background-color: #3E3E3E;
    }

    div[data-baseweb="slider"] div[role="slider"] {
        background-color: #1DB954 !important;
    }

    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 700;
        letter-spacing: -0.5px;
        font-family: 'Google Sans', Helvetica, sans-serif;
    }
    p, label {
        color: #B3B3B3 !important;
        font-size: 13px;
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

if "mostrar_ajustes" not in st.session_state:
  st.session_state["mostrar_ajustes"] = False

if "playlist_creada_url" not in st.session_state:
  st.session_state["playlist_creada_url"] = ""

# =====================================================================
# BARRA LATERAL (SIDEBAR)
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
      "<h3 style='font-size: 13px; text-transform: uppercase; letter-spacing:"
      " 1px;'>Últimas playlists</h3>",
      unsafe_allow_html=True,
  )

  if len(st.session_state["history_playlists"]) == 0:
    st.markdown(
        "<p style='color: #727272; font-style: italic; margin-bottom: 10px;'>Aún"
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
          f"<p style='color: #FFFFFF; font-size: 13px; margin: 5px 0;"
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

  st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)

  if st.button(
      "Crear una nueva playlist",
      key="btn_sidebar_crear",
      type="primary",
      use_container_width=True,
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
# HERO SECTION (Visible en el paso de creación)
# =====================================================================
if st.session_state["paso_actual"] == "creacion":
  st.markdown('<div class="hero-container">', unsafe_allow_html=True)
  st.markdown(
      """
      <div class="hero-title">
          pl<div class="ai-wave-badge">ai</div>lister
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
  st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)

# =====================================================================
# PASO 1: BLOQUE DE ENTRADA ESTILO GOOGLE AI STUDIO / GEMINI PLAYGROUND
# =====================================================================
if st.session_state["paso_actual"] == "creacion":

  # Desplegable de Ajustes
  if st.session_state["mostrar_ajustes"]:
    st.markdown(
        "<div style='background: #181818; border: 1px solid #333; padding:"
        " 14px; border-radius: 12px; margin-bottom: 12px;'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#FFFFFF; font-weight:600; margin-bottom:8px;'>Ajustes"
        " de generación:</p>",
        unsafe_allow_html=True,
    )
    num_canciones = st.slider(
        "Cantidad de canciones", min_value=5, max_value=50, value=15, key="slider_can"
    )
    num_artistas = st.slider(
        "Artistas distintos", min_value=1, max_value=15, value=5, key="slider_art"
    )
    temperatura = st.slider(
        "Creatividad", min_value=0.0, max_value=1.0, value=0.7, key="slider_temp"
    )
    st.markdown("</div>", unsafe_allow_html=True)
  else:
    num_canciones = 15
    num_artistas = 5
    temperatura = 0.7

  # Campo de entrada de texto principal
  prompt_usuario = st.text_area(
      "Escribe aquí lo que deseas escuchar...",
      value="",
      height=120,
      key="main_prompt_box",
      label_visibility="collapsed",
  )

  # Fila inferior con botones integrados e iconos SVG lineales (Ajustes a la izquierda, Ejecutar a la derecha)
  col_btn1, col_btn2 = st.columns([1, 1])
  with col_btn1:
    if st.button("🎛️ Filtros / Ajustes", key="btn_toggle_ajustes"):
      st.session_state["mostrar_ajustes"] = not st.session_state["mostrar_ajustes"]
      st.rerun()

  with col_btn2:
    if st.button("Ejecutar", type="primary", use_container_width=True, key="btn_enviar_gemini"):
      if not prompt_usuario.strip():
        st.error("Por favor, escribe lo que deseas escuchar.")
      else:
        resultado_ia = ""
        with st.spinner("Generando curación musical única con IA..."):
          try:
            ai_client = genai.Client()
            prompt_sistema = (
                f"Eres un curador musical experto. Genera una lista EXACTA de {num_canciones} "
                f"canciones reales, coherentes y adaptadas al prompt del usuario, "
                f"incorporando aproximadamente {num_artistas} artistas diferentes.\n\n"
                f"REGLAS ABSOLUTAS:\n"
                f"1. PROHIBIDO usar resultados genéricos o repetitivos.\n"
                f"2. Devuelve exclusivamente la lista en formato de texto plano, una por línea.\n"
                f"3. Formato estricto por línea: 'Artista - Canción'.\n"
                f"4. Sin numeración, viñetas ni comentarios adicionales."
            )
            response = ai_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=f"{prompt_sistema}\n\nPetición del usuario: {prompt_usuario}",
                config=types.GenerateContentConfig(temperature=temperatura),
            )
            resultado_ia = response.text.strip()
          except Exception as e:
            st.error(f"Error al conectar con la Inteligencia Artificial: {e}")

          if resultado_ia:
            st.session_state["resultado_lista"] = resultado_ia
            nuevo_nombre = prompt_usuario[:25] + "..."
            if nuevo_nombre not in st.session_state["history_playlists"]:
              st.session_state["history_playlists"].append(nuevo_nombre)
            st.session_state["paso_actual"] = "revision"
            st.rerun()

# =====================================================================
# PASO 2: REVISIÓN DE LA PLAYLIST & PREVISUALIZACIÓN DE AUDIO
# =====================================================================
elif st.session_state["paso_actual"] == "revision":
  st.markdown(
      "<h2 style='font-size: 18px; margin-bottom: 6px;'>Revisión y Previsualización"
      " de Audio</h2>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p>Escucha fragmentos de 30 segundos, edita o descarta canciones antes"
      " de exportarlas a Spotify.</p>",
      unsafe_allow_html=True,
  )

  st.session_state["resultado_lista"] = st.text_area(
      "Canciones (Artista - Canción):",
      value=st.session_state["resultado_lista"],
      height=160,
      key="editable_result_box",
  )

  st.markdown("<div style='margin: 14px 0;'></div>", unsafe_allow_html=True)
  st.markdown(
      "<h3 style='font-size: 15px; color: #1DB954 !important;'>🎧 Previsualización"
      " de pistas</h3>",
      unsafe_allow_html=True,
  )

  if CLIENT_ID != "TU_CLIENT_ID_REAL":
    try:
      auth_manager = SpotifyOAuth(
          client_id=CLIENT_ID,
          client_secret=CLIENT_SECRET,
          redirect_uri=REDIRECT_URI,
          scope="playlist-modify-public",
          cache_path=None,
          show_dialog=False,
      )
      sp = spotipy.Spotify(auth_manager=auth_manager)
      lines_preview = [
          l.strip()
          for l in st.session_state["resultado_lista"].splitlines()
          if l.strip()
      ][:6]

      for idx, track_query in enumerate(lines_preview):
        res = sp.search(q=track_query, type="track", limit=1)
        items = res["tracks"]["items"]
        if items and items[0].get("preview_url"):
          t_name = items[0]["name"]
          a_name = items[0]["artists"][0]["name"]
          p_url = items[0]["preview_url"]
          st.markdown(
              f"<p style='font-size: 12px; margin-bottom: 2px; color:#FFFFFF;'>"
              f"<b>{idx+1}. {a_name} - {t_name}</b></p>",
              unsafe_allow_html=True,
          )
          st.audio(p_url)
        else:
          st.markdown(
              f"<p style='font-size: 12px; color:#727272;'>{idx+1}. {track_query}"
              " (Audio preview no disponible en Spotify)</p>",
              unsafe_allow_html=True,
          )
    except Exception:
      st.markdown(
          "<p style='font-size: 12px; color:#727272;'>Configura tus credenciales"
          " de Spotify para habilitar los previews de audio.</p>",
          unsafe_allow_html=True,
      )
  else:
    st.markdown(
        "<p style='font-size: 12px; color:#727272;'>Los previews de audio de"
        " Spotify se activarán al configurar tus credenciales reales en el"
        " código.</p>",
        unsafe_allow_html=True,
    )

  st.markdown("<div style='margin: 14px 0;'></div>", unsafe_allow_html=True)

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
# PASO 3: EXPORTACIÓN A SPOTIFY Y MENSAJE FINAL
# =====================================================================
elif st.session_state["paso_actual"] == "exportacion":
  st.markdown(
      "<h2 style='font-size: 18px; margin-bottom: 6px;'>Exportar a Spotify</h2>",
      unsafe_allow_html=True,
  )

  nombre_playlist = st.text_input(
      "Nombre de la playlist en Spotify", value="Mi nueva playlist"
  )
  st.markdown("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)

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
      "<h2 style='font-size: 20px; color: #1DB954 !important;'>¡Playlist"
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
        " #3E3E3E; border-radius:500px; padding:8px 16px; font-weight:500;"
        ' cursor:pointer; font-size:13px;">Compartir en WhatsApp</button></a>',
        unsafe_allow_html=True,
    )

  st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)

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