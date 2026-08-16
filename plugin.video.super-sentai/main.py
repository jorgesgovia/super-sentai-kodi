# -*- coding: utf-8 -*-

import sys
import re
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
    return (
        text
        .replace("&#39;", "'")
        .replace("&quot;", '"')
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )


def get_episodes():

    response = requests.get(
        FOLDER_URL,
        timeout=20
    )

    response.raise_for_status()

    data = decode_html(
        response.text
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

    return (
        "https://drive.usercontent.google.com/download"
        "?id="
        + file_id
        + "&export=download"
    )


def show_episodes():

    episodes = get_episodes()

    for item in episodes:

        episode = item["episode"]
        file_id = item["fileId"]

        url = drive_url(file_id)

        list_item = xbmcgui.ListItem(
            label="Episodio %02d" % episode
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


show_episodes()
