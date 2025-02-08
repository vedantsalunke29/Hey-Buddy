import os
import time
import speech_recognition as sr
import subprocess
import json
import threading
from queue import Queue
import signal

class MusicController:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.playlist_queue = Queue()
        self.current_video_id = None
        self.should_play = True
        self.current_process = None
        self.recommendation_thread = None

    def listen_with_timeout(self, timeout=5):
        with sr.Microphone() as source:
            try:
                audio = self.recognizer.listen(source, timeout=timeout)
                return self.recognizer.recognize_google(audio).lower()
            except (sr.UnknownValueError, sr.WaitTimeoutError, sr.RequestError):
                return None

    def check_for_wake_word(self):
        max_retries = 3
        retry_delay = 1  
        
        for attempt in range(max_retries):
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    print("Listening for 'Hi Buddy'...")
                    audio = self.recognizer.listen(source, phrase_time_limit=3)
                    text = self.recognizer.recognize_google(audio).lower()
                    return "hi buddy" in text
            except (sr.UnknownValueError, sr.WaitTimeoutError):
                print("Didn't catch that, try again...")
                return False
            except (sr.RequestError, ConnectionError, ConnectionResetError) as e:
                if attempt < max_retries - 1:
                    print(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                    continue
                print(f"Failed after {max_retries} attempts: {e}")
                return False
            except Exception as e:
                print(f"Unexpected error: {e}")
                return False

    def extract_playback_mode(self, song_name):
        if "video" in song_name:
            mode = "video"
            song = song_name.replace("video", "").strip()
        else:
            mode = "audio"
            song = song_name.replace("audio", "").strip()
        song = song.replace("play", "").strip()
        return song, mode

    def fetch_recommendations(self):
        """Continuously fetch recommendations to keep queue filled"""
        while self.should_play:
            try:
                if self.current_video_id and self.playlist_queue.qsize() < 2:
                    result = subprocess.run(
                        ["./scripts/ytmusic_play.sh", self.current_video_id, "audio", "recommend"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    if result.returncode == 0 and result.stdout:
                        try:
                            video_info = json.loads(result.stdout)
                            if video_info and video_info.get('id'):
                                if video_info['id'] != self.current_video_id:
                                    print(f"\nQueuing next: {video_info['title']} by {video_info['channel']}")
                                    self.playlist_queue.put(video_info)
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                print(f"Error fetching recommendations: {e}")
            time.sleep(5)  # Wait before checking queue again

    def stop_current_playback(self):
        """Safely stop current playback"""
        if self.current_process and self.current_process.poll() is None:
            try:
                os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
            except:
                try:
                    self.current_process.terminate()
                except:
                    pass
            time.sleep(0.5)

    def play_music(self):
        while self.should_play:
            try:
                if not self.playlist_queue.empty():
                    video_info = self.playlist_queue.get()
                    self.current_video_id = video_info['id']
                    
                    print(f"\nNow playing: {video_info['title']}")
                    print(f"By: {video_info['channel']}")
                    
                    # Play the current song
                    self.current_process = subprocess.Popen(
                        ["./scripts/ytmusic_play.sh", self.current_video_id, video_info['mode'], "play"],
                        preexec_fn=os.setsid
                    )
                    
                    # Wait for the song to finish
                    self.current_process.wait()
                
                time.sleep(1)
            except Exception as e:
                print(f"Playback error: {e}")
                continue

    def main(self):
        # Start the continuous recommendation fetcher
        self.recommendation_thread = threading.Thread(target=self.fetch_recommendations, daemon=True)
        self.recommendation_thread.start()

        # Start the music player thread
        player_thread = threading.Thread(target=self.play_music, daemon=True)
        player_thread.start()

        while True:
            if self.check_for_wake_word():
                print("Activated! Waiting for song name...")
                song_name = self.listen_with_timeout(timeout=5)
                
                if song_name:
                    cleaned_song, mode = self.extract_playback_mode(song_name)
                    print(f"Searching for: {cleaned_song} in {mode} mode")
                    
                    # Stop current playback
                    self.stop_current_playback()
                    
                    # Clear current queue
                    while not self.playlist_queue.empty():
                        self.playlist_queue.get()
                    
                    # Get initial song
                    try:
                        result = subprocess.run(
                            ["./scripts/ytmusic_play.sh", cleaned_song, mode, "search"],
                            stdout=subprocess.PIPE,
                            text=True,
                            check=True
                        )
                        video_info = json.loads(result.stdout)
                        self.playlist_queue.put(video_info)
                    except Exception as e:
                        print(f"Error starting playback: {e}")
                else:
                    print("No song detected, going back to sleep...")
            
            time.sleep(0.1)

if __name__ == "__main__":
    controller = MusicController()
    try:
        controller.main()
    except KeyboardInterrupt:
        print("\nExiting...")
        controller.should_play = False
        controller.stop_current_playback()