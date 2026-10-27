import html
import json
import os
import re
import time

import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from google import genai
from google.genai import types

# ---------- Configuración ----------
st.set_page_config(
    page_title="pl(ai)lister",
    page_icon="♪",
    layout="centered",
    initial_sidebar_state="collapsed",
)

SPOTIFY_SCOPES = "playlist-modify-public playlist-modify-private"
DEFAULT_MODEL = "gemini-2.5-flash"


def secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)


SPOTIFY_CLIENT_ID = secret("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = secret("SPOTIFY_CLIENT_SECRET")
GEMINI_API_KEY = secret("GEMINI_API_KEY")
GEMINI_MODEL = secret("GEMINI_MODEL", DEFAULT_MODEL)
REDIRECT_URI = secret("SPOTIFY_REDIRECT_URI", "").strip()

# En Streamlit Cloud, configura SPOTIFY_REDIRECT_URI
# con la URL pública exacta de tu aplicación.
if not REDIRECT_URI:
    REDIRECT_URI = "http://localhost:8501"


# ---------- Estilos ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&display=swap');

:root { color-scheme: dark; }

.stApp {
  background: #121212;
  color: #f5f5f5;
  font-family: 'Google Sans', Inter, system-ui, sans-serif;
}

.block-container {
  max-width: 760px;
  padding: 2rem 1.15rem 3rem;
}

header[data-testid="stHeader"] {
  background: transparent;
}

section[data-testid="stSidebar"] {
  background: #090909;
  border-right: 1px solid #292929;
}

h1, h2, h3, p, label {
  font-family: 'Google Sans', Inter, sans-serif;
}

h1 {
  letter-spacing: -1.6px;
  font-size: clamp(2rem, 7vw, 3rem);
}

h2 {
  letter-spacing: -.5px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -1.7px;
  margin-bottom: 1.4rem;
  color: #fff;
}

.brand-ai {
  width: 27px;
  height: 27px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #1ed760;
  border-radius: 50%;
  color: #1ed760;
  font-size: 12px;
  letter-spacing: -.4px;
}

.eyebrow {
  color: #1ed760;
  font-size: .76rem;
  text-transform: uppercase;
  letter-spacing: 1.4px;
  font-weight: 700;
}

.muted {
  color: #a7a7a7;
}

.st-key-prompt_shell {
  background: #1e1e1e;
  border: 1px solid #343434;
  border-radius: 22px;
  padding: 12px 14px 10px;
  margin-top: 1.2rem;
  margin-bottom: 1rem;
}

.st-key-prompt_shell div[data-testid="stTextArea"] textarea {
  background: transparent !important;
}

.st-key-prompt_shell div[data-testid="stHorizontalBlock"] {
  align-items: center;
}

.st-key-prompt_shell div[data-testid="stButton"] button {
  min-height: 38px;
}

div[data-testid="stTextArea"] textarea {
  background: #1e1e1e !important;
  color: #f5f5f5 !important;
  border: 0 !important;
  box-shadow: none !important;
  border-radius: 14px !important;
  padding: 8px 4px !important;
  font-size: 1rem !important;
  resize: vertical !important;
}

div[data-testid="stTextArea"] label {
  display: none;
}

div[data-testid="stTextArea"] [data-baseweb="textarea"] {
  border: 0 !important;
  box-shadow: none !important;
}

.stButton > button {
  min-height: 42px;
  border-radius: 999px;
  border: 1px solid #414141;
  background: #292929;
  color: #f5f5f5;
  font-weight: 500;
}

.stButton > button:hover {
  border-color: #777;
  color: #fff;
  background: #333;
}

.stButton > button[kind="primary"] {
  background: #1ed760 !important;
  border-color: #1ed760 !important;
  color: #07150b !important;
  font-weight: 750 !important;
}

.stButton > button[kind="primary"]:hover {
  background: #3be477 !important;
}

div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
  background: #1ed760;
}

