#!/usr/bin/env bash

# Check if required parameters are provided
if [[ -z "$1" ]]; then
    echo "No search query or video ID provided"
    exit 1
fi

query="$1"
mode="${2:-audio}"  # Default to audio if not specified
action="${3:-play}"  # Default to play if not specified

# Load YouTube API Key
YT_API_KEY="$(cat "${HOME}"/.api_keys/YT_API_KEY)"

function is_music_video() {
    local video_id="$1"
    local details_url="https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id=${video_id}&key=${YT_API_KEY}"
    local result=$(curl -s "$details_url")
    
    # Check duration (avoid very short or very long videos)
    local duration=$(echo "$result" | jq -r '.items[0].contentDetails.duration')
    # Convert duration to seconds
    duration=$(echo "$duration" | sed 's/PT\([0-9]*\)M\([0-9]*\)S/\1 * 60 + \2/' | bc)
    
    # Check if duration is between 2 and 8 minutes
    if (( duration < 120 || duration > 480 )); then
        return 1
    fi
    
    # Check if title or description contains music-related keywords
    local title=$(echo "$result" | jq -r '.items[0].snippet.title' | tr '[:upper:]' '[:lower:]')
    local description=$(echo "$result" | jq -r '.items[0].snippet.description' | tr '[:upper:]' '[:lower:]')
    
    if [[ "$title" =~ (official|music|audio|lyrics|song) ]] || \
       [[ "$description" =~ (official|music|audio|lyrics|song) ]]; then
        return 0
    fi
    
    return 1
}

function search_video() {
    local search_term="${1// /+}"
    # Add music-specific keywords to improve results
    local urlstring="https://www.googleapis.com/youtube/v3/search?part=snippet&q=${search_term}+official+audio+song&type=video&videoCategoryId=10&maxResults=10&key=${YT_API_KEY}"
    
    local result=$(curl -s "${urlstring}")
    
    # Try each result until we find a valid music video
    for i in {0..9}; do
        local video_id=$(echo "$result" | jq -r ".items[$i].id.videoId")
        local title=$(echo "$result" | jq -r ".items[$i].snippet.title")
        local channel=$(echo "$result" | jq -r ".items[$i].snippet.channelTitle")
        
        if [[ "$video_id" != "null" && ! -z "$video_id" ]] && is_music_video "$video_id"; then
            echo "{\"id\":\"${video_id}\",\"title\":\"${title}\",\"channel\":\"${channel}\",\"mode\":\"${mode}\"}"
            return 0
        fi
    done
    
    echo "Error: No valid music results found" >&2
    exit 1
}

function get_recommendations() {
    local video_id="$1"
    local urlstring="https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId=${video_id}&type=video&videoCategoryId=10&maxResults=10&key=${YT_API_KEY}"
    
    local result=$(curl -s "${urlstring}")
    
    # Try each result until we find a valid music video
    for i in {0..9}; do
        local next_id=$(echo "$result" | jq -r ".items[$i].id.videoId")
        local title=$(echo "$result" | jq -r ".items[$i].snippet.title")
        local channel=$(echo "$result" | jq -r ".items[$i].snippet.channelTitle")
        
        if [[ "$next_id" != "null" && ! -z "$next_id" && "$next_id" != "$video_id" ]] && \
           is_music_video "$next_id"; then
            echo "{\"id\":\"${next_id}\",\"title\":\"${title}\",\"channel\":\"${channel}\",\"mode\":\"${mode}\"}"
            return 0
        fi
    done
    
    # If no recommendations found, try searching for similar songs
    search_video "songs by ${channel}"
}

function play_video() {
    local video_id="$1"
    local mode="$2"
    
    if [[ "$mode" == "audio" ]]; then
        # Use yt-dlp for audio-only playback with format selection
        yt-dlp -f "bestaudio[ext=m4a]" "https://music.youtube.com/watch?v=${video_id}" -o - 2>/dev/null | \
        mpv --no-video --no-terminal --volume=70 - 2>/dev/null
    else
        # Video playback with regular mpv
        mpv --no-terminal --volume=70 "https://music.youtube.com/watch?v=${video_id}" 2>/dev/null
    fi
}

case "$action" in
    "search")
        search_video "$query"
        ;;
    "recommend")
        get_recommendations "$query"
        ;;
    "play")
        play_video "$query" "$mode"
        ;;
    *)
        echo "Invalid action specified" >&2
        exit 1
        ;;
esac