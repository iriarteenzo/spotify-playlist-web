
import html
import json
import os
import re
import secrets
import time

import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from google import genai
from google.genai import types


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="pl(ai)lister",
    page_icon="♪",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL_DEFAULT = "gemini-2.5-flash"
SPOTIFY_SCOPES = "playlist-modify-public playlist-modify-private"


def get_secret(name, default=""):
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = os.getenv(name, default)
    return value or default


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GEMINI_MODEL = get_secret("GEMINI_MODEL", MODEL_DEFAULT)
SPOTIFY_CLIENT_ID = get_secret("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = get_secret("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = get_secret(
    "SPOTIFY_REDIRECT_URI",
    "http://localhost:8501",
).rstrip("/")


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap');

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap');

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap');

/* --- 1. DESIGN SYSTEM: VARIABLES DINÁMICAS (DARK/LIGHT) --- */
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #121212;
    --panel: #1a1a1a;
    --panel-sub: #222222;
    --panel-hover: #2a2a2a;
    --border: #333333;
    --border-focus: #555555;
    --text: rgba(255, 255, 255, 0.92);
    --muted: rgba(255, 255, 255, 0.60);
    --input-bg: #181818;
    --sidebar-bg: #0a0a0a;
  }
}

@media (prefers-color-scheme: light) {
  :root {
    --bg: #f8f9fa;
    --panel: #ffffff;
    --panel-sub: #f1f3f5;
    --panel-hover: #e9ecef;
    --border: #dee2e6;
    --border-focus: #adb5bd;
    --text: #212529;
    --muted: #6c757d;
    --input-bg: #ffffff;
    --sidebar-bg: #f1f3f5;
  }
}

:root {
  --green: #1ed760;
  --green-hover: #1abc54;
}

/* --- 2. TIPOGRAFÍA Y CONTENEDOR GENERAL --- */
.stApp {
  background-color: var(--bg);
  color: var(--text);
  font-family: 'Google Sans', sans-serif;
  font-size: 15px;
  line-height: 1.55;
}

.block-container {
  max-width: 760px;
  padding: 32px 20px 48px;
}

header[data-testid="stHeader"] {
  background: transparent;
}

h1, h2, h3 {
  font-family: 'DM Serif Display', Georgia, serif !important;
  font-weight: 400 !important;
  letter-spacing: -.35px;
  line-height: 1.15;
  color: var(--text);
}

h1 {
  font-size: clamp(2rem, 4vw, 2.8rem) !important;
  margin-bottom: 12px !important;
}

p, label, input, textarea, button {
  font-family: 'Google Sans', sans-serif;
  color: var(--text);
}

/* --- 3. LOGOTIPO ADAPTATIVO --- */
.brand {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -1.5px;
  margin-bottom: 24px;
  color: var(--text);
}

.brand-ai {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--green);
  border-radius: 50%;
  color: var(--green);
  font-size: 11px;
  font-weight: 700;
}

.eyebrow {
  color: var(--green);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1.8px;
  font-weight: 700;
  margin-bottom: 8px;
}

.muted {
  color: var(--muted);
  font-size: 15px;
}

/* --- 4. COMPONENTES: SHELL Y FORMULARIOS --- */
.st-key-prompt_shell {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 16px;
  margin-top: 24px;
  margin-bottom: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.03);
}

.st-key-prompt_shell textarea, div[data-testid="stTextInput"] input {
  background: var(--input-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  color: var(--text) !important;
  font-size: 15px !important;
}

.st-key-prompt_shell textarea:focus, div[data-testid="stTextInput"] input:focus {
  border-color: var(--green) !important;
  box-shadow: 0 0 0 1px var(--green) !important;
}

/* --- 5. BOTONES Y VARIANTES --- */
.stButton > button, .stLinkButton > a {
  min-height: 46px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--panel-sub);
  color: var(--text);
  font-size: 14px;
  font-weight: 600;
  padding: 0 16px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}

.stButton > button:hover, .stLinkButton > a:hover {
  border-color: var(--border-focus);
  background: var(--panel-hover);
  color: var(--text);
}

.stButton > button[kind="primary"] {
  background: var(--green) !important;
  border-color: var(--green) !important;
  color: #07150b !important;
  font-weight: 700 !important;
}

.stButton > button[kind="primary"]:hover {
  background: var(--green-hover) !important;
  border-color: var(--green-hover) !important;
}

