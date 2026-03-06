"""
file_sorter.py - Sorts files into folders by identified test type.
"""

# === IMPORTS ===
import heapq
import os
import shutil
import time

from Finders.File_sorter.config_loader import load_test_configs
from Finders.File_sorter.file_identifier import identify_file, SUPPORTED_EXTENSIONS
from Finders.File_sorter.path_resolver import resolve_sort_path
from Finders.File_sorter.unique_path import get_unique_path
from Finders.File_sorter.file_cache import FileCache


# === CONSTANTS ===
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_TOP_SLOWEST = 5


# === MAIN CLASS ===
class FileSorter:
    """Sorts files into folders by identified test type.

    Args:
        yaml_path: Path to test_identifiers.yaml. None for bundled default.
        max_file_size: Skip files larger than this (bytes). 0 to disable.
        max_scan_rows: Max rows for FIND_KEYS area search.
        max_scan_cols: Max columns for FIND_KEYS area search.
        cache_size: Max entries in the identification cache.
        message_callback: Callable for status messages. Default: print.
        progress_callback: Callable(current, total, filename) -> bool.
            Return False to cancel. Default: no-op (always continues).
    """

    def __init__(
        self,
        yaml_path=None,
        max_file_size=DEFAULT_MAX_FILE_SIZE,
        max_scan_rows=20,
        max_scan_cols=30,
        cache_size=1000,
        message_callback=None,
        progress_callback=None,
    ):
        self.configs = load_test_configs(yaml_path=yaml_path)
        self.max_file_size = max_file_size
        self.max_scan_rows = max_scan_rows
        self.max_scan_cols = max_scan_cols
        self.cache = FileCache(max_size=cache_size)
        self._message = message_callback or print
        self._progress = progress_callback or (lambda c, t, f: True)

    def sort_files(self, input_folder, output_folder):
        """Sort all supported files from input_folder into output_folder.

        Args:
            input_folder: Root folder to scan recursively.
            output_folder: Root output folder (subfolders created per strategy).

        Returns:
            dict with summary:
                "sorted": {test_type: count, ...}
                "unidentified": [filepath, ...]
                "skipped": [filepath, ...]  (too large)
                "total": int
                "slowest": [(elapsed, filepath), ...]
        """
        files = self._collect_files(input_folder)
        total = len(files)

        summary = {
            "sorted": {},
            "unidentified": [],
            "skipped": [],
            "total": total,
            "slowest": [],
        }

        if total == 0:
            self._message("No supported files found.")
            return summary

        self._message(f"Found {total} files to process.")
        slowest_heap = []

        for i, filepath in enumerate(files):
            filename = os.path.basename(filepath)

            should_continue = self._progress(i + 1, total, filename)
            if should_continue is False:
                self._message("Sort cancelled by user.")
                break

            # Check file size
            if self.max_file_size > 0:
                try:
                    size = os.path.getsize(filepath)
                except OSError:
                    summary["skipped"].append(filepath)
                    continue
                if size > self.max_file_size:
                    self._message(f"Skipped (too large): {filename}")
                    summary["skipped"].append(filepath)
                    continue

            # Identify
            start = time.monotonic()
            test_type, config = self._identify(filepath)
            elapsed = time.monotonic() - start

            # Track slowest (bounded)
            if len(slowest_heap) < DEFAULT_TOP_SLOWEST:
                heapq.heappush(slowest_heap, (elapsed, filepath))
            elif elapsed > slowest_heap[0][0]:
                heapq.heapreplace(slowest_heap, (elapsed, filepath))

            if test_type is None:
                summary["unidentified"].append(filepath)
                unid_dir = os.path.join(output_folder, "Unidentified")
                os.makedirs(unid_dir, exist_ok=True)
                unid_path = get_unique_path(os.path.join(unid_dir, filename))
                shutil.copy2(filepath, unid_path)
                continue

            # Resolve output path and copy
            dest_dir = resolve_sort_path(test_type, config, output_folder)
            os.makedirs(dest_dir, exist_ok=True)

            dest_path = os.path.join(dest_dir, filename)
            dest_path = get_unique_path(dest_path)

            shutil.copy2(filepath, dest_path)

            summary["sorted"][test_type] = summary["sorted"].get(test_type, 0) + 1

        summary["slowest"] = sorted(slowest_heap, reverse=True)

        self._print_summary(summary)
        return summary

    def _collect_files(self, input_folder):
        """Walk input_folder recursively, return list of supported files."""
        files = []
        for dirpath, _, filenames in os.walk(input_folder):
            for name in filenames:
                ext = os.path.splitext(name)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    files.append(os.path.join(dirpath, name))
        return sorted(files)

    def _identify(self, filepath):
        """Identify a file, using cache if available."""
        cached = self.cache.get_cached_type(filepath)
        if cached is not None:
            # Look up full config for cached type name
            for name, config in self.configs:
                if name == cached:
                    return (name, config)

        name, config = identify_file(
            filepath, self.configs,
            max_scan_rows=self.max_scan_rows,
            max_scan_cols=self.max_scan_cols,
        )

        if name is not None:
            self.cache.set_cached_type(filepath, name)

        return (name, config)

    def _print_summary(self, summary):
        """Print a summary of the sort results."""
        self._message(f"\n--- Sort Summary ---")
        self._message(f"Total files: {summary['total']}")

        sorted_count = sum(summary["sorted"].values())
        self._message(f"Sorted: {sorted_count}")

        if summary["sorted"]:
            for test_type in sorted(summary["sorted"]):
                count = summary["sorted"][test_type]
                self._message(f"  {test_type}: {count}")

        if summary["unidentified"]:
            self._message(f"Unidentified: {len(summary['unidentified'])}")

        if summary["skipped"]:
            self._message(f"Skipped (too large): {len(summary['skipped'])}")

        if summary["slowest"]:
            self._message(f"\nTop {len(summary['slowest'])} slowest:")
            for elapsed, path in summary["slowest"]:
                name = os.path.basename(path)
                self._message(f"  {elapsed:.2f}s  {name}")


