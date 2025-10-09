from __future__ import annotations
from typing import List, Dict
from yt_dlx_backend import YouTubeFetcher
import asyncio
import time
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Input, Markdown
from textual.binding import Binding

DEBOUNCE_TIME = 0.4  # seconds


class YoutubeDownloader(App):
    """Youtube downloader with search, keyboard navigation and download."""

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
    .selected {
        background: #444;
        color: red;
    }
    """

    BINDINGS = [
        Binding("ctrl+j", "move_down", "Move down"),
        Binding("ctrl+k", "move_up", "Move up"),
        Binding("enter", "activate", "Download"),
    ]

    def __init__(self):
        super().__init__()
        self._last_input_time = 0.0
        self._pending_task: asyncio.Task | None = None
        self.results_data: List[Dict[str, str]] = []
        self.selected_index: int = -1
        self.focus_on_results = False

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search for a Youtube Video", id="video_search")
        with VerticalScroll(id="results-container"):
            yield Markdown(id="results")

    def on_mount(self) -> None:
        self.results = self.query_one("#results", Markdown)
        self.input = self.query_one("#video_search", Input)
        self.set_focus(self.input)

    # ──────────────────────────
    # INPUT EVENTS / SEARCH
    # ──────────────────────────

    def on_input_changed(self, message: Input.Changed) -> None:
        """Debounce search when input changes."""
        self._last_input_time = time.time()
        self.selected_index = -1  # reset selection when typing
        self.focus_on_results = False
        if self._pending_task and not self._pending_task.done():
            self._pending_task.cancel()
        self._pending_task = asyncio.create_task(self._debounced_search(message.value))

    async def _debounced_search(self, query: str):
        try:
            await asyncio.sleep(DEBOUNCE_TIME)
            if time.time() - self._last_input_time >= DEBOUNCE_TIME:
                if query.strip():
                    self.search_video_worker(query)
                else:
                    self.results_data = []
                    self.results.update("")
        except asyncio.CancelledError:
            pass

    @work(exclusive=True)
    async def search_video_worker(self, query: str):
        results = await asyncio.to_thread(YouTubeFetcher.youtube_search, query, 7)
        self.results_data = results
        self.selected_index = -1
        self.update_results_markdown()

    # ──────────────────────────
    # NAVIGATION
    # ──────────────────────────

    def action_move_down(self) -> None:
        if not self.results_data:
            return
        if not self.focus_on_results:
            self.focus_on_results = True
            self.selected_index = 0
        else:
            self.selected_index = (self.selected_index + 1) % len(self.results_data)
        self.update_results_markdown()

    def action_move_up(self) -> None:
        if not self.results_data:
            return

        # If at top of list and going up, return focus to input
        if self.focus_on_results and self.selected_index == 0:
            self.focus_on_results = False
            self.selected_index = -1
            self.set_focus(self.input)
            self.update_results_markdown()
            return  # ✅ Prevents unwanted wrap-around

        elif self.focus_on_results:
            self.selected_index = (self.selected_index - 1) % len(self.results_data)
            self.update_results_markdown()

    # ──────────────────────────
    # DOWNLOAD
    # ──────────────────────────

    def action_activate(self) -> None:
        if self.focus_on_results and 0 <= self.selected_index < len(self.results_data):
            video = self.results_data[self.selected_index]
            title = video["title"].replace("/", "_").replace(":", "_")
            url = video["url"]
            output_dir = Path.home() / "Downloads"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{title}.mp4"
            # ✅ notify user download started
            self.notify(f"⬇️ Downloading: {title}", severity="information")
            self.download_worker(url, str(output_file), title)

    @work()
    async def download_worker(self, url: str, output_path: str, title: str):
        try:
            await asyncio.to_thread(
                YouTubeFetcher.download_video, url=url, output_path=output_path
            )
            self.notify(f"✅ Downloaded: {title}", severity="information")
        except Exception as e:
            self.notify(f"❌ Failed: {title} ({e})", severity="error")

    # ──────────────────────────
    # MARKDOWN RENDERING
    # ──────────────────────────

    def update_results_markdown(self) -> None:
        """Render results with selection highlight."""
        lines = []
        for i, res in enumerate(self.results_data):
            res_title = res["title"]
            res_url = res["url"]
            if i == self.selected_index and self.focus_on_results:
                lines.append(f"### → **{res_title}**")
            else:
                lines.append(f"## [{i}] {res_title}")
            lines.append(f"{res_url}")
            lines.append("---\n")
        self.results.update("\n".join(lines))


if __name__ == "__main__":
    app = YoutubeDownloader()
    app.run()
