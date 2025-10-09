"""Module to test result of youtube search function"""

from yt_dlx_backend import YouTubeFetcher
from rich import traceback, print

traceback.install()


def search_video(query: str, max_results=7) -> None:
    """Looks up a Youtube Video."""
    results = YouTubeFetcher.youtube_search("john mayer stop this train")
    return results


if __name__ == "__main__":
    result = search_video("john mayer stop this train")
    print(result)
