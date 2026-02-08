import flet as ft
import pyaudio
import numpy as np
import whisper
import queue
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor

# MyLibrary
import components as cp

@ft.control
class voiceControlApp(ft.Container):
    def __init__(self):
        super().__init__()

        # 音声認識エンジンを保持
        self.recog_engine = VoiceRecog(on_update_callback=self.update_result_ui)
        
        self.status_text = ft.Text("", )
        self.result_display = ft.Text("ここに（ry")
        self.is_recoding = False
        self.btn_start = cp.StartVoiceButton(
            content="ダジャレを言う",
            icon=ft.Icons.KEYBOARD_VOICE,
            on_click=self.button_clicked,
            visible=True,
        )
        self.btn_finish = cp.FinishVoiceButton(
            content="判定する",
            icon=ft.Icons.KEYBOARD_VOICE_OUTLINED,
            on_click=self.button_clicked,
            visible=False,
        )

        # Fletページ
        self.content = ft.Column(
            controls=[
                self.status_text,
                self.result_display,
                self.btn_start,
                self.btn_finish,
            ]
        )

    async def button_clicked(self, e):
        self.is_recoding = not self.is_recoding
        self.btn_start.visible = not self.btn_start.visible
        self.btn_finish.visible = not self.btn_finish.visible
        if self.is_recoding:
            self.status_text.value = "マイク使用中..."
            self.status_text.color = ft.Colors.RED_400
            self.page.update()
            # 解析エンジンの開始
            await self.recog_engine.start()
        else:
            self.status_text.value = ""
            # 解析エンジンの終了
            self.recog_engine.stop()

    async def update_result_ui(self, text):
        self.result_display.value = text

        if self.page:
            self.page.update()
        

class VoiceRecog():
    CHUNK = 1024
    FORMAT = pyaudio.paFloat32
    CHANNELS = 1
    RATE = 16000

    def __init__(self, on_update_callback):
        super().__init__
        # 認識結果をUIに渡すためのコールバック関数
        self.on_update_callback = on_update_callback
        # PyAudioインスタンスを設定
        self.p = pyaudio.PyAudio()
        # マイクチェック（デバッグ）
        self.mic_check()
        # Whisperモデルのロード
        self.whisper_model = whisper.load_model("small")
        # 音声データを格納するキュー
        self.audio_queue = queue.Queue()
        # 音声認識の結果を格納する変数
        self.transciption = ""
        # 音声入力のセットアップ
        self.is_running = False
        self.stream = None
        

    def mic_check(self):
        try:
            self.default_info = self.p.get_default_input_device_info()
            print("[Dev] --- Microphone Info ---")
            print(f"Input mic: {self.default_info['name']}")
            print(f"Index: {self.default_info['index']}")
            print(f"Sampling Rate: {self.default_info['defaultSampleRate']}")
        except IOError:
            print("使用可能なマイクが見つかりません。")

    async def start(self):
        if self.is_running:
            return
        
        # 前回のデータが残っていたら空にする
        while not self.audio_queue.empty():
            self.audio_queue.get()
        
        self.is_running = True
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self.audio_callback
        )

        # 音声処理
        asyncio.create_task(self.proc_audio())

    def audio_callback(self, in_data, frame_count, time_info, status):
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        self.audio_queue.put(audio_data)
        return (in_data, pyaudio.paContinue)
    
    async def proc_audio(self):
        accumulated_audio = np.array([], dtype=np.float32)

        # しきい値の設定
        SILENCE_THRESHOLD = 0.01
        SILENCE_DURATION = 0.1
        # 無音時間計測変数
        silence_passtime = 0

        while self.is_running:
            try:
                # キューからデータを取得
                data = self.audio_queue.get_nowait()

                # データの音量を計算
                rms = np.sqrt(np.mean(data**2))
                if rms < SILENCE_THRESHOLD:
                    # 無音のとき
                    # print(f"[Dev] 無音")
                    if silence_passtime < SILENCE_DURATION:
                        silence_passtime += (len(data) / self.RATE)
                else:
                    # 音があるとき
                    # print(f"[Dev] 有音")
                    silence_passtime = 0
                    accumulated_audio = np.append(accumulated_audio, data)

                # 解析
                if silence_passtime >= SILENCE_DURATION and len(accumulated_audio) > 100:
                    result = self.whisper_model.transcribe(accumulated_audio, language='ja')
                    text = str(result["text"]).strip()
                    if text:
                        print(f"[Devtranscribe] {text}")
                        if self.on_update_callback:
                            await self.on_update_callback(text)

                    # バッファリセット
                    accumulated_audio = np.array([], dtype=np.float32)

            except queue.Empty:
                await asyncio.sleep(0.1)

    def stop(self):
        self.is_running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        print(f"[Dev] Recording ended.")

    def __del__(self):
        try:
            self.p.terminate()
        except:
            pass