div[data-testid="stSlider"] [data-testid="stTickBar"] {
  background: #1ed760;
}

div[data-testid="stExpander"] {
  border: 1px solid #333;
  border-radius: 14px;
}

.track-row {
  border-bottom: 1px solid #2b2b2b;
  padding: 12px 0;
  display: flex;
  gap: 12px;
  align-items: center;
}

.track-index {
  color: #888;
  width: 24px;
  flex-shrink: 0;
  font-size: .85rem;
}

.track-title {
  color: #f5f5f5;
  font-size: .96rem;
  font-weight: 600;
}

.track-artist {
  color: #aaa;
  font-size: .84rem;
  margin-top: 3px;
}

.track-album {
  color: #777;
  font-size: .78rem;
  margin-top: 2px;
}

.track-link {
  color: #1ed760;
  text-decoration: none;
  font-size: .8rem;
  white-space: nowrap;
}

.result-card {
  background: #1b1b1b;
  border: 1px solid #303030;
  border-radius: 16px;
  padding: 16px;
  margin: 12px 0;
}

div[data-testid="stAlert"] {
  border-radius: 12px;
}

hr {
  border-color: #303030;
}

small {
  color: #888;
}
</style>
""", unsafe_allow_html=True)


# ---------- Iconos SVG ----------
def icon(name, size=18):
    paths = {
        "sliders": (
            '<path d="M4 21v-7m0-4V3m8 18v-9m0-4V3'
            'm8 18v-5m0-4V3"/>'
            '<path d="M2 14h4m4-6h4m4 8h4"/>'
        ),
        "send": (
            '<path d="m22 2-7 20-4-9-9-4Z"/>'
            '<path d="M22 2 11 13"/>'
        ),
        "music": (
            '<path d="M9 18V5l12-2v13"/>'
            '<circle cx="6" cy="18" r="3"/>'
            '<circle cx="18" cy="16" r="3"/>'
        ),
        "check": '<path d="m5 12 4 4L19 6"/>',
        "external": (
            '<path d="M15 3h6v6"/>'
            '<path d="M10 14 21 3"/>'
            '<path d="M19 13v6a2 2 0 0 1-2 2H5'
            'a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h6"/>'
        ),
    }

    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.7" '
        'stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{paths[name]}</svg>'
    )


# ---------- Spotify ----------
def spotify_oauth():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None

    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SPOTIFY_SCOPES,
        cache_path=None,
        open_browser=False,
    )


def spotify_client():
    token = st.session_state.get("spotify_token")

    if not token:
        return None

    if token.get("expires_at", 0) < time.time() + 60:
        oauth = spotify_oauth()

        if oauth:
            try:
                token = oauth.refresh_access_token(
                    token["refresh_token"]
                )
                st.session_state.spotify_token = token
            except Exception:
                st.session_state.pop("spotify_token", None)
                return None

    return spotipy.Spotify(auth=token["access_token"])


def connect_spotify():
    oauth = spotify_oauth()

    if not oauth:
        st.error(
            "Configura SPOTIFY_CLIENT_ID y "
            "SPOTIFY_CLIENT_SECRET en los secretos de Streamlit."
        )
        return

    state = st.session_state.get("oauth_state")

    if not state:
        import secrets

        state = secrets.token_urlsafe(24)
        st.session_state.oauth_state = state

    st.link_button(
        "Conectar con Spotify",
        oauth.get_authorize_url(state=state),
        use_container_width=True,
    )


# ---------- Procesamiento de canciones ----------
def parse_tracks(raw, requested_count):
    if isinstance(raw, str):
        raw = raw.strip()

        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            parsed_tracks = []

            for line in raw.splitlines():
                match = re.match(
                    r"^(.+?)\s+[–—-]\s+(.+)$",
                    line.strip(),
                )

                if match:
                    parsed_tracks.append({
                        "artist": match.group(1).strip(),
                        "title": match.group(2).strip(),
                    })

            raw = {"tracks": parsed_tracks}

    tracks = raw.get("tracks", []) if isinstance(raw, dict) else []
    cleaned = []
    seen = set()

    for item in tracks:
        if not isinstance(item, dict):
            continue

        artist = str(item.get("artist", "")).strip()
        title = str(item.get("title", "")).strip()

        if not artist or not title:
            continue

        key = (artist.casefold(), title.casefold())

        if key not in seen:
            cleaned.append({
                "artist": artist,
                "title": title,
            })
            seen.add(key)

        if len(cleaned) >= requested_count:
            break

    return cleaned


def generate_tracks(prompt, count, artist_count, temperature):
    client = genai.Client(api_key=GEMINI_API_KEY)

    system = f"""
