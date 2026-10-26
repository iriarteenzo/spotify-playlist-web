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

st.set_page_config(
    page_title="Playlistador", page_icon="P", layout="centered"
)

st.title("Playlistador")
st.write(
    "Genera listas a partir de tus artistas favoritos o sube tu propio archivo"
    " de texto para crear playlists en segundos."
)

# Pestañas para organizar la herramienta de forma limpia y moderna
tab1, tab2 = st.tabs(
    ["Crear playlist desde TXT", "Genera tu playlist"]
)

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
    if not CLIENT_ID or CLIENT_ID == "TU_CLIENT_ID":
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
              description="Creada automáticamente desde Spotify Playlist Studio",
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
  st.write(
      "Introduce hasta 5 artistas o bandas que conozcas. Buscaremos temas"
      " populares suyos y de artistas similares para armar tu lista."
  )

  # Entradas para hasta 5 artistas
  artistas = []
  col1, col2 = st.columns(2)
  with col1:
    a1 = st.text_input("Artista 1 (Ej: Daft Punk)")
    a2 = st.text_input("Artista 2 (Ej: The Strokes)")
    a3 = st.text_input("Artista 3 (Opcional)")
  with col2:
    a4 = st.text_input("Artista 4 (Opcional)")
    a5 = st.text_input("Artista 5 (Opcional)")

  for a in [a1, a2, a3, a4, a5]:
    if a.strip():
      artistas.append(a.strip())

  canciones_por_artista = st.slider(
      "¿Cuántas canciones incluir por cada artista/similar?",
      min_value=1,
      max_value=10,
      value=3,
  )

  if st.button("Generar Archivo .txt de Canciones", use_container_width=True):
    if not artistas:
      st.error("Por favor, introduce al menos un artista.")
    elif not CLIENT_ID or CLIENT_ID == "TU_CLIENT_ID":
      st.error(
          "Configura tus credenciales de Spotify en el código para usar el"
          " buscador de artistas."
      )
    else:
      with st.spinner("Buscando canciones y artistas similares..."):
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
            # Buscar el artista para obtener su ID y artistas relacionados
            result_search = sp.search(q=artista, type="artist", limit=1)
            artists_items = result_search["artists"]["items"]

            if artists_items:
              artist_id = artists_items[0]["id"]
              artist_name = artists_items[0]["name"]

              # Obtener top tracks del artista principal
              top_tracks = sp.artist_top_tracks(artist_id, country="US")[
                  "tracks"
              ]
              selected_tracks = top_tracks[:canciones_por_artista]
              for track in selected_tracks:
                lista_generada.append(
                    f"{track['artists'][0]['name']} - {track['name']}"
                )

              # Obtener artistas relacionados para enriquecer la playlist
              related_artists = sp.artist_related_artists(artist_id)[
                  "artists"
              ]
              # Seleccionar un par de artistas similares aleatorios
              sample_related = random.sample(
                  related_artists, min(2, len(related_artists))
              )

              for rel_artist in sample_related:
                rel_top_tracks = sp.artist_top_tracks(
                    rel_artist["id"], country="US"
                )["tracks"]
                rel_selected = rel_top_tracks[: max(1, canciones_por_artista - 1)]
                for track in rel_selected:
                  lista_generada.append(
                      f"{track['artists'][0]['name']} - {track['name']}"
                  )

          # Eliminar duplicados manteniendo orden
          lista_generada = list(dict.fromkeys(lista_generada))

          texto_resultado = "\n".join(lista_generada)

          st.success(
              f"¡Se han generado {len(lista_generada)} canciones basadas en tus"
              " gustos!"
          )

          # Mostrar vista previa en la web
          st.text_area("Vista previa del TXT:", texto_resultado, height=200)

          # Botón de descarga directa del .txt
          st.download_button(
              label="Descargar archivo .txt",
              data=texto_resultado,
              file_name="playlist_generada.txt",
              mime="text/plain",
              type="primary",
              use_container_width=True,
          )

        except Exception as e:
          st.error(f"Error al generar la lista: {e}")