import random
import re
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from google import genai
import streamlit as st

# ================= CONFIGURACIÓN DE TUS CREDENCIALES =================
# (Sustituye los asteriscos por tus credenciales reales de Spotify Developer)
CLIENT_ID = "TU_CLIENT_ID"
CLIENT_SECRET = "ce6c0302d9b147aabdcd3f8f4a62bab0"
REDIRECT_URI = "https://spotify-playlist-web-ktnmkfkhdjehk7qzx4eoxq.streamlit.app/"  # O pon http://localhost:8888 si lo pruebas en local
# ======================================================================

st.set_page_config(page_title="Playlistador", page_icon="P", layout="centered")

st.title("Playlistador")
st.write(
    "Genera listas a partir de tus artistas favoritos o sube tu propio archivo"
    " de texto para crear playlists en segundos."
)

# Pestañas para organizar la herramienta de forma limpia y moderna
tab1, tab2 = st.tabs(["Crear playlist desde TXT", "Genera tu playlist"])

# ================= PESTAÑA 1: CREAR PLAYLIST =================
with tab1:
  st.header("Sube tu archivo y crea la playlist")
  playlist_name_input = st.text_input(
      "Nombre de la playlist", value="Mi nueva playlist"
  )
  uploaded_file = st.file_uploader(
      "Sube tu archivo de canciones (.txt)", type=["txt"]
  )

  if st.button(
      "Crear playlist",
      type="primary",
      use_container_width=True,
  ):
    if not CLIENT_ID or CLIENT_ID == "TU_CLIENT_ID_REAL":
      st.error(
          "Por favor, configura tus credenciales de Spotify en el código"
          " antes de continuar."
      )
    elif not uploaded_file:
      st.error("Por favor, sube un archivo .txt con las canciones.")
    else:
      with st.spinner("Conectando con Spotify y procesando canciones..."):
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

          string_data = uploaded_file.getvalue().decode("utf-8")
          lines = string_data.splitlines()

          st.info(f"Buscando {len(lines)} canciones en Spotify...")

          user_id = sp.me()["id"]
          playlist = sp.user_playlist_create(
              user=user_id,
              name=playlist_name_input,
              public=True,
              description="Creada automáticamente desde Playlistador",
          )
          playlist_id = playlist["id"]

          track_uris = []
          progress_bar = st.progress(0)
          status_text = st.empty()

          for i, line in enumerate(lines):
            raw_query = line.strip()
            if not raw_query:
              continue

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
            time.sleep(0.2)

            if len(track_uris) >= 50:
              sp.playlist_add_items(playlist_id, track_uris)
              track_uris = []

          if track_uris:
            sp.playlist_add_items(playlist_id, track_uris)

          st.success("¡Playlist creada con éxito en tu cuenta de Spotify!")

        except Exception as e:
          st.error(f"Ocurrió un error durante el proceso: {e}")

# ================= PESTAÑA 2: GENERADOR MÁGICO CON GEMINI =================
with tab2:
  subtitle_tab2 = (
      "Genera una playlist con IA"
  )
  st.header("Generador de playlist con Gemini")
  st.write(subtitle_tab2)

  num_artistas = st.slider(
      "¿Cuántos artistas de referencia quieres usar?",
      min_value=1,
      max_value=5,
      value=3,
      key="slider_num_artistas",
  )

  artistas = []
  cols = st.columns(2)
  for i in range(num_artistas):
    with cols[i % 2]:
      artista_input = st.text_input(
          f"Artista {i+1}", key=f"gemini_artista_{i}", placeholder="Ej: Daft Punk"
      )
      if artista_input.strip():
        artistas.append(artista_input.strip())

  canciones_por_artista = st.slider(
      "¿Cuántas canciones por artista?",
      min_value=1,
      max_value=10,
      value=4,
      key="slider_canciones_por_artista",
  )

  if st.button(
      "Generar playlist",
      type="primary",
      use_container_width=True,
      key="btn_generar_gemini",
  ):
    if not artistas:
      st.error("Por favor, introduce al menos un artista de referencia.")
    else:
      with st.spinner("Gemini está curando y seleccionando las canciones..."):
        try:
          # Inicializar el cliente de Gemini (toma automáticamente la API Key del entorno o Streamlit Secrets)
          ai_client = genai.Client()

          prompt = (
              f"Actúa como un DJ experto y curador musical. A partir de los"
              f" siguientes artistas o géneros de referencia: {', '.join(artistas)},"
              f" genera una lista de canciones recomendadas. Debe incluir tanto"
              f" éxitos de estos artistas como de otros artistas muy similares"
              f" del mismo género. Necesito un total aproximado de"
              f" {num_artistas * canciones_por_artista} canciones.\n\n"
              f"REQUISITO ESTRICTO DE FORMATO: Devuelve exclusivamente la"
              f" lista de canciones en formato de texto plano, una por línea,"
              f" exactamente con este formato exacto: 'Nombre del Artista -"
              f" Nombre de la Canción'. No incluyas números, ni introducciones,"
              f" ni viñetas, solo las líneas de texto."
          )

          response = ai_client.models.generate_content(
              model="gemini-2.5-flash",
              contents=prompt,
          )

          texto_resultado = response.text.strip()

          if texto_resultado:
            st.success(
                "¡Lista generada con éxito por Gemini con cero bloqueos!"
            )
            st.text_area(
                "Vista previa del TXT generado:", texto_resultado, height=200
            )

            # Botón de descarga directa del .txt para pasarlo a la Pestaña 1 si se quiere
            st.download_button(
                label="📥 Descargar archivo .txt para la Pestaña 1",
                data=texto_resultado,
                file_name="playlist_gemini.txt",
                mime="text/plain",
                type="primary",
                use_container_width=True,
                key="download_gemini_txt",
            )
          else:
            st.error(
                "Gemini no devolvió resultados. Inténtalo de nuevo con otros"
                " nombres."
            )

        except Exception as e:
          st.error(
              f"Error al conectar con Gemini: {e}. Asegúrate de configurar tu"
              " API Key de Google GenAI."
          )