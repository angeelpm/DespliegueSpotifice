#!/usr/bin/env python3

import hashlib
import json
import logging
import secrets
import sys
from pathlib import Path

import Ice
from Ice import identityToString as id2str

Ice.loadSlice('-I{} spotifice_v2.ice'.format(Ice.getSliceDir()))
import Spotifice  # type: ignore # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MediaServer")


class StreamedFile:
    def __init__(self, track_info, media_dir):
        self.track = track_info
        filepath = media_dir / track_info.filename

        try:
            self.file = open(filepath, 'rb')
        except Exception as e:
            raise Spotifice.IOError(track_info.filename, f"Error opening media file: {e}")

    def read(self, size):
        return self.file.read(size)

    def close(self):
        try:
            if self.file:
                self.file.close()
        except Exception as e:
            logger.error(f"Error closing file for track '{self.track.id}': {e}")

    def __repr__(self):
        return f"<StreamState '{self.track.id}'>"


class MediaServerI(Spotifice.MediaServer):
    def __init__(self, media_dir, playlists_dir, users_file):
        self.media_dir = Path(media_dir)
        self.playlists_dir = Path(playlists_dir)
        self.tracks = {}
        self.playlists = {}
        self.users = {}
        self.sessions = {}  # Keep active sessions
        
        self.load_media()
        self.load_playlists()
        self.load_users(users_file)

    def ensure_track_exists(self, track_id):
        if track_id not in self.tracks:
            raise Spotifice.TrackError(track_id, "Track not found")
        
    def ensure_playlist_exists(self, playlist_id):
        if playlist_id not in self.playlists:
            raise Spotifice.PlaylistError(playlist_id, "Playlist not found")

    def load_media(self):
        for filepath in sorted(Path(self.media_dir).iterdir()):
            if not filepath.is_file() or filepath.suffix.lower() != ".mp3":
                continue

            self.tracks[filepath.name] = self.track_info(filepath)

        logger.info(f"Load media:  {len(self.tracks)} tracks")

    @staticmethod
    def track_info(filepath):
        return  Spotifice.TrackInfo(
            id=filepath.name,
            title=filepath.stem,
            filename=filepath.name)

    def load_playlists(self):
        for filepath in sorted(Path(self.playlists_dir).iterdir()):
            if not filepath.is_file() or filepath.suffix.lower() != ".playlist":
                continue
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                created_raw = data.get("created_at", "")
                try:
                    import time
                    from datetime import datetime
                    created_at = int(time.mktime(datetime.strptime(created_raw, "%d-%m-%Y").timetuple()))
                except Exception:
                    created_at = 0  
                    
                playlist = Spotifice.Playlist(
                    id=data["id"],
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    owner=data.get("owner", ""),
                    created_at=created_at,
                    track_ids=[
                        tid for tid in data.get("track_ids", [])
                        if tid in self.tracks
                    ]
                )
                self.playlists[playlist.id] = playlist
            except Exception as e:
                logger.error(f"Error loading playlist '{filepath.name}': {e}")

        logger.info(f"Loaded playlists: {len(self.playlists)}")
    
    def load_users(self, users_file):
        """Load user credentials from JSON file."""
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                self.users = json.load(f)
            logger.info(f"Loaded users: {len(self.users)}")
        except Exception as e:
            logger.error(f"Error loading users file '{users_file}': {e}")
            self.users = {}
    
    @staticmethod
    def verify_password(password, salt, digest):
        """Verify password using MD5 hash with salt."""
        computed = hashlib.md5((password + salt).encode('utf-8')).hexdigest()
        return secrets.compare_digest(computed, digest)
        
    def get_all_tracks(self, current=None):
        return list(self.tracks.values())

    def get_track_info(self, track_id, current=None):
        self.ensure_track_exists(track_id)
        return self.tracks[track_id]
    
    def get_all_playlists(self, current=None):
        return list(self.playlists.values())

    def get_playlist(self, playlist_id, current=None):
        self.ensure_playlist_exists(playlist_id)
        return self.playlists[playlist_id]
    
    def authenticate(self, render, username, password, current=None):
        """Authenticate user and return SecureStreamManager proxy."""
        str_render_id = id2str(render.ice_getIdentity())
        
        if username not in self.users:
            raise Spotifice.AuthError(username, "User not found")
        
        user_data = self.users[username]
        salt = user_data.get("salt", "")
        digest = user_data.get("digest", "")
        
        if not self.verify_password(password, salt, digest):
            raise Spotifice.AuthError(username, "Invalid password")
        
        # Close any existing session for this user
        if username in self.sessions:
            try:
                old_session, old_id = self.sessions[username]
                old_session.close()
                current.adapter.remove(old_id)
                logger.info(f"Closed previous session for user '{username}'")
            except Exception as e:
                logger.warning(f"Error closing previous session: {e}")
        
        session = SecureStreamManagerI(self, render.ice_getIdentity(), username)
        
        adapter = current.adapter
        session_id = Ice.Identity(name=f"session-{username}-{secrets.token_hex(8)}", category="")
        proxy = adapter.add(session, session_id)
        
        # Keep session alive by storing reference
        self.sessions[username] = (session, session_id)
        
        logger.info(f"User '{username}' authenticated from render '{str_render_id}'")
        return Spotifice.SecureStreamManagerPrx.checkedCast(proxy)


