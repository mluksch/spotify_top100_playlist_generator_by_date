import datetime
import datetime as dt
import os
from typing import Optional

import bs4
import requests
import spotipy

# https://spotipy.readthedocs.io/en/2.19.0/
client = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(
    scope="playlist-modify-private,playlist-modify-private,playlist-read-collaborative,playlist-read-private,playlist-modify-public",
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="http://localhost:9090",
    show_dialog=True,
    cache_path="token.txt"
))


def get_top_100(date: dt.datetime):
    date_fmt = date.strftime("%Y-%m-%d")
    base_url = f"https://www.billboard.com/charts/hot-100/{date_fmt}"
    res = requests.get(base_url)
    html = res.text
    soup = bs4.BeautifulSoup(markup=html, features="html.parser")
    rows = soup.select(".chart-results-list .o-chart-results-list-row")
    results = []
    for row in rows:
        song_pos = int(row.get("data-detail-target"))
        song_title = row.select_one("ul li h3.c-title").get_text().strip()
        author = row.select_one("ul li ul li span").get_text().strip()
        print(f"({song_pos}) Song \"{song_title}\" from \"{author}\" detected")
        results.append({"pos": song_pos, "title": song_title, "author": author})
    results.sort(key=lambda item: item["pos"], reverse=False)
    return results


def get_date():
    date_fmt = input("Enter a date (format: YYYY-MM-DD) for the top 100 playlist of that date:\n")
    return dt.datetime.strptime(date_fmt, "%Y-%m-%d")


def create_new_playlist(date: datetime.datetime):
    name = date.strftime("%d-%m-%Y Top-100")
    return client.user_playlist_create(user=client.current_user()["id"], name=name, public=True, collaborative=False,
                                       description='')["uri"]


def add_tracks_to_playlist(track_ids: [str], playlist_id):
    print(f"Adding {len(track_ids)} Songs to playlist...")
    client.playlist_add_items(playlist_id=playlist_id, items=track_ids)
    print(f"New playlist created.")


def search_song(song_title, artist, date: datetime.datetime) -> Optional[str]:
    try:
        query = f"track: {song_title} year: {date.year}"
        results = client.search(q=query, type='track')
        track = results["tracks"]["items"][0]
        return track["id"]
    except Exception as e:
        return None


def process():
    date = get_date()
    songs = get_top_100(date)
    track_ids = [search_song(song_title=item["title"], artist=item["author"],
                             date=date) for item in songs]
    playlist_id = create_new_playlist(date)
    add_tracks_to_playlist([id for id in track_ids if id], playlist_id)


process()

# p = create_new_playlist(date=datetime.datetime.now())
# print(f"p: {p}")

# s = search_song(song_title="Born to be wild", artist="acdc",
#                date=datetime.datetime.now())
# print(f"s: {s}")
