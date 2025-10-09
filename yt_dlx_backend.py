from dataclasses import dataclass
from argparse import ArgumentParser
from yt_dlp import YoutubeDL
from typing import List, Dict
import os
import sys
import re
from rich import traceback, print

traceback.install()


@dataclass
class YouTubeFetcher:
    DEFAULT_PATH: str = os.path.expanduser("~/Downloads")
    DEFAULT_CODEC: str = "mp4"
    VALID_CODECS = {"mp3", "mp4", "m4a", "opus", "webm"}

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
            choices=YouTubeFetcher.VALID_CODECS,
            default=YouTubeFetcher.DEFAULT_CODEC,
            help="Output format (mp3, mp4, m4a, opus, webm). Default: mp4",
        )
        parser.add_argument(
            "-o",
            "--output",
            default=YouTubeFetcher.DEFAULT_PATH,
            help="Output file or directory (can include extension, e.g. '~/Music/song.mp3')",
        )
        parser.add_argument(
            "-a",
            "--audio",
            action="store_true",
            help="Add 'audio' to the search query (useful when searching for songs)",
        )

        return parser.parse_args()

    # -----------------------------
    # YouTube Search
    # -----------------------------
    @staticmethod
    def youtube_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        ydl_opts = {"quiet": True, "extract_flat": "in_playlist", "skip_download": True}
        with YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch{max_results}:{query}"
            info = ydl.extract_info(search_query, download=False)
            return [{"title": e["title"], "url": e["url"]} for e in info["entries"]]

    # -----------------------------
    # User Video Selection
    # -----------------------------
    @staticmethod
    def select_video(videos: List[Dict[str, str]]) -> Dict[str, str]:
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
    # Filename Sanitization
    # -----------------------------
    @staticmethod
    def sanitize_filename(name: str) -> str:
        return re.sub(r'[<>:"/\\|?*\n\r\t]', "", name).strip()

    # -----------------------------
    # Auto-numbering for existing files
    # -----------------------------
    @staticmethod
    def auto_number(path: str) -> str:
        base, ext = os.path.splitext(path)
        counter = 1
        new_path = path
        while os.path.exists(new_path):
            new_path = f"{base} ({counter}){ext}"
            counter += 1
        return new_path

    # -----------------------------
    # Download Logic
    # -----------------------------
    @staticmethod
    def download_video(url: str, fmt: str, output_path: str):
        output_path = os.path.expanduser(output_path)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        is_dir = not os.path.splitext(output_path)[1]

        # Safe filename template
        safe_title_template = "%(title)s"
        outtmpl = (
            os.path.join(output_path, f"{safe_title_template}.%(ext)s")
            if is_dir
            else output_path
        )

        is_audio = fmt in {"mp3", "m4a", "opus"}

        ydl_opts = {"outtmpl": outtmpl, "quiet": False, "restrictfilenames": True}

        if is_audio:
            ydl_opts.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": fmt,
                            "preferredquality": "192",
                        }
                    ],
                }
            )
        else:
            ydl_opts.update(
                {
                    "format": f"bestvideo[ext={fmt}]+bestaudio/best"
                    if fmt != "webm"
                    else "bestvideo+bestaudio/best",
                    "merge_output_format": fmt,
                }
            )

        print(f"\n📥 Downloading to: {output_path}")
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Determine final path
            filename = YouTubeFetcher.sanitize_filename(info.get("title", "video"))
            final_path = os.path.join(
                output_path if is_dir else os.path.dirname(output_path),
                f"{filename}.{fmt}",
            )

            # Auto-number if file exists
            final_path = YouTubeFetcher.auto_number(final_path)
            print(f"✅ Saved as: {final_path}")

    # -----------------------------
    # Main Entrypoint
    # -----------------------------
    @staticmethod
    def main():
        args = YouTubeFetcher.parse_arguments()
        query = args.query.strip()
        fmt = args.format
        output_path = args.output.strip()

        # Use extension from -o if it matches a codec
        ext = os.path.splitext(output_path)[1].lstrip(".").lower()
        if ext in YouTubeFetcher.VALID_CODECS:
            fmt = ext

        if args.audio and not ("youtube.com/watch" in query or "youtu.be/" in query):
            query = f"{query} audio"

        try:
            if "youtube.com/watch" in query or "youtu.be/" in query:
                print("Detected direct YouTube link.")
                YouTubeFetcher.download_video(query, fmt, output_path)
                return

            print(f"🔍 Searching for: {query}")
            videos = YouTubeFetcher.youtube_search(query)
            if not videos:
                print("No results found.")
                sys.exit(1)

            selection = YouTubeFetcher.select_video(videos)
            YouTubeFetcher.download_video(selection["url"], fmt, output_path)

        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    YouTubeFetcher.main()
