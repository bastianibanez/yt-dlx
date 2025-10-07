#!/usr/bin/env python3
from dataclasses import dataclass
from argparse import ArgumentParser, REMAINDER
from yt_dlp import YoutubeDL
from typing import List, Dict
import os
import sys


@dataclass
class YouTubeFetcher:
    DEFAULT_PATH: str = os.path.expanduser("~/Downloads")
    DEFAULT_FORMAT: str = "bestvideo+bestaudio/best"

    # -----------------------------
    # Argument Parsing
    # -----------------------------
    @staticmethod
    def parse_arguments():
        parser = ArgumentParser(description="Search or download YouTube videos easily")

        parser.add_argument("query", help="Search term or YouTube URL")
        parser.add_argument(
            "-f",
            "--format",
            help="Download format (e.g., best, bestvideo+bestaudio, bestaudio[ext=m4a])",
            default=YouTubeFetcher.DEFAULT_FORMAT,
        )
        parser.add_argument(
            "-o",
            "--output",
            help="Output folder (default: ~/Downloads)",
            default=YouTubeFetcher.DEFAULT_PATH,
        )
        parser.add_argument(
            "-a",
            "--audio",
            nargs="?",
            const="mp3",
            metavar="CODEC",
            help="Add 'audio' to the search and download only audio (optional codec: mp3, m4a, opus)",
        )

        return parser.parse_args()

    # -----------------------------
    # YouTube Search
    # -----------------------------
    @staticmethod
    def youtube_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Perform a YouTube search and return flat results."""
        ydl_opts = {
            "quiet": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch{max_results}:{query}"
            info = ydl.extract_info(search_query, download=False)
            return [{"title": e["title"], "url": e["url"]} for e in info["entries"]]

    # -----------------------------
    # User Video Selection
    # -----------------------------
    @staticmethod
    def select_video(videos: List[Dict[str, str]]) -> Dict[str, str]:
        """Display results and prompt user to select one."""
        for i, result in enumerate(videos, start=1):
            print(f"[{i}] {result['title']}\n    {result['url']}\n")

        while True:
            choice = input(": ")
            if not choice.isdigit():
                print("Invalid selection. Try again.")
                continue
            idx = int(choice)
            if 1 <= idx <= len(videos):
                return videos[idx - 1]
            print("Invalid selection. Try again.")

    # -----------------------------
    # Download Logic
    # -----------------------------
    @staticmethod
    def download_video(url: str, fmt: str, output_path: str, audio_codec: str = None):
        """Download video (or audio) with given format and path."""
        os.makedirs(output_path, exist_ok=True)

        ydl_opts = {
            "format": fmt,
            "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
        }

        # Add audio extraction if requested
        if audio_codec:
            ydl_opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": audio_codec,
                            "preferredquality": "192",
                        }
                    ],
                }
            )

        print(f"\n📥 Downloading to: {output_path}")
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    # -----------------------------
    # Main Entrypoint
    # -----------------------------
    @staticmethod
    def main():
        args = YouTubeFetcher.parse_arguments()
        query = args.query.strip()
        fmt = args.format
        output_path = os.path.expanduser(args.output)
        audio_codec = args.audio  # None or string like "mp3", "m4a", etc.

        # Append 'audio' to query if doing audio search
        if audio_codec and not ("youtube.com/watch" in query or "youtu.be/" in query):
            query = f"{query} audio"

        try:
            # Direct URL download
            if "youtube.com/watch" in query or "youtu.be/" in query:
                print("Detected direct YouTube link.")
                YouTubeFetcher.download_video(query, fmt, output_path, audio_codec)
                return

            # Search & selection
            print(f"🔍 Searching for: {query}")
            videos = YouTubeFetcher.youtube_search(query)
            if not videos:
                print("No results found.")
                sys.exit(1)

            selection = YouTubeFetcher.select_video(videos)
            YouTubeFetcher.download_video(
                selection["url"], fmt, output_path, audio_codec
            )

        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    YouTubeFetcher.main()
