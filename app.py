import html
import json
import os
import secrets
import time

import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from google import genai
from google.genai import types
from openai import OpenAI


# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="pl(ai)lister",
    page_icon="♪",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
SPOTIFY_SCOPES = "playlist-modify-public playlist-modify-private"


def get_secret(key, default=""):
    try:
        return st.secrets.get(key, default) or default
    except Exception:
        return os.getenv(key, default) or default


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GEMINI_MODEL = get_secret("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)

OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
OPENAI_MODEL = get_secret("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

PUTER_API_KEY = get_secret("PUTER_API_KEY")

SPOTIFY_CLIENT_ID = get_secret("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = get_secret("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = get_secret(
    "SPOTIFY_REDIRECT_URI",
    "http://localhost:8501",
).rstrip("/")


# =========================================================
# DESIGN SYSTEM
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&display=swap');

:root {
    --bg: #121212;
    --surface: #1E1E1E;
    --surface-hover: #292929;
    --border: #383838;
    --text: #F5F5F5;
    --muted: #A7A7A7;
    --green: #1ED760;
    --green-hover: #3BE477;
    --green-text: #07150B;

    --font: "Google Sans", Arial, sans-serif;
    --radius: 16px;
    --radius-pill: 999px;
    --control-height: 46px;
}

html, body, [class*="css"], .stApp {
    font-family: var(--font) !important;
}

.stApp {
    background: var(--bg);
    color: var(--text);
}

header[data-testid="stHeader"] {
    background: transparent;
}

#MainMenu, footer {
    visibility: hidden;
}

.block-container {
    max-width: 880px;
    padding: 28px 28px 32px !important;
}

/* Tipografía */

h1, h2, h3, p, label, input, textarea, button {
    font-family: var(--font) !important;
}

h1 {
    color: var(--text) !important;
    font-size: clamp(30px, 4vw, 40px) !important;
    font-weight: 600 !important;
    line-height: 1.15 !important;
    letter-spacing: -1px !important;
    margin-bottom: 12px !important;
}

h2 {
    color: var(--text) !important;
    font-size: 24px !important;
    font-weight: 600 !important;
    letter-spacing: -.4px !important;
}

h3 {
    color: var(--text) !important;
    font-size: 18px !important;
    font-weight: 600 !important;
}

p {
    line-height: 1.6;
}

.muted {
    color: var(--muted);
    font-size: 14px;
    line-height: 1.6;
}

.eyebrow {
    color: var(--green);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.3px;
    text-transform: uppercase;
    margin-bottom: 10px;
}

/* Marca */

.brand {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: 28px;
    color: var(--text);
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -1.2px;
    line-height: 1.2;
}

.brand-ai {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border: 2px solid var(--green);
    border-radius: 50%;
    color: var(--green);
    font-size: 10px;
    letter-spacing: -.3px;
}

/* Barra lateral */

section[data-testid="stSidebar"] {
    background: #090909;
    border-right: 1px solid #292929;
}

section[data-testid="stSidebar"] > div {
    padding: 24px 18px;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: rgba(255,255,255,.9) !important;
}

section[data-testid="stSidebar"] hr {
    border-color: #303030;
    margin: 20px 0;
}

.sidebar-label {
    color: rgba(255,255,255,.65);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 12px;
}

/* Botones */

.stButton > button,
.stLinkButton > a,
div[data-testid="stFormSubmitButton"] button {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: var(--control-height) !important;
    height: var(--control-height);
    padding: 0 18px !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-pill) !important;
    background: var(--surface-hover) !important;
    color: var(--text) !important;
    font-family: var(--font) !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    text-decoration: none !important;
    box-shadow: none !important;
    transition: background .15s ease, border-color .15s ease;
}

.stButton > button:hover,
.stLinkButton > a:hover {
    background: #353535 !important;
    border-color: #555 !important;
    color: #fff !important;
}

.stButton > button[kind="primary"],
div[data-testid="stFormSubmitButton"] button,
.stLinkButton > a[kind="primary"] {
    background: var(--green) !important;
    border-color: var(--green) !important;
    color: var(--green-text) !important;
}

.stButton > button[kind="primary"]:hover,
div[data-testid="stFormSubmitButton"] button:hover,
.stLinkButton > a[kind="primary"]:hover {
    background: var(--green-hover) !important;
    border-color: var(--green-hover) !important;
    color: var(--green-text) !important;
}

.stButton > button:focus-visible,
.stLinkButton > a:focus-visible {
    outline: 2px solid var(--green) !important;
    outline-offset: 3px !important;
}

/* Campos */

div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    font-family: var(--font) !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    padding: 14px 16px !important;
    box-shadow: none !important;
}

