
import json
import os
import re
import secrets
from urllib.parse import urlencode

import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from google import genai


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="pl(ai)lister",
    page_icon="♫",
    layout="centered",
    initial_sidebar_state="expanded",
)

DEFAULT_MODEL = "gemini-3.8-flash"
DEFAULT_TRACK_COUNT = 20
DEFAULT_ARTIST_COUNT = 12

SPOTIFY_SCOPES = (
    "playlist-modify-public "
    "playlist-modify-private"
)


def get_setting(name, default=""):
    """Lee primero Streamlit Secrets y después variables de entorno."""
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default

    return os.getenv(name, value) or default


def get_model_name():
    """Normaliza nombres de modelos escritos con espacios o prefijos."""
    model = str(
        get_setting("GEMINI_MODEL", DEFAULT_MODEL)
    ).strip().strip("\"'")

    model = re.sub(r"^models/", "", model, flags=re.IGNORECASE)
    model = model.replace(" ", "-").lower()

    return model or DEFAULT_MODEL


def get_spotify_redirect_uri():
    return str(
        get_setting("SPOTIFY_REDIRECT_URI", "")
    ).strip().rstrip("/")


def get_spotify_oauth():
    client_id = get_setting("SPOTIFY_CLIENT_ID")
    client_secret = get_setting("SPOTIFY_CLIENT_SECRET")
    redirect_uri = get_spotify_redirect_uri()

    if not client_id or not client_secret or not redirect_uri:
        raise ValueError(
            "Falta configurar SPOTIFY_CLIENT_ID, "
            "SPOTIFY_CLIENT_SECRET o SPOTIFY_REDIRECT_URI."
        )

    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SPOTIFY_SCOPES,
        cache_path=None,
        open_browser=False,
    )


# ============================================================
# ESTADO DE LA APLICACIÓN
# ============================================================

