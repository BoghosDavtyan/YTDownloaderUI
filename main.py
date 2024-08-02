import os
import threading
import subprocess
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.checkbox import CheckBox
from kivy.clock import Clock
from yt_dlp import YoutubeDL


class YouTubeDownloader(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.url_input = TextInput(multiline=False, hint_text='Enter YouTube URL')
        self.download_button = Button(text='Download', on_press=self.start_download)
        self.status_label = Label(text='')
        self.progress_bar = ProgressBar(max=100)

        settings_layout = GridLayout(cols=2, spacing=10)

        self.rename_check = CheckBox(active=False)
        settings_layout.add_widget(Label(text='Rename video:'))
        settings_layout.add_widget(self.rename_check)
        self.rename_input = TextInput(multiline=False, hint_text='New filename', disabled=True)
        settings_layout.add_widget(self.rename_input)
        settings_layout.add_widget(Label())  # Empty label for alignment

        self.trim_check = CheckBox(active=False)
        settings_layout.add_widget(Label(text='Trim video:'))
        settings_layout.add_widget(self.trim_check)
        self.trim_start = TextInput(multiline=False, hint_text='Start time (HH:MM:SS)', disabled=True)
        self.trim_end = TextInput(multiline=False, hint_text='End time (HH:MM:SS)', disabled=True)
        settings_layout.add_widget(self.trim_start)
        settings_layout.add_widget(self.trim_end)

        self.rename_check.bind(active=self.on_rename_active)
        self.trim_check.bind(active=self.on_trim_active)

        layout.add_widget(self.url_input)
        layout.add_widget(settings_layout)
        layout.add_widget(self.download_button)
        layout.add_widget(self.status_label)
        layout.add_widget(self.progress_bar)

        return layout

    def on_rename_active(self, checkbox, value):
        self.rename_input.disabled = not value

    def on_trim_active(self, checkbox, value):
        self.trim_start.disabled = not value
        self.trim_end.disabled = not value

    def start_download(self, instance):
        url = self.url_input.text
        if not url:
            self.status_label.text = 'Please enter a valid URL'
            return

        self.download_button.disabled = True
        self.status_label.text = 'Downloading...'
        self.progress_bar.value = 0

        threading.Thread(target=self.download_video, args=(url,)).start()

    def download_video(self, url):
        def progress_hook(d):
            if d['status'] == 'downloading':
                p = d['_percent_str']
                p = float(p.replace('%', ''))
                Clock.schedule_once(lambda dt: self.update_progress(p))
            elif d['status'] == 'finished':
                Clock.schedule_once(lambda dt: self.post_process(d['filename']))

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': '%(title)s.%(ext)s',
            'progress_hooks': [progress_hook],
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            Clock.schedule_once(lambda dt: self.download_error(str(e)))

    def post_process(self, filename):
        if self.rename_check.active and self.rename_input.text:
            new_filename = self.rename_input.text
            if not new_filename.endswith('.mp4'):
                new_filename += '.mp4'
            os.rename(filename, new_filename)
            filename = new_filename

        if self.trim_check.active and self.trim_start.text and self.trim_end.text:
            self.trim_video(filename, self.trim_start.text, self.trim_end.text)
        else:
            self.download_complete(filename)

    def trim_video(self, filename, start_time, end_time):
        output_filename = 'trimmed_' + filename
        cmd = ['ffmpeg', '-i', filename, '-ss', start_time, '-to', end_time, '-c', 'copy', output_filename]

        try:
            subprocess.run(cmd, check=True)
            os.remove(filename)  # Remove original file
            os.rename(output_filename, filename)  # Rename trimmed file to original name
            self.download_complete(filename)
        except subprocess.CalledProcessError as e:
            self.download_error(f"Error trimming video: {str(e)}")

    def update_progress(self, value):
        self.progress_bar.value = value

    def download_complete(self, filename):
        self.status_label.text = f'Completed: {os.path.basename(filename)}'
        self.download_button.disabled = False
        self.progress_bar.value = 100

    def download_error(self, error_message):
        self.status_label.text = f'Error: {error_message}'
        self.download_button.disabled = False
        self.progress_bar.value = 0


if __name__ == '__main__':
    YouTubeDownloader().run()