div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stTextInput"] input:focus {
    border-color: #777 !important;
    box-shadow: 0 0 0 1px #777 !important;
}

textarea::placeholder,
input::placeholder {
    color: #999 !important;
    opacity: 1 !important;
}

div[data-testid="stTextArea"] label {
    display: none !important;
}

div[data-testid="stTextInput"] label {
    color: var(--text) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    margin-bottom: 8px !important;
}

/* Composer */

.composer {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 18px;
    margin: 24px 0 16px;
}

.st-key-prompt_input textarea {
    min-height: 120px !important;
    background: transparent !important;
    border: 0 !important;
    padding: 8px 2px !important;
    font-size: 15px !important;
}

.st-key-prompt_input textarea:focus {
    border: 0 !important;
    box-shadow: none !important;
}

.st-key-prompt_input [data-baseweb="textarea"] {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

.st-key-adjust_button button,
.st-key-generate_button button {
    width: 100% !important;
    min-height: 46px !important;
    height: 46px !important;
}

/* Slider */

div[data-testid="stSlider"] [role="slider"] {
    background: var(--green) !important;
    border-color: var(--green) !important;
}

.slider-labels {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    margin: -4px 0 16px;
}

.slider-side {
    color: var(--muted);
    flex: 1;
    font-size: 11px;
    line-height: 1.5;
}

.slider-side strong {
    display: block;
    color: var(--text);
    font-size: 11px;
    letter-spacing: .6px;
    margin-bottom: 3px;
}

.slider-side:last-child {
    text-align: right;
}

/* Modal */

div[data-testid="stDialog"] > div,
div[role="dialog"] {
    background: #181818 !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
}

/* Canciones */

.track-row {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 4px;
    border-bottom: 1px solid #303030;
}

.track-index {
    width: 24px;
    flex-shrink: 0;
    color: var(--muted);
    font-size: 12px;
}

.track-info {
    flex: 1;
    min-width: 0;
}

.track-title {
    color: var(--text);
    font-size: 14px;
    font-weight: 600;
    line-height: 1.45;
}

.track-artist {
    color: var(--muted);
    font-size: 12px;
    margin-top: 3px;
}

.track-album {
    color: #888;
    font-size: 11px;
    margin-top: 3px;
}

.track-link {
    color: var(--green);
    font-size: 12px;
    text-decoration: none;
    white-space: nowrap;
}

.result-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px;
    margin: 16px 0;
}

hr {
    border-color: #303030;
}