DEFAULT_STATE = {
    "step": "create",
    "prompt": "",
    "count": DEFAULT_TRACK_COUNT,
    "artist_count": DEFAULT_ARTIST_COUNT,
    "temperature": 0.7,
    "tracks": [],
    "resolved": [],
    "missing": [],
    "playlist_name": "",
    "playlist_url": "",
    "spotify_token": None,
    "oauth_state": None,
    "history": [],
    "review_text": "",
    "last_error": "",
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_app():
    """Inicia una playlist nueva sin desconectar Spotify."""
    keep = {
        "spotify_token": st.session_state.get("spotify_token"),
    }

    for key, value in DEFAULT_STATE.items():
        st.session_state[key] = value

    st.session_state.spotify_token = keep["spotify_token"]


# ============================================================
# ESTILO
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&display=swap');

    :root {
        --bg: #101010;
        --panel: #191919;
        --panel-hover: #242424;
        --text: #f5f5f5;
        --muted: #b3b3b3;
        --subtle: #777777;
        --green: #1ed760;
        --border: #303030;
    }

    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Google Sans', Arial, sans-serif;
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: #090909;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] * {
        color: #e8e8e8;
    }

    .block-container {
        max-width: 860px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3, p, label {
        color: var(--text);
        font-family: 'Google Sans', Arial, sans-serif;
    }

    h1 {
        font-size: 2.25rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.06em;
    }

    h2 {
        font-size: 1.35rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.025em;
    }

    .brand {
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: -0.04em;
        margin: 0.2rem 0 2rem 0;
    }

    .brand span {
        color: var(--green);
    }

    .eyebrow {
        color: var(--muted);
        font-size: 0.76rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .muted {
        color: var(--muted);
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .panel {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.25rem;
        margin: 0.7rem 0 1rem 0;
    }

    .stTextArea textarea,
    .stTextInput input,
    .stNumberInput input {
        background: #202020 !important;
        color: var(--text) !important;
        border: 1px solid #393939 !important;
        border-radius: 12px !important;
    }

    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: var(--green) !important;
        box-shadow: 0 0 0 1px var(--green) !important;
    }

    .stSlider [data-baseweb="slider"] div[role="slider"] {
        background: var(--green) !important;
    }

    .stButton > button,
    .stLinkButton > a,
    .stDownloadButton > button {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 44px;
        width: 100%;
        border-radius: 999px;
        font-family: 'Google Sans', Arial, sans-serif;
        font-size: 0.92rem;
        font-weight: 600;
        border: 1px solid #484848;
        transition: background 0.15s ease, transform 0.15s ease;
    }

    .stButton > button[kind="primary"],
    .stLinkButton > a[kind="primary"] {
        background: var(--green) !important;
        color: #07190c !important;
        border-color: var(--green) !important;
    }

    .stButton > button[kind="secondary"],
    .stLinkButton > a[kind="secondary"] {
        background: #242424 !important;
        color: var(--text) !important;
    }

    .stButton > button:hover,
    .stLinkButton > a:hover {
        filter: brightness(1.08);
        transform: translateY(-1px);
    }

    div[data-testid="stForm"] {
        border: 0;
        padding: 0;
    }

    div[data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--border);
        padding: 0.8rem;
        border-radius: 12px;
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    hr {
        border-color: var(--border);
    }

    a {
        color: var(--green);
    }

    .track-row {
        border-bottom: 1px solid var(--border);
        padding: 0.65rem 0;
        color: var(--text);
    }

    .small-note {
        font-size: 0.78rem;
        color: var(--muted);
    }

    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SPOTIFY: AUTORIZACIÓN Y TOKEN
# ============================================================

def process_spotify_callback():
    """Procesa el retorno de Spotify en la misma página de Streamlit."""
    params = st.query_params

    error = params.get("error")
    code = params.get("code")
    returned_state = params.get("state")
    expected_state = st.session_state.get("oauth_state")

    if error:
        st.session_state.last_error = (
            f"Spotify no autorizó la conexión: {error}"
        )
        st.session_state.oauth_state = None
        st.query_params.clear()
        return

    if not code:
        return

    if not expected_state or returned_state != expected_state:
        st.session_state.last_error = (
            "No se pudo validar la sesión de Spotify. "
            "Vuelve a pulsar «Conectar con Spotify»."
        )
        st.session_state.oauth_state = None
        st.query_params.clear()
        return

    try:
        oauth = get_spotify_oauth()
        token_info = oauth.get_access_token(
            code=code,
            as_dict=True,
            check_cache=False,
        )

        if not token_info or not token_info.get("access_token"):
            raise RuntimeError(
                "Spotify no devolvió un token de acceso válido."
            )

        st.session_state.spotify_token = token_info
        st.session_state.oauth_state = None
        st.session_state.last_error = ""

    except Exception as exc:
        st.session_state.last_error = (
            "No se pudo completar la conexión con Spotify. "
            f"Detalle: {exc}"
        )

    finally:
        st.query_params.clear()


def get_spotify_client():
    token_info = st.session_state.get("spotify_token")

    if not token_info:
        return None

    try:
        oauth = get_spotify_oauth()

        if oauth.is_token_expired(token_info):
            refreshed = oauth.refresh_access_token(
                token_info["refresh_token"]
            )
            st.session_state.spotify_token = refreshed
            token_info = refreshed

        return spotipy.Spotify(
            auth=token_info["access_token"],
            requests_timeout=20,
            retries=2,
        )

    except Exception as exc:
        st.session_state.last_error = (
            f"Error al renovar la sesión de Spotify: {exc}"
        )
        st.session_state.spotify_token = None
        return None


def spotify_authorize_url():
    oauth = get_spotify_oauth()
    state = secrets.token_urlsafe(24)

    st.session_state.oauth_state = state

    # Spotipy incorpora client_id, redirect_uri, scopes y state.
    return oauth.get_authorize_url(state=state)


process_spotify_callback()


# ============================================================
# GEMINI: GENERACIÓN DE PLAYLIST
# ============================================================

def generate_playlist(prompt, count, artist_count, creativity):
    api_key = get_setting("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "Falta GEMINI_API_KEY en Streamlit Secrets "
            "o en las variables de entorno."
        )

    # Importante: usamos el identificador API, no el nombre comercial.
    model = get_model_name()
    client = genai.Client(api_key=api_key)

    temperature = max(0.1, min(1.5, float(creativity)))

    instructions = f"""
Eres un experto curador musical. Crea una selección de canciones
para una playlist de Spotify a partir de la petición del usuario.

PETICIÓN:
{prompt}

REQUISITOS:
- Devuelve exactamente {count} canciones.
- Intenta incluir al menos {artist_count} artistas diferentes.
- Prioriza canciones reales y publicadas.
- No inventes títulos ni artistas.
- Mantén la coherencia musical con la petición.
- Evita repetir canciones.
- Responde exclusivamente con JSON válido, sin Markdown ni comentarios.
- Usa este formato:
{{
  "playlist_name": "Nombre breve de la playlist",
  "tracks": [
    {{"artist": "Nombre del artista", "title": "Título de la canción"}}
  ]
}}
"""

    response = client.models.generate_content(
        model=model,
        contents=instructions,
        config={
            "temperature": temperature,
            "response_mime_type": "application/json",
        },
    )

    text = getattr(response, "text", None)

    if not text:
        raise RuntimeError(
            "Gemini devolvió una respuesta vacía. "
            "Intenta generar la playlist otra vez."
        )

    # Elimina cercas Markdown por si el modelo las devuelve.
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini no devolvió un JSON válido. "
            "Intenta generar la selección otra vez."
        ) from exc

    raw_tracks = data.get("tracks", [])
    tracks = []
    seen = set()

    for item in raw_tracks:
        if not isinstance(item, dict):
            continue

        artist = str(item.get("artist", "")).strip()
        title = str(item.get("title", "")).strip()

        if not artist or not title:
            continue

        key = (artist.casefold(), title.casefold())

        if key in seen:
            continue

        seen.add(key)
        tracks.append({
            "artist": artist,
            "title": title,
        })

        if len(tracks) >= count:
            break

    if not tracks:
        raise RuntimeError(
            "Gemini no generó canciones utilizables. "
            "Prueba con una descripción más concreta."
        )

    playlist_name = str(
        data.get("playlist_name", "")
    ).strip() or "Mi playlist pl(ai)lister"

    return playlist_name, tracks


# ============================================================
# SPOTIFY: BÚSQUEDA Y EXPORTACIÓN
# ============================================================

def find_spotify_tracks(sp, tracks):
    resolved = []
    missing = []

    progress = st.progress(0, text="Buscando canciones en Spotify…")

    for index, track in enumerate(tracks):
        artist = track["artist"]
        title = track["title"]

        try:
            result = sp.search(
                q=f'track:"{title}" artist:"{artist}"',
                type="track",
                limit=5,
            )

            items = result.get("tracks", {}).get("items", [])

            if not items:
                # Segunda búsqueda más flexible.
                result = sp.search(
                    q=f"{title} {artist}",
                    type="track",
                    limit=5,
                )
                items = result.get("tracks", {}).get("items", [])

            if items:
                selected = items[0]
                resolved.append({
                    "artist": artist,
                    "title": title,
                    "spotify_artist": ", ".join(
                        artist_obj["name"]
                        for artist_obj in selected.get("artists", [])
                    ),
                    "spotify_title": selected.get("name", title),
                    "uri": selected["uri"],
                    "url": selected.get("external_urls", {}).get(
                        "spotify", ""
                    ),
                })
            else:
                missing.append(track)

        except Exception:
            missing.append(track)

        progress.progress(
            (index + 1) / max(len(tracks), 1),
            text=f"Buscando canciones: {index + 1}/{len(tracks)}",
        )

    progress.empty()
    return resolved, missing


def create_spotify_playlist(sp, playlist_name, tracks):
    user = sp.current_user()
    user_id = user["id"]

    playlist = sp.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=False,
        description="Creada con pl(ai)lister.",
    )

    uris = [track["uri"] for track in tracks]

    # Spotify admite hasta 100 canciones por solicitud.
    for start in range(0, len(uris), 100):
        sp.playlist_add_items(
            playlist["id"],
            uris[start:start + 100],
        )

    return playlist.get("external_urls", {}).get("spotify", "")


