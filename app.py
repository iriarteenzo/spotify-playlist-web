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

st.set_page_config(page_title="plAIlist", page_icon="P", layout="centered")

st.title("plAIlist")
st.write(
    "Crea playlists mágicas con IA mediante lenguaje natural o sube tu propio"
    " archivo de texto."
)

st.markdown("---")

# =====================================================================
# SECCIÓN 1: GENERADOR INTELIGENTE CON GEMINI
# =====================================================================
st.header("✨ Generador Mágico con IA")
st.write(
    "Describe la música que buscas o selecciona un ejemplo para empezar"
    " rápido:"
)

# 1. Carrusel / Banco de Ejemplos de Prompts (Usando botones en columnas o pills)
ejemplos = [
    "Playlist de Navidad incluyendo a John Mayer, Mariah Carey y Ed Sheeran...",
    "Rock clásico de los 80s ideal para correr por la mañana, enérgico y motivador",
    "Indie pop y bedroom pop suave para trabajar o concentrarse por la tarde",
    "Tech house y minimal para una sesión de fiesta nocturna con amigos",
    "Jazz instrumental y lo-fi relajante para acompañar una cena tranquila",
    "Rock en español alternativo de los 90s y 2000s (Soda Stereo, Café Tacvba)",
    "Liquid drum and bass melódico para un viaje largo en coche",
    "Pop comercial bailable de los 2010s para limpiar la casa",
    "Blues y soul profundo para un domingo lluvioso",
    "Reggaeton clásico del perreo viejo y urbano",
]

# Mostramos los ejemplos como botones rápidos seleccionables
selected_prompt = None
st.markdown("**💡 Ejemplos recomendados (haz clic para usar):**")

# Creamos un contenedor desplazable o filas de botones de ejemplo rápidos
cols_ej = st.columns(2)
for idx, ej in enumerate(ejemplos):
  with cols_ej[idx % 2]:
    if st.button(
        f"📌 {ej[:45]}...", key=f"ej_{idx}", use_container_width=True
    ):
      st.session_state["prompt_input"] = ej

# Campo de texto principal vinculado al estado para aceptar los ejemplos
prompt_usuario = st.text_area(
    "¿Qué tipo de playlist quieres crear?",
    value=st.session_state.get(
        "prompt_input",
        "Playlist de rock alternativo noventero con toques modernos",
    ),
    height=100,
    key="input_prompt_principal",
)

# Controles avanzados de la IA
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
  num_canciones = st.slider("Canciones", min_value=5, max_value=50, value=20)
with col_c2:
  num_artistas = st.slider(
      "Artistas dif.", min_value=1, max_value=15, value=6
  )
with col_c3:
  # Control de Temperatura (Creatividad / Diversidad)
  temperatura = st.slider(
      "Creatividad",
      min_value=0.0,
      max_value=1.0,
      value=0.7,
      help=(
          "Valores bajos (0.1) son más estrictos y fieles al prompt. Valores"
          " altos (0.9) son más diversos y creativos."
      ),
  )

# Botón de Generación con Gemini
if st.button(
    "🪄 Generar Lista con IA", type="primary", use_container_width=True
):
  if not prompt_usuario.strip():
    st.error("Por favor, introduce una descripción para la playlist.")
  else:
    with st.spinner("Gemini está curando tu selección musical..."):
      try:
        ai_client = genai.Client()

        instruccion_sistema = (
            f"Actúa como un DJ profesional y curador musical experto. Genera"
            f" una lista exacta de {num_canciones} canciones basada en la"
            f" solicitud del usuario. Debe incluir aproximadamente"
            f" {num_artistas} artistas diferentes.\n\n"
            f"REQUISITO ESTRICTO DE FORMATO: Devuelve exclusivamente la lista"
            f" de canciones en formato de texto plano, una por línea,"
            f" exactamente con este formato: 'Nombre del Artista - Nombre de la"
            f" Canción'. No incluyas números, ni viñetas, ni texto introductorio."
        )

        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{instruccion_sistema}\n\nSolicitud: {prompt_usuario}",
            config=types.GenerateContentConfig(temperature=temperatura),
        )

        resultado_ia = response.text.strip()

        if resultado_ia:
          st.success("¡Lista generada con éxito por Gemini!")
          st.text_area(
              "Resultado (Listo para crear o descargar):",
              resultado_ia,
              height=180,
              key="txt_generado_ia",
          )

          # Botón para descargar el TXT generado
          st.download_button(
              label="📥 Descargar como archivo .txt",
              data=resultado_ia,
              file_name="playlist_gemini.txt",
              mime="text/plain",
              use_container_width=True,
          )

          st.session_state["resultado_lista"] = resultado_ia
        else:
          st.error("La IA no devolvió resultados. Inténtalo de nuevo.")

      except Exception as e:
        st.error(
            f"Error al conectar con Gemini: {e}. Comprueba tu GEMINI_API_KEY."
        )

st.markdown("---")

# =====================================================================
# SECCIÓN 2: CREAR EN SPOTIFY (DESDE IA O DESDE ARCHIVO TXT)
# =====================================================================
st.header("🚀 Enviar a Spotify")
st.write(
    "Puedes crear la playlist directamente en tu cuenta usando el resultado de"
    " arriba o subiendo tu propio archivo de texto."
)

tipo_origen = st.radio(
    "¿De dónde quieres sacar las canciones?",
    [
        "Usar el texto generado por la IA arriba",
        "Subir mi propio archivo .txt",
    ],
)

nombre_playlist = st.text_input(
    "Nombre de la Playlist en Spotify", value="Mi Playlist desde Playlistador"
)

texto_a_procesar = ""

if tipo_origen == "Usar el texto generado por la IA arriba":
  if "resultado_lista" in st.session_state:
    texto_a_procesar = st.session_state["resultado_lista"]
  else:
    st.info("Genera una lista arriba con IA primero para usar esta opción.")
else:
  archivo_subido = st.file_uploader(
      "Sube tu archivo de canciones (.txt)", type=["txt"]
  )
  if archivo_subido:
    texto_a_procesar = archivo_subido.getvalue().decode("utf-8")

if st.button(
    "🎵 Crear Playlist en mi Spotify",
    type="primary",
    use_container_width=True,
):
  if not texto_a_procesar.strip():
    st.error("No hay canciones para procesar. Genera una lista o sube un TXT.")
  elif not CLIENT_ID or CLIENT_ID == "TU_CLIENT_ID_REAL":
    st.error("Configura tus credenciales reales de Spotify en el código.")
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
            description="Creada automáticamente con Playlistador Pro & Gemini",
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
                f"✅ Encontrada: {tracks[0]['name']} -"
                f" {tracks[0]['artists'][0]['name']}"
            )
          else:
            status_text.text(f"❌ No encontrada: {raw_query}")

          progress_bar.progress((i + 1) / len(lines))
          time.sleep(0.1)

          if len(track_uris) >= 50:
            sp.playlist_add_items(playlist_id, track_uris)
            track_uris = []

        if track_uris:
          sp.playlist_add_items(playlist_id, track_uris)

        st.success(
            "🎉 ¡Playlist creada con éxito en tu cuenta de Spotify y lista para"
            " escuchar!"
        )

      except Exception as e:
        st.error(f"Error al conectar con Spotify: {e}")