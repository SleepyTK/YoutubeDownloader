import sys
import re
import os
import subprocess
import requests
import uuid
import logging
import time
import threading
import yt_dlp
import queue
from packaging import version
from pathlib import Path
from customtkinter import (
	set_default_color_theme, CTk, CTkFrame, CTkLabel, CTkButton,
	CTkEntry, CTkScrollableFrame, CTkProgressBar, CTkOptionMenu,
	CTkFont, CTkToplevel, CTkImage
)
from tkinter import filedialog, messagebox, StringVar
from PIL import Image, ImageDraw  
import io
from concurrent.futures import ThreadPoolExecutor

def detect_gpu(ffmpeg_path: str) -> str:
	"""Detects the available GPU and returns its type."""
	try:
		result = subprocess.run(
			[ffmpeg_path, '-hide_banner', '-encoders'],
			capture_output=True,
			text=True,
			timeout=10,
			check=True,
			shell=False,
			env={'PATH': os.environ['PATH']},
			creationflags=subprocess.CREATE_NO_WINDOW
		)
		encoders = result.stdout.lower()

		if 'amf' in encoders or 'h264_amf' in encoders or 'hevc_amf' in encoders:
			print("Detected GPU: AMD")
			return 'amd'
		if 'nvenc' in encoders or 'cuda' in encoders:
			print("Detected GPU: NVIDIA")
			return 'nvidia'
		if 'qsv' in encoders or 'h264_qsv' in encoders or 'hevc_qsv' in encoders:
			print("Detected GPU: Intel")
			return 'intel'

		print("No GPU encoder found, defaulting to CPU")
		return 'cpu'
	except subprocess.TimeoutExpired as e:
			logging.critical("FFmpeg detection timed out")
			raise

def sanitize_filename(filename: str) -> str:
	"""Sanitizes a filename by removing invalid characters and limiting length."""
	filename = re.sub(r'[\\/*?:"<>|]', '', filename)
	filename = filename.encode('ascii', 'ignore').decode('ascii')
	return filename.strip()[:120]

class UpdateHandler:
	"""Handles application updates by checking and downloading the latest version."""
	def __init__(self):
		self.current_version = self.get_current_version()
		self.repo_owner = "SleepyTK"
		self.repo_name = "YoutubeDownloader"
		self.exe_name = "YouTube_Downloader.exe"

	def get_current_version(self):
		"""Gets the current version from the version file."""
		try:
			base_path = Path(sys._MEIPASS)
		except AttributeError:
			base_path = Path(os.path.dirname(__file__))
		
		version_file = base_path / "version.txt"
		return version_file.read_text().strip()

	def check_update(self):
		"""Checks for updates by querying the GitHub API."""
		try:
			response = requests.get(
				f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest",
				timeout=5
			)
			if response.status_code == 200:
				latest_data = response.json()
				latest_version_str = latest_data['tag_name']
				latest_version = version.parse(latest_version_str.lstrip('v'))
				current_version = version.parse(self.current_version)
				print(f"Current Version: {current_version}")
				print(f"Latest Version: {latest_version}")
				
				if latest_version > current_version:
					return {
						'url': latest_data['assets'][1]['browser_download_url'],
						'version': latest_version_str
					}
		except Exception as e:
			logging.error(f"Update check failed: {e}")
		return None

	def perform_update(self, download_url):
		"""Downloads and replaces the current executable with the latest version."""
		try:
			temp_exe = Path(os.environ['TEMP']) / "update_temp.exe"
			response = requests.get(download_url)
			if response.status_code != 200:
				raise Exception(f"Download failed with status {response.status_code}")
			temp_exe.write_bytes(response.content)

			import textwrap
			bat_script = textwrap.dedent(f"""
				@echo off
				timeout /t 1 /nobreak >nul
				del /F /Q "{sys.executable}"
				move /Y "{temp_exe}" "{sys.executable}"
				start "" "{sys.executable}"
				del %0
			""")

			script_path = Path(os.environ['TEMP']) / "updater.bat"
			script_path.write_text(bat_script)

			subprocess.Popen(
				['cmd.exe', '/C', str(script_path)],
				shell=True,
				creationflags=subprocess.CREATE_NO_WINDOW
			)
			return True
		except Exception as e:
			messagebox.showerror("Update Error", f"Failed to update: {str(e)}")
			return False