@media (max-width: 760px) {
    .block-container {
        padding: 20px 16px 28px !important;
    }

    .brand {
        margin-bottom: 22px;
    }

    .composer {
        padding: 14px;
        border-radius: 16px;
        margin-top: 20px;
    }

    h1 {
        font-size: 31px !important;
    }
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# ICONOS
# =========================================================

ICONS = {
    "external": (
        '<path d="M15 3h6v6"/>'
        '<path d="M10 14 21 3"/>'
        '<path d="M19 13v6a2 2 0 0 1-2 2H5'
        'a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h6"/>'
    ),
    "check": '<path d="m5 12 4 4L19 6"/>',
    "spotify": (
        '<circle cx="12" cy="12" r="10" fill="#1ED760" stroke="none"/>'
        '<path d="M6.5 9.2c3.9-1.2 8.5-.8 11.2 1" '
        'stroke="#07150B" stroke-width="1.7"/>'
        '<path d="M7.2 12.2c3.2-1 7-.6 9.4 1" '
        'stroke="#07150B" stroke-width="1.5"/>'
        '<path d="M7.8 15c2.7-.7 5.5-.4 7.5.8" '
        'stroke="#07150B" stroke-width="1.4"/>'
    ),
}


def icon(name, size=18):
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.7" '
        'stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true">'
        f'{ICONS[name]}</svg>'
    )


def brand():
    st.markdown(
        '<div class="brand">pl'
        '<span class="brand-ai">ai</span>lister</div>',
        unsafe_allow_html=True,
    )


# =========================================================
# SPOTIFY
# =========================================================

def spotify_oauth():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return None

    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPES,
        cache_path=None,
        open_browser=False,
    )


def spotify_client():
    token = st.session_state.get("spotify_token")
    if not token:
        return None

    oauth = spotify_oauth()
    if not oauth:
        return None

    if token.get("expires_at", 0) < time.time() + 60:
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            st.session_state.pop("spotify_token", None)
            return None

        try:
            token = oauth.refresh_access_token(refresh_token)
            st.session_state.spotify_token = token
        except Exception:
            st.session_state.pop("spotify_token", None)
            return None

    return spotipy.Spotify(auth=token["access_token"])


def spotify_connect_button():
    oauth = spotify_oauth()

    if not oauth:
        st.caption("Configura las credenciales de Spotify en Secrets.")
        return

    if not st.session_state.get("oauth_state"):
        st.session_state.oauth_state = secrets.token_urlsafe(24)

    url = html.escape(
        oauth.get_authorize_url(state=st.session_state.oauth_state),
        quote=True,
    )

    st.markdown(
        f'<a href="{url}" target="_self" style="'
        'display:flex;align-items:center;justify-content:center;gap:10px;'
        'height:46px;padding:0 16px;background:#1ED760;color:#07150B;'
        'border:1px solid #1ED760;border-radius:999px;text-decoration:none;'
        'font-family:Google Sans,Arial,sans-serif;font-size:14px;'
        'font-weight:600">'
        f'{icon("spotify", 20)}Conectar con Spotify</a>',
        unsafe_allow_html=True,
    )


# =========================================================
# GENERACIÓN DE CANCIONES (MULTI-LLM: GEMINI / OPENAI / PUTER)
# =========================================================

def generate_tracks(prompt, count, artist_count, temperature):
    provider = st.session_state.get("ai_provider", "Gemini")

    instructions = f"""
Actúa como curador musical experto.

Devuelve únicamente JSON válido con esta estructura:
{{"tracks":[{{"artist":"artista","title":"canción"}}]}}

Genera {count} canciones reales y distintas de aproximadamente
{artist_count} artistas diferentes.

Respeta el género, época, idioma, ambiente, referencias y exclusiones
del usuario. No inventes canciones. Evita duplicados.
No incluyas explicaciones ni Markdown.
"""

    response_text = ""

    if provider == "Gemini":
        if not GEMINI_API_KEY:
            raise ValueError("Falta GEMINI_API_KEY en los Secrets.")
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"{instructions}\n\nPetición del usuario:\n{prompt}",
            config=types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
            ),
        )
        response_text = response.text

    elif provider == "OpenAI":
        if not OPENAI_API_KEY:
            raise ValueError("Falta OPENAI_API_KEY en los Secrets.")
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        response_text = response.choices[0].message.content

    elif provider == "Puter (OpenAI Gratis)":
        if not PUTER_API_KEY:
            raise ValueError("Falta PUTER_API_KEY en los Secrets.")
        client = OpenAI(
            base_url="https://api.puter.com/v1",
            api_key=PUTER_API_KEY,
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
        )
        response_text = response.choices[0].message.content

    # Limpieza básica por si el modelo devuelve markdown ```json ... ```
    if response_text.startswith("```"):
        response_text = response_text.strip("`").removeprefix("json").strip()

    try:
        data = json.loads(response_text or "")
    except json.JSONDecodeError as exc:
        raise ValueError(f"{provider} devolvió una respuesta JSON no válida.") from exc

    tracks = []
    seen = set()

    for item in data.get("tracks", []):
        if not isinstance(item, dict):
            continue

        artist = str(item.get("artist", "")).strip()
        title = str(item.get("title", "")).strip()
        key = (artist.casefold(), title.casefold())

        if artist and title and key not in seen:
            tracks.append({"artist": artist, "title": title})
            seen.add(key)

        if len(tracks) == count:
            break

    if len(tracks) < count:
        raise ValueError(
            f"Solo se recibieron {len(tracks)} canciones válidas "
            f"de las {count} solicitadas. Prueba otra petición."
        )

    return tracks


