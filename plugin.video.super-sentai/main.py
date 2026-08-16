# -*- coding: utf-8 -*-

import sys
import re
import json
import urllib.request
import urllib.parse

import xbmc
import xbmcgui
import xbmcplugin

HANDLE = int(sys.argv[1])

# ============================================================
# SUPER SENTAI - CONFIGURACION DE TEMPORADA
# ============================================================

FOLDER_ID = "1PXkjbU32tpllgv6K-z-tbZuUyjDZ6zS6"
FOLDER_URL = "https://drive.google.com/drive/folders/" + FOLDER_ID + "?hl=es"

SHOW_TITLE = "Chōshinsei Flashman"
SHOW_TITLE_EN = "Supernova Flashman"

YEAR = 1986
SEASON = 1
EPISODES_TOTAL = 50

# IDs oficiales
IMDB_ID = "tt0090407"
TMDB_ID = "70787"
WIKIDATA_ID = "Q1328971"

# ============================================================
# ARTES PERSONALIZADOS
# ============================================================

POSTER = "https://image.tmdb.org/t/p/original/wyGFaD0V2bU2Q5uEtJDStZSRoG2.jpg"
FANART = "https://image.tmdb.org/t/p/original/rOR8GXwBrvQ03zLC9o4Jp5NwZzC.jpg"

# Logo/trailer proporcionados para la serie
TRAILER = "https://www.youtube.com/watch?v=Q_oVf3qpwIk"

# ============================================================
# INFORMACION GENERAL DE LA SERIE
# ============================================================

SHOW_PLOT = (
    "En 1966, cinco niños fueron secuestrados de la Tierra por los "
    "Cazadores Alienígenas del Imperio del Experimento Reconstructivo Mess. "
    "Los niños fueron rescatados por la raza Flash y criados en distintos "
    "planetas del sistema Flash, donde fueron entrenados para combatir a "
    "Mess. Veinte años después regresan a la Tierra como los Flashman para "
    "enfrentarse al imperio invasor y buscar a sus familias biológicas."
)

SHOW_GENRES = [
    "Action",
    "Adventure",
    "Science Fiction",
    "Superhero",
    "Tokusatsu",
    "Fantasy",
    "Drama"
]

SHOW_CAST = [
    "Touta Tarumi",
    "Yasuhiro Ishiwata",
    "Kihachiro Uemura",
    "Youko Nakamura",
    "Mayumi Yoshida",
    "Akira Ishihama",
    "Unshô Ishizuka",
    "Kôji Shimizu",
    "Yutaka Hirose"
]

SHOW_DIRECTORS = [
    "Minoru Yamada",
    "Nagafumi Hori",
    "Shohei Tôjô",
    "Takao Nagaishi"
]

SHOW_WRITERS = [
    "Hirohisa Soda",
    "Kunio Fujii"
]

SHOW_STUDIO = "Toei Company"

# IMDb actualmente muestra 8.0/10.
# Se incluyen como fallback para que Kodi no quede vacío si
# una fuente externa no devuelve rating.
IMDB_RATING = 8.0
IMDB_VOTES = 282

# TMDB puede cambiar con el tiempo; el campo se mantiene
# preparado para enriquecimiento automático.
TMDB_RATING = 0.0
TMDB_VOTES = 0

# ============================================================
# GOOGLE DRIVE
# ============================================================

def decode_html(text):
    return (
        text.replace("&#39;", "'")
            .replace("&quot;", '"')
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
    )


