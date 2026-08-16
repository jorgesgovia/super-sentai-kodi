# -*- coding: utf-8 -*-

import sys
import re
import urllib.request

import xbmc
import xbmcgui
import xbmcplugin

HANDLE = int(sys.argv[1])

# ============================================================
# SUPER SENTAI - CONFIGURACION GENERAL
# ============================================================

FOLDER_ID = "1PXkjbU32tpllgv6K-z-tbZuUyjDZ6zS6"
FOLDER_URL = (
    "https://drive.google.com/drive/folders/"
    + FOLDER_ID
    + "?hl=es"
)

# ============================================================
# METADATA DE LA SERIE
# ============================================================

SERIES = {
    "title": "Chōshinsei Flashman",
    "originaltitle": "Chōshinsei Flashman",
    "year": 1986,

    "poster": "https://image.tmdb.org/t/p/original/wyGFaD0V2bU2Q5uEtJDStZSRoG2.jpg",

    "fanart": "https://image.tmdb.org/t/p/original/rOR8GXwBrvQ03zLC9o4Jp5NwZzC.jpg",

    "trailer": "https://www.youtube.com/watch?v=Q_oVf3qpwIk",

    "wikidata": "Q1328971",

    "imdb": "tt0090407",

    # TMDB se resolvera automaticamente mediante IMDb/Wikidata
    "tmdb": "",

    "studio": "Toei Company",

    "country": "JP",

    "genre": [
        "Action",
        "Adventure",
        "Science Fiction",
        "Tokuzatsu"
    ],

    "plot": (
        "Chōshinsei Flashman es una serie japonesa de Super Sentai "
        "producida por Toei Company y emitida entre 1986 y 1987."
    )
}

# ============================================================
# TEMPORADAS
# ============================================================

SEASONS = {
    1: {
        "name": "Chōshinsei Flashman",
        "year": 1986,
        "folder_id": FOLDER_ID
    }
}

# ============================================================
# HTML
# ============================================================

def decode_html(text):

    return (
        text
        .replace("&#39;", "'")
        .replace("&quot;", '"')
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )


# ============================================================
# GOOGLE DRIVE
# ============================================================

def get_episodes():

    request = urllib.request.Request(
        FOLDER_URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        raw = response.read()

    data = decode_html(
        raw.decode(
            "utf-8",
            errors="ignore"
        )
    )

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

        episode = int(
            episode_match.group(1)
        )

        if episode < 1 or episode > 99:
            continue

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


# ============================================================
# GOOGLE DRIVE PLAYBACK
# ============================================================

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
# METADATA DE SERIE
# ============================================================

def set_series_metadata(list_item):

    info = {
        "title": SERIES["title"],
        "originaltitle": SERIES["originaltitle"],
        "year": SERIES["year"],
        "plot": SERIES["plot"],
        "studio": SERIES["studio"],
        "country": SERIES["country"],
        "genre": SERIES["genre"]
    }

    list_item.setInfo(
        "video",
        info
    )

    list_item.setArt({
        "poster": SERIES["poster"],
        "thumb": SERIES["poster"],
        "fanart": SERIES["fanart"],
        "banner": SERIES["fanart"],
        "landscape": SERIES["fanart"]
    })

    list_item.setProperty(
        "IsPlayable",
        "false"
    )


# ============================================================
# METADATA DE EPISODIO
# ============================================================

def set_episode_metadata(
    list_item,
    episode,
    filename
):

    title = (
        "Chōshinsei Flashman - "
        "Episodio %02d" % episode
    )

    info = {
        "title": title,
        "originaltitle": filename,
        "tvshowtitle": SERIES["title"],
        "season": 1,
        "episode": episode,
        "year": SERIES["year"],
        "plot": (
            "%s\n\n"
            "Serie: %s\n"
            "Temporada: 1\n"
            "Episodio: %02d"
            % (
                filename,
                SERIES["title"],
                episode
            )
        ),
        "studio": SERIES["studio"],
        "genre": SERIES["genre"],
        "country": SERIES["country"]
    }

    list_item.setInfo(
        "video",
        info
    )

    list_item.setArt({
        "poster": SERIES["poster"],
        "thumb": SERIES["poster"],
        "fanart": SERIES["fanart"],
        "landscape": SERIES["fanart"]
    })

    list_item.setProperty(
        "IsPlayable",
        "true"
    )

    list_item.setProperty(
        "mediatype",
        "episode"
    )


# ============================================================
# CARPETA PRINCIPAL
# ============================================================

def show_main():

    list_item = xbmcgui.ListItem(
        label=SERIES["title"]
    )

    set_series_metadata(
        list_item
    )

    xbmcplugin.addDirectoryItem(
        HANDLE,
        "?action=season&season=1",
        list_item,
        True
    )

    xbmcplugin.setContent(
        HANDLE,
        "tvshows"
    )

    xbmcplugin.endOfDirectory(
        HANDLE
    )


# ============================================================
# TEMPORADA
# ============================================================

def show_season():

    season = int(
        sys.argv[2].split("=")[1]
    )

    season_data = SEASONS.get(
        season
    )

    if not season_data:

        xbmcgui.Dialog().ok(
            "Super Sentai",
            "Temporada no encontrada."
        )

        xbmcplugin.endOfDirectory(
            HANDLE
        )

        return

    episodes = get_episodes()

    if not episodes:

        xbmcgui.Dialog().ok(
            "Super Sentai",
            "No se encontraron episodios.",
            "Google Drive no devolvio archivos MP4."
        )

        xbmcplugin.endOfDirectory(
            HANDLE
        )

        return

    for item in episodes:

        episode = item["episode"]
        filename = item["filename"]
        file_id = item["fileId"]

        url = drive_url(
            file_id
        )

        list_item = xbmcgui.ListItem(
            label="Episodio %02d" % episode
        )

        set_episode_metadata(
            list_item,
            episode,
            filename
        )

        xbmcplugin.addDirectoryItem(
            HANDLE,
            url,
            list_item,
            False
        )

    xbmcplugin.setContent(
        HANDLE,
        "episodes"
    )

    xbmcplugin.endOfDirectory(
        HANDLE
    )


# ============================================================
# ROUTER
# ============================================================

def main():

    try:

        action = ""

        if len(sys.argv) > 2:

            action = sys.argv[2]

        if action == "?action=season&season=1":

            show_season()

        else:

            show_main()

    except Exception as error:

        xbmc.log(
            "SUPER SENTAI ERROR: %s"
            % error,
            xbmc.LOGERROR
        )

        xbmcgui.Dialog().ok(
            "Super Sentai",
            "Ocurrio un error:",
            str(error)
        )

        xbmcplugin.endOfDirectory(
            HANDLE
        )


main()
