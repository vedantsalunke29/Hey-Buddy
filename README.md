# Song Sage

Song Sage is a voice-activated music assistant that allows you to search and play songs from YouTube Music using voice commands. Simply say "Hey Song Sage" to activate it, and then tell it the song you want to listen to. It supports both audio-only and video playback modes and automatically fetches similar song recommendations as the current song finishes playing.

## Features
- **Voice Activation**: Wake up the assistant by saying "Hey Song Sage".
- **Song Search**: Ask the assistant to play any song, and it will search for it on YouTube Music.
- **Playback Mode**: Choose between audio-only or video playback modes.
- **Song Recommendations**: Automatically fetches similar songs from YouTube Music once a song is finished playing.
- **Continuous Listening**: Always ready to listen for new commands or songs.
- **Cross-Language Compatibility**: Recognizes different song requests regardless of accent or dialect.

## Installation

### Install Dependencies
Python 3.7+
Install required Python packages:
```bash
pip install speechrecognition subprocess json threading queue
```
Install necessary tools for music playback:
```bash
brew install yt-dlp mpv
```
### Set Up YouTube API Key
1. Create a new project on the Google Developer Console.
2. Enable the YouTube Data API v3.
3. Generate an API key and save it in the following location:
```plaintext
~/.api_keys/YT_API_KEY
```

### Permissions
Ensure that the microphone, audio, and video playback tools have appropriate permissions on your system.

## Usage

1. **Start the Assistant**
Run the `app.py` script to start the assistant:
```bash
python app.py
```

2. **Activate the Assistant**
Once activated by saying "Hey Song Sage", the assistant will listen for song commands. For example:
```plaintext
You: "Hey Song Sage, play Tere Liye video"
Assistant: "Searching for: Tere Liye in video mode"
```

3. **Playback Mode**
- **Audio Mode**: Only the audio of the song will be played.
- **Video Mode**: The video will be played along with the audio.

4. **Song Recommendations**
Once a song finishes, Song Sage will automatically fetch a similar song and add it to the playback queue.

## File Structure
```plaintext
Song-Sage/
│
├── app.py               # Main Python script to handle voice recognition, music control, and user interaction.
├── scripts/
│   └── ytmusic_play.sh  # Shell script to interact with YouTube Music, perform search, and handle playback modes.
├── .api_keys/
│   └── YT_API_KEY       # YouTube API key for querying YouTube Data API.
└── README.md            # Project description and instructions.
```

## Core Usage

### Python (app.py)
The Python script `app.py` handles:
- **Voice Recognition**: The assistant listens for the wake word “Hey Song Sage” and then waits for a song name.
  - Utilizes the `speech_recognition` library to capture and process voice input.
  - Uses Google's speech recognition service to interpret the user's speech.
- **Song Search**: Once the wake word is detected, the assistant listens for a song name and determines whether the user wants video or audio playback.
  - Uses a custom method `extract_playback_mode()` to distinguish between video and audio commands.
  - Initiates song search by passing the query to the `ytmusic_play.sh` shell script.
- **Playback Control**: The Python script controls the music playback by launching subprocesses and running shell scripts in the background.
  - If a song is found, it is played using the specified mode (audio/video).
  - The assistant waits for the song to finish and automatically fetches recommendations.
- **Queue Management**: Songs are queued in a FIFO manner, ensuring that the assistant continuously plays new songs after the current one finishes.
- **Recommendation Fetching**: Continuously fetches recommended songs while the current song is playing. Recommendations are added to the playlist queue, ensuring a smooth experience.

### Shell Script (ytmusic_play.sh)
The shell script `ytmusic_play.sh` handles the actual interaction with YouTube Music and controls playback.
- **Search for Songs**:
  - The script constructs a search query using the YouTube Data API v3 and fetches relevant songs based on the user's input.
  - The API query is constructed to fetch music-related videos using specific keywords like “official”, “audio”, or “song”.
  - Returns video IDs, titles, and channels from the YouTube API.
- **Check for Valid Music Videos**:
  - The script checks the video details (such as duration and title/description) to ensure the result is a valid music video.
  - Filters results based on video duration (between 2 and 8 minutes).
  - Ensures that the video title or description contains music-related keywords (like "song", "audio", "lyrics").
- **Play Music**:
  - Depending on the user’s mode (audio or video), the script uses `yt-dlp` for audio-only playback or `mpv` for full video playback.
  - For audio mode, it extracts the best audio quality and plays it through `mpv`.
  - For video mode, it plays the video with `mpv`.
- **Get Recommendations**:
  - After playing a song, the script fetches song recommendations based on the video ID, providing the user with similar content.

## Contributing
Feel free to fork the repository and contribute to improving the functionality of Song Sage. You can submit issues or pull requests, and we’d love to hear your feedback!
