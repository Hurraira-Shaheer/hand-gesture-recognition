import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv()

SCOPE = "user-modify-playback-state user-read-playback-state"

def get_spotify_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope=SCOPE,
        cache_path=".spotify_cache"
    ))

sp = get_spotify_client()

def play_pause():
    try:
        playback = sp.current_playback()
        if not playback:
            return {"error": "No active device"}
        if playback["is_playing"]:
            sp.pause_playback()
            return {"action": "paused"}
        else:
            sp.start_playback()
            return {"action": "playing"}
    except Exception as e:
        return {"error": str(e)}

def next_track():
    try:
        sp.next_track()
        return {"action": "next_track"}
    except Exception as e:
        return {"error": str(e)}

def previous_track():
    try:
        sp.previous_track()
        return {"action": "previous_track"}
    except Exception as e:
        return {"error": str(e)}

def volume_up():
    try:
        playback = sp.current_playback()
        if not playback:
            return {"error": "No active device"}
        current = playback["device"]["volume_percent"]
        new_volume = min(100, current + 10)
        sp.volume(new_volume)
        return {"action": "volume_up", "volume": new_volume}
    except Exception as e:
        return {"error": str(e)}

def volume_down():
    try:
        playback = sp.current_playback()
        if not playback:
            return {"error": "No active device"}
        current = playback["device"]["volume_percent"]
        new_volume = max(0, current - 10)
        sp.volume(new_volume)
        return {"action": "volume_down", "volume": new_volume}
    except Exception as e:
        return {"error": str(e)}

def stop():
    try:
        sp.pause_playback()
        return {"action": "stopped"}
    except Exception as e:
        return {"error": str(e)}

def get_current_track():
    try:
        playback = sp.current_playback()
        if not playback or not playback.get("item"):
            return None
        track = playback["item"]
        return {
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "is_playing": playback["is_playing"],
            "volume": playback["device"]["volume_percent"],
            "cover_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None
        }
    except Exception as e:
        return None