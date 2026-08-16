# -*- coding: utf-8 -*-

import sys
import re
import html
import requests

import xbmcgui
import xbmcplugin


HANDLE = int(sys.argv[1])

FOLDER_ID = "1PXkjbU32tpllgv6K-z-tbZuUyjDZ6zS6"

FOLDER_URL = (
    "https://drive.google.com/drive/folders/"
    + FOLDER_ID
    + "?hl=es"
)


def decode_html(text):
    return html.unescape(text)


def get_episodes():

    response = requests.get(
        FOLDER_URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=20
    )

    response.raise_for_status()

    data = decode_html(response.text)

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

        if episode < 1 or episode > 50:
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


def drive_url(file_id):

    base_url = (
        "https://drive.usercontent.google.com/download"
        "?id=" + file_id +
        "&export=download"
    )

    session = requests.Session()

    session.headers.update({
        "User-Agent": "Mozilla/5.0"
    })

    response = session.get(
        base_url,
        allow_redirects=True,
        timeout=30
    )

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    if "video/mp4" in content_type:
        return response.url

    text = response.text

    uuid_match = re.search(
        r'name="uuid"\s+value="([^"]+)"',
        text,
        re.I
    )

    if not uuid_match:
        raise Exception(
            "Google Drive no proporcionó UUID"
        )

    uuid = uuid_match.group(1)

    final_url = (
        "https://drive.usercontent.google.com/download"
        "?id=" + file_id +
        "&export=download"
        "&confirm=t"
        "&uuid=" + uuid
    )

    return final_url

def show_error(message):

    xbmcgui.Dialog().ok(
        "Super Sentai",
        message
    )


def show_episodes():

    try:

        episodes = get_episodes()

        if not episodes:

            show_error(
                "No se encontraron episodios en Google Drive."
            )

            xbmcplugin.endOfDirectory(
                HANDLE,
                succeeded=False
            )

            return

        for item in episodes:

            episode = item["episode"]
            file_id = item["fileId"]

            # Pasamos el fileId mediante una URL del addon.
            # La resolución real se hará al seleccionar el episodio.
            url = (
                "plugin://plugin.video.super-sentai/"
                "?action=play"
                "&file_id=" + file_id
            )

            list_item = xbmcgui.ListItem(
                label="Episodio %02d" % episode
            )

            list_item.setProperty(
                "IsPlayable",
                "true"
            )

            list_item.setInfo(
                "video",
                {
                    "title":
                        "Choushinsei Flashman - "
                        "Episodio %02d" % episode
                }
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

        show_error(
            "Error:\n\n" + str(error)
        )

        xbmcplugin.endOfDirectory(
            HANDLE,
            succeeded=False
        )


def play_episode(file_id):

    try:

        url = drive_url(file_id)

        xbmcplugin.setResolvedUrl(
            HANDLE,
            True,
            xbmcgui.ListItem(
                path=url
            )
        )

    except Exception as error:

        show_error(
            "Error al preparar el video:\n\n"
            + str(error)
        )


params = {}

if len(sys.argv) > 2:
    query = sys.argv[2].lstrip("?")

    for part in query.split("&"):
        if "=" in part:
            key, value = part.split("=", 1)
            params[key] = value

if params.get("action") == "play":
    play_episode(params.get("file_id", ""))
else:
    show_episodes()

