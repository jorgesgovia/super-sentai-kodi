# -*- coding: utf-8 -*-

import sys
import re
import urllib.request
import urllib.parse

import xbmc
import xbmcgui
import xbmcplugin


HANDLE = int(sys.argv[1])

FOLDER_ID = "1PXkjbU32tpllgv6K-z-tbZuUyjDZ6zS6"

FOLDER_URL = (
    "https://drive.google.com/drive/folders/"
    + FOLDER_ID
    + "?hl=es"
)

POSTER = (
    "https://image.tmdb.org/t/p/original/"
    "wyGFaD0V2bU2Q5uEtJDStZSRoG2.jpg"
)

BACKGROUND = (
    "https://imgbs.com/uploads/flashman-a8f83054.jpg"
)

LOGO = (
    "https://image.tmdb.org/t/p/original/"
    "7jASxo9DcEkuhCQhuJpgkmjoTgt.png"
)


def log(text):

    xbmc.log(
        "[Super Sentai] " + str(text),
        xbmc.LOGINFO
    )


def add_item(
    label,
    url,
    folder=False,
    playable=False,
    poster=None,
    info=None
):

    item = xbmcgui.ListItem(
        label=label
    )

    item.setArt({
        "thumb": poster or POSTER,
        "poster": poster or POSTER,
        "fanart": BACKGROUND,
        "icon": LOGO
    })

    if info:

        item.setInfo(
            "video",
            info
        )

    if playable:

        item.setProperty(
            "IsPlayable",
            "true"
        )

    xbmcplugin.addDirectoryItem(
        HANDLE,
        url,
        item,
        isFolder=folder
    )


def finish():

    xbmcplugin.endOfDirectory(
        HANDLE
    )


def get_drive_episodes():

    log("Consultando Google Drive")

    request = urllib.request.Request(
        FOLDER_URL,
        headers={
            "User-Agent":
                "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        raw = response.read().decode(
            "utf-8",
            errors="ignore"
        )

    raw = (
        raw.replace(
            "&#39;",
            "'"
        )
        .replace(
            "&quot;",
            '"'
        )
        .replace(
            "&amp;",
            "&"
        )
        .replace(
            "&lt;",
            "<"
        )
        .replace(
            "&gt;",
            ">"
        )
    )

    results = {}

    regex = re.compile(
        r'data-id="([^"]+)"'
        r'[\s\S]{0,3000}?'
        r'aria-label="([^"]+\.mp4)[^"]*"',
        re.IGNORECASE
    )

    for match in regex.finditer(raw):

        file_id = match.group(1)

        filename = match.group(2)

        episode_match = re.search(
            r'\bE(\d{1,2})\b',
            filename,
            re.IGNORECASE
        )

        if not episode_match:
            continue

        episode = int(
            episode_match.group(1)
        )

        if episode < 1 or episode > 50:
            continue

        if episode not in results:

            results[episode] = {
                "episode": episode,
                "filename": filename,
                "file_id": file_id
            }

    episodes = list(
        results.values()
    )

    episodes.sort(
        key=lambda x: x["episode"]
    )

    log(
        "Episodios encontrados: "
        + str(len(episodes))
    )

    return episodes


def get_drive_stream(file_id):

    url = (
        "https://drive.usercontent.google.com/download"
        "?id="
        + urllib.parse.quote(
            file_id
        )
        + "&export=download"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        html = response.read().decode(
            "utf-8",
            errors="ignore"
        )

    uuid_match = re.search(
        r'name="uuid"\s+value="([^"]+)"',
        html,
        re.IGNORECASE
    )

    if not uuid_match:

        raise Exception(
            "Google Drive no proporcionó UUID"
        )

    uuid = uuid_match.group(1)

    return (
        "https://drive.usercontent.google.com/download"
        "?id="
        + urllib.parse.quote(file_id)
        + "&export=download"
        "&confirm=t"
        "&uuid="
        + urllib.parse.quote(uuid)
    )


def show_root():

    log("Mostrando serie")

    add_item(
        "Choushinsei Flashman",
        "?action=seasons",
        folder=True,
        poster=POSTER,
        info={
            "title":
                "Choushinsei Flashman",

            "originaltitle":
                "Choushinsei Flashman",

            "year":
                1986,

            "genre":
                "Action / Adventure / Science Fiction",

            "studio":
                "Toei Company",

            "rating":
                8.2,

            "plot":
                "Serie Super Sentai Choushinsei Flashman."
        }
    )

    finish()


def show_seasons():

    add_item(
        "Temporada 1",
        "?action=episodes&season=1",
        folder=True,
        poster=POSTER,
        info={
            "title":
                "Temporada 1"
        }
    )

    finish()


def show_episodes():

    try:

        episodes = get_drive_episodes()

    except Exception as error:

        log(
            "ERROR DRIVE: "
            + str(error)
        )

        xbmcgui.Dialog().notification(
            "Super Sentai",
            "No se pudo consultar Google Drive",
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )

        finish()

        return

    for video in episodes:

        episode = video["episode"]

        label = (
            "%02d — Episodio %d"
            % (
                episode,
                episode
            )
        )

        url = (
            "?action=play"
            "&episode="
            + str(episode)
            + "&file_id="
            + urllib.parse.quote(
                video["file_id"]
            )
        )

        add_item(
            label,
            url,
            folder=False,
            playable=True,
            poster=POSTER,
            info={
                "title":
                    "Episodio %d"
                    % episode,

                "season":
                    1,

                "episode":
                    episode,

                "tvshowtitle":
                    "Choushinsei Flashman",

                "year":
                    1986,

                "plot":
                    "Choushinsei Flashman — Episodio %d."
                    % episode
            }
        )

    finish()


def play_episode(file_id, episode):

    log(
        "Reproduciendo episodio "
        + str(episode)
    )

    try:

        stream = get_drive_stream(
            file_id
        )

    except Exception as error:

        log(
            "ERROR STREAM: "
            + str(error)
        )

        xbmcgui.Dialog().notification(
            "Super Sentai",
            "No se pudo obtener el video",
            xbmcgui.NOTIFICATION_ERROR,
            5000
        )

        return

    item = xbmcgui.ListItem(
        label=
        "Choushinsei Flashman "
        "— Episodio "
        + str(episode)
    )

    item.setInfo(
        "video",
        {
            "title":
                "Episodio %d"
                % episode,

            "tvshowtitle":
                "Choushinsei Flashman",

            "season":
                1,

            "episode":
                episode
        }
    )

    item.setArt({
        "thumb": POSTER,
        "poster": POSTER,
        "fanart": BACKGROUND
    })

    item.setPath(
        stream
    )

    xbmcplugin.setResolvedUrl(
        HANDLE,
        True,
        item
    )


def router():

    params = {}

    if len(sys.argv) > 2:

        params = dict(
            urllib.parse.parse_qsl(
                sys.argv[2][1:]
            )
        )

    action = params.get(
        "action"
    )

    log(
        "ACTION: "
        + str(action)
    )

    if not action:

        show_root()

        return

    if action == "seasons":

        show_seasons()

        return

    if action == "episodes":

        show_episodes()

        return

    if action == "play":

        play_episode(
            params.get("file_id"),
            params.get("episode")
        )

        return

    show_root()


router()
