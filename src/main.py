import sys, re, os, subprocess, requests, uuid, logging, time, threading, yt_dlp, queue
from packaging import version
from pathlib import Path
from customtkinter import set_default_color_theme, CTk, CTkFrame, CTkLabel, CTkButton, CTkEntry, CTkScrollableFrame, CTkProgressBar, CTkOptionMenu, CTkFont, CTkToplevel
from tkinter import filedialog, messagebox, StringVar

def detect_gpu(ffmpeg_path):
	try:
		result = subprocess.run([ffmpeg_path, '-hide_banner', '-encoders'], 
								capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
		encoders = result.stdout.lower()
		if 'nvenc' in encoders or 'cuda' in encoders:
			return 'nvidia'
		if 'amf' in encoders or 'amd' in encoders:
			return 'amd'
		if 'qsv' in encoders or 'intel' in encoders:
			return 'intel'
		return 'cpu'
	except Exception as e:
		print(f"GPU detection error: {str(e)}")
		return 'cpu'

def sanitize_filename(filename):
	filename = re.sub(r'[\\/*?:"<>|]', '', filename)
	filename = filename.encode('ascii', 'ignore').decode('ascii')
	return filename.strip()[:120]

class UpdateHandler:
	def __init__(self):
		self.current_version = self.get_current_version()
		self.repo_owner = "SleepyTK"
		self.repo_name = "YoutubeDownloader"
		self.exe_name = "YouTube_Downloader.exe"

	def get_current_version(self):
		"""Get version from bundled file"""
		try:
			base_path = Path(sys._MEIPASS)
		except AttributeError:
			base_path = Path(os.path.dirname(__file__))
		
		version_file = base_path / "version.txt"
		return version_file.read_text().strip()

	def check_update(self):
		try:
			response = requests.get(
				f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest",
				timeout=5
			)
			if response.status_code == 200:
				latest_data = response.json()
				latest_version_str = latest_data['tag_name']
				# Remove the 'v' prefix if present
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
		"""Download and replace EXE"""
		try:
			temp_exe = Path(os.environ['TEMP']) / "update_temp.exe"
			response = requests.get(download_url)
			if response.status_code != 200:
				raise Exception(f"Download failed with status {response.status_code}")
			temp_exe.write_bytes(response.content)

			import textwrap
			bat_script = textwrap.dedent(f"""\
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
	def __init__(self):
		super().__init__()
		self.title("YouTube Downloader v1.0.0")
		self.geometry("885x450")
		self.resizable(0, 0)
		self.attributes('-topmost', True)
		self.my_font = CTkFont(family="System", weight="bold")
		set_default_color_theme("green")
  
		self.search_queue = queue.Queue()
		self.search_cache = {}
		self.current_search_id = 0
		self.last_search_time = 0
		
		# FFmpeg path detection
		try:
			base_path = Path(sys._MEIPASS)
		except AttributeError:
			base_path = Path(os.path.dirname(os.path.abspath(__file__)))

		self.ffmpeg_path = str(base_path / 'ffmpeg' / 'ffmpeg.exe')
		self.ffprobe_path = str(base_path / 'ffmpeg' / 'ffprobe.exe')

		print(f"FFmpeg path: {self.ffmpeg_path}")
		print(f"FFmpeg exists: {os.path.exists(self.ffmpeg_path)}")
		
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

		self.main_frame = CTkFrame(master=self, corner_radius=6)
		self.main_frame.pack(pady=10, padx=10, expand=True, fill="both")

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

		self.search_entry = CTkEntry(
			master=self.main_frame,
			height=30,
			width=275,
			corner_radius=0,
			font=self.my_font,
			placeholder_text="Search YouTube Videos..."
		)
		self.search_entry.place(x=580, y=340)
		self.search_entry.bind("<Return>", lambda event: self.perform_search())

		self.encoder_menu = CTkOptionMenu(
			master=self.main_frame,
			values=self.get_available_encoders(self.ffmpeg_path),
			height=30,
			width=275,
			corner_radius=0,
			font=self.my_font,
			dropdown_font=self.my_font
		)
		self.encoder_menu.place(x=580, y=380)

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
		
		self.update_handler = UpdateHandler()
		self.check_for_updates()

	def check_for_updates(self):
		"""Non-blocking update check"""
		def update_check():
			try:
				if update_info := self.update_handler.check_update():
					self.after(0, lambda: self.show_update_prompt(update_info))
			except Exception as e:
				print(f"Update check error: {e}")
		threading.Thread(target=update_check, daemon=True).start()
	
	
	def show_update_prompt(self, update_info):
		"""CTk update dialog"""
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
		"""Handle update confirmation"""
		dialog.destroy()
		self.progress_label.configure(text="Downloading update...")
		success = self.update_handler.perform_update(download_url)
		if success:
			self.destroy()

	def perform_search(self):
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
			"""Background search with result validation"""
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
			"""Handle results from the queue"""
			try:
					results = self.search_queue.get_nowait()
					self._update_ui(results)
			except queue.Empty:
					pass

	def _show_loading(self):
			"""Display loading indicator"""
			self._clear_search_results()
			CTkLabel(
					self.search_results_frame,
					text="Searching...",
					font=self.my_font
			).pack(pady=10)

	def _clear_search_results(self):
			"""Safely clear previous results"""
			for widget in self.search_results_frame.winfo_children():
					try:
							widget.destroy()
					except:
							pass

	def _update_ui(self, search_results):
			"""Optimized UI update with widget recycling"""
			self._clear_search_results()
			
			if not search_results or not search_results.get('entries'):
					CTkLabel(
							self.search_results_frame,
							text="No results found.",
							font=self.my_font
					).pack(pady=10)
					return

			container = CTkFrame(self.search_results_frame)
			container.pack(fill="both", expand=True)
			
			for video in search_results.get("entries", []):
					if not video:
							continue
							
					result_frame = CTkFrame(container, corner_radius=0)
					result_frame.pack(fill="x", padx=5, pady=2, anchor="nw")

					title_var = StringVar(value=video.get('title', 'Untitled'))
					
					CTkLabel(
							result_frame,
							textvariable=title_var,
							font=self.my_font,
							wraplength=150
					).pack(side="left", padx=5, pady=5)

					CTkButton(
							result_frame,
							text="ADD",
							width=60,
							corner_radius=0,
							font=self.my_font,
							command=lambda url=video.get('url'): self.add_link(url)
					).pack(side="right", padx=5, pady=5)

			self.search_results_frame.update_idletasks()

	def get_available_encoders(self, ffmpeg_path):
		encoders = ['libx264 (CPU)']
		try:
			result = subprocess.run([ffmpeg_path, '-hide_banner', '-encoders'], 
								capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
			encoder_output = result.stdout.lower()

			if 'nvenc' in encoder_output:
				encoders.extend(['h264_nvenc (NVIDIA)', 'hevc_nvenc (NVIDIA)'])
			if 'amf' in encoder_output:
				encoders.append('h264_amf (AMD)')
			if 'qsv' in encoder_output:
				encoders.append('h264_qsv (Intel)')

		except Exception as e:
			print(f"Encoder detection error: {str(e)}")
		return encoders

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
					encoder = self.encoder_menu.get().split(' ')[0]
					
					encoder_args = {
						'libx264': [
							'-c:v', 'libx264',
							'-preset', 'fast',
							'-crf', '23',
							'-b:v', '5M',
							'-pix_fmt', 'yuv420p',
							'-movflags', '+faststart'
						],
						'h264_nvenc': [
							'-c:v', 'h264_nvenc',
							'-preset', 'p6',
							'-rc', 'vbr',
							'-cq', '23',
							'-b:v', '5M',
							'-maxrate', '10M',
							'-profile:v', 'main',
							'-pix_fmt', 'yuv420p'
						],
						'h264_amf': [
							'-c:v', 'h264_amf',
							'-usage', 'transcoding',
							'-quality', 'balanced',
							'-b:v', '5M',
							'-maxrate', '10M',
							'-profile:v', 'main',
							'-pix_fmt', 'yuv420p'
						],
						'h264_qsv': [
							'-c:v', 'h264_qsv',
							'-preset', 'fast',
							'-global_quality', '23',
							'-b:v', '5M',
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

	def update_progress(self, data):
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