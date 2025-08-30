# -*- coding: utf-8 -*-

import sys, os, time, glob, re
parent_folder_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(parent_folder_path)
sys.path.append(os.path.join(parent_folder_path, 'lib'))
sys.path.append(os.path.join(parent_folder_path, 'plugin'))

from collections import defaultdict
from flowlauncher import FlowLauncher

# --- Config ---
SEARCH_FOLDERS = [
    r"C:\Path\to\Projects\here",
]
MAX_RESULTS = 15
MAX_PER_FOLDER = 2          # set to 1 if you only want the newest per folder
SORT_MODE = "mtime"         # "mtime" (last saved) or "atime" (last opened; may be disabled on Windows)

# --- Helpers ---
def file_timestamp(path):
    return (os.path.getmtime(path) if SORT_MODE == "mtime" else os.path.getatime(path))

def human(ts):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))

class CubaseRecent(FlowLauncher):
    def _scan(self, name_filter: str):
        """
        Scan all folders, filter by name BEFORE limiting,
        return list of (timestamp, fullpath).
        """
        q = (name_filter or "").lower()
        items = []
        for root_folder in SEARCH_FOLDERS:
            pattern = os.path.join(root_folder, "**", "*.cpr")
            for fp in glob.iglob(pattern, recursive=True):
                try:
                    if q and q not in os.path.basename(fp).lower():
                        continue
                    ts = file_timestamp(fp)
                    items.append((ts, fp))
                except (FileNotFoundError, PermissionError):
                    pass
        # global newest first
        items.sort(key=lambda t: t[0], reverse=True)
        return items

    def _limit_per_folder(self, items):
        """
        Keep at most MAX_PER_FOLDER per containing folder,
        then re-sort globally to preserve newest-first.
        """
        per = defaultdict(int)
        kept = []
        for ts, fp in items:
            folder = os.path.dirname(fp)
            if per[folder] < MAX_PER_FOLDER:
                kept.append((ts, fp))
                per[folder] += 1
        kept.sort(key=lambda t: t[0], reverse=True)  # ensure final order
        return kept[:MAX_RESULTS]

    def query(self, query):
        # scan + name filter first (finds older matches too)
        all_items = self._scan(query)
        # reduce duplicates (per-folder cap) then trim
        items = self._limit_per_folder(all_items)

        if not items:
            return [{
                "Title": "No Cubase projects found",
                "SubTitle": f"Searched: {', '.join(SEARCH_FOLDERS)}",
                "IcoPath": "Images/cubase.ico"
            }]

        label = "Last modified" if SORT_MODE == "mtime" else "Last opened"
        results = []
        # Give explicit Score to lock the order shown by Flow
        # Highest score for first item, decrement afterwards.
        score = 100
        for ts, fp in items:
            results.append({
                "Title": os.path.basename(fp),
                "SubTitle": f"{label}: {human(ts)} — {fp}",
                "IcoPath": "Images/cubase.ico",
                "Score": score,
                "JsonRPCAction": {
                    "method": "open_file",
                    "parameters": [fp],
                    "dontHideAfterAction": False
                },
                "ContextData": fp
            })
            if score > 0:
                score -= 1
        return results

    def context_menu(self, data):
        fp = data or ""
        return [{
            "Title": "Open containing folder",
            "SubTitle": fp,
            "IcoPath": "Images/cubase.ico",
            "JsonRPCAction": {"method": "open_folder", "parameters": [fp]}
        }]

    def open_file(self, filepath):
        if filepath and os.path.exists(filepath):
            os.startfile(filepath)

    def open_folder(self, filepath):
        if filepath and os.path.exists(filepath):
            os.startfile(os.path.dirname(filepath))

if __name__ == "__main__":
    CubaseRecent()