Eres un curador musical experto. Devuelve exclusivamente JSON válido
con esta estructura:
{{"tracks":[{{"artist":"nombre real del artista","title":"título real de la canción"}}]}}

Genera exactamente {count} canciones reales y distintas, de
aproximadamente {artist_count} artistas diferentes.

Respeta el estilo, época, idioma, energía y exclusiones indicadas
por el usuario.

Evita duplicados, versiones en directo salvo que se pidan,
canciones inventadas y elecciones genéricas.

No incluyas explicaciones, markdown ni campos adicionales.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"{system}\n\nPetición del usuario: {prompt}",
        config=types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
        ),
    )

    tracks = parse_tracks(response.text or "", count)

    if len(tracks) < count:
        raise ValueError(
            f"Gemini devolvió {len(tracks)} canciones válidas "
            f"de las {count} solicitadas. Prueba otra vez "
            "o ajusta la petición."
        )

    return tracks


def find_spotify_tracks(sp, tracks):
    resolved = []
    missing = []
    seen_uris = set()

    progress = st.progress(
        0,
        text="Buscando canciones en Spotify…",
    )

    for index, track in enumerate(tracks):
        query = (
            f'track:"{track["title"]}" '
            f'artist:"{track["artist"]}"'
        )

        try:
            results = sp.search(
                q=query,
                type="track",
                limit=5,
            )
            items = results.get("tracks", {}).get("items", [])

            if not items:
                results = sp.search(
                    q=f'{track["title"]} {track["artist"]}',
                    type="track",
                    limit=5,
                )
                items = results.get("tracks", {}).get("items", [])

            match = next(
                (
                    item for item in items
                    if item["uri"] not in seen_uris
                ),
                None,
            )

            if match:
                seen_uris.add(match["uri"])

                resolved.append({
                    "artist": ", ".join(
                        artist["name"]
                        for artist in match.get("artists", [])
                    ),
                    "title": match["name"],
                    "album": match.get("album", {}).get("name", ""),
                    "uri": match["uri"],
                    "url": match.get(
                        "external_urls", {}
                    ).get("spotify", ""),
                    "id": match.get("id", ""),
                })
            else:
                missing.append(track)

        except Exception:
            missing.append(track)

        progress.progress(
            (index + 1) / len(tracks),
            text=(
                "Buscando canciones en Spotify… "
                f"{index + 1}/{len(tracks)}"
            ),
        )

    progress.empty()
    return resolved, missing


# ---------- Reiniciar flujo ----------
def reset_app():
    for key in (
        "tracks",
        "missing",
        "resolved",
        "playlist_url",
        "playlist_name",
        "review_text",
    ):
        st.session_state.pop(key, None)

    st.session_state.step = "create"


# ---------- Estado de la aplicación ----------
defaults = {
    "step": "create",
    "history": [],
    "prompt": "",
    "show_settings": False,
    "count": 15,
    "artist_count": 5,
    "temperature": 0.7,
}

for key, value in defaults.items():
    st.session_state.setdefault(key, value)


# ---------- Callback OAuth de Spotify ----------
params = st.query_params

if params.get("error"):
    st.error(
        "Spotify ha cancelado o rechazado la autorización. "
        "Puedes intentarlo de nuevo."
    )
    st.query_params.clear()