/* --- 6. SIDEBAR Y ELEMENTOS DE LISTA --- */
section[data-testid="stSidebar"] {
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
}

.track-row {
  border-bottom: 1px solid var(--border);
  padding: 14px 4px;
  display: flex;
  gap: 12px;
  align-items: center;
  background: var(--panel);
}

.track-index {
  color: var(--muted);
  width: 24px;
  font-size: 13px;
  font-weight: 600;
}

.track-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.track-artist, .track-album {
  color: var(--muted);
  font-size: 12px;
}

.result-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  margin: 16px 0;
}

/* --- 7. RESPONSIVIDAD MÓVIL --- */
@media (max-width: 640px) {
  .block-container {
    padding: 16px 12px 32px;
  }
  h1 {
    font-size: 2rem !important;
  }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 3. ICONOGRAFÍA SVG
# ============================================================

ICONS = {
    "sliders": (
        '<path d="M4 21v-7m0-4V3m8 18v-9m0-4V3m8 18v-5m0-4V3"/>'
        '<path d="M2 14h4m4-6h4m4 8h4"/>'
    ),
    "send": (
        '<path d="m22 2-7 20-4-9-9-4Z"/>'
        '<path d="M22 2 11 13"/>'
    ),
    "check": '<path d="m5 12 4 4L19 6"/>',
    "external": (
        '<path d="M15 3h6v6"/>'
        '<path d="M10 14 21 3"/>'
        '<path d="M19 13v6a2 2 0 0 1-2 2H5'
        'a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h6"/>'
    ),
    "spotify": (
        '<circle cx="12" cy="12" r="10" fill="#1ED760" stroke="none"/>'
        '<path d="M6.5 9.2c3.9-1.2 8.5-.8 11.2 1"'
        ' stroke="#07150B" stroke-width="1.7"/>'
        '<path d="M7.2 12.2c3.2-1 7-.6 9.4 1"'
        ' stroke="#07150B" stroke-width="1.5"/>'
        '<path d="M7.8 15c2.7-.7 5.5-.4 7.5.8"'
        ' stroke="#07150B" stroke-width="1.4"/>'
    ),
}


def svg_icon(name, size=18):
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.7" '
        'stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true">'
        f'{ICONS[name]}</svg>'
    )


def render_brand():
    st.markdown(
        '<div class="brand">pl'
        '<span class="brand-ai">ai</span>lister</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# 4. SPOTIFY AUTHENTICATION
# ============================================================

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


def render_spotify_connect():
    oauth = spotify_oauth()

    if not oauth:
        st.caption(
            "Configura las credenciales de Spotify en Secrets."
        )
        return

    if not st.session_state.get("oauth_state"):
        st.session_state.oauth_state = secrets.token_urlsafe(24)

    auth_url = oauth.get_authorize_url(
        state=st.session_state.oauth_state
    )

    safe_url = html.escape(auth_url, quote=True)

    st.markdown(
        f"""
        <a href="{safe_url}" target="_self"
           style="
             display:flex;
             align-items:center;
             justify-content:center;
             gap:10px;
             min-height:46px;
             padding:0 16px;
             background:#1ED760;
             color:#07150B;
             border-radius:999px;
             text-decoration:none;
             font-family:'Google Sans',Arial,sans-serif;
             font-size:14px;
             font-weight:650;
             border:1px solid #1ED760;
           ">
           {svg_icon("spotify", 21)}
           Conectar con Spotify
        </a>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 5. GENERACIÓN CON GEMINI
# ============================================================

def parse_tracks(raw, requested_count):
    if isinstance(raw, str):
        try:
            raw = json.loads(raw.strip())
        except json.JSONDecodeError:
            raise ValueError(
                "Gemini no devolvió JSON válido. Inténtalo de nuevo."
            )

    if not isinstance(raw, dict):
        raise ValueError("La respuesta de Gemini no tiene el formato esperado.")

    tracks = raw.get("tracks", [])

    if not isinstance(tracks, list):
        raise ValueError("No se encontró una lista de canciones válida.")

    result = []
    seen = set()

    for item in tracks:
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
        result.append({"artist": artist, "title": title})

        if len(result) >= requested_count:
            break

    return result


def generate_tracks(prompt, count, artist_count, temperature):
    client = genai.Client(api_key=GEMINI_API_KEY)

    system_prompt = f"""
Actúa como un curador musical experto.

Devuelve exclusivamente JSON válido con esta estructura:
{{"tracks":[{{"artist":"artista","title":"canción"}}]}}

Genera {count} canciones reales y distintas, con aproximadamente
{artist_count} artistas diferentes.

Respeta género, época, idioma, energía, referencias y exclusiones
especificadas por el usuario.

Evita canciones inventadas, duplicados y versiones en directo
salvo que el usuario las solicite.

Devuelve únicamente el JSON, sin Markdown ni explicaciones.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"{system_prompt}\n\nPetición:\n{prompt}",
        config=types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
        ),
    )

    tracks = parse_tracks(response.text or "", count)

    if len(tracks) < count:
        raise ValueError(
            f"Se obtuvieron {len(tracks)} canciones válidas de "
            f"{count}. Prueba otra petición."
        )

    return tracks


