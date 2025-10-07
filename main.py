from argparse import ArgumentParser
from re import search
from ddgs import DDGS
from pprint import pprint
from yt_dlp import YoutubeDL

DEFAULT_TITLE = "Eden Wrong"
DEFAULT_DL_PATH = "~/Downloads/"


def parse_arguments():
    parser = ArgumentParser()

    parser.add_argument("query")

    return parser.parse_args()


def search_videos(title=DEFAULT_TITLE, url=""):
    url = url or None
    results = DDGS().text(title, max_results=50)
    return results


def select_video(videos: list):
    for i, result in enumerate(videos, start=1):
        url = result["url"]
        title = result["title"]

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
    url = selection["url"]
    print(url)
    with YoutubeDL() as ydl:
        ydl.download([url])


def youtube_search(query, max_results=5):
    ydl_opts = {
        "quiet": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        search_query = f"ytsearch{max_results}:{query}"
        info = ydl.extract_info(search_query, download=False)
        return [
            {"title": entry["title"], "url": entry["url"]} for entry in info["entries"]
        ]


def main():
    try:
        args = parse_arguments()
        title = args.title
        print(args)

        if not args.title:
            title = DEFAULT_TITLE
        print(title)

        vids = youtube_search(title, 5)
        selection = select_video(vids)

        download_video(selection)
    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)
    except Exception as e:
        print(e)
        exit(1)


if __name__ == "__main__":
    main()