# ============================================================
# CABECERA Y BARRA LATERAL
# ============================================================

with st.sidebar:
    st.markdown(
        '<div class="brand">pl(<span>ai</span>)lister</div>',
        unsafe_allow_html=True,
    )

    st.caption("TU GUSTO. TU PROMPT. TU PLAYLIST.")

    if st.button(
        "＋  Nueva playlist",
        key="new_playlist",
        type="primary",
        use_container_width=True,
    ):
        reset_app()
        st.rerun()

    st.divider()

    st.markdown("**Spotify**")

    connected = bool(st.session_state.get("spotify_token"))

    if connected:
        st.success("Spotify conectado")

        if st.button(
            "Desconectar Spotify",
            key="disconnect_spotify",
            use_container_width=True,
        ):
            st.session_state.spotify_token = None
            st.session_state.oauth_state = None
            st.rerun()

    else:
        try:
            auth_url = spotify_authorize_url()

            st.markdown(
                f"""
                <a href="{auth_url}" target="_self"
                   style="
                     display:flex;
                     align-items:center;
                     justify-content:center;
                     gap:10px;
                     width:100%;
                     box-sizing:border-box;
                     min-height:44px;
                     padding:10px 14px;
                     background:#1ed760;
                     color:#07190c;
                     text-decoration:none;
                     border-radius:999px;
                     font-weight:600;
                     font-size:14px;
                   ">
                    <svg width="20" height="20" viewBox="0 0 24 24"
                         fill="currentColor" aria-hidden="true">
                        <path d="M12 1.8a10.2 10.2 0 1 0 0 20.4
                        10.2 10.2 0 0 0 0-20.4zm4.68 14.72a.63.63
                        0 0 1-.87.21c-2.38-1.45-5.37-1.78-8.9-.98a.63.63
                        0 1 1-.28-1.23c3.86-.88 7.17-.49 9.84 1.13
                        .3.18.4.57.21.87zm1.24-2.76a.78.78 0 0 1-1.07.26
                        c-2.72-1.67-6.87-2.15-10.09-1.18a.78.78 0 1
                        1-.45-1.49c3.68-1.11 8.25-.57 11.35 1.34
                        .37.22.49.7.26 1.07zm.1-2.87c-3.27-1.94-8.68-2.12
                        -11.8-1.17a.94.94 0 1 1-.55-1.8c3.58-1.09
                        9.54-.88 13.31 1.35a.94.94 0 0 1-.96 1.62z"/>
                    </svg>
                    Conectar con Spotify
                </a>
                """,
                unsafe_allow_html=True,
            )

        except ValueError as exc:
            st.warning(str(exc))

    with st.expander("Ajustes"):
        st.markdown("**Número de canciones**")
        st.slider(
            "Canciones",
            min_value=5,
            max_value=50,
            step=5,
            key="count",
            label_visibility="collapsed",
        )

        st.markdown("**Diversidad de artistas**")
        st.slider(
            "Artistas",
            min_value=3,
            max_value=30,
            step=1,
            key="artist_count",
            label_visibility="collapsed",
        )

        st.markdown("**Creatividad**")
        st.slider(
            "Creatividad",
            min_value=0.1,
            max_value=1.5,
            step=0.1,
            key="temperature",
            label_visibility="collapsed",
        )
        st.caption("BAJA: prioriza resultados previsibles")
        st.caption("ALTA: permite mezclas más inesperadas")

    st.divider()
    st.caption("Hecho para descubrir música.")