# ============================================================
# 6. BÚSQUEDA EN SPOTIFY
# ============================================================

def find_spotify_tracks(sp, tracks):
    found = []
    missing = []
    seen_uris = set()

    progress = st.progress(0, text="Buscando canciones en Spotify…")

    for index, track in enumerate(tracks):
        query = (
            f'track:"{track["title"]}" '
            f'artist:"{track["artist"]}"'
        )

        try:
            results = sp.search(q=query, type="track", limit=5)
            items = results.get("tracks", {}).get("items", [])

            if not items:
                results = sp.search(
                    q=f'{track["title"]} {track["artist"]}',
                    type="track",
                    limit=5,
                )
                items = results.get("tracks", {}).get("items", [])

            match = next(
                (item for item in items if item["uri"] not in seen_uris),
                None,
            )

            if match:
                seen_uris.add(match["uri"])

                found.append({
                    "artist": ", ".join(
                        artist["name"]
                        for artist in match.get("artists", [])
                    ),
                    "title": match["name"],
                    "album": match.get("album", {}).get("name", ""),
                    "uri": match["uri"],
                    "url": match.get("external_urls", {}).get("spotify", ""),
                })
            else:
                missing.append(track)

        except Exception:
            missing.append(track)

        progress.progress(
            (index + 1) / max(len(tracks), 1),
            text=f"Buscando canciones en Spotify… {index + 1}/{len(tracks)}",
        )

    progress.empty()
    return found, missing


# ============================================================
# 7. ESTADO DE SESIÓN
# ============================================================

DEFAULTS = {
    "step": "create",
    "prompt": "",
    "count": 15,
    "artist_count": 5,
    "temperature": 0.7,
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
        "tracks",
        "resolved",
        "missing",
        "playlist_url",
        "playlist_name",
        "review_text",
    ):
        st.session_state.pop(key, None)

    st.session_state.step = "create"
    st.session_state.prompt = ""


# ============================================================
# 8. MODAL DE AJUSTES
# ============================================================

