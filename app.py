import re
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st

st.set_page_config(
    page_title="Spotify Playlist Creator", page_icon="🎵", layout="centered"
)

st.title("🎵 Creador de Playlists desde TXT")
st.write(
    "Sube tu archivo de texto con canciones y créalas automáticamente en tu"
    " cuenta de Spotify."
)

# Configuración de credenciales (puedes poner las tuyas por defecto o pedirlas)
st.sidebar.header("🔑 Credenciales de Spotify")
client_id = st.sidebar.text_input("Client ID", type="password")
client_secret = st.sidebar.text_input("Client Secret", type="password")

# URL de redirección (cuando subas tu app a Streamlit Cloud, cambia esto por tu URL final)
redirect_uri = st.sidebar.text_input(
    "Redirect URI", value="http://localhost:8888/callback"
)

uploaded_file = st.file_uploader(
    "Sube tu archivo de canciones (.txt)", type=["txt"]
)

if st.button(
    "🚀 Crear Playlist en Spotify", type="primary", use_container_width=True
):
  if not client_id or not client_secret:
    st.error("Por favor, introduce tu Client ID y Client Secret en la barra lateral.")
  elif not uploaded_file:
    st.error("Por favor, sube un archivo .txt con las canciones.")
  else:
    with st.spinner("Conectando con Spotify y procesando canciones..."):
      try:
        # Autenticación
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope="playlist-modify-public playlist-modify-private",
            cache_path=None,  # Evita crear archivos de caché locales en la nube
            show_dialog=True,
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)

        # Leer archivo subido
        string_data = uploaded_file.getvalue().decode("utf-8")
        lines = string_data.splitlines()

        st.info(f"Buscando {len(lines)} canciones...")

        # Crear playlist
        user_id = sp.me()["id"]
        playlist = sp.user_playlist_create(
            user=user_id,
            name="Mi Playlist Web",
            public=True,
            description="Creada desde Web App gratuita",
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
            status_text.text(f"✅ Encontrada: {tracks[0]['name']}")
          else:
            status_text.text(f"❌ No encontrada: {raw_query}")

          # Actualizar barra de progreso
          progress_bar.progress((i + 1) / len(lines))
          time.sleep(0.2)

          if len(track_uris) >= 50:
            sp.playlist_add_items(playlist_id, track_uris)
            track_uris = []

        if track_uris:
          sp.playlist_add_items(playlist_id, track_uris)

        st.success("🎉 ¡Playlist creada con éxito en tu cuenta de Spotify!")

      except Exception as e:
        st.error(f"Ocurrió un error durante el proceso: {e}")