elif params.get("code"):
    oauth = spotify_oauth()
    received_state = params.get("state", "")
    expected_state = st.session_state.get("oauth_state", "")

    if oauth and expected_state and received_state == expected_state:
        try:
            st.session_state.spotify_token = oauth.get_access_token(
                params["code"],
                check_cache=False,
            )
            st.session_state.pop("oauth_state", None)
            st.query_params.clear()
            st.rerun()

        except Exception:
            st.error(
                "No se pudo completar la conexión con Spotify. "
                "Comprueba la URL de redirección."
            )
    else:
        st.error(
            "No se pudo validar la autorización de Spotify. "
            "Vuelve a iniciar la conexión."
        )


# ---------- Barra lateral ----------
with st.sidebar:
    st.markdown(
        '<div class="brand">pl'
        '<span class="brand-ai">ai</span>lister</div>',
        unsafe_allow_html=True,
    )

    st.caption("TU MÚSICA, CURADA CON IA")

    if st.button(
        "＋  Nueva playlist",
        use_container_width=True,
        type="primary",
    ):
        reset_app()
        st.rerun()

    st.divider()
    st.markdown("**Últimas playlists**")

    if not st.session_state.history:
        st.caption("Tus playlists creadas aparecerán aquí.")

    else:
        for item in reversed(st.session_state.history[-10:]):
            if st.button(
                item["name"],
                key=f'history_{item["id"]}',
                use_container_width=True,
            ):
                st.session_state.playlist_url = item["url"]
                st.session_state.playlist_name = item["name"]
                st.session_state.step = "success"
                st.rerun()

    st.divider()

    if spotify_client():
        st.markdown("Spotify conectado")

        if st.button(
            "Desconectar Spotify",
            use_container_width=True,
        ):
            st.session_state.pop("spotify_token", None)
            st.rerun()

    else:
        st.caption("Spotify no conectado")
        connect_spotify()

    if not GEMINI_API_KEY:
        st.warning(
            "Falta GEMINI_API_KEY en los Secrets de Streamlit."
        )

    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        st.caption(
            "Añade SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET "
            "a los Secrets para habilitar Spotify."
        )

    elif not secret("SPOTIFY_REDIRECT_URI", "").strip():
        st.caption(
            "En Streamlit Cloud, configura SPOTIFY_REDIRECT_URI "
            "con la URL pública exacta de esta app."
        )

    st.caption("Gemini · Spotify Web API")


# ---------- Cabecera ----------
st.markdown(
    '<div class="brand">pl'
    '<span class="brand-ai">ai</span>lister</div>',
    unsafe_allow_html=True,
)


# ---------- Paso 1: generar canciones ----------
if st.session_state.step == "create":
    st.markdown(
        '<div class="eyebrow">Descubrimiento musical con IA</div>',
        unsafe_allow_html=True,
    )

    st.title("¿Qué quieres escuchar?")

    st.markdown(
        '<p class="muted">Describe un sonido, una época, '
        'un estado de ánimo o una mezcla imposible. '
        'Nosotros hacemos el resto.</p>',
        unsafe_allow_html=True,
    )

    with st.container(key="prompt_shell"):
        st.text_area(
            "Tu petición",
            key="prompt",
            height=112,
            placeholder=(
                "Ej.: Rock alternativo de los 2000, oscuro y "
                "enérgico, con grupos menos conocidos y algunos "
                "clásicos. Sin baladas."
            ),
            label_visibility="collapsed",
        )

        left, right = st.columns(
            [1, 1],
            vertical_alignment="center",
        )

        with left:
            if st.button(
                "⚙  Ajustes",
                key="toggle_settings",
            ):
                st.session_state.show_settings = (
                    not st.session_state.show_settings
                )
                st.rerun()

        with right:
            generate = st.button(
                "Generar  ↗",
                key="generate",
                type="primary",
                use_container_width=True,
            )

    if st.session_state.show_settings:
        with st.container(border=True):
            st.markdown("**Ajustes de generación**")

            st.slider(
                "Cantidad de canciones",
                5,
                50,
                key="count",
            )

            st.slider(
                "Cantidad de artistas",
                1,
                15,
                key="artist_count",
            )

            st.slider(
                "Creatividad",
                0.0,
                1.0,
                step=0.1,
                key="temperature",
            )

            st.caption(
                "Una creatividad baja prioriza resultados "
                "previsibles; una alta permite mezclas más "
                "inesperadas."
            )

    if generate:
        if not st.session_state.prompt.strip():
            st.warning("Describe qué tipo de música quieres escuchar.")

        elif not GEMINI_API_KEY:
            st.error(
                "Falta GEMINI_API_KEY en los secretos de Streamlit."
            )

        else:
            try:
                with st.spinner(
                    "Buscando la combinación musical adecuada…"
                ):
                    st.session_state.tracks = generate_tracks(
                        st.session_state.prompt.strip(),
                        st.session_state.count,
                        st.session_state.artist_count,
                        st.session_state.temperature,
                    )

                st.session_state.step = "review"
                st.rerun()

            except Exception as exc:
                st.error(f"No se pudo generar la playlist: {exc}")