# Mostrar errores que vienen de un callback o acción anterior.
if st.session_state.get("last_error"):
    st.error(st.session_state.last_error)


# ============================================================
# PANTALLA: CREAR
# ============================================================

if st.session_state.step == "create":
    st.markdown(
        '<div class="eyebrow">TU CURADOR MUSICAL CON IA</div>',
        unsafe_allow_html=True,
    )

    st.title("¿Qué quieres escuchar?")
    st.markdown(
        '<p class="muted">Describe un sonido, una época, un estado de '
        'ánimo o una mezcla imposible. Te prepararemos una selección '
        'que después podrás revisar y guardar en Spotify.</p>',
        unsafe_allow_html=True,
    )

    with st.form("playlist_prompt_form"):
        prompt_value = st.text_area(
            "Describe tu playlist",
            value=st.session_state.prompt,
            key="prompt_input",
            placeholder=(
                "Ej.: rock alternativo de los 2000, guitarras potentes, "
                "melancólico pero enérgico, con canciones poco obvias…"
            ),
            height=150,
            label_visibility="collapsed",
        )

        submitted = st.form_submit_button(
            "Generar selección  →",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        prompt_value = prompt_value.strip()

        if not prompt_value:
            st.warning("Describe qué tipo de música quieres escuchar.")
        else:
            st.session_state.prompt = prompt_value

            try:
                with st.spinner("Buscando la combinación adecuada…"):
                    playlist_name, tracks = generate_playlist(
                        prompt=prompt_value,
                        count=int(st.session_state.count),
                        artist_count=int(st.session_state.artist_count),
                        creativity=float(st.session_state.temperature),
                    )

                st.session_state.playlist_name = playlist_name
                st.session_state.tracks = tracks
                st.session_state.resolved = []
                st.session_state.missing = []
                st.session_state.review_text = "\n".join(
                    f'{track["artist"]} - {track["title"]}'
                    for track in tracks
                )
                st.session_state.last_error = ""
                st.session_state.step = "review"
                st.rerun()

            except Exception as exc:
                st.error(
                    "No se pudo generar la selección. "
                    f"Detalle: {exc}"
                )


# ============================================================
# PANTALLA: REVISAR SELECCIÓN
# ============================================================

elif st.session_state.step == "review":
    st.markdown(
        '<div class="eyebrow">PASO 02 · REVISAR</div>',
        unsafe_allow_html=True,
    )

    st.title(st.session_state.playlist_name or "Tu selección")
    st.markdown(
        '<p class="muted">Puedes editar la lista antes de buscar las '
        'canciones en Spotify. Usa una línea por canción con el formato '
        '<b>Artista - Canción</b>.</p>',
        unsafe_allow_html=True,
    )

    review_value = "\n".join(
        f'{track["artist"]} - {track["title"]}'
        for track in st.session_state.tracks
    )

    edited_text = st.text_area(
        "Canciones",
        value=review_value,
        key="track_review_editor",
        height=350,
        label_visibility="collapsed",
    )

    left, right = st.columns(2)

    with left:
        if st.button(
            "← Volver",
            key="back_to_create",
            use_container_width=True,
        ):
            st.session_state.step = "create"
            st.rerun()

    with right:
        find_clicked = st.button(
            "Buscar en Spotify  →",
            key="find_on_spotify",
            type="primary",
            use_container_width=True,
        )

    if find_clicked:
        parsed_tracks = []

        for line in edited_text.splitlines():
            line = line.strip()

            if not line:
                continue

            match = re.match(
                r"^\s*(.+?)\s+[–—-]\s+(.+?)\s*$",
                line,
            )

            if match:
                parsed_tracks.append({
                    "artist": match.group(1).strip(),
                    "title": match.group(2).strip(),
                })

        if not parsed_tracks:
            st.warning(
                "No se detectaron canciones. "
                "Escribe cada una como Artista - Canción."
            )
        else:
            st.session_state.tracks = parsed_tracks
            sp = get_spotify_client()

            if not sp:
                st.warning(
                    "Conecta Spotify desde la barra lateral antes "
                    "de buscar y exportar la playlist."
                )
            else:
                try:
                    with st.spinner(
                        "Buscando las canciones en el catálogo de Spotify…"
                    ):
                        resolved, missing = find_spotify_tracks(
                            sp,
                            parsed_tracks,
                        )

                    st.session_state.resolved = resolved
                    st.session_state.missing = missing
                    st.session_state.step = "export"
                    st.session_state.last_error = ""
                    st.rerun()

                except Exception as exc:
                    st.error(
                        "No se pudieron buscar las canciones. "
                        f"Detalle: {exc}"
                    )


# ============================================================
# PANTALLA: EXPORTAR
# ============================================================

elif st.session_state.step == "export":
    st.markdown(
        '<div class="eyebrow">PASO 03 · EXPORTAR</div>',
        unsafe_allow_html=True,
    )

    st.title("Tu playlist está casi lista")

    resolved = st.session_state.resolved
    missing = st.session_state.missing

    c1, c2 = st.columns(2)
    c1.metric("Encontradas", len(resolved))
    c2.metric("No encontradas", len(missing))

    if resolved:
        st.markdown("### Canciones que se añadirán")

        for index, track in enumerate(resolved, start=1):
            st.markdown(
                f"""
                <div class="track-row">
                    <span style="color:#888;display:inline-block;width:30px">
                        {index:02d}
                    </span>
                    <b>{track["spotify_title"]}</b>
                    <span style="color:#b3b3b3"> ·
                        {track["spotify_artist"]}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if missing:
        with st.expander(
            f"Canciones no encontradas ({len(missing)})"
        ):
            for track in missing:
                st.write(f'{track["artist"]} - {track["title"]}')

    st.divider()

    playlist_name = st.text_input(
        "Nombre de la playlist",
        value=st.session_state.playlist_name,
        key="export_playlist_name",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "← Volver a revisar",
            key="back_to_review",
            use_container_width=True,
        ):
            st.session_state.step = "review"
            st.rerun()

    with col2:
        export_clicked = st.button(
            "Crear en Spotify  →",
            key="create_spotify_playlist",
            type="primary",
            use_container_width=True,
            disabled=not resolved,
        )

    if export_clicked:
        sp = get_spotify_client()

        if not sp:
            st.error(
                "La sesión de Spotify ha caducado. "
                "Vuelve a conectarte desde la barra lateral."
            )
        elif not playlist_name.strip():
            st.warning("Escribe un nombre para la playlist.")
        else:
            try:
                with st.spinner("Creando tu playlist en Spotify…"):
                    playlist_url = create_spotify_playlist(
                        sp,
                        playlist_name.strip(),
                        resolved,
                    )

                st.session_state.playlist_name = playlist_name.strip()
                st.session_state.playlist_url = playlist_url
                st.session_state.step = "success"
                st.session_state.last_error = ""
                st.rerun()

            except Exception as exc:
                st.error(
                    "No se pudo crear la playlist en Spotify. "
                    f"Detalle: {exc}"
                )


# ============================================================
# PANTALLA: ÉXITO
# ============================================================

elif st.session_state.step == "success":
    st.markdown(
        '<div class="eyebrow">LISTA PARA ESCUCHAR</div>',
        unsafe_allow_html=True,
    )

    st.title("Playlist creada.")
    st.markdown(
        f'<p class="muted">{st.session_state.playlist_name}</p>',
        unsafe_allow_html=True,
    )

    st.success(
        f"Se han añadido {len(st.session_state.resolved)} canciones."
    )

    playlist_url = st.session_state.playlist_url

    if playlist_url:
        st.link_button(
            "♫  Abrir en Spotify",
            playlist_url,
            type="primary",
            use_container_width=True,
        )

    if st.button(
        "＋  Crear otra playlist",
        key="create_another_playlist",
        use_container_width=True,
    ):
        reset_app()
        st.rerun()
