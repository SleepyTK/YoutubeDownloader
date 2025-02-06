import re
import os
from customtkinter import set_default_color_theme, CTk, CTkFrame, CTkLabel, CTkButton, CTkEntry, CTkScrollableFrame, CTkProgressBar, CTkOptionMenu, CTkFont
from tkinter import filedialog
import yt_dlp
import threading
from pytube import Search

def sanitize_filename(filename):
    return re.sub(r'[^\w\s-]', '', filename).replace(' ', '_')

class App(CTk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader with Search")
        self.geometry("885x450")  # Increased window size
        self.resizable(0, 0)
        self.attributes('-topmost', True)
        self.my_font = CTkFont(family="System", weight="bold")
        set_default_color_theme("green")

        # Main container
        self.main_frame = CTkFrame(master=self, corner_radius=6)
        self.main_frame.pack(pady=10, padx=10, expand=True, fill="both")

        # Left side components (existing)
        self.link_entry = CTkEntry(
            master=self.main_frame,
            height=30,
            width=275,
            corner_radius=0,
            font=self.my_font,
            placeholder_text="Enter YouTube URL here..."
        )
        self.link_entry.place(x=10, y=10)

        self.add_button = CTkButton(
            master=self.main_frame,
            height=30,
            width=275,
            corner_radius=0,
            text="ADD LINK",
            command=self.add_link,
            font=self.my_font
        )
        self.add_button.place(x=10, y=50)

        self.directory_label = CTkLabel(
            master=self.main_frame,
            height=240,
            width=275,
            text="No directory selected",
            fg_color="#292929",
            wraplength=275,
            font=self.my_font
        )
        self.directory_label.place(x=10, y=90)

        self.dir_button = CTkButton(
            master=self.main_frame,
            height=30,
            width=275,
            corner_radius=0,
            text="CHOOSE SAVE LOCATION",
            command=self.select_directory,
            font=self.my_font
        )
        self.dir_button.place(x=10, y=340)

        # Right side components - Search Section
        self.search_entry = CTkEntry(
            master=self.main_frame,
            height=30,
            width=275,
            corner_radius=0,
            font=self.my_font,
            placeholder_text="Search YouTube..."
        )
        self.search_entry.place(x=580, y=340)

        self.search_button = CTkButton(
            master=self.main_frame,
            height=30,
            width=275,
            corner_radius=0,
            text="SEARCH",
            command=self.perform_search,
            font=self.my_font
        )
        self.search_button.place(x=580, y=380)

        self.search_results_frame = CTkScrollableFrame(
            master=self.main_frame,
            width=260,
            height=320,
            corner_radius=0
        )
        self.search_results_frame.place(x=580, y=10)

        self.scrollable_frame = CTkScrollableFrame(
            master=self.main_frame,
            width=260,
            height=320,
            corner_radius=0
        )
        self.scrollable_frame.place(x=295, y=10)

        self.audio_button = CTkButton(
            master=self.main_frame,
            height=30,
            width=135,
            corner_radius=0,
            text="DOWNLOAD AUDIO",
            command=lambda: self.download_all("audio"),
            font=self.my_font
        )
        self.audio_button.place(x=295, y=340)

        self.resolution_menu = CTkOptionMenu(
            master=self.main_frame,
            values=["1080p", "720p", "480p", "360p"],
            height=30,
            width=135,
            corner_radius=0,
            font=self.my_font,
            dropdown_font=self.my_font
        )
        self.resolution_menu.set("720p")
        self.resolution_menu.place(x=438, y=380)

        self.video_button = CTkButton(
            master=self.main_frame,
            height=30,
            width=135,
            corner_radius=0,
            text="DOWNLOAD VIDEO",
            command=lambda: self.download_all("video"),
            font=self.my_font
        )
        self.video_button.place(x=437, y=340)

        # Progress components (adjusted position)
        self.progress_bar = CTkProgressBar(
            master=self.main_frame,
            orientation="horizontal",
            width=420,
            height=30,
            corner_radius=0
        )
        self.progress_bar.set(0)
        self.progress_bar.place(x=10, y=380)

        self.progress_label = CTkLabel(
            master=self.main_frame,
            text="Ready",
            height=15,
            font=CTkFont(size=10),
            fg_color="transparent"
        )
        self.progress_label.place(x=10, y=410)

        self.link_entry.bind("<Return>", lambda event: self.add_link())
        self.links = []
        self.link_rows = []

    def perform_search(self):
        query = self.search_entry.get()
        if query:
            # Clear previous results
            for widget in self.search_results_frame.winfo_children():
                widget.destroy()
            
            # Perform search with pytube
            search = Search(query)
            for video in search.results[:10]:  # Show top 5 results
                result_frame = CTkFrame(self.search_results_frame, corner_radius=0)
                result_frame.pack(fill="x", padx=5, pady=2)
                
                CTkLabel(
                    result_frame,
                    text=video.title,
                    font=self.my_font,
                    wraplength=150
                ).pack(side="left", padx=5, pady=5)
                
                CTkButton(
                    result_frame,
                    text="ADD",
                    width=60,
                    corner_radius=0,
                    font=self.my_font,
                    command=lambda url=video.watch_url: self.add_link(url)
                ).pack(side="right", padx=5, pady=5)

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory_label.configure(text=f"Save Location: {directory}")
            self.download_directory = directory

    def add_link(self, url=None):
        link = url or self.link_entry.get()
        if link:
            self.links.append(link)
            link_row = CTkFrame(master=self.scrollable_frame, corner_radius=0)
            link_row.pack(fill="x", padx=5, pady=2)
            CTkLabel(link_row, text=link, font=self.my_font, wraplength=150).pack(side="left", padx=5, pady=5)
            CTkButton(
                link_row,
                text="REMOVE",
                corner_radius=0,
                font=self.my_font,
                command=lambda: self.remove_link(link, link_row)
            ).pack(side="right", padx=5, pady=5)
            self.link_rows.append(link_row)
            if not url:
                self.link_entry.delete(0, "end")

    def remove_link(self, link, row):
        if link in self.links:
            self.links.remove(link)
        row.destroy()
        self.link_rows.remove(row)

    def download_all(self, media_type):
        if not hasattr(self, 'download_directory'):
            self.progress_label.configure(text="Error: Select save location first!")
            return
        
        threading.Thread(target=self.process_downloads, args=(media_type,)).start()

    def process_downloads(self, media_type):
        total = len(self.links)
        for index, link in enumerate(self.links, 1):
            try:
                ydl_opts = {
                    'outtmpl': os.path.join(self.download_directory, f'%(title)s.%(ext)s'),
                    'progress_hooks': [self.update_progress],
                    'quiet': True,
                }

                if media_type == "audio":
                    # Direct audio download without conversion
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = []  # No FFmpeg conversion
                else:
                    # Direct video download in native format
                    res = int(self.resolution_menu.get()[:-1])
                    ydl_opts['format'] = f'bestvideo[height<={res}]+bestaudio'

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([link])

                self.update_overall_progress(index/total, index, total)
                
            except Exception as e:
                print(f"Error: {e}")
                self.update_overall_progress(index/total, index, total)

        self.after(0, self.clear_links)

    def update_progress(self, data):
        if data['status'] == 'downloading':
            progress = data.get('downloaded_bytes', 0) / data.get('total_bytes', 1)
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"Downloading: {os.path.basename(data['filename'])}")

    def update_overall_progress(self, progress, current, total):
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"Completed: {current}/{total}")

    def clear_links(self):
        for row in self.link_rows:
            row.destroy()
        self.links.clear()
        self.link_rows.clear()
        self.progress_label.configure(text="All downloads completed!")

if __name__ == "__main__":
    app = App()
    app.mainloop()