# ---------- Paso 2: revisar canciones ----------
elif st.session_state.step == "review":
    tracks = st.session_state.get("tracks", [])

    st.markdown(
        '<div class="eyebrow">Paso 2 · Revisión</div>',
        unsafe_allow_html=True,
    )

    st.title("Tu selección musical")

    st.caption(
        f"{len(tracks)} canciones propuestas · "
        "Puedes editar la lista antes de buscar las versiones "
        "de Spotify."
    )

    edited = st.text_area(
        "Canciones, una por línea (Artista - Canción)",
        value="\n".join(
            f'{track["artist"]} - {track["title"]}'
            for track in tracks
        ),
        height=min(420, max(180, len(tracks) * 34)),
        key="review_text",
    )

    col_back, col_search = st.columns(2)

    with col_back:
        if st.button("← Volver", use_container_width=True):
            st.session_state.step = "create"
            st.rerun()

    with col_search:
        search_clicked = st.button(
            "Buscar en Spotify",
            type="primary",
            use_container_width=True,
        )

    if search_clicked:
        lines = []

        for line in edited.splitlines():
            match = re.match(
                r"^\s*(.+?)\s+[–—-]\s+(.+?)\s*$",
                line,
            )

            if match:
                lines.append({
                    "artist": match.group(1),
                    "title": match.group(2),
                })

        if not lines:
            st.warning(
                "Añade canciones con el formato Artista - Canción."
            )

        elif not spotify_client():
            st.warning(
                "Conecta Spotify desde el menú lateral "
                "para buscar las canciones."
            )

        else:
            with st.spinner(
                "Verificando las canciones en Spotify…"
            ):
                resolved, missing = find_spotify_tracks(
                    spotify_client(),
                    lines,
                )

            st.session_state.resolved = resolved
            st.session_state.missing = missing
            st.session_state.step = "export"
            st.rerun()


