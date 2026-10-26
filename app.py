import random
import re
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
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

# ================= PESTAÑA 2: GENERADOR MÁGICO =================
with tab2:
  st.header("Genera un TXT basado en tus gustos")
  st.write("Genera una playlist automática a partir de tus artistas favoritos.")

  num_artistas = st.slider(
      "¿Cuántos artistas de referencia quieres usar?",
      min_value=1,
      max_value=5,
      value=3,
  )

  artistas = []
  cols = st.columns(2)
  for i in range(num_artistas):
    with cols[i % 2]:
      artista_input = st.text_input(
          f"Artista {i+1}", key=f"artista_{i}", placeholder="Ej: Daft Punk"
      )
      if artista_input.strip():
        artistas.append(artista_input.strip())

  canciones_por_artista = st.slider(
      "¿Cuántas canciones incluir por cada artista?",
      min_value=1,
      max_value=10,
      value=3,
  )

  if st.button("Generar Archivo .txt de Canciones", use_container_width=True):
    if not artistas:
      st.error("Por favor, introduce al menos un nombre de artista válido.")
    elif not CLIENT_ID or CLIENT_ID == "TU_CLIENT_ID_REAL":
      st.error("Configura tus credenciales de Spotify en el código.")
    else:
      with st.spinner("Buscando canciones en Spotify..."):
        try:
          auth_manager = SpotifyOAuth(
              client_id=CLIENT_ID,
              client_secret=CLIENT_SECRET,
              redirect_uri=REDIRECT_URI,
              scope="",
              cache_path=None,
          )
          sp = spotipy.Spotify(auth_manager=auth_manager)

          lista_generada = []

          for artista in artistas:
            # Búsqueda segura del artista
            result_search = sp.search(q=artista, type="artist", limit=1)
            artists_items = result_search["artists"]["items"]

            if not artists_items and len(artista) > 3:
              # Intento de rescate si hay error tipográfico (primera palabra)
              query_simplificada = artista.split()[0]
              result_search = sp.search(
                  q=query_simplificada, type="artist", limit=1
              )
              artists_items = result_search["artists"]["items"]

            if artists_items:
              artist_id = artists_items[0]["id"]
              artist_real_name = artists_items[0]["name"]
              st.write(f"✅ Encontrado: **{artist_real_name}**")

              # Extraer top tracks directamente sin bloqueos
              top_tracks = sp.artist_top_tracks(artist_id, country="US")[
                  "tracks"
              ]
              selected_tracks = top_tracks[:canciones_por_artista]

              for track in selected_tracks:
                lista_generada.append(
                    f"{track['artists'][0]['name']} - {track['name']}"
                )
            else:
              st.warning(f"⚠️ No se encontró el artista: '{artista}'.")

            time.sleep(0.1)

          if lista_generada:
            lista_generada = list(dict.fromkeys(lista_generada))
            texto_resultado = "\n".join(lista_generada)

            st.success(
                f"¡Se han generado {len(lista_generada)} canciones con éxito!"
            )
            st.text_area("Vista previa del TXT:", texto_resultado, height=200)

            st.download_button(
                label="Descargar archivo .txt",
                data=texto_resultado,
                file_name="playlist_generada.txt",
                mime="text/plain",
                type="primary",
                use_container_width=True,
            )
          else:
            st.error(
                "No se pudieron extraer canciones. Verifica los nombres de los"
                " artistas."
            )

        except Exception as e:
          st.error(f"Error técnico al generar la lista: {e}")