class App(CTk):
	THUMBNAIL_WIDTH = 128
	THUMBNAIL_HEIGHT = 72
	"""Main application window."""
	def __init__(self):
		super().__init__(fg_color='#040D12')
		self.title("YouTube Downloader v1.0.4")
		self.geometry("860x550")
		self.resizable(0, 0)
		self.attributes('-topmost', True)
		self.my_font = CTkFont(family="Helvetica", weight="bold")
		set_default_color_theme("green")
		
		self.search_queue = queue.Queue()
		self.search_cache = {}
		self.current_search_id = 0
		self.last_search_time = 0
  
		self.thumbnail_cache = {}
		self.thumbnail_executor = ThreadPoolExecutor(max_workers=4)
		self.placeholder_image = self._create_placeholder_image()
			
		try:
			base_path = Path(sys._MEIPASS)
		except AttributeError:
			base_path = Path(os.path.dirname(os.path.abspath(__file__)))

		self.ffmpeg_path = str(base_path / 'ffmpeg' / 'ffmpeg.exe')
		self.ffprobe_path = str(base_path / 'ffmpeg' / 'ffprobe.exe')
		
		try:
			result = subprocess.run(
				[self.ffmpeg_path, '-version'],
				capture_output=True,
				text=True,
				creationflags=subprocess.CREATE_NO_WINDOW
			)
			print(f"FFmpeg output:\n{result.stdout}")
			print(f"FFmpeg error:\n{result.stderr}")
			
			if result.returncode != 0:
				raise Exception("FFmpeg test failed")
		except Exception as e:
			error_msg = str(e)
			self.after(0, lambda msg=error_msg: self.progress_label.configure(
				text=f"FFmpeg verification failed: {msg}"
			))
			return

		self.main_frame = CTkFrame(master=self, corner_radius=6, fg_color='#040D12')
		self.main_frame.pack(pady=10, padx=10, expand=True, fill="both")

		self.link_entry = CTkEntry(
			master=self.main_frame,
			height=30,
			width=300,
			corner_radius=0,
			font=self.my_font,
			placeholder_text="Manually Enter YouTube URL here...",
			fg_color='#183D3D',
			text_color='#93B1A6',
			placeholder_text_color='#93B1A6'
		)
		self.link_entry.place(x=10, y=340)

		self.add_button = CTkButton(
			master=self.main_frame,
			height=30,
			width=100,
			corner_radius=0,
			text="ADD LINK",
			command=self.add_link,
			font=self.my_font,
			fg_color='#183D3D',
			text_color='#93B1A6',
		)
		self.add_button.place(x=315, y=340)

		self.directory_label = CTkLabel(
			master=self.main_frame,
			height=60,
			width=405,
			text="No directory selected",
			wraplength=275,
			font=self.my_font,
			text_color='#93B1A6',
		)
		self.directory_label.place(x=10, y=420)

		self.dir_button = CTkButton(
			master=self.main_frame,
			height=30,
			width=405,
			corner_radius=0,
			text="CHOOSE SAVE LOCATION",
			command=self.select_directory,
			font=self.my_font,
			fg_color='#183D3D',
			text_color='#93B1A6',
		)
		self.dir_button.place(x=10, y=490)

		self.search_entry = CTkEntry(
			master=self.main_frame,
			height=30,
			width=300,
			corner_radius=0,
			font=self.my_font,
			placeholder_text="Search YouTube Videos...",
			fg_color='#183D3D',
			text_color='#93B1A6',
			placeholder_text_color='#93B1A6'
		)
		self.search_entry.place(x=425, y=340)
		self.search_entry.bind("<Return>", lambda event: self.perform_search())

		self.search_button = CTkButton(
			master=self.main_frame,
			height=30,
			width=100,
			corner_radius=0,
			text="SEARCH",
			command=self.perform_search,
			font=self.my_font,
			fg_color='#183D3D',
			text_color='#93B1A6',
		)
		self.search_button.place(x=729, y=340)

		self.encoder_menu = CTkOptionMenu(
			master=self.main_frame,
			values=self.get_available_encoders(self.ffmpeg_path),
			height=30,
			width=405,
			corner_radius=0,
			font=self.my_font,
			dropdown_font=self.my_font,
			fg_color='#183D3D',
			dropdown_fg_color='#183D3D',
			button_color='#183D3D',
			text_color='#93B1A6',
			dropdown_text_color='#93B1A6',
		)
		self.encoder_menu.place(x=425, y=420)

		self.search_results_frame = CTkScrollableFrame(
			master=self.main_frame,
			width=self.THUMBNAIL_WIDTH + 260,
			height=320,
			corner_radius=0,
   		fg_color='#183D3D'
		)
		self.search_results_frame.place(x=425, y=10)

		self.scrollable_frame = CTkScrollableFrame(
			master=self.main_frame,
			width=self.THUMBNAIL_WIDTH + 260,
			height=320,
			corner_radius=0,
			fg_color='#183D3D'
		)
		self.scrollable_frame.place(x=10, y=10)

		self.audio_button = CTkButton(
			master=self.main_frame,
			height=30,
			width=200,
			corner_radius=0,
			text="DOWNLOAD AUDIO",
			command=lambda: self.download_all("audio"),
			font=self.my_font,
			fg_color='#183D3D',
			text_color='#93B1A6',
		)
		self.audio_button.place(x=10, y=380)

		self.resolution_menu = CTkOptionMenu(
			master=self.main_frame,
			values=["1080p", "720p", "480p", "360p"],
			height=30,
			width=200,
			corner_radius=0,
			font=self.my_font,
			dropdown_font=self.my_font,
			fg_color='#183D3D',
			dropdown_fg_color='#183D3D',
			button_color='#183D3D',
			text_color='#93B1A6',
			dropdown_text_color='#93B1A6',
		)
		self.resolution_menu.set("720p")
		self.resolution_menu.place(x=425, y=380)
		
		self.bitrate_menu = CTkOptionMenu(
			master=self.main_frame,
			values=["10Mpbs", "6Mbps", "5Mbps", "4Mbps", "3Mbps", "2Mbps"],
			height=30,
			width=200,
			corner_radius=0,
			font=self.my_font,
			dropdown_font=self.my_font,
			fg_color='#183D3D',
			dropdown_fg_color='#183D3D',
			button_color='#183D3D',
			text_color='#93B1A6',
			dropdown_text_color='#93B1A6',
		)
		self.bitrate_menu.set("5Mbps")
		self.bitrate_menu.place(x=630, y=380)

		self.video_button = CTkButton(
			master=self.main_frame,
			height=30,
			width=200,
			corner_radius=0,
			text="DOWNLOAD VIDEO",
			command=lambda: self.download_all("video"),
			font=self.my_font,
			fg_color='#183D3D',
			text_color='#93B1A6',
		)
		self.video_button.place(x=215, y=380)

		self.progress_bar = CTkProgressBar(
			master=self.main_frame,
			orientation="horizontal",
			width=405,
			height=50,
			corner_radius=0,
			fg_color='#183D3D',
		)
		self.progress_bar.set(0)
		self.progress_bar.place(x=425, y=460)

		self.progress_label = CTkLabel(
			master=self.main_frame,
			text="Ready",
			height=15,
			font=CTkFont(size=10),
			fg_color="transparent",
			text_color='#93B1A6',
		)
		self.progress_label.place(x=425, y=510)

		self.link_entry.bind("<Return>", lambda event: self.add_link())
		self.links = []
		self.link_rows = []
		
		self.update_handler = UpdateHandler()
		self.check_for_updates()

	def check_for_updates(self):
		"""checks if there's an actual update for the update prompt to show"""
		def update_check():
			try:
				if update_info := self.update_handler.check_update():
					self.after(0, lambda: self.show_update_prompt(update_info))
			except Exception as e:
				print(f"Update check error: {e}")
		threading.Thread(target=update_check, daemon=True).start()

	def show_update_prompt(self, update_info):
		"""shows the update prompt to the user"""
		dialog = CTkToplevel(self)
		dialog.title("Update Available")
		dialog.geometry("200x175")
		
		CTkLabel(dialog, text=f"Version {update_info['version']} is available!\nUpdate now?").pack(pady=10)
		
		button_frame = CTkFrame(dialog)
		button_frame.pack(pady=10)
		
		CTkButton(button_frame, text="Update Now", command=lambda: self.start_update(update_info['url'], dialog)).pack(side='top', padx=10, pady=10)
		CTkButton(button_frame, text="Later", command=dialog.destroy).pack(side='bottom', padx=10, pady=10)
		
		dialog.after(100, lambda: dialog.attributes('-topmost', True))
		dialog.mainloop()

	def start_update(self, download_url, dialog):
		"""Gets rid of the update prompt and starts the update"""
		dialog.destroy()
		self.progress_label.configure(text="Downloading update...")
		success = self.update_handler.perform_update(download_url)
		if success:
			self.destroy()

	def perform_search(self):
			"""starts searching youtube based on your search"""
			query = self.search_entry.get().strip()
			if not query:
					self._clear_search_results()
					return

			self._show_loading()

			if query in self.search_cache:
					self._update_ui(self.search_cache[query])
					return

			self.current_search_id += 1
			search_id = self.current_search_id
			threading.Thread(
					target=self._async_search,
					args=(query, search_id),
					daemon=True
			).start()

	def _async_search(self, query, search_id):
		"""searches meta data of videos"""
		try:
				ydl_opts = {
						"quiet": True,
						"extract_flat": "in_playlist",
						"skip_download": True,
						"ignoreerrors": True,
						"noplaylist": True,
						"extractor_args": {
								"youtube": {
										"skip": ["hls", "dash", "translated_subs"]
								}
						}
				}

				with yt_dlp.YoutubeDL(ydl_opts) as ydl:
						results = ydl.extract_info(f"ytsearch10:{query}", download=False)

				if search_id == self.current_search_id:
						self.search_cache[query] = results
						self.search_queue.put(results)
						self.after(0, self._process_search_results)
						
		except Exception as e:
				print(f"Search error: {e}")
				self.search_queue.put(None)
				self.after(0, self._process_search_results)

	def _process_search_results(self):
		"""processes the search results from async search and sends them to update ui"""
		try:
				results = self.search_queue.get_nowait()
				self._update_ui(results)
		except queue.Empty:
				pass

	def _show_loading(self):
		"""shows a label to show the user that the program is searching videos"""
		self._clear_search_results()
		CTkLabel(
			self.search_results_frame,
			text="Searching...",
			font=self.my_font
		).pack(pady=10)

	def _clear_search_results(self):
		"""clears any widgets in the search results window"""
		for widget in self.search_results_frame.winfo_children():
			try:
				widget.destroy()
			except:
				pass

	def _update_ui(self, search_results):
			self._clear_search_results()
			
			if not search_results or not search_results.get('entries'):
					CTkLabel(self.search_results_frame, text="No results found.", font=self.my_font).pack(pady=10)
					return

			for video in search_results.get("entries", []):
					if not video:
							continue
							
					result_frame = CTkFrame(self.search_results_frame, height=self.THUMBNAIL_HEIGHT, fg_color="#040D12")
					result_frame.pack(fill="x", padx=5, pady=3)

					thumbnail_label = CTkLabel(
							result_frame, 
							image=self.placeholder_image,
							text="",
							width=self.THUMBNAIL_WIDTH,
							height=self.THUMBNAIL_HEIGHT,
					)
					thumbnail_label.pack(side="left", padx=5, pady=5)

					content_frame = CTkFrame(result_frame, fg_color="transparent")
					content_frame.pack(side="left", fill="both", expand=True, padx=3)

					content_frame.grid_columnconfigure(0, weight=1)

					title_var = StringVar(value=video.get('title', 'Untitled'))
					title_label = CTkLabel(
							content_frame,
							textvariable=title_var,
							font=self.my_font,
							text_color= '#93B1A6',
							wraplength=160,
							width= 175,
							justify='left',
							anchor="w"
					)
					title_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

					CTkButton(
						content_frame,
						text="ADD",
						width=60,
						corner_radius=5,
						font=self.my_font,
						text_color='#93B1A6',
						fg_color='#183D3D',
						command=lambda v=video: self.add_link(  # v captures current video
							url=v.get('url'),
							video_id=v.get('id'),
							title=v.get('title')
						)
					).grid(row=0, column=1, padx=5, sticky="e")

					video_id = video.get('id')
					if video_id:
							self._load_thumbnail(video_id, thumbnail_label)
  
	def _create_placeholder_image(self):
		img = Image.new('RGB', (self.THUMBNAIL_WIDTH, self.THUMBNAIL_HEIGHT), (40, 40, 40))
		return CTkImage(light_image=img, dark_image=img, size=(self.THUMBNAIL_WIDTH, self.THUMBNAIL_HEIGHT))

	def _load_thumbnail(self, video_id, label):
			if video_id in self.thumbnail_cache:
					self._update_thumbnail(label, self.thumbnail_cache[video_id])
					return

			self.thumbnail_executor.submit(
					self._download_thumbnail,
					video_id,
					label
			)

	def _download_thumbnail(self, video_id, label):
		try:
			url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
			response = requests.get(url, timeout=5)
			if response.status_code == 200:
				mask = Image.new("L", (self.THUMBNAIL_WIDTH, self.THUMBNAIL_HEIGHT), 0)
				draw = ImageDraw.Draw(mask)
				draw.rounded_rectangle(
					(0, 0, self.THUMBNAIL_WIDTH, self.THUMBNAIL_HEIGHT),
					radius=10,
					fill=255
				)

				image = Image.open(io.BytesIO(response.content))
				image = image.resize((self.THUMBNAIL_WIDTH, self.THUMBNAIL_HEIGHT), Image.LANCZOS)

				image.putalpha(mask)
				
				ctk_image = CTkImage(
					light_image=image,
					dark_image=image,
					size=(self.THUMBNAIL_WIDTH, self.THUMBNAIL_HEIGHT)
				)
				self.thumbnail_cache[video_id] = ctk_image
				self._update_thumbnail(label, ctk_image)
		except Exception as e:
				print(f"Thumbnail download failed: {e}")

	def _update_thumbnail(self, label, image):
			self.after(0, lambda: label.configure(image=image))

	def get_available_encoders(self, ffmpeg_path):
			"""checks what encoders are available and what gpu you have to return the available encoders"""
			encoders = ['libx264 (CPU)']
			detected_gpu = detect_gpu(ffmpeg_path)
			print(f"GPU Detected: {detected_gpu}")

			try:
				result = subprocess.run([ffmpeg_path, '-hide_banner', '-encoders'], 
							capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
				encoder_output = result.stdout.lower()
		
				print(f"Available Encoders from FFmpeg:\n{encoder_output}")

				if 'nvenc' in encoder_output and detected_gpu == 'nvidia':
					encoders.extend(['h264_nvenc (NVIDIA)', 'hevc_nvenc (NVIDIA)'])
				if 'amf' in encoder_output and detected_gpu == 'amd':
					encoders.append('h264_amf (AMD)')
				if 'qsv' in encoder_output and detected_gpu == 'intel':
					encoders.append('h264_qsv (Intel)')

			except Exception as e:
				print(f"Encoder detection error: {str(e)}")
			print(f"Final Encoder List: {encoders}")
			return encoders

	def select_directory(self):
		"""Here the user can select a directory to download the files to"""
		directory = filedialog.askdirectory()
		if directory:
			self.directory_label.configure(text=f"Save Location: {directory}")
			self.download_directory = directory

	def add_link(self, url=None, video_id=None, title=None):
		"""Adds links to the download list with thumbnails and titles"""
		link = url or self.link_entry.get()
		if link:
			self.links.append(link)
   
			link_row = CTkFrame(
				master=self.scrollable_frame, 
				height=self.THUMBNAIL_HEIGHT, 
				fg_color="#040D12"
			)
			link_row.pack(fill="x", padx=5, pady=3)

			thumbnail_label = CTkLabel(
				link_row,
				image=self.placeholder_image,
				text="",
				width=self.THUMBNAIL_WIDTH,
				height=self.THUMBNAIL_HEIGHT,
			)
			thumbnail_label.pack(side="left", padx=5, pady=5)

			content_frame = CTkFrame(link_row, fg_color="transparent")
			content_frame.pack(side="left", fill="both", expand=True, padx=3)

			title_text = title or "Loading..."
			title_label = CTkLabel(
				content_frame,
				text=title_text,
				font=self.my_font,
				text_color='#93B1A6',
				wraplength=150,
				width=150,
				justify='left',
				anchor="w"
			)
			title_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

			# Remove button
			CTkButton(
				content_frame,
				text="REMOVE",
				width=60,
				corner_radius=5,
				font=self.my_font,
				text_color='#93B1A6',
				fg_color='#183D3D',
				command=lambda: self.remove_link(link, link_row)
			).grid(row=0, column=1, padx=5, sticky="e")

			# Store references for later updates
			link_row.thumbnail = thumbnail_label
			link_row.title = title_label
			self.link_rows.append(link_row)

			# Fetch metadata if not provided
			if not (video_id and title):
				self.thumbnail_executor.submit(
					self.fetch_link_metadata, 
					link, 
					link_row
				)
			else:
				self._load_thumbnail(video_id, thumbnail_label)
				title_label.configure(text=title)

			if not url:
				self.link_entry.delete(0, "end")
    
	def fetch_link_metadata(self, link, link_row):
		"""Fetches metadata for manually entered URLs"""
		try:
			with yt_dlp.YoutubeDL({
				'quiet': True,
				'extract_flat': True,
				'skip_download': True,
				'noplaylist': True
			}) as ydl:
				info = ydl.extract_info(link, download=False)
				video_id = info.get('id')
				title = info.get('title', link)
				
				self.after(0, lambda: [
					link_row.title.configure(text=title),
					self._load_thumbnail(video_id, link_row.thumbnail) 
					if video_id else None
				])
		except Exception as e:
			self.after(0, lambda: [
				link_row.title.configure(text=link),
				link_row.thumbnail.configure(image=self.placeholder_image)
			])

	def remove_link(self, link, row):
		"""removes the link from the links list"""
		if link in self.links:
			self.links.remove(link)
		row.destroy()
		self.link_rows.remove(row)

	def download_all(self, media_type):
		"""checks if the user has selected a download directory and then starts the download"""
		if not hasattr(self, 'download_directory'):
			self.progress_label.configure(text="Error: Select save location first!")
			return
		
		threading.Thread(target=self.process_downloads, args=(media_type,)).start()

	def process_downloads(self, media_type):
		"""goes through all the links you've added and downloads them either as mp3 or mp4"""
		self.video_button.configure(state="disabled")
		self.audio_button.configure(state="disabled")
		self.after(0, lambda: self.progress_label.configure(text="Initializing..."))
		
		if not os.path.isfile(self.ffmpeg_path):
			self.after(0, lambda: self.progress_label.configure(text=f"FFmpeg not found at {self.ffmpeg_path}"))
			return

		try:
			subprocess.run([self.ffmpeg_path, '-version'], check=True, 
						 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		except Exception as e:
			self.after(0, lambda: self.progress_label.configure(text=f"FFmpeg error: {str(e)}"))
			return

		total = len(self.links)
		for index, link in enumerate(self.links, 1):
			try:
				if not link.startswith(('http://', 'https://')):
					raise ValueError("Invalid URL")
		
				ydl_opts = {
					'ffmpeg_location': self.ffmpeg_path,
					'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
					'outtmpl': os.path.join(self.download_directory, '%(title)s.%(ext)s'),
					'merge_output_format': 'mp4',
					'verbose': True
				}

				with yt_dlp.YoutubeDL(ydl_opts) as ydl:
					info = ydl.extract_info(link, download=False)
					video_title = sanitize_filename(info.get('title', 'untitled'))
					video_id = info.get('id') or str(uuid.uuid4())[:8]

				if media_type == "audio":
					ydl_opts.update({
						'outtmpl': os.path.join(self.download_directory, f'{video_title}.%(ext)s'),
						'format': 'bestaudio/best',
						'postprocessors': [{
							'key': 'FFmpegExtractAudio',
							'preferredcodec': 'mp3',
							'preferredquality': '320',
						}]
					})
				else:
					res = int(self.resolution_menu.get()[:-1])
					bit = str(self.bitrate_menu.get()[:-3])
					print(f"BITRATE MENU SELECTION: {bit}")
					encoder = self.encoder_menu.get().split(' ')[0]
					
					encoder_args = {
						'libx264': [
							'-c:v', 'libx264',
							'-preset', 'fast',
							'-crf', '23',
							'-b:v', f'{bit}',
							'-pix_fmt', 'yuv420p',
							'-movflags', '+faststart'
						],
						'h264_nvenc': [
							'-c:v', 'h264_nvenc',
							'-preset', 'p6',
							'-rc', 'vbr',
							'-cq', '23',
							'-b:v', f'{bit}',
							'-maxrate', '10M',
							'-profile:v', 'main',
							'-pix_fmt', 'yuv420p'
						],
						'h264_amf': [
							'-c:v', 'h264_amf',
							'-usage', 'transcoding',
							'-quality', 'balanced',
							'-b:v', f'{bit}',
							'-maxrate', '10M',
							'-profile:v', 'main',
							'-pix_fmt', 'yuv420p'
						],
						'h264_qsv': [
							'-c:v', 'h264_qsv',
							'-preset', 'fast',
							'-global_quality', '23',
							'-b:v', f'{bit}',
							'-maxrate', '10M',
							'-profile:v', 'main',
							'-pix_fmt', 'yuv420p'
						]
					}
					
					base_args = [
						'-c:a', 'aac', 
						'-b:a', '192k',
						'-ar', '48000',
						'-ac', '2'
					]
					
					ydl_opts.update({
						'outtmpl': os.path.join(self.download_directory, f'{video_title}.mp4'),
						'format': f'bestvideo[height<={res}][vcodec!^=av01]+bestaudio/best',
						'postprocessors': [{
							'key': 'FFmpegVideoConvertor',
							'preferedformat': 'mp4',
						}],
						'postprocessor_args': encoder_args.get(encoder, encoder_args['libx264']) + base_args
					})

				self.after(0, lambda: self.progress_label.configure(
					text=f"Processing {index}/{total}"
				))
				
				with yt_dlp.YoutubeDL(ydl_opts) as ydl:
					ydl.params['verbose'] = True
					ydl.download([link])

				self.update_overall_progress(index/total, index, total)
				
			except Exception as e:
				error_msg = f"Failed: {str(e)}"
				self.after(0, lambda: self.progress_label.configure(text=error_msg))
				self.update_overall_progress(index/total, index, total)

		self.after(0, self.clear_links)
		self.video_button.configure(state="normal")
		self.audio_button.configure(state="normal")

	def update_progress(self, data):
		"""updates the progress bar for the user to see the progress of the downloads"""
		if data['status'] == 'downloading':
			progress = data.get('downloaded_bytes', 0) / data.get('total_bytes', 1)
			self.progress_bar.set(progress)
			self.progress_label.configure(text=f"Downloading: {os.path.basename(data['filename'])}")
			
		elif data['status'] == 'processing':
			try:
				current = data.get('elapsed', 0)
				duration = data.get('info_dict', {}).get('duration') or 1
				self.progress_bar.set(current / duration)
				self.progress_label.configure(text=f"Converting: {data.get('_current_audio_ext', 'file')}")
			except:
				self.progress_bar.set(1)
				self.progress_label.configure(text="Finalizing...")

		elif data['status'] == 'finished':
			self.progress_bar.set(1)
			self.progress_label.configure(text="Finalizing...")
			self.after(2000, lambda: self.progress_bar.set(0))

	def update_overall_progress(self, progress, current, total):
		"""updates the user on the overall progress"""
		self.progress_bar.set(progress)
		self.progress_label.configure(text=f"Completed: {current}/{total}")

	def clear_links(self):
		"""removes all the links from the link list when done downloading"""
		for row in self.link_rows:
			row.destroy()
		self.links.clear()
		self.link_rows.clear()
		self.progress_label.configure(text="All downloads completed!")

if __name__ == "__main__":
	app = App()
	app.mainloop()

