import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from yt_dlp import YoutubeDL


class YouTubeDownloader(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.url_input = TextInput(multiline=False, hint_text='Enter YouTube URL')
        self.download_button = Button(text='Download', on_press=self.download_video)
        self.status_label = Label(text='')

        layout.add_widget(self.url_input)
        layout.add_widget(self.download_button)
        layout.add_widget(self.status_label)

        return layout

    def download_video(self, instance):
        url = self.url_input.text
        if not url:
            self.status_label.text = 'Please enter a valid URL'
            return

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': '%(title)s.%(ext)s',
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                self.status_label.text = f'Downloaded: {filename}'
        except Exception as e:
            self.status_label.text = f'Error: {str(e)}'


if __name__ == '__main__':
    YouTubeDownloader().run()