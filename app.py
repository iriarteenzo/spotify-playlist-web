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
# ESTILOS CSS PERSONALIZADOS (UI ESTILO SPOTIFY)
# =====================================================================
st.markdown(
    """
    <style>
    /* Fondo general oscuro estilo Spotify */
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
        font-family: 'Circular Std', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Contenedor tipo tarjeta Spotify */
    .spotify-card {
        background-color: #181818;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #282828;
        margin-bottom: 20px;
        transition: background-color 0.3s ease;
    }
    .spotify-card:hover {
        background-color: #282828;
    }

    /* Botones principales estilo Spotify (Verdes) */
    .stButton>button[kind="primary"] {
        background-color: #1DB954 !important;
        color: #000000 !important;
        font-weight: 700;
        border-radius: 500px;
        border: none;
        padding: 10px 24px;
        transition: transform 0.1s ease, background-color 0.2s;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #1ed760 !important;
        transform: scale(1.02);
    }

    /* Botones secundarios */
    .stButton>button {
        background-color: #282828;
        color: #FFFFFF;
        border: 1px solid #3E3E3E;
        border-radius: 500px;
        font-weight: 600;
    }
    .stButton>button:hover {
        border-color: #FFFFFF;
        color: #FFFFFF;
    }

    /* Campos de texto y inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #242424;
        color: #FFFFFF;
        border: 1px solid #3E3E3E;
        border-radius: 8px;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #1DB954;
    }

    /* Títulos */
    h1, h2, h3 {
        color: #FFFFFF;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    p, label {
        color: #B3B3B3;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("PlAIlister")
st.write(
    "Crea playlists inteligentes con inteligencia artificial o gestiona tus"
    " archivos de texto."
)

st.markdown("---")

# =====================================================================
# SECCION 1: GENERADOR INTELIGENTE CON GEMINI (CARRUSEL DE EJEMPLOS)
# =====================================================================
st.subheader("Generador de listas con Inteligencia Artificial")
st.write(
    "Utiliza los ejemplos del carrusel o escribe tu propia solicitud detallada."
)

# Lista de 10 ejemplos diversos de prompts
ejemplos_prompts = [
    "Playlist navideña incluyendo a John Mayer, Mariah Carey y Ed Sheeran",
    "Rock clásico de los 80s ideal para correr por la mañana con alta energia",
    "Indie pop y bedroom pop suave para trabajar o concentrarse por la tarde",
    "Tech house y minimal para una sesion de fiesta nocturna con amigos",
    "Jazz instrumental y lo-fi relajante para acompañar una cena tranquila",
    "Rock en español alternativo de los 90s y 2000s con Soda Stereo y Cafe Tacvba",
    "Liquid drum and bass melódico para un viaje largo en carretera",
    "Pop comercial bailable de los 2010s para actividades del hogar",
    "Blues y soul profundo para un domingo de descanso",
    "Reggaeton clásico del genero urbano antiguo",
]

# Inicializar el índice del carrusel en el session_state
if "carousel_index" not in st.session_state:
  st.session_state["carousel_index"] = 0

# Controles de navegación del carrusel en una tarjeta estilo Spotify
st.markdown('<div class="spotify-card">', unsafe_allow_html=True)
st.markdown("**Ideas de consultas sugeridas:**")

col_prev, col_text, col_next = st.columns([1, 8, 1])

with col_prev:
  if st.button("<", key="prev_btn", use_container_width=True):
    st.session_state["carousel_index"] = (
        st.session_state["carousel_index"] - 1
    ) % len(ejemplos_prompts)

with col_text:
  current_example = ejemplos_prompts[st.session_state["carousel_index"]]
  st.markdown(
      f"<div style='text-align: center; font-size: 15px; color:"
      f" #FFFFFF;'><b>[{st.session_state['carousel_index'] + 1}/{len(ejemplos_prompts)}]</b>"
      f" {current_example}</div>",
      unsafe_allow_html=True,
  )

with col_next:
  if st.button(">", key="next_btn", use_container_width=True):
    st.session_state["carousel_index"] = (
        st.session_state["carousel_index"] + 1
    ) % len(ejemplos_prompts)

# Botón para aplicar el ejemplo actual directamente al campo de texto
if st.button(
    "Utilizar este ejemplo seleccionado",
    key="apply_example",
    use_container_width=True,
):
  st.session_state["prompt_input_field"] = current_example

st.markdown("</div>", unsafe_allow_html=True)

# Campo de texto principal vinculado al estado
prompt_usuario = st.text_area(
    "Describe la musica que deseas generar:",
    value=st.session_state.get(
        "prompt_input_field", ejemplos_prompts[0]
    ),
    height=90,
    key="main_prompt_box",
)

# Controles avanzados: Cantidad de canciones, artistas y temperatura
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
  num_canciones = st.slider(
      "Cantidad de canciones", min_value=5, max_value=50, value=20
  )
with col_c2:
  num_artistas = st.slider(
      "Artistas distintos", min_value=1, max_value=15, value=6
  )
with col_c3:
  temperatura = st.slider(
      "Creatividad (Temperatura)",
      min_value=0.0,
      max_value=1.0,
      value=0.7,
      help="Valores bajos generan resultados estrictos. Valores altos aportan diversidad.",
  )

# Botón de Generación con Gemini
if st.button(
    "Generar lista con Inteligencia Artificial",
    type="primary",
    use_container_width=True,
):
  if not prompt_usuario.strip():
    st.error("Por favor, introduce una descripcion valida.")
  else:
    with st.spinner("Generando seleccion musical..."):
      try:
        ai_client = genai.Client()

        instruccion_sistema = (
            f"Actúa como un curador musical profesional. Genera una lista"
            f" exacta de {num_canciones} canciones basada en la solicitud. Debe"
            f" incluir aproximadamente {num_artistas} artistas diferentes.\n\n"
            f"REQUISITO ESTRICTO: Devuelve exclusivamente la lista de"
            f" canciones en formato de texto plano, una por línea, con este"
            f" formato exacto: 'Artista - Cancion'. Sin números, sin viñetas,"
            f" sin introducciones."
        )

        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{instruccion_sistema}\n\nSolicitud: {prompt_usuario}",
            config=types.GenerateContentConfig(temperature=temperatura),
        )

        resultado_ia = response.text.strip()

        if resultado_ia:
          st.success("Lista generada correctamente.")
          st.text_area(
              "Resultado obtenido:",
              resultado_ia,
              height=160,
              key="text_area_resultado_ia",
          )

          st.download_button(
              label="Descargar archivo de texto",
              data=resultado_ia,
              file_name="playlist_generada.txt",
              mime="text/plain",
              use_container_width=True,
          )

          st.session_state["resultado_lista"] = resultado_ia
        else:
          st.error("No se obtuvieron resultados de la IA.")

      except Exception as e:
        st.error(f"Error al conectar con el servicio de IA: {e}")

st.markdown("---")

# =====================================================================
# SECCION 2: ENVIAR A SPOTIFY (DESDE IA O DESDE ARCHIVO TXT)
# =====================================================================
st.subheader("Exportar a Spotify")
st.write(
    "Selecciona el origen de los datos para crear la playlist de forma automática"
    " en tu cuenta."
)

tipo_origen = st.radio(
    "Origen de canciones:",
    [
        "Usar el texto generado por la IA",
        "Subir un archivo de texto externo (.txt)",
    ],
)

nombre_playlist = st.text_input(
    "Nombre de la playlist en Spotify", value="Mi nueva playlist"
)

texto_a_procesar = ""

if tipo_origen == "Usar el texto generado por la IA":
  if "resultado_lista" in st.session_state:
    texto_a_procesar = st.session_state["resultado_lista"]
  else:
    st.info("Genera una lista con inteligencia artificial primero.")
else:
  archivo_subido = st.file_uploader(
      "Sube tu archivo de texto (.txt)", type=["txt"]
  )
  if archivo_subido:
    texto_a_procesar = archivo_subido.getvalue().decode("utf-8")

if st.button(
    "Crear playlist en Spotify", type="primary", use_container_width=True
):
  if not texto_a_procesar.strip():
    st.error("No hay canciones disponibles para procesar.")
  elif not CLIENT_ID or CLIENT_ID == "TU_CLIENT_ID_REAL":
    st.error("Configura tus credenciales de Spotify en el código.")
  else:
    lines = [
        line.strip() for line in texto_a_procesar.splitlines() if line.strip()
    ]
    with st.spinner(f"Conectando con Spotify y buscando {len(lines)} temas..."):
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
            description="Creada automáticamente con Playlistador Pro",
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