# =========================================================
# BÚSQUEDA DE CANCIONES
# =========================================================

def find_spotify_tracks(sp, tracks):
    found, missing = [], []
    seen_uris = set()

    progress = st.progress(0, text="Buscando en Spotify…")

    for i, track in enumerate(tracks):
        query = f'track:"{track["title"]}" artist:"{track["artist"]}"'

        try:
            result = sp.search(q=query, type="track", limit=5)
            items = result.get("tracks", {}).get("items", [])

            if not items:
                result = sp.search(
                    q=f'{track["title"]} {track["artist"]}',
                    type="track",
                    limit=5,
                )
                items = result.get("tracks", {}).get("items", [])

            match = next(
                (item for item in items if item["uri"] not in seen_uris),
                None,
            )

            if match:
                seen_uris.add(match["uri"])
                found.append({
                    "title": match["name"],
                    "artist": ", ".join(
                        a["name"] for a in match.get("artists", [])
                    ),
                    "album": match.get("album", {}).get("name", ""),
                    "uri": match["uri"],
                    "url": match.get("external_urls", {}).get("spotify", ""),
                })
            else:
                missing.append(track)

        except Exception:
            missing.append(track)

        progress.progress(
            (i + 1) / max(len(tracks), 1),
            text=f"Buscando en Spotify… {i + 1}/{len(tracks)}",
        )

    progress.empty()
    return found, missing


# =========================================================
# ESTADO DE LA APP
# =========================================================

DEFAULTS = {
    "step": "create",
    "prompt": "",
    "count": 15,
    "artist_count": 5,
    "temperature": 0.7,
    "ai_provider": "Gemini",
    "history": [],
    "tracks": [],
    "resolved": [],
    "missing": [],
    "playlist_name": "",
    "playlist_url": "",
}

for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def reset_app():
    for key in (
        "tracks", "resolved", "missing",
        "playlist_name", "playlist_url", "review_text",
    ):
        st.session_state.pop(key, None)

    st.session_state.step = "create"
    st.session_state.prompt = ""


# =========================================================
# MODAL DE AJUSTES
# =========================================================