def get_drive_page():
    request = urllib.request.Request(
        FOLDER_URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()

    return decode_html(
        raw.decode("utf-8", errors="ignore")
    )


def get_episodes():
    data = get_drive_page()

    regex = re.compile(
        r'data-id="([^"]+)"[\s\S]{0,3000}?'
        r'aria-label="([^"]+\.mp4)[^"]*"',
        re.I
    )

    results = {}

    for match in regex.finditer(data):
        file_id = match.group(1)
        filename = match.group(2)

        episode_match = re.search(
            r'\bE(\d{1,2})\b',
            filename,
            re.I
        )

        if not episode_match:
            continue

        episode = int(episode_match.group(1))

        if 1 <= episode <= EPISODES_TOTAL:
            if episode not in results:
                results[episode] = {
                    "episode": episode,
                    "filename": filename,
                    "fileId": file_id
                }

    return sorted(
        results.values(),
        key=lambda x: x["episode"]
    )


def drive_url(file_id):

    base_url = (
        "https://drive.usercontent.google.com/download"
        "?id=" + file_id +
        "&export=download"
    )

    request = urllib.request.Request(
        base_url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()

        if "video/mp4" in content_type:
            return response.geturl()

        html = response.read().decode(
            "utf-8",
            errors="ignore"
        )

    uuid_match = re.search(
        r'name="uuid"\s+value="([^"]+)"',
        html,
        re.I
    )

    if not uuid_match:
        raise Exception(
            "Google Drive no devolvio UUID"
        )

    uuid = uuid_match.group(1)

    return (
        "https://drive.usercontent.google.com/download"
        "?id=" + file_id +
        "&export=download"
        "&confirm=t"
        "&uuid=" + uuid
    )


# ============================================================
# METADATA DE EPISODIOS
# ============================================================

def clean_html(text):
    if not text:
        return ""

    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )

    replacements = {
        "&amp;": "&",
        "&quot;": '"',
        "&#39;": "'",
        "&lt;": "<",
        "&gt;": ">"
    }

    for a, b in replacements.items():
        text = text.replace(a, b)

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def get_tvmaze_data():

    url = (
        "https://api.tvmaze.com/shows/"
        "70787?embed[]=episodes"
    )

    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Kodi Super Sentai"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:

            return json.loads(
                response.read().decode(
                    "utf-8",
                    errors="ignore"
                )
            )

    except Exception as error:

        xbmc.log(
            "SUPER SENTAI TVMAZE ERROR: %s"
            % error,
            xbmc.LOGWARNING
        )

        return None


def build_episode_metadata(episodes):

    metadata = {}

    external = get_tvmaze_data()

    if external:
        for ep in external.get(
            "_embedded",
            {}
        ).get(
            "episodes",
            []
        ):

            number = ep.get(
                "number"
            )

            if not number:
                continue

            if ep.get("season") != SEASON:
                continue

            image = ep.get("image") or {}

            metadata[number] = {
                "title": ep.get("name") or
                         "Episodio %02d" % number,

                "plot": clean_html(
                    ep.get("summary") or ""
                ),

                "aired": ep.get(
                    "airdate"
                ) or "",

                "runtime": ep.get(
                    "runtime"
                ) or 30,

                "rating": (
                    ep.get("rating") or {}
                ).get("average") or 0,

                "thumb": (
                    image.get("original") or
                    image.get("medium") or
                    POSTER
                )
            }

    for item in episodes:

        number = item["episode"]

        if number not in metadata:

            metadata[number] = {
                "title":
                    "Episodio %02d" % number,

                "plot":
                    "",

                "aired":
                    "",

                "runtime":
                    30,

                "rating":
                    0,

                "thumb":
                    POSTER
            }

    return metadata


# ============================================================
# UTILIDADES KODI
# ============================================================

def set_common_art(list_item):

    list_item.setArt({
        "poster": POSTER,
        "thumb": POSTER,
        "fanart": FANART,
        "landscape": FANART,
        "banner": POSTER,
        "clearart": POSTER
    })


def set_show_info(list_item):

    info = {
        "title": SHOW_TITLE,
        "originaltitle": SHOW_TITLE_EN,
        "sorttitle": SHOW_TITLE,

        "tvshowtitle": SHOW_TITLE,

        "year": YEAR,
        "season": SEASON,

        "plot": SHOW_PLOT,
        "outline": SHOW_PLOT,

        "genre": " / ".join(
            SHOW_GENRES
        ),

        "studio": SHOW_STUDIO,

        "director": " / ".join(
            SHOW_DIRECTORS
        ),

        "writer": " / ".join(
            SHOW_WRITERS
        ),

        "cast": SHOW_CAST,

        "rating": IMDB_RATING,
        "votes": IMDB_VOTES,

        "imdbnumber": IMDB_ID,

        "mpaa": "TV-PG",

        "episodeguide": "",
    }

    list_item.setInfo(
        "video",
        info
    )

    # Campos adicionales utilizados por skins
    try:
        list_item.setProperty(
            "imdb_id",
            IMDB_ID
        )

        list_item.setProperty(
            "tmdb_id",
            TMDB_ID
        )

        list_item.setProperty(
            "wikidata_id",
            WIKIDATA_ID
        )

        list_item.setProperty(
            "trailer",
            TRAILER
        )

        list_item.setProperty(
            "tvshow.imdb_id",
            IMDB_ID
        )

        list_item.setProperty(
            "tvshow.tmdb_id",
            TMDB_ID
        )

    except Exception:
        pass


def set_episode_info(
    list_item,
    item,
    metadata
):

    number = item["episode"]

    data = metadata.get(
        number,
        {}
    )

    title = data.get(
        "title"
    ) or (
        "Episodio %02d" % number
    )

    plot = data.get(
        "plot"
    ) or (
        "Episodio %02d de %s."
        % (number, SHOW_TITLE)
    )

    aired = data.get(
        "aired"
    ) or ""

    rating = data.get(
        "rating"
    ) or 0

    runtime = data.get(
        "runtime"
    ) or 30

    thumb = data.get(
        "thumb"
    ) or POSTER

    info = {
        "title": title,

        "originaltitle": title,

        "tvshowtitle": SHOW_TITLE,

        "season": SEASON,

        "episode": number,

        "plot": plot,

        "outline": plot,

        "aired": aired,

        "year": (
            int(aired[:4])
            if aired and len(aired) >= 4
            else YEAR
        ),

        "genre": " / ".join(
            SHOW_GENRES
        ),

        "studio": SHOW_STUDIO,

        "director": " / ".join(
            SHOW_DIRECTORS
        ),

        "writer": " / ".join(
            SHOW_WRITERS
        ),

        "rating": rating,

        "duration": runtime * 60,

        "imdbnumber":
            IMDB_ID,

        "mpaa":
            "TV-PG"
    }

    list_item.setInfo(
        "video",
        info
    )

    list_item.setArt({
        "thumb": thumb,
        "poster": POSTER,
        "fanart": FANART,
        "landscape": thumb,
        "banner": POSTER
    })

    try:

        list_item.setProperty(
            "imdb_id",
            IMDB_ID
        )

        list_item.setProperty(
            "tmdb_id",
            TMDB_ID
        )

        list_item.setProperty(
            "season_number",
            str(SEASON)
        )

        list_item.setProperty(
            "episode_number",
            str(number)
        )

        list_item.setProperty(
            "IsPlayable",
            "true"
        )

    except Exception:
        pass


# ============================================================
# CARPETA DE LA TEMPORADA
# ============================================================

def show_season():

    list_item = xbmcgui.ListItem(
        label=SHOW_TITLE
    )

    set_common_art(
        list_item
    )

    set_show_info(
        list_item
    )

    list_item.setLabel2(
        "Temporada %d" % SEASON
    )

    list_item.setProperty(
        "FolderPath",
        "plugin://plugin.video.super-sentai/"
    )

    xbmcplugin.addDirectoryItem(
        HANDLE,
        "plugin://plugin.video.super-sentai/"
        "?season=%d" % SEASON,
        list_item,
        True
    )

    xbmcplugin.endOfDirectory(
        HANDLE
    )


# ============================================================
# EPISODIOS
# ============================================================

def show_episodes():

    try:

        episodes = get_episodes()

        if not episodes:

            xbmcgui.Dialog().ok(
                "Super Sentai",
                "No se encontraron episodios.",
                "Google Drive no devolvió archivos MP4."
            )

            xbmcplugin.endOfDirectory(
                HANDLE
            )

            return

        metadata = build_episode_metadata(
            episodes
        )

        for item in episodes:

            episode = item["episode"]

            url = drive_url(
                item["fileId"]
            )

            list_item = xbmcgui.ListItem(
                label="E%02d - %s"
                % (
                    episode,
                    metadata.get(
                        episode,
                        {}
                    ).get(
                        "title",
                        "Episodio %02d"
                        % episode
                    )
                )
            )

            set_episode_info(
                list_item,
                item,
                metadata
            )

            xbmcplugin.addDirectoryItem(
                HANDLE,
                url,
                list_item,
                False
            )

        xbmcplugin.endOfDirectory(
            HANDLE
        )

    except Exception as error:

        xbmc.log(
            "SUPER SENTAI ERROR: %s"
            % error,
            xbmc.LOGERROR
        )

        xbmcgui.Dialog().ok(
            "Super Sentai",
            "Ocurrió un error:",
            str(error)
        )

        xbmcplugin.endOfDirectory(
            HANDLE
        )


# ============================================================
# ROUTER
# ============================================================

def router():

    query = sys.argv[2] if len(sys.argv) > 2 else ""

    if "season=" in query:

        show_episodes()

    else:

        show_season()


router()