# ---------- Paso 3: revisar coincidencias y exportar ----------
elif st.session_state.step == "export":
    resolved = st.session_state.get("resolved", [])
    missing = st.session_state.get("missing", [])

    st.markdown(
        '<div class="eyebrow">Paso 3 · Confirmación</div>',
        unsafe_allow_html=True,
    )

    st.title("Revisa las coincidencias")

    st.caption(
        f"{len(resolved)} canciones encontradas · "
        f"{len(missing)} sin coincidencia"
    )

    if resolved:
        for index, track in enumerate(resolved, 1):
            safe_title = html.escape(track["title"])
            safe_artist = html.escape(track["artist"])
            safe_album = html.escape(track["album"])
            safe_url = html.escape(track["url"], quote=True)

            st.markdown(
                f'<div class="track-row">'
                f'<div class="track-index">{index:02}</div>'
                f'<div style="flex:1;min-width:0">'
                f'<div class="track-title">{safe_title}</div>'
                f'<div class="track-artist">{safe_artist}</div>'
                f'<div class="track-album">{safe_album}</div>'
                f'</div>'
                f'<a class="track-link" href="{safe_url}" '
                f'target="_blank" rel="noopener">'
                f'Abrir {icon("external", 13)}</a>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if missing:
        with st.expander(
            f"Canciones no encontradas ({len(missing)})"
        ):
            for track in missing:
                st.write(
                    f'{track["artist"]} - {track["title"]}'
                )

    st.divider()

    with st.form("export_form"):
        playlist_name = st.text_input(
            "Nombre de la playlist",
            value="Mi playlist con pl(ai)lister",
            max_chars=100,
        )

        privacy = st.radio(
            "Privacidad",
            ["Privada", "Pública"],
            horizontal=True,
        )

        description = st.text_input(
            "Descripción (opcional)",
            value="Creada con pl(ai)lister y Gemini",
            max_chars=300,
        )

        submitted = st.form_submit_button(
            "Crear playlist en Spotify",
            type="primary",
            use_container_width=True,
        )

    back, new = st.columns(2)

    with back:
        if st.button(
            "← Volver a canciones",
            use_container_width=True,
        ):
            st.session_state.step = "review"
            st.rerun()

    with new:
        if st.button("Cancelar", use_container_width=True):
            reset_app()
            st.rerun()

    if submitted:
        sp = spotify_client()

        if not sp:
            st.error(
                "La sesión de Spotify ha caducado. "
                "Vuelve a conectar tu cuenta."
            )

        elif not resolved:
            st.error("No hay canciones encontradas para exportar.")

        else:
            try:
                me = sp.current_user()

                playlist = sp.user_playlist_create(
                    user=me["id"],
                    name=(
                        playlist_name.strip()
                        or "Mi playlist con pl(ai)lister"
                    ),
                    public=(privacy == "Pública"),
                    description=description.strip(),
                )

                uris = [track["uri"] for track in resolved]

                for start in range(0, len(uris), 100):
                    sp.playlist_add_items(
                        playlist["id"],
                        uris[start:start + 100],
                    )

                url = playlist.get(
                    "external_urls", {}
                ).get("spotify", "")

                st.session_state.playlist_url = url
                st.session_state.playlist_name = (
                    playlist_name.strip()
                    or "Mi playlist"
                )

                st.session_state.history.append({
                    "id": playlist["id"],
                    "name": (
                        playlist_name.strip()
                        or "Mi playlist"
                    ),
                    "url": url,
                })

                st.session_state.step = "success"
                st.rerun()

            except Exception:
                st.error(
                    "No se pudo crear la playlist. "
                    "Comprueba la conexión y los permisos de Spotify."
                )


# ---------- Paso 4: confirmación ----------
elif st.session_state.step == "success":
    st.markdown(
        '<div class="eyebrow">Todo listo</div>',
        unsafe_allow_html=True,
    )

    st.title("Playlist creada")

    safe_playlist_name = html.escape(
        st.session_state.get("playlist_name", "Tu playlist")
    )

    st.markdown(
        f'<div class="result-card">'
        f'{icon("check", 22)} '
        f'<strong>{safe_playlist_name}</strong>'
        f'<p class="muted">Ya puedes escucharla en Spotify.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    url = st.session_state.get("playlist_url", "")

    if url:
        st.link_button(
            "Abrir en Spotify  ↗",
            url,
            type="primary",
            use_container_width=True,
        )

        st.code(url, language=None)

    if st.button(
        "＋ Crear otra playlist",
        use_container_width=True,
    ):
        reset_app()
        st.rerun()


# ---------- Pie de página ----------
st.markdown("<hr>", unsafe_allow_html=True)

st.markdown(
    '<p style="text-align:center;color:#777;font-size:.78rem">'
    'pl(ai)lister · Descubre música a tu manera</p>',
    unsafe_allow_html=True,
)