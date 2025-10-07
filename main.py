from argparse import ArgumentParser
from re import search
from ddgs import DDGS
from pprint import pprint
from yt_dlp import YoutubeDL

DEFAULT_TITLE = "Eden Wrong"
DEFAULT_DL_PATH = "~/Downloads/"

TEST_URLS = [
    "https://en.wikipedia.org/wiki/Eden_Woon",
    "https://genius.com/Eden-wrong-lyrics",
    "https://www.youtube.com/watch?v=3D-3zkeyfJs",
    "https://www.azlyrics.com/lyrics/eden/wrong.html",
    "https://www.lyricsondemand.com/eden/wrong",
    "https://www.songlyrics.com/eden/wrong-lyrics/",
    "https://www.youtube.com/watch?v=E0FfQsK9ExQ",
    "https://www.songtell.com/eden/wrong",
    "https://www.shazam.com/song/1440854326/wrong",
    "https://www.letras.com/eden/wrong/",
    "https://chordify.net/chords/eden-songs/wrong-chords",
    "https://osu.ppy.sh/beatmapsets/944830",
    "https://www.vagalume.com.br/eden/wrong.html",
    "https://www.musixmatch.com/ja/lyrics/Eden/wrong",
    "https://www.ouvirmusica.com.br/eden/wrong/",
    "https://www.ilyricshub.com/lyrics-eden/",
    "https://open.spotify.com/track/5743xMYXTQJvCIIiSRTXTZ",
    "https://www.letras.com/the-eden-project/wrong/",
    "https://mcmxcv.fandom.com/wiki/wrong",
    "https://open.spotify.com/album/79Z3VtLMkzNNINdL6POnRK",
]


def parse_arguments():
    parser = ArgumentParser()

    parser.add_argument("-t", "--title")
    parser.add_argument("-u", "--url")
    return parser.parse_args()


def search_videos(title=DEFAULT_TITLE, url=""):
    url = url or None
    results = DDGS().text(title, max_results=50)
    return results


def filter_results(results, site="youtube.com/watch"):
    if "www." not in site:
        site = f"www.{site}"
    if "https://" not in site:
        site = f"https://{site}"
    return [video for video in results if site in video["href"]]


def select_video(videos: list):
    for i, result in enumerate(videos, start=1):
        url = result["href"]
        title = result["title"]
        body = result["body"]

        print(f"[{i}] {title}")
        print(f"    {url}", end="\n\n")

    while True:
        selection = input(": ")
        if not selection.isnumeric():
            print("Invalid selection... Try Again")
            continue
        selection = int(selection)
        if not 0 < selection <= len(videos):
            print("Invalid selection... Try Again")
            continue

        return videos[selection - 1]


def download_video(selection: dict, path=DEFAULT_DL_PATH):
    url = selection["href"]
    print(url)
    with YoutubeDL() as ydl:
        ydl.download([url])


def main():
    args = parse_arguments()
    url = args.url or None
    title = args.title or DEFAULT_TITLE

    search = search_videos()
    vids = filter_results(search)
    selection = select_video(vids)
    download_video(selection)


if __name__ == "__main__":
    main()
