from __future__ import annotations
from typing import List, Dict
from yt_dlx_backend import YouTubeFetcher
import asyncio
import time

from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Input, Markdown

DEBOUNCE_TIME = 0.4  # seconds


class YoutubeDownloader(App):
    """Downloads a youtube video."""

    CSS = """
    Input {
        background: #222;
        color: white;
        border: none;
    }
    #results {
        background: black;
        color: white;
    }
    """

    def __init__(self):
        super().__init__()
        self._last_input_time = 0.0
        self._pending_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search for a Youtube Video", id="video_search")
        with VerticalScroll(id="results-container"):
            yield Markdown(id="results")

    def on_mount(self) -> None:
        self.results = self.query_one("#results", Markdown)
        self.input = self.query_one("#video_search", Input)

    def on_input_changed(self, message: Input.Changed) -> None:
        """Debounce search when input changes."""
        self._last_input_time = time.time()
        # Cancel previous pending search
        if self._pending_task and not self._pending_task.done():
            self._pending_task.cancel()
        # Schedule a new search after debounce
        self._pending_task = asyncio.create_task(self._debounced_search(message.value))

    async def _debounced_search(self, query: str):
        """Wait for debounce period before launching search worker."""
        try:
            await asyncio.sleep(DEBOUNCE_TIME)
            # only search if no newer input has occurred
            if time.time() - self._last_input_time >= DEBOUNCE_TIME:
                if query.strip():
                    self.search_video_worker(query)
                else:
                    self.results.update("")
        except asyncio.CancelledError:
            pass

    @work(exclusive=True)  # ensures only one search runs at a time
    async def search_video_worker(self, query: str):
        """Run the search in a background worker thread."""
        results = await asyncio.to_thread(YouTubeFetcher.youtube_search, query, 7)
        md = self.make_word_markdown(results)
        self.results.update(md)

    def make_word_markdown(self, results: List[Dict[str, str]]) -> str:
        """Convert the results into markdown."""
        lines = []
        for i, res in enumerate(results):
            res_title = res["title"]
            res_url = res["url"]
            lines.append(f"## [{i}] {res_title}")
            lines.append(f"{res_url}")
            lines.append("---\n")
        return "\n".join(lines)


if __name__ == "__main__":
    app = YoutubeDownloader()
    app.run()