class SecureStreamManagerI(Spotifice.SecureStreamManager):
    """Session-based stream manager with authentication."""
    
    def __init__(self, server, render_identity, username):
        self.server = server
        self.render_identity = render_identity
        self.username = username
        self.active_stream = None
        
    def open_stream(self, track_id, current=None):
        """Open stream for authenticated user's session."""
        str_render_id = id2str(self.render_identity)
        self.server.ensure_track_exists(track_id)
        
        if self.active_stream:
            self.active_stream.close()
            
        self.active_stream = StreamedFile(
            self.server.tracks[track_id], self.server.media_dir)
        
        logger.info(f"Open stream for track '{track_id}' on render '{str_render_id}' (user: {self.username})")

    def close_stream(self, current=None):
        """Close the active stream for this session."""
        if self.active_stream:
            self.active_stream.close()
            self.active_stream = None
            logger.info(f"Closed stream for user '{self.username}' (render: {id2str(self.render_identity)})")

    def get_audio_chunk(self, chunk_size, current=None):
        """Get audio chunk from active stream."""
        str_render_id = id2str(self.render_identity)
        
        if not self.active_stream:
            raise Spotifice.StreamError(str_render_id, "No open stream for this session")
        
        try:
            data = self.active_stream.read(chunk_size)
            if not data:
                logger.info(f"Track exhausted: '{self.active_stream.track.id}'")
                self.close_stream(current)
            return data
        except Exception as e:
            raise Spotifice.IOError(
                self.active_stream.track.filename, f"Error reading file: {e}")
    
    def get_user_info(self, current=None):
        """Return information about the authenticated user."""
        if self.username not in self.server.users:
            return Spotifice.UserInfo(
                username=self.username,
                fullname="Unknown",
                email="",
                is_premium=False,
                created_at=0
            )
        
        user_data = self.server.users[self.username]
        
        created_raw = user_data.get("created_at", "")
        try:
            import time
            from datetime import datetime
            created_at = int(time.mktime(datetime.strptime(created_raw, "%d-%m-%Y").timetuple()))
        except Exception:
            created_at = 0
        
        return Spotifice.UserInfo(
            username=self.username,
            fullname=user_data.get("fullname", ""),
            email=user_data.get("email", ""),
            is_premium=user_data.get("is_premium", False),
            created_at=created_at
        )
    
    def close(self, current=None):
        """Close the session and cleanup resources."""
        self.close_stream(current)
        
        # Remove session from server's active sessions
        if self.username in self.server.sessions:
            del self.server.sessions[self.username]
            logger.info(f"Session removed from server for user '{self.username}'")
        
        logger.info(f"Session closed for user '{self.username}'")


def main(ic):
    properties = ic.getProperties()
    media_dir = properties.getPropertyWithDefault(
        'MediaServer.Content', 'media')
    playlist_dir = properties.getPropertyWithDefault(
        'MediaServer.Playlists', 'playlists')
    users_file = properties.getPropertyWithDefault(
        'MediaServer.UsersFile', 'users.json')
    
    adapter = ic.createObjectAdapter("MediaServerAdapter")
    servant = MediaServerI(
        Path(media_dir), Path(playlist_dir), Path(users_file))
    proxy = adapter.add(servant, ic.stringToIdentity("mediaServer1"))
    logger.info(f"MediaServer: {proxy}")

    adapter.activate()
    ic.waitForShutdown()

    logger.info("Shutdown")


if __name__ == "__main__":
    try:
        with Ice.initialize(sys.argv) as communicator:
            main(communicator)
    except KeyboardInterrupt:
        logger.info("Server interrupted by user.")
