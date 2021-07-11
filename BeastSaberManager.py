from bs4 import BeautifulSoup
from urllib.request import urlopen
import json
from collections import defaultdict
import re
import sys


class BeastSaberManager:

    def parse_page(self, soup):
        map_details = []
        for article in soup.find_all("article"):
            mapper = article.find("span", {"class": "mapper_id vcard"})
            if mapper is not None:
                mapper = mapper.contents[0].strip()
            else:
                mapper = article.find("strong", {"class": "mapper_id vcard"}).find("a").contents[
                    0].strip()
            if article.find("i", {"class": "fa fa-thumbs-up fa-fw"}) is not None:
                upvotes = int(article.find("i", {"class": "fa fa-thumbs-up fa-fw"}).
                              find_parent().contents[2])
                downvotes = int(article.find("i", {"class": "fa fa-thumbs-down fa-fw"}).
                                find_parent().contents[2])
            else:
                upvotes = 0
                downvotes = 0
            if upvotes + downvotes == 0:
                up_perc = 70
            else:
                up_perc = 100 * upvotes / (upvotes + downvotes)
            map_details.append({
                "title": article.find("header").find("a").attrs["title"],
                "link": article.find("header").find("a").attrs["href"],
                "mapper": mapper,
                "difficulties": [difficulty_link.contents[0].strip() for difficulty_link
                                 in article.find_all("a", {"class": "post-difficulty"})],
                "upvotes": upvotes,
                "downvotes": downvotes,
                "up_perc": up_perc
            })
        next_button = soup.find("a", class_="next page-numbers")
        if next_button is not None:
            next_url = next_button.attrs["href"]
        else:
            next_url = None
        return map_details, next_url

    def find_all(self, artist, song):
        url = self.get_search_url(artist, song)
        map_details = []
        while url is not None:
            soup = self.get_soup_parser(url)
            new_maps, url = self.parse_page(soup)
            map_details += new_maps
        return map_details

    def get_search_url(self, artist, song):
        artist = re.sub("[^a-zA-Z ]", " ", artist).replace(" ", "%20")
        song = re.sub("[^a-zA-Z (\-]", " ", song) \
            .replace("(", "-") \
            .replace(" ", "%20") \
            .split("-")[0]
        url = f"https://bsaber.com/?s={artist}%20{song}"
        return url

    def get_soup_parser(self, url):
        print(f"loading {url}")
        page = urlopen(url)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        print("page loaded")
        return soup

    def filter_maps(self, map_list, upvote_percentage=70, difficulties=["Expert", "Expert+"]):
        valid_list = []
        for map_details in map_list:
            if map_details["up_perc"] < upvote_percentage:
                continue
            difficulty_check_pass = False
            for diff in difficulties:
                if diff in map_details["difficulties"]:
                    difficulty_check_pass = True
            if not difficulty_check_pass:
                continue
            valid_list.append(map_details)
        return valid_list

    def filter_to_songs(self, map_list, song_list):
        selected_maps = defaultdict(list)
        for song in song_list:
            song_trunc = self.truncate_title(song)
            for map_info in map_list:
                if song_trunc.lower().replace(" ", "") in map_info["title"].lower().replace(" ",
                                                                                            ""):
                    selected_maps[song].append(map_info)
        return selected_maps

    @staticmethod
    def truncate_title(title):
        return re.sub("[^a-zA-Z (\-]", " ", title).replace("(", "-").split("-")[0]


if __name__ == '__main__':
    # stdout_file = open("stdout.txt", "w+")
    # stdout_original = sys.stdout
    # sys.stdout = stdout_file

    bsm = BeastSaberManager()
    with open("all_songs.json", "r") as f:
        songs = json.load(f)
    all_maps = {}
    for artist, tracks in songs.items():
        try:
            print(f"Looking for {artist} songs")
            if len(tracks) > 1:
                song_search = ""
            else:
                song_search = tracks[0]
            artist_maps = bsm.find_all(artist, song_search)
            filtered_maps = bsm.filter_maps(artist_maps)
            filtered_maps = bsm.filter_to_songs(filtered_maps, tracks)
            if len(filtered_maps) > 0:
                all_maps[artist] = filtered_maps
            with open("all_maps.json", "w+") as f:
                json.dump(all_maps, f, indent=4)
        except Exception as e:
            print("ERROR: " + str(e))