@st.dialog("Ajustes de generación", width="small")
def settings_dialog():
    st.markdown(
        '<p class="muted">Personaliza el tamaño y el carácter '
        'de tu selección musical.</p>',
        unsafe_allow_html=True,
    )

    st.slider(
        "Cantidad de canciones",
        min_value=5,
        max_value=50,
        step=1,
        key="count",
    )

    st.slider(
        "Cantidad de artistas",
        min_value=1,
        max_value=15,
        step=1,
        key="artist_count",
    )

    st.markdown("**Creatividad**")

    st.slider(
        "Nivel de creatividad",
        min_value=0.0,
        max_value=1.0,
        step=0.1,
        key="temperature",
        label_visibility="collapsed",
    )

    st.markdown(
        """
        <div class="slider-labels">
          <div class="slider-side">
            <strong>BAJA</strong>
            Prioriza resultados previsibles
          </div>
          <div class="slider-side">
            <strong>ALTA</strong>
            Permite mezclas más inesperadas
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        f'{st.session_state.count} canciones · '
        f'{st.session_state.artist_count} artistas'
    )

    if st.button(
        "Guardar ajustes",
        type="primary",
        use_container_width=True,
    ):
        st.rerun()


# ============================================================
# 9. GESTIÓN DEL CALLBACK DE SPOTIFY
# ============================================================

params = st.query_params

if params.get("error"):
    st.session_state.pop("oauth_state", None)
    st.query_params.clear()
    st.error("La autorización de Spotify fue cancelada o rechazada.")

elif params.get("code"):
    oauth = spotify_oauth()
    received_state = params.get("state", "")
    expected_state = st.session_state.get("oauth_state", "")

    if oauth and expected_state and received_state == expected_state:
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
                "No se pudo completar la conexión con Spotify. "
                "Comprueba la URL de redirección y las credenciales."
            )
    else:
        st.session_state.pop("oauth_state", None)
        st.query_params.clear()
        st.error(
            "No se pudo validar la autorización. "
            "Vuelve a conectar Spotify."
        )


# ============================================================
# 10. BARRA LATERAL
# ============================================================

with st.sidebar:
    render_brand()

    st.markdown(
        '<div class="sidebar-heading">Tu espacio musical</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "＋  Nueva playlist",
        type="primary",
        use_container_width=True,
    ):
        reset_app()
        st.rerun()

    st.divider()

    st.markdown(
        '<div class="sidebar-heading">Historial reciente</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.history:
        st.caption("Tus playlists aparecerán aquí.")

    else:
        for item in reversed(st.session_state.history[-10:]):
            if st.button(
                item["name"],
                key=f'history_{item["id"]}',
                use_container_width=True,
            ):
                st.session_state.playlist_name = item["name"]
                st.session_state.playlist_url = item["url"]
                st.session_state.step = "success"
                st.rerun()

    st.divider()

    st.markdown(
        '<div class="sidebar-heading">Conexiones</div>',
        unsafe_allow_html=True,
    )

    if spotify_client():
        st.markdown(
            '<p style="color:#1ED760;font-size:14px;font-weight:600">'
            '● Spotify conectado</p>',
            unsafe_allow_html=True,
        )

        if st.button("Desconectar Spotify", use_container_width=True):
            st.session_state.pop("spotify_token", None)
            st.rerun()

    else:
        st.caption("Conecta tu cuenta para exportar playlists.")
        render_spotify_connect()

    if not GEMINI_API_KEY:
        st.warning("Falta configurar GEMINI_API_KEY en Secrets.")

    st.markdown(
        '<p style="color:rgba(255,255,255,.65);font-size:12px;'
        'margin-top:22px">Gemini · Spotify Web API</p>',
        unsafe_allow_html=True,
    )


# ============================================================
# 11. PANTALLA PRINCIPAL
# ============================================================

if st.session_state.step == "create":
    render_brand()

    st.markdown(
        '<div class="eyebrow">Descubrimiento musical con IA</div>',
        unsafe_allow_html=True,
    )

    st.title("¿Qué quieres escuchar?")

    st.markdown(
        '<p class="muted">Describe un sonido, una época, un estado '
        'de ánimo o una mezcla inesperada. Tu próxima playlist '
        'empieza aquí.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="composer">', unsafe_allow_html=True)

    st.text_area(
        "Tu petición",
        key="prompt_input",
        height=125,
        placeholder=(
            "Ej.: Rock alternativo de los 2000, oscuro y enérgico, "
            "con algunos clásicos y grupos menos conocidos. "
            "Sin baladas."
        ),
        label_visibility="collapsed",
    )

    left, right = st.columns(
        [1, 1],
        gap="medium",
        vertical_alignment="center",
    )

    with left:
        if st.button(
            "⚙  Ajustes",
            key="adjust_button",
            use_container_width=True,
        ):
            settings_dialog()

    with right:
        generate = st.button(
            "Generar playlist  ↗",
            key="generate_button",
            type="primary",
            use_container_width=True,
        )

    st.markdown(
        '<div class="composer-hint">Cuanto más específica sea '
        'tu petición, más personalizada será la selección.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<p class="status-note">Genera una selección, revisa las '
        'canciones y expórtala a Spotify cuando esté lista.</p>',
        unsafe_allow_html=True,
    )

    if generate:
        prompt = st.session_state.prompt_input.strip()

        if not prompt:
            st.warning("Describe qué música quieres escuchar.")

        elif not GEMINI_API_KEY:
            st.error(
                "Falta GEMINI_API_KEY en Settings → Secrets."
            )

        else:
            try:
                with st.spinner("Creando tu selección musical…"):
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


# ============================================================
# 12. REVISIÓN DE CANCIONES
# ============================================================

elif st.session_state.step == "review":
    render_brand()

    st.markdown(
        '<div class="eyebrow">Paso 1 · Revisión</div>',
        unsafe_allow_html=True,
    )

    st.title("Tu selección musical")

    tracks = st.session_state.tracks

    st.markdown(
        f'<p class="muted">{len(tracks)} canciones propuestas. '
        'Edita la lista antes de buscarlas en Spotify.</p>',
        unsafe_allow_html=True,
    )

    st.text_area(
        "Canciones, una por línea: Artista - Canción",
        value="\n".join(
            f'{track["artist"]} - {track["title"]}'
            for track in tracks
        ),
        height=350,
        key="review_text",
    )

    back, search = st.columns(2, gap="medium")

    with back:
        if st.button("← Volver", use_container_width=True):
            st.session_state.step = "create"
            st.rerun()

    with search:
        search_clicked = st.button(
            "Buscar en Spotify  ↗",
            type="primary",
            use_container_width=True,
        )

    if search_clicked:
        edited_tracks = []

        for line in st.session_state.review_text.splitlines():
            match = re.match(
                r"^\s*(.+?)\s+[–—-]\s+(.+?)\s*$",
                line,
            )

            if match:
                edited_tracks.append({
                    "artist": match.group(1).strip(),
                    "title": match.group(2).strip(),
                })

        if not edited_tracks:
            st.warning(
                "Introduce canciones con el formato "
                "Artista - Canción."
            )

        elif not spotify_client():
            st.warning(
                "Conecta Spotify desde la barra lateral antes de continuar."
            )

        else:
            try:
                found, missing = find_spotify_tracks(
                    spotify_client(),
                    edited_tracks,
                )

                st.session_state.resolved = found
                st.session_state.missing = missing
                st.session_state.step = "export"
                st.rerun()

            except Exception as exc:
                st.error(f"Error al buscar canciones: {exc}")


# ============================================================
# 13. EXPORTACIÓN
# ============================================================

elif st.session_state.step == "export":
    render_brand()

    st.markdown(
        '<div class="eyebrow">Paso 2 · Confirmación</div>',
        unsafe_allow_html=True,
    )

    st.title("Revisa las coincidencias")

    resolved = st.session_state.resolved
    missing = st.session_state.missing

    st.markdown(
        f'<p class="muted">{len(resolved)} canciones encontradas · '
        f'{len(missing)} sin coincidencia.</p>',
        unsafe_allow_html=True,
    )

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
            f'Abrir {svg_icon("external", 13)}</a>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if missing:
        with st.expander(f"Canciones no encontradas ({len(missing)})"):
            for track in missing:
                st.write(f'{track["artist"]} - {track["title"]}')

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
            "Descripción",
            value="Creada con pl(ai)lister y Gemini",
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
            st.error("Conecta Spotify para crear la playlist.")

        elif not resolved:
            st.error("No hay canciones válidas para exportar.")

        elif not playlist_name.strip():
            st.error("Escribe un nombre para la playlist.")

        else:
            try:
                user = sp.current_user()

                playlist = sp.user_playlist_create(
                    user=user["id"],
                    name=playlist_name.strip(),
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

                st.session_state.playlist_name = playlist_name.strip()
                st.session_state.playlist_url = url

                st.session_state.history.append({
                    "id": playlist["id"],
                    "name": playlist_name.strip(),
                    "url": url,
                })

                st.session_state.step = "success"
                st.rerun()

            except Exception as exc:
                st.error(
                    "No se pudo crear la playlist. "
                    "Comprueba los permisos de Spotify e inténtalo "
                    f"de nuevo. Detalle: {exc}"
                )


# ============================================================
# 14. CONFIRMACIÓN
# ============================================================

elif st.session_state.step == "success":
    render_brand()

    st.markdown(
        '<div class="eyebrow">Completado</div>',
        unsafe_allow_html=True,
    )

    st.title("Playlist creada")

    name = html.escape(
        st.session_state.get("playlist_name", "Tu playlist")
    )

    st.markdown(
        f'<div class="result-card">'
        f'<div style="color:#1ED760;margin-bottom:12px">'
        f'{svg_icon("check", 25)}'
        f'</div>'
        f'<div style="font-size:21px;font-weight:650">{name}</div>'
        f'<p class="muted">Tu selección ya está disponible en Spotify.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    url = st.session_state.get("playlist_url", "")

    if url:
        st.link_button(
            "Abrir playlist en Spotify  ↗",
            url,
            type="primary",
            use_container_width=True,
        )

    if st.button(
        "＋ Crear otra playlist",
        use_container_width=True,
    ):
        reset_app()
        st.rerun()
