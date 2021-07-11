import requests
import json
from collections import defaultdict


class SpotifyManager:
    def __init__(self):
        with open("auth.json", "r") as f:
            api_key = json.load(f)["api_key"]
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(api_key)
        }

    def get_playlists(self):
        """
        Gets all playlists from the account of the user whose bearer token is in use
        :return: An array of json objects in the form {"id": "playlist_id", "name": "playlist_name"}
        """
        next_call = "https://api.spotify.com/v1/me/playlists"
        summary = []

        while next_call is not None:
            resp = requests.get(url=next_call, headers=self.headers)

            if resp.status_code != 200:
                raise RuntimeError(resp.content)

            response_body = json.loads(resp.content)

            summary += [{
                key: playlist_details[key] for key in ["id", "name"]
            } for playlist_details in response_body["items"]]

            next_call = response_body["next"]

        with open("all_playlists.json", "w+") as f:
            json.dump(summary, f, indent=4)

        return summary

    def get_playlist_songs(self, playlists, multi_artist=False, include_albums=True):
        summary = defaultdict(lambda: defaultdict(set))

        for playlist in playlists:
            print(f"processing {playlist['name']}")
            id = playlist["id"]
            next_call = f"https://api.spotify.com/v1/playlists/{id}/tracks?market=GB"

            while next_call is not None:
                resp = requests.get(url=next_call, headers=self.headers)

                if resp.status_code != 200:
                    raise RuntimeError(resp.content)

                response_body = json.loads(resp.content)

                tracks = [item["track"] for item in response_body["items"]]
                for track in tracks:
                    if multi_artist:
                        artist = " & ".join([artist["name"] for artist in track["artists"]])
                    else:
                        artist = track["artists"][0]["name"]
                    album = track["album"]["name"] if include_albums else "default"
                    song = str(track["name"])
                    summary[artist][album].add(song)

                next_call = response_body["next"]

        song_count = 0
        for artist in summary.values():
            for album in artist.values():
                song_count += len(album)
        print(song_count)

        if include_albums:
            summary = {
                artist: {
                    album: list(songs)
                    for album, songs in albums.items()
                }
                for artist, albums in summary.items()
            }
        else:
            summary = {
                artist: list(albums["default"])
                for artist, albums in summary.items()
            }

        with open("all_songs.json", "w+") as f:
            json.dump(summary, f, indent=4)

        return summary


if __name__ == '__main__':
    sm = SpotifyManager()
    # playlists = sm.get_playlists()
    with open("all_playlists.json", "r") as f:
        playlists = json.load(f)
    tracks = sm.get_playlist_songs(playlists, include_albums=False)
