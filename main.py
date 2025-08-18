# -*- coding: utf-8 -*-

import sys, os, time, glob

parent_folder_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(parent_folder_path)
sys.path.append(os.path.join(parent_folder_path, 'lib'))
sys.path.append(os.path.join(parent_folder_path, 'plugin'))

from flowlauncher import FlowLauncher

class CubaseRecent(FlowLauncher):

    # Define your Cubase project folders
    SEARCH_FOLDERS = [
        r"C:\Users\420ha\OneDrive\Austausch\01_Studio\01_currentProjects"
    ]
    MAX_RESULTS = 15

    def find_recent_cpr_files(self):
        files = []
        for folder in self.SEARCH_FOLDERS:
            pattern = os.path.join(folder, "**", "*.cpr")
            for file_path in glob.glob(pattern, recursive=True):
                try:
                    atime = os.path.getmtime(file_path)  # last accessed time
                    files.append((atime, file_path))
                except (FileNotFoundError, PermissionError):
                    pass

        files.sort(reverse=True, key=lambda x: x[0])  # newest first
        return files[:self.MAX_RESULTS]

    def query(self, query):
        results = []
        for atime, file_path in self.find_recent_cpr_files():
            if query.lower() not in os.path.basename(file_path).lower():
                continue  # live filtering
            last_access = time.strftime("%Y-%m-%d %H:%M", time.localtime(atime))
            results.append({
                "Title": os.path.basename(file_path),
                "SubTitle": f"Last opened: {last_access} — {file_path}",
                "IcoPath": "Images/cubase.ico",
                "JsonRPCAction": {
                    "method": "open_file",
                    "parameters": [file_path],
                    "dontHideAfterAction": False
                }
            })

        return results

    def context_menu(self, data):
        return [
            {
                "Title": "Open containing folder",
                "SubTitle": data,
                "IcoPath": "Images/cubase.ico",
                "JsonRPCAction": {
                    "method": "open_folder",
                    "parameters": [data]
                }
            }
        ]

    def open_file(self, filepath):
        os.startfile(filepath)  # open with Cubase (default .cpr app)

    def open_folder(self, filepath):
        folder = os.path.dirname(filepath)
        os.startfile(folder)

if __name__ == "__main__":
    CubaseRecent()