# === PROGRESS DIALOG ===
class ProgressDialog:
    """wxPython progress dialog with file counter, filename display, and cancel."""

    def __init__(self, total_files):
        import wx
        self._wx = wx
        self.total_files = total_files
        self._cancelled = False

        self._dlg = wx.Dialog(None, title="Sorting Files",
                              style=wx.DEFAULT_DIALOG_STYLE)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.counter_label = wx.StaticText(self._dlg, label="File 0 of 0")
        sizer.Add(self.counter_label, 0, wx.ALL | wx.EXPAND, 10)

        self.filename_label = wx.StaticText(self._dlg, label="")
        sizer.Add(self.filename_label, 0, wx.ALL | wx.EXPAND, 10)

        self.progress_bar = wx.Gauge(self._dlg, range=max(1, total_files))
        sizer.Add(self.progress_bar, 0, wx.ALL | wx.EXPAND, 10)

        cancel_btn = wx.Button(self._dlg, wx.ID_CANCEL, "Cancel")
        cancel_btn.Bind(wx.EVT_BUTTON, self._on_cancel)
        sizer.Add(cancel_btn, 0, wx.ALL | wx.CENTER, 10)

        self._dlg.SetSizer(sizer)
        self._dlg.SetSize(400, 200)
        self._dlg.Centre()

    def show(self):
        self._dlg.Show()

    def update(self, current_index, filename):
        self.counter_label.SetLabel(f"File {current_index} of {self.total_files}")
        self.filename_label.SetLabel(f"Processing: {filename}")
        self.progress_bar.SetValue(current_index)
        self._dlg.Refresh()
        self._wx.SafeYield()

    def is_cancelled(self):
        return self._cancelled

    def destroy(self):
        self._dlg.Destroy()

    def _on_cancel(self, event):
        self._cancelled = True
        self._dlg.EndModal(self._wx.ID_CANCEL)


def _create_progress_callback():
    """Create a progress callback that manages a wxPython progress dialog."""
    progress_dialog = None

    def progress_handler(current_index, total_count, filename):
        nonlocal progress_dialog

        if progress_dialog is None:
            progress_dialog = ProgressDialog(total_count)
            progress_dialog.show()

        progress_dialog.update(current_index, filename)

        if progress_dialog.is_cancelled():
            progress_dialog.destroy()
            return False

        if current_index >= total_count:
            progress_dialog.destroy()

        return True

    return progress_handler


# === STANDALONE ENTRY POINT ===
def main():
    """Entry point for standalone execution.

    Uses dog_box dialogs to prompt for input and output folders,
    and a progress dialog during sorting.
    """
    import wx
    from Helpers.dog_box.work_files import select_output_folder

    app = wx.App(False)

    input_folder = select_output_folder(title="Select INPUT folder to sort")
    if input_folder is None:
        print("No input folder selected. Exiting.")
        return

    output_folder = select_output_folder(title="Select OUTPUT folder for sorted files")
    if output_folder is None:
        print("No output folder selected. Exiting.")
        return

    print(f"Input:  {input_folder}")
    print(f"Output: {output_folder}")

    sorter = FileSorter(progress_callback=_create_progress_callback())
    sorter.sort_files(input_folder, output_folder)

    app.Destroy()


if __name__ == "__main__":
    import sys
    # Ensure project root is on sys.path for direct execution
    _project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)
    main()