@st.dialog("Ajustes de generación", width="small")
def settings_dialog():
    st.markdown(
        '<p class="muted">Personaliza tu selección musical y el proveedor de IA.</p>',
        unsafe_allow_html=True,
    )

    st.selectbox(
        "Proveedor de IA",
        options=["Gemini", "OpenAI", "Puter (OpenAI Gratis)"],
        key="ai_provider",
    )

    st.slider("Cantidad de canciones", 5, 50, key="count")
    st.slider("Cantidad de artistas", 1, 15, key="artist_count")

    st.markdown("**Creatividad**")

    st.slider(
        "Creatividad",
        0.0, 1.0,
        step=0.1,
        key="temperature",
        label_visibility="collapsed",
    )

    st.markdown(
        '<div class="slider-labels">'
        '<div class="slider-side"><strong>BAJA</strong>'
        'Prioriza resultados previsibles</div>'
        '<div class="slider-side"><strong>ALTA</strong>'
        'Permite mezclas más inesperadas</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button("Guardar ajustes", type="primary", use_container_width=True):
        st.rerun()


# =========================================================
# CALLBACK DE SPOTIFY
# =========================================================

params = st.query_params

if params.get("error"):
    st.session_state.pop("oauth_state", None)
    st.query_params.clear()
    st.error("La autorización de Spotify fue cancelada o rechazada.")

elif params.get("code"):
    oauth = spotify_oauth()
    state_received = params.get("state", "")
    state_expected = st.session_state.get("oauth_state", "")

    if oauth and state_expected and state_received == state_expected:
        try:
            token = oauth.get_access_token(
                params["code"],
                check_cache=False,
            )
            st.session_state.spotify_token = token
            st.session_state.pop("oauth_state", None)
            st.query_params.clear()
            st.rerun()
        except Exception:
            st.error(
                "No se pudo conectar con Spotify. "
                "Comprueba las credenciales y la URL de redirección."
            )
    else:
        st.session_state.pop("oauth_state", None)
        st.query_params.clear()
        st.error("No se pudo validar la autorización de Spotify.")


# =========================================================
# BARRA LATERAL
# =========================================================

with st.sidebar:
    brand()

    st.markdown('<div class="sidebar-label">Playlists</div>',
                unsafe_allow_html=True)

    if st.button("＋   Nueva playlist", type="primary",
                 use_container_width=True):
        reset_app()
        st.rerun()

    st.divider()

    st.markdown('<div class="sidebar-label">Historial reciente</div>',
                unsafe_allow_html=True)

    if not st.session_state.history:
        st.caption("Tus playlists aparecerán aquí.")
    else:
        for item in reversed(st.session_state.history[-10:]):
            if st.button(item["name"], key=f'history_{item["id"]}',
                         use_container_width=True):
                st.session_state.playlist_name = item["name"]
                st.session_state.playlist_url = item["url"]
                st.session_state.step = "success"
                st.rerun()

    st.divider()

    st.markdown('<div class="sidebar-label">Spotify</div>',
                unsafe_allow_html=True)

    if spotify_client():
        st.markdown(
            '<p style="color:#1ED760;font-size:13px;font-weight:600">'
            '● Conectado</p>',
            unsafe_allow_html=True,
        )
        if st.button("Desconectar", use_container_width=True):
            st.session_state.pop("spotify_token", None)
            st.rerun()
    else:
        spotify_connect_button()

    provider = st.session_state.get("ai_provider", "Gemini")
    if provider == "Gemini" and not GEMINI_API_KEY:
        st.warning("Falta GEMINI_API_KEY en Secrets.")
    elif provider == "OpenAI" and not OPENAI_API_KEY:
        st.warning("Falta OPENAI_API_KEY en Secrets.")
    elif provider == "Puter (OpenAI Gratis)" and not PUTER_API_KEY:
        st.warning("Falta PUTER_API_KEY en Secrets.")


# =========================================================
# CREAR PLAYLIST
# =========================================================

if st.session_state.step == "create":
    brand()

    st.markdown(
        '<div class="eyebrow">Descubrimiento musical con IA</div>',
        unsafe_allow_html=True,
    )

    st.title("¿Qué quieres escuchar?")

    st.markdown(
        '<p class="muted">Describe un género, una época, un ambiente '
        'o una mezcla musical. Nosotros preparamos la selección.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="composer">', unsafe_allow_html=True)

    st.text_area(
        "Petición musical",
        key="prompt_input",
        height=120,
        placeholder=(
            "Ej.: Rock alternativo de los 2000, oscuro y enérgico, "
            "con clásicos y grupos menos conocidos. Sin baladas."
        ),
        label_visibility="collapsed",
    )

    left, right = st.columns(2, gap="medium")

    with left:
        if st.button("⚙   Ajustes", key="adjust_button",
                     use_container_width=True):
            settings_dialog()

    with right:
        generate = st.button(
            "Generar playlist   ↗",
            key="generate_button",
            type="primary",
            use_container_width=True,
        )

    st.markdown(
        '<p class="muted" style="font-size:12px;margin:12px 2px 0">'
        'Puedes revisar y editar las canciones antes de exportarlas.</p>',
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if generate:
        prompt = st.session_state.prompt_input.strip()
        provider = st.session_state.get("ai_provider", "Gemini")

        if not prompt:
            st.warning("Describe qué música quieres escuchar.")
        elif provider == "Gemini" and not GEMINI_API_KEY:
            st.error("Configura GEMINI_API_KEY en los Secrets.")
        elif provider == "OpenAI" and not OPENAI_API_KEY:
            st.error("Configura OPENAI_API_KEY en los Secrets.")
        elif provider == "Puter (OpenAI Gratis)" and not PUTER_API_KEY:
            st.error("Configura PUTER_API_KEY en los Secrets.")
        else:
            try:
                with st.spinner(f"Creando tu selección musical con {provider}…"):
                    tracks = generate_tracks(
                        prompt,
                        st.session_state.count,
                        st.session_state.artist_count,
                        st.session_state.temperature,
                    )

                st.session_state.tracks = tracks
                st.session_state.step = "review"
                st.rerun()

            except Exception as exc:
                st.error(f"No se pudo generar la selección: {exc}")


# =========================================================
# REVISAR CANCIONES
# =========================================================

elif st.session_state.step == "review":
    brand()

    st.markdown('<div class="eyebrow">Paso 1 · Revisión</div>',
                unsafe_allow_html=True)
    st.title("Tu selección musical")

    st.markdown(
        f'<p class="muted">{len(st.session_state.tracks)} canciones. '
        'Edita la lista antes de buscarlas en Spotify.</p>',
        unsafe_allow_html=True,
    )

    st.text_area(
        "Artista - Canción (una por línea)",
        value="\n".join(
            f'{t["artist"]} - {t["title"]}'
            for t in st.session_state.tracks
        ),
        height=330,
        key="review_text",
    )

    left, right = st.columns(2, gap="medium")

    with left:
        if st.button("← Volver", use_container_width=True):
            st.session_state.step = "create"
            st.rerun()

    with right:
        search_clicked = st.button(
            "Buscar en Spotify   ↗",
            type="primary",
            use_container_width=True,
        )

    if search_clicked:
        edited = []

        for line in st.session_state.review_text.splitlines():
            match = __import__("re").match(
                r"^\s*(.+?)\s+[–—-]\s+(.+?)\s*$",
                line,
            )
            if match:
                edited.append({
                    "artist": match.group(1).strip(),
                    "title": match.group(2).strip(),
                })

        if not edited:
            st.warning("Usa el formato Artista - Canción.")
        elif not spotify_client():
            st.warning("Conecta Spotify desde la barra lateral.")
        else:
            found, missing = find_spotify_tracks(spotify_client(), edited)
            st.session_state.resolved = found
            st.session_state.missing = missing
            st.session_state.step = "export"
            st.rerun()


# =========================================================
# EXPORTAR A SPOTIFY
# =========================================================

elif st.session_state.step == "export":
    brand()

    st.markdown('<div class="eyebrow">Paso 2 · Exportación</div>',
                unsafe_allow_html=True)
    st.title("Revisa las coincidencias")

    resolved = st.session_state.resolved
    missing = st.session_state.missing

    st.markdown(
        f'<p class="muted">{len(resolved)} encontradas · '
        f'{len(missing)} sin coincidencia.</p>',
        unsafe_allow_html=True,
    )

    for i, track in enumerate(resolved, 1):
        title = html.escape(track["title"])
        artist = html.escape(track["artist"])
        album = html.escape(track["album"])
        url = html.escape(track["url"], quote=True)

        st.markdown(
            f'<div class="track-row">'
            f'<div class="track-index">{i:02}</div>'
            f'<div class="track-info">'
            f'<div class="track-title">{title}</div>'
            f'<div class="track-artist">{artist}</div>'
            f'<div class="track-album">{album}</div>'
            f'</div>'
            f'<a class="track-link" href="{url}" target="_blank" '
            f'rel="noopener">Abrir {icon("external", 13)}</a>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if missing:
        with st.expander(f"Canciones no encontradas ({len(missing)})"):
            for track in missing:
                st.write(f'{track["artist"]} - {track["title"]}')

    st.divider()

    with st.form("export_form"):
        name = st.text_input(
            "Nombre de la playlist",
            value="Mi playlist con pl(ai)lister",
            max_chars=100,
        )
        privacy = st.radio("Privacidad", ["Privada", "Pública"],
                           horizontal=True)
        description = st.text_input(
            "Descripción",
            value="Creada con pl(ai)lister y la IA",
            max_chars=300,
        )
        submitted = st.form_submit_button(
            "Crear playlist en Spotify",
            type="primary",
            use_container_width=True,
        )

    left, right = st.columns(2, gap="medium")

    with left:
        if st.button("← Volver", use_container_width=True):
            st.session_state.step = "review"
            st.rerun()

    with right:
        if st.button("Cancelar", use_container_width=True):
            reset_app()
            st.rerun()

    if submitted:
        sp = spotify_client()

        if not sp:
            st.error("Conecta Spotify antes de exportar.")
        elif not resolved:
            st.error("No hay canciones encontradas para exportar.")
        elif not name.strip():
            st.error("Escribe un nombre para la playlist.")
        else:
            try:
                user = sp.current_user()
                playlist = sp.user_playlist_create(
                    user=user["id"],
                    name=name.strip(),
                    public=(privacy == "Pública"),
                    description=description.strip(),
                )

                uris = [track["uri"] for track in resolved]
                for start in range(0, len(uris), 100):
                    sp.playlist_add_items(
                        playlist["id"],
                        uris[start:start + 100],
                    )

                playlist_url = playlist.get(
                    "external_urls", {}
                ).get("spotify", "")

                st.session_state.playlist_name = name.strip()
                st.session_state.playlist_url = playlist_url
                st.session_state.history.append({
                    "id": playlist["id"],
                    "name": name.strip(),
                    "url": playlist_url,
                })
                st.session_state.step = "success"
                st.rerun()

            except Exception as exc:
                st.error(f"No se pudo crear la playlist: {exc}")


# =========================================================
# CONFIRMACIÓN
# =========================================================

elif st.session_state.step == "success":
    brand()

    st.markdown('<div class="eyebrow">Completado</div>',
                unsafe_allow_html=True)
    st.title("Playlist creada")

    name = html.escape(
        st.session_state.get("playlist_name", "Tu playlist")
    )

    st.markdown(
        f'<div class="result-card">'
        f'<div style="color:#1ED760;margin-bottom:12px">'
        f'{icon("check", 24)}</div>'
        f'<div style="font-size:20px;font-weight:600">{name}</div>'
        f'<p class="muted">Tu selección está lista en Spotify.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    url = st.session_state.get("playlist_url", "")
    if url:
        st.link_button(
            "Abrir playlist en Spotify   ↗",
            url,
            type="primary",
            use_container_width=True,
        )

    if st.button("＋ Crear otra playlist", use_container_width=True):
        reset_app()
        st.rerun()
