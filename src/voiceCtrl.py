import flet as ft
import pyaudio
import numpy as np
import whisper
import queue

# MyLibrary
import components as cp

@ft.control
class voiceControlApp(ft.Container):
    CHUNK = 1024
    FORMAT = pyaudio.paFloat32
    CHANNELS = 1
    RATE = 16000

    def __init__(self):
        super().__init__()
        # Whisperモデルのロード
        self.whisper_model = whisper.load_model("base")
        # 音声データを格納するキュー
        self.audio_queue = queue.Queue()
        # 音声認識の結果を格納する変数
        self.transciption = ""

        # Fletページ
        self.content = ft.Column(
            controls=[
                cp.VoiceRecogButton(
                    icon=ft.Icons.KEYBOARD_VOICE,
                ),
            ]
        )

    def audio_callback(self, in_data, frame_count, time_info, status):
        self.audio_data = np.frombuffer(in_data, dtype=np.float32)
        self.audio_queue.put(self.audio_data)
        return (in_data, pyaudio.paContinue)
    
    def proc_audio(self):
        global transcription
        self.audio_data = np.array([])

        while True:
            # キューから音声データを取得
            if not self.audio_queue.empty():
                self.audio_data = np.append(self.audio_data, self.audio_queue.get())

            # 一定量のデータが溜まったら処理
            if len(self.audio_data) > self.RATE * 5:
                # Whisperで音声認識
                result = self.whisper_model.transcribe(self.audio_data)
                self.transcription = result["text"]
                print("認識結果:", self.transcription)
                # 処理済みデータをクリア
                self.audio_data = np.array([])