# -*- coding: utf-8 -*-

import sys
import re
import urllib.request

import xbmc
import xbmcgui
import xbmcplugin

HANDLE = int(sys.argv[1])

FOLDER_ID = "1PXkjbU32tpllgv6K-z-tbZuUyjDZ6zS6"
FOLDER_URL = "https://drive.google.com/drive/folders/" + FOLDER_ID + "?hl=es"

def decode_html(text):
    return (
        text.replace("&#39;", "'")
            .replace("&quot;", '"')
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
    )

def get_episodes():
    request = urllib.request.Request(
        FOLDER_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read()

    data = decode_html(raw.decode("utf-8", errors="ignore"))

    regex = re.compile(
        r'data-id="([^"]+)"[\s\S]{0,3000}?'
        r'aria-label="([^"]+\.mp4)[^"]*"',
        re.I
    )

    results = {}

    for match in regex.finditer(data):
        file_id = match.group(1)
        filename = match.group(2)

        episode_match = re.search(r'\bE(\d{1,2})\b', filename, re.I)

        if not episode_match:
            continue

        episode = int(episode_match.group(1))

        if 1 <= episode <= 50 and episode not in results:
            results[episode] = {
                "episode": episode,
                "filename": filename,
                "fileId": file_id
            }

    return sorted(results.values(), key=lambda x: x["episode"])

def drive_url(file_id):
    return (
        "https://drive.usercontent.google.com/download"
        "?id=" + file_id + "&export=download"
    )

def show_episodes():
    try:
        episodes = get_episodes()

        if not episodes:
            xbmcgui.Dialog().ok(
                "Super Sentai",
                "No se encontraron episodios.",
                "Google Drive no devolvió archivos MP4."
            )
            xbmcplugin.endOfDirectory(HANDLE)
            return

        for item in episodes:
            episode = item["episode"]
            url = drive_url(item["fileId"])

            list_item = xbmcgui.ListItem(
                label="Episodio %02d" % episode
            )

            list_item.setInfo(
                "video",
                {
                    "title": "Choushinsei Flashman - Episodio %02d" % episode
                }
            )

            xbmcplugin.addDirectoryItem(
                HANDLE,
                url,
                list_item,
                False
            )

        xbmcplugin.endOfDirectory(HANDLE)

    except Exception as error:
        xbmc.log(
            "SUPER SENTAI ERROR: %s" % error,
            xbmc.LOGERROR
        )

        xbmcgui.Dialog().ok(
            "Super Sentai",
            "Ocurrió un error:",
            str(error)
        )

        xbmcplugin.endOfDirectory(HANDLE)

show_episodes()
