#!/usr/bin/env python3

import logging
import sys

import Ice
from Ice import identityToString as id2str

from gst_player import GstPlayer

Ice.loadSlice('-I{} spotifice_v2.ice'.format(Ice.getSliceDir()))
import Spotifice  # type: ignore # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MediaRender")


class MediaRenderI(Spotifice.MediaRender):
    def __init__(self, player):
        self.player = player
        self.server: Spotifice.MediaServerPrx = None
        self.stream_manager: Spotifice.SecureStreamManagerPrx = None
        self.current_track = None
        self.playlist = None
        self.current_index = -1
        self.repeat = False
        self.state = Spotifice.PlaybackState.STOPPED
        self.history = [] 


    def ensure_player_stopped(self):
        if self.player.is_playing():
            raise Spotifice.PlayerError(reason="Already playing")

    def ensure_server_bound(self):
        if not self.server or not self.stream_manager:
            raise Spotifice.BadReference(reason="No MediaServer bound")

    # --- RenderConnectivity ---

    def bind_media_server(self, media_server, stream_manager, current=None):
        """Bind both MediaServer and SecureStreamManager (session)."""
        if stream_manager is None:
            raise AttributeError("stream_manager cannot be None")
            
        try:
            proxy = media_server.ice_timeout(500)
            proxy.ice_ping()
        except Ice.ConnectionRefusedException as e:
            raise Spotifice.BadReference(reason=f"MediaServer not reachable: {e}")

        self.server = media_server
        self.stream_manager = stream_manager
        self.history = []
        logger.info(f"Bound to MediaServer '{id2str(media_server.ice_getIdentity())}'")


    def unbind_media_server(self, current=None):
        self.stop(current)
        
        if self.stream_manager:
            try:
                self.stream_manager.close()
            except Ice.ObjectNotExistException:
                logger.warning("Session already closed or destroyed")
            except Exception as e:
                logger.error(f"Error closing session: {e}")
        
        self.server = None
        self.stream_manager = None
        self.history = []
        logger.info("Unbound MediaServer")

    # --- ContentManager ---

    def _load_track_internal(self, track_id, current=None, cancel_playlist=False):
        """Método interno para cargar una pista. Usado por load_track y next."""
        was_playing = self.state == Spotifice.PlaybackState.PLAYING
        if was_playing:
            self.stop(current)
        
        self.current_track = self.server.get_track_info(track_id)
        
        if cancel_playlist:
            self.playlist = None
            self.current_index = -1
        
        if not self.history or self.history[-1] != track_id:
            self.history.append(track_id)
        
        logger.info(f"Current track set to: {self.current_track.title}")
        
        if was_playing:
            self.play(current)

    def load_track(self, track_id, current=None):
        self.ensure_server_bound()

        try:
            cancel_playlist = True
            if self.playlist and track_id in self.playlist.track_ids:
                cancel_playlist = False
                self.current_index = self.playlist.track_ids.index(track_id)
            
            self._load_track_internal(track_id, current, cancel_playlist=cancel_playlist)
        except Spotifice.TrackError as e:
            logger.error(f"Error setting track: {e.reason}")
            raise
        
    def load_playlist(self, playlist_id, current=None):
        self.ensure_server_bound()
        playlist = self.server.get_playlist(playlist_id)

        if not playlist.track_ids:
            raise Spotifice.PlaylistError(reason="Empty playlist")

        self.playlist = playlist
        self.current_index = 0
        self.history = []
        first_track_id = playlist.track_ids[0]
        self._load_track_internal(first_track_id, current, cancel_playlist=False)
        logger.info(f"Loaded playlist '{playlist_id}' with {len(playlist.track_ids)} tracks")

    def get_current_track(self, current=None):
        return self.current_track

    # --- PlaybackController ---

    def play(self, current=None):
        def get_chunk_hook(chunk_size):
            try:
                return self.stream_manager.get_audio_chunk(chunk_size)
            except Spotifice.IOError as e:
                logger.error(e)
            except Ice.ObjectNotExistException:
                logger.error("Stream manager session no longer exists")
            except Ice.Exception as e:
                logger.critical(e)

        def track_exhausted_hook():
            """Llamado cuando una pista termina de reproducirse."""
            logger.info("Track exhausted")
            
            if self.playlist and self.current_index < len(self.playlist.track_ids) - 1:
                try:
                    self.next(current)
                except Exception as e:
                    logger.error(f"Error loading next track: {e}")
                    self.state = Spotifice.PlaybackState.STOPPED
            elif not self.playlist and self.repeat and self.current_track:
                try:
                    logger.info(f"Repeating single track: {self.current_track.id}")
                    self.state = Spotifice.PlaybackState.STOPPED
                    self.play(current)
                except Exception as e:
                    logger.error(f"Error repeating track: {e}")
                    self.state = Spotifice.PlaybackState.STOPPED
            else:
                self.state = Spotifice.PlaybackState.STOPPED

        assert current, "remote invocation required"

        self.ensure_server_bound()

        if not self.current_track:
            raise Spotifice.TrackError(reason="No track loaded")

        if self.state == Spotifice.PlaybackState.PLAYING:
            raise Spotifice.PlayerError(reason="Already playing")

        if self.state == Spotifice.PlaybackState.PAUSED:
            self.player.resume()
            self.state = Spotifice.PlaybackState.PLAYING
            logger.info("Resumed playback")
            return
    
        try:
            self.stream_manager.open_stream(self.current_track.id)
        except Spotifice.BadIdentity as e:
            raise Spotifice.StreamError(reason=f"Stream setup failed: {e.reason}")

        self.player.configure(get_chunk_hook, track_exhausted_hook)
        if not self.player.confirm_play_starts():
            raise Spotifice.PlayerError(reason="Failed to confirm playback")

        self.state = Spotifice.PlaybackState.PLAYING
        logger.info(f"Playing: {self.current_track.id}")

    def get_status(self, current=None):
        return Spotifice.PlaybackStatus(
            state=self.state,
            current_track_id=self.current_track.id if self.current_track else "",
            repeat=self.repeat
        )
    
    def set_repeat(self, value, current=None):
        self.repeat = value
        logger.info(f"Repeat mode set to {self.repeat}")


    def previous(self, current=None):
        if len(self.history) < 2:
            raise Spotifice.PlaylistError("", "No previous track available")
        
        self.history.pop()
        
        prev_track_id = self.history[-1]
        self.history.pop()  
        
        if self.playlist:
            try:
                self.current_index = self.playlist.track_ids.index(prev_track_id)
            except ValueError:
                pass
        
        self._load_track_internal(prev_track_id, current, cancel_playlist=False)
        logger.info(f"Previous track: {prev_track_id}")
    
    def next(self, current=None):
        if not self.playlist:
            raise Spotifice.PlaylistError("", "No playlist loaded")

        if self.current_index >= len(self.playlist.track_ids) - 1:
            if self.repeat:
                self.current_index = 0
                next_track_id = self.playlist.track_ids[self.current_index]
                self._load_track_internal(next_track_id, current, cancel_playlist=False)
                logger.info(f"Next track (wrapped): {next_track_id}")
            else:
                raise Spotifice.PlaylistError("", "End of playlist")
        else:
            self.current_index += 1
            next_track_id = self.playlist.track_ids[self.current_index]
            self._load_track_internal(next_track_id, current, cancel_playlist=False)
            logger.info(f"Next track: {next_track_id}")


    def pause(self, current=None):
        if self.state == Spotifice.PlaybackState.PAUSED:
            raise Spotifice.PlayerError(reason="Already paused")
        if not self.player.is_playing():
            raise Spotifice.PlayerError(reason="Not playing")
        self.player.pause()
        self.state = Spotifice.PlaybackState.PAUSED
        logger.info("Paused")


    def stop(self, current=None):
        if self.stream_manager and current:
            try:
                self.stream_manager.close_stream()
            except Ice.ObjectNotExistException:
                logger.warning("Stream manager session already closed")
            except Exception as e:
                logger.error(f"Error closing stream: {e}")

        if not self.player.stop():
            raise Spotifice.PlayerError(reason="Failed to confirm stop")

        self.state = Spotifice.PlaybackState.STOPPED
        logger.info("Stopped")


def main(ic, player):
    servant = MediaRenderI(player)

    adapter = ic.createObjectAdapter("MediaRenderAdapter")
    proxy = adapter.add(servant, ic.stringToIdentity("mediaRender1"))
    logger.info(f"MediaRender: {proxy}")

    adapter.activate()
    ic.waitForShutdown()

    logger.info("Shutdown")


if __name__ == "__main__":
    player = GstPlayer()
    player.start()
    try:
        with Ice.initialize(sys.argv) as communicator:
            main(communicator, player)
    except KeyboardInterrupt:
        logger.info("Server interrupted by user.")
    finally:
        player.shutdown()
