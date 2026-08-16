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

    # Primera petición.
    response = session.get(
        base_url,
        allow_redirects=True,
        timeout=30
    )

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    # Si Google ya entrega el MP4 directamente.
    if "video/mp4" in content_type:

        return response.url

    # Google Drive puede mostrar la advertencia
    # de análisis de virus para archivos grandes.
    text = response.text

    uuid_match = re.search(
        r'name="uuid"\s+value="([^"]+)"',
        text,
        re.I
    )

    confirm_match = re.search(
        r'name="confirm"\s+value="([^"]+)"',
        text,
        re.I
    )

    if not uuid_match:
        raise Exception(
            "Google Drive no proporcionó UUID de descarga"
        )

    uuid = uuid_match.group(1)

    confirm = (
        confirm_match.group(1)
        if confirm_match
        else "t"
    )

    final_url = (
        "https://drive.usercontent.google.com/download"
        "?id=" + file_id +
        "&export=download" +
        "&confirm=" + confirm +
        "&uuid=" + uuid
    )

    # Comprobamos que la segunda URL sea realmente el vídeo.
    check = session.head(
        final_url,
        allow_redirects=True,
        timeout=30
    )

    final_type = check.headers.get(
        "Content-Type",
        ""
    ).lower()

    if "video/mp4" not in final_type:
        raise Exception(
            "Google Drive no devolvió video/mp4"
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

            try:

                url = drive_url(file_id)

            except Exception as error:

                list_item = xbmcgui.ListItem(
                    label="Episodio %02d — ERROR" % episode
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
                    "",
                    list_item,
                    False
                )

                continue

            list_item = xbmcgui.ListItem(
                label="Episodio %02d" % episode,
                path=url
            )

            list_item.setProperty(
                "IsPlayable",
                "true"
            )

            list_item.setMimeType(
                "video/mp4"
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


show_episodes()
