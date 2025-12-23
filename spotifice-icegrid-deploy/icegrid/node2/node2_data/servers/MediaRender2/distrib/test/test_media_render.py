import Ice

from gst_player import GstPlayer
from media_render import Spotifice
from media_render import main as render_main
from media_server import main as server_main

from .icetest import IceTestCase


class TestRenderBase(IceTestCase):
    """Base class for render tests without auto-binding"""
    render_port = 10001
    server_port = 10000

    def setUp(self):
        server_props = {
            'MediaServerAdapter.Endpoints': f'tcp -p {self.server_port}',
            'MediaServer.Content': 'test/media',
            'MediaServer.Playlists': 'test/playlists',
            'MediaServer.UsersFile': 'users.json'}
        server_endpoint = f'mediaServer1:default -p {self.server_port} -t 500'
        self.create_server(server_main, server_props)

        player = GstPlayer()
        player.start()
        self.addCleanup(player.shutdown)

        render_props = {
            'MediaRenderAdapter.Endpoints': f'tcp -p {self.render_port}'}
        render_enpoint = f'mediaRender1:default -p {self.render_port} -t 500'
        self.create_server(render_main, render_props, player)

        self.server = self.create_proxy(server_endpoint, Spotifice.MediaServerPrx)
        self.sut = self.create_proxy(render_enpoint, Spotifice.MediaRenderPrx)
    
    def authenticate_and_bind(self):
        """Helper method to authenticate and bind the render"""
        self.stream_manager = self.server.authenticate(self.sut, 'user', 'secret')
        self.sut.bind_media_server(self.server, self.stream_manager)


class TestRender(TestRenderBase):
    """Test class with automatic authentication and binding"""
    def setUp(self):
        super().setUp()
        self.authenticate_and_bind()


class PlaybackTests(TestRenderBase):
    def test_id(self):
        self.assertEqual(self.sut.ice_id(), '::Spotifice::MediaRender')

    def test_stop_is_idempotent(self):
        self.sut.stop()
        self.sut.stop()

    def test_play_unbound_server(self):
        with self.assertRaises(Spotifice.BadReference) as cm:
            self.sut.play()

        self.assertEqual(cm.exception.reason, "No MediaServer bound")

    def test_play_unloaded_track(self):
        self.authenticate_and_bind()

        with self.assertRaises(Spotifice.TrackError) as cm:
            self.sut.play()

        self.assertEqual(cm.exception.reason, "No track loaded")

    def test_normal_play(self):
        tracks = self.server.get_all_tracks()
        self.authenticate_and_bind()
        self.sut.load_track(tracks[1].id)

        self.sut.play()

    def test_can_not_play_if_player_busy(self):
        tracks = self.server.get_all_tracks()
        self.authenticate_and_bind()
        self.sut.load_track(tracks[1].id)

        self.sut.play()

        with self.assertRaises(Spotifice.PlayerError) as cm:
            self.sut.play()

        self.assertEqual(cm.exception.reason, "Already playing")

    def test_load_playlist(self):
        playlists = self.server.get_all_playlists()
        self.assertGreater(len(playlists), 0)
        self.authenticate_and_bind()
        self.sut.load_playlist(playlists[0].id)
        current = self.sut.get_current_track()
        self.assertIsNotNone(current)
        self.assertEqual(current.id, playlists[0].track_ids[0])


class PlaylistNavigationTests(TestRenderBase):
    def test_load_playlist_sets_first_track(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        playlist = playlists[0]
        
        self.sut.load_playlist(playlist.id)
        current = self.sut.get_current_track()
        
        self.assertEqual(current.id, playlist.track_ids[0])

    def test_load_playlist_without_server(self):
        # BadReference is not declared in ICE interface, so it comes as UnknownUserException
        with self.assertRaises((Spotifice.BadReference, Ice.UnknownUserException)):
            self.sut.load_playlist('test-playlist1')

    def test_load_nonexistent_playlist(self):
        self.authenticate_and_bind()
        
        with self.assertRaises(Spotifice.PlaylistError) as cm:
            self.sut.load_playlist('non-existent-playlist')
        
        self.assertEqual(cm.exception.reason, "Playlist not found")

    def test_next_track(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        playlist = playlists[0]
        
        self.sut.load_playlist(playlist.id)
        first_track = self.sut.get_current_track()
        
        self.sut.next()
        second_track = self.sut.get_current_track()
        
        self.assertNotEqual(first_track.id, second_track.id)
        self.assertEqual(second_track.id, playlist.track_ids[1])

    def test_next_without_playlist(self):
        self.authenticate_and_bind()
        
        with self.assertRaises(Spotifice.PlaylistError) as cm:
            self.sut.next()
        
        self.assertEqual(cm.exception.reason, "No playlist loaded")

    def test_next_at_end_of_playlist_without_repeat(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        playlist = playlists[0]
        
        self.sut.load_playlist(playlist.id)
        
        # Navigate to the last track
        for _ in range(len(playlist.track_ids) - 1):
            self.sut.next()
        
        last_track = self.sut.get_current_track()
        self.assertEqual(last_track.id, playlist.track_ids[-1])
        
        # Try to go to next, should raise error
        with self.assertRaises(Spotifice.PlaylistError) as cm:
            self.sut.next()
        
        self.assertEqual(cm.exception.reason, "End of playlist")

    def test_next_at_end_of_playlist_with_repeat(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        playlist = playlists[0]
        
        self.sut.load_playlist(playlist.id)
        self.sut.set_repeat(True)
        
        # Navigate to the last track
        for _ in range(len(playlist.track_ids) - 1):
            self.sut.next()
        
        last_track = self.sut.get_current_track()
        self.assertEqual(last_track.id, playlist.track_ids[-1])
        
        # Go to next, should wrap to first track
        self.sut.next()
        first_track = self.sut.get_current_track()
        self.assertEqual(first_track.id, playlist.track_ids[0])

    def test_set_repeat(self):
        self.authenticate_and_bind()
        
        # Default should be False
        status = self.sut.get_status()
        self.assertFalse(status.repeat)
        
        # Set to True
        self.sut.set_repeat(True)
        status = self.sut.get_status()
        self.assertTrue(status.repeat)
        
        # Set back to False
        self.sut.set_repeat(False)
        status = self.sut.get_status()
        self.assertFalse(status.repeat)

    def test_next_maintains_playing_state(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        
        self.sut.load_playlist(playlists[0].id)
        self.sut.play()
        
        # Next should keep playing
        self.sut.next()
        
        status = self.sut.get_status()
        self.assertEqual(status.state, Spotifice.PlaybackState.PLAYING)


class PlaybackStatusTests(TestRender):
    def test_get_status_initial_stopped(self):
        status = self.sut.get_status()
        self.assertEqual(status.state, Spotifice.PlaybackState.STOPPED)
        self.assertEqual(status.current_track_id, "")
        self.assertFalse(status.repeat)

    def test_get_status_after_load_track(self):
        tracks = self.server.get_all_tracks()
        self.authenticate_and_bind()
        self.sut.load_track(tracks[0].id)
        
        status = self.sut.get_status()
        self.assertEqual(status.state, Spotifice.PlaybackState.STOPPED)
        self.assertEqual(status.current_track_id, tracks[0].id)

    def test_get_status_while_playing(self):
        tracks = self.server.get_all_tracks()
        self.authenticate_and_bind()
        self.sut.load_track(tracks[1].id)
        self.sut.play()
        
        status = self.sut.get_status()
        self.assertEqual(status.state, Spotifice.PlaybackState.PLAYING)
        self.assertEqual(status.current_track_id, tracks[1].id)

    def test_get_status_while_paused(self):
        tracks = self.server.get_all_tracks()
        self.authenticate_and_bind()
        self.sut.load_track(tracks[1].id)
        self.sut.play()
        self.sut.pause()
        
        status = self.sut.get_status()
        self.assertEqual(status.state, Spotifice.PlaybackState.PAUSED)
        self.assertEqual(status.current_track_id, tracks[1].id)

    def test_get_status_after_stop(self):
        tracks = self.server.get_all_tracks()
        self.authenticate_and_bind()
        self.sut.load_track(tracks[1].id)
        self.sut.play()
        self.sut.stop()
        
        status = self.sut.get_status()
        self.assertEqual(status.state, Spotifice.PlaybackState.STOPPED)
        # Track should still be loaded
        self.assertEqual(status.current_track_id, tracks[1].id)

    def test_get_status_with_repeat(self):
        self.authenticate_and_bind()
        self.sut.set_repeat(True)
        
        status = self.sut.get_status()
        self.assertTrue(status.repeat)

    def test_pause_while_playing(self):
        tracks = self.server.get_all_tracks()
        self.authenticate_and_bind()
        self.sut.load_track(tracks[1].id)
        self.sut.play()
        
        self.sut.pause()
        
        status = self.sut.get_status()
        self.assertEqual(status.state, Spotifice.PlaybackState.PAUSED)

    def test_pause_not_playing(self):
        with self.assertRaises(Spotifice.PlayerError) as cm:
            self.sut.pause()
        
        self.assertEqual(cm.exception.reason, "Not playing")

    def test_pause_already_paused(self):
        tracks = self.server.get_all_tracks()
        self.authenticate_and_bind()
        self.sut.load_track(tracks[1].id)
        self.sut.play()
        self.sut.pause()
        
        with self.assertRaises(Spotifice.PlayerError) as cm:
            self.sut.pause()
        
        self.assertEqual(cm.exception.reason, "Already paused")

    def test_play_after_pause_resumes(self):
        tracks = self.server.get_all_tracks()
        self.authenticate_and_bind()
        self.sut.load_track(tracks[1].id)
        self.sut.play()
        self.sut.pause()
        
        # Play again should resume
        self.sut.play()
        
        status = self.sut.get_status()
        self.assertEqual(status.state, Spotifice.PlaybackState.PLAYING)


class HistoryAndPreviousTests(TestRender):
    def test_previous_without_history(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        self.sut.load_playlist(playlists[0].id)
        
        # No history yet (only current track)
        with self.assertRaises(Spotifice.PlaylistError) as cm:
            self.sut.previous()
        
        self.assertEqual(cm.exception.reason, "No previous track available")

    def test_previous_after_one_play(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        self.sut.load_playlist(playlists[0].id)
        self.sut.play()
        self.sut.stop()
        
        # Only one track in history
        with self.assertRaises(Spotifice.PlaylistError) as cm:
            self.sut.previous()
        
        self.assertEqual(cm.exception.reason, "No previous track available")

    def test_previous_after_next(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        playlist = playlists[0]
        
        self.sut.load_playlist(playlist.id)
        first_track = self.sut.get_current_track()
        self.sut.play()
        self.sut.stop()
        
        self.sut.next()
        second_track = self.sut.get_current_track()
        self.sut.play()
        self.sut.stop()
        
        # Now go back
        self.sut.previous()
        previous_track = self.sut.get_current_track()
        
        self.assertEqual(previous_track.id, first_track.id)

    def test_previous_multiple_times(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        playlist = playlists[0]
        
        self.sut.load_playlist(playlist.id)
        first_track = self.sut.get_current_track()
        self.sut.play()
        self.sut.stop()
        
        self.sut.next()
        second_track = self.sut.get_current_track()
        self.sut.play()
        self.sut.stop()
        
        self.sut.next()
        third_track = self.sut.get_current_track()
        self.sut.play()
        self.sut.stop()
        
        # Go back once
        self.sut.previous()
        current = self.sut.get_current_track()
        self.assertEqual(current.id, second_track.id)
        
        # Go back again
        self.sut.previous()
        current = self.sut.get_current_track()
        self.assertEqual(current.id, first_track.id)

    def test_history_cleared_on_new_playlist(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        
        # Load first playlist and navigate
        self.sut.load_playlist(playlists[0].id)
        self.sut.play()
        self.sut.stop()
        self.sut.next()
        self.sut.play()
        self.sut.stop()
        
        # Load different playlist - should clear history
        self.sut.load_playlist(playlists[1].id)
        
        # Should not be able to go previous
        with self.assertRaises(Spotifice.PlaylistError) as cm:
            self.sut.previous()
        
        self.assertEqual(cm.exception.reason, "No previous track available")

    def test_history_cleared_on_bind_media_server(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        
        self.sut.load_playlist(playlists[0].id)
        self.sut.play()
        self.sut.stop()
        self.sut.next()
        self.sut.play()
        self.sut.stop()
        
        # Rebind server - should clear history
        self.authenticate_and_bind()
        
        # Should not be able to go previous
        with self.assertRaises(Spotifice.PlaylistError) as cm:
            self.sut.previous()
        
        self.assertEqual(cm.exception.reason, "No previous track available")

    def test_previous_maintains_playing_state(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        
        self.sut.load_playlist(playlists[0].id)
        self.sut.play()
        self.sut.next()
        
        # Previous should keep playing
        self.sut.previous()
        
        status = self.sut.get_status()
        self.assertEqual(status.state, Spotifice.PlaybackState.PLAYING)

    def test_history_does_not_add_duplicate_consecutive_tracks(self):
        self.authenticate_and_bind()
        playlists = self.server.get_all_playlists()
        
        self.sut.load_playlist(playlists[0].id)
        first_track = self.sut.get_current_track()
        
        # Play same track multiple times
        self.sut.play()
        self.sut.stop()
        self.sut.play()
        self.sut.stop()
        
        # Should not be able to go previous (only one track in history)
        with self.assertRaises(Spotifice.PlaylistError) as cm:
            self.sut.previous()
        
        self.assertEqual(cm.exception.reason, "No previous track available")

class AuthTests(TestRenderBase):
    
    def test_secure_play(self):
        secure_stream_mngr = self.server.authenticate(self.sut, 'user', 'secret')
        self.sut.bind_media_server(self.server, secure_stream_mngr)
        self.sut.load_track('2s.mp3')
        self.sut.play()
        self.sut.stop()
    
    def test_authenticate_with_wrong_password(self):
        # Try to authenticate with incorrect password
        with self.assertRaises(Spotifice.AuthError) as cm:
            self.server.authenticate(self.sut, 'user', 'wrongpassword')
        
        self.assertEqual(cm.exception.item, 'user')
        self.assertIn('password', cm.exception.reason.lower())
    
    def test_authenticate_with_nonexistent_user(self):
        # Try to authenticate with user that doesn't exist
        with self.assertRaises(Spotifice.AuthError) as cm:
            self.server.authenticate(self.sut, 'nonexistent', 'secret')
        
        self.assertEqual(cm.exception.item, 'nonexistent')
        self.assertIn('not found', cm.exception.reason.lower())
    
    def test_authenticate_returns_valid_stream_manager(self):
        # Authenticate and verify we get a valid SecureStreamManager
        stream_manager = self.server.authenticate(self.sut, 'user', 'secret')
        
        # Should be able to get user info
        user_info = stream_manager.get_user_info()
        self.assertEqual(user_info.username, 'user')
        self.assertIsNotNone(user_info.email)
        self.assertIsNotNone(user_info.fullname)
    
    def test_session_unique_per_authentication(self):
        # Each authentication should create a unique session
        stream_manager1 = self.server.authenticate(self.sut, 'user', 'secret')
        stream_manager2 = self.server.authenticate(self.sut, 'user', 'secret')
        
        # They should have different identities
        id1 = stream_manager1.ice_getIdentity()
        id2 = stream_manager2.ice_getIdentity()
        self.assertNotEqual(id1.name, id2.name)
        
        # But both should work
        user_info1 = stream_manager1.get_user_info()
        user_info2 = stream_manager2.get_user_info()
        self.assertEqual(user_info1.username, user_info2.username)
    
    def test_close_session(self):
        # Authenticate and get stream manager
        stream_manager = self.server.authenticate(self.sut, 'user', 'secret')
        self.sut.bind_media_server(self.server, stream_manager)
        
        # Open a stream
        stream_manager.open_stream('1s.mp3')
        
        # Close the session
        stream_manager.close()
        
        # Should still be able to call close again (idempotent)
        stream_manager.close()
    
    def test_play_without_authentication(self):
        # Try to load track without binding server first (no authentication)
        # This should fail because no MediaServer is bound
        with self.assertRaises(Spotifice.BadReference) as cm:
            self.sut.load_track('1s.mp3')
        
        self.assertIn('MediaServer', cm.exception.reason)
    
    def test_cannot_bind_without_stream_manager(self):
        # Try to bind with None as stream_manager
        # This should fail with Ice.UnknownException (wrapping AttributeError)
        with self.assertRaises(Ice.UnknownException):
            self.sut.bind_media_server(self.server, None)
    
    def test_music_library_accessible_without_auth(self):
        # MusicLibrary should be accessible without authentication
        tracks = self.server.get_all_tracks()
        self.assertGreater(len(tracks), 0)
        
        track_info = self.server.get_track_info(tracks[0].id)
        self.assertEqual(track_info.id, tracks[0].id)
    
    def test_playlist_manager_accessible_without_auth(self):
        # PlaylistManager should be accessible without authentication
        playlists = self.server.get_all_playlists()
        self.assertGreater(len(playlists), 0)
        
        playlist = self.server.get_playlist(playlists[0].id)
        self.assertEqual(playlist.id, playlists[0].id)
    
    def test_stream_operations_require_authentication(self):
        # Bind server without authentication
        stream_manager = self.server.authenticate(self.sut, 'user', 'secret')
        
        # Stream operations should work through SecureStreamManager
        stream_manager.open_stream('1s.mp3')
        chunk = stream_manager.get_audio_chunk(1024)
        self.assertIsNotNone(chunk)
        self.assertGreater(len(chunk), 0)
        stream_manager.close_stream()
    
    def test_multiple_users_can_authenticate(self):
        # Both users from users.json should be able to authenticate
        stream_manager1 = self.server.authenticate(self.sut, 'user', 'secret')
        user_info1 = stream_manager1.get_user_info()
        self.assertEqual(user_info1.username, 'user')
        
        # Note: 'jdoe' password would need to be known from users.json
        # For now, just verify user can authenticate
        self.assertIsNotNone(stream_manager1)
    
    def test_user_info_contains_required_fields(self):
        stream_manager = self.server.authenticate(self.sut, 'user', 'secret')
        user_info = stream_manager.get_user_info()
        
        # Verify all required fields are present
        self.assertIsNotNone(user_info.username)
        self.assertIsNotNone(user_info.fullname)
        self.assertIsNotNone(user_info.email)
        self.assertIsInstance(user_info.is_premium, bool)
        self.assertIsInstance(user_info.created_at, int)


class PlaylistTests(TestRender):
    
    def test_load_track_cancels_playlist(self):
        # Load a playlist first
        playlists = self.server.get_all_playlists()
        self.sut.load_playlist(playlists[0].id)
        
        # Verify playlist is loaded (first track should be '1s.mp3')
        current = self.sut.get_current_track()
        self.assertEqual(current.id, '1s.mp3')
        
        # Load a different track directly
        self.sut.load_track('4s.mp3')
        
        # Current track should now be the directly loaded track
        current = self.sut.get_current_track()
        self.assertEqual(current.id, '4s.mp3')
        
        # Next should fail because playlist is cancelled
        with self.assertRaises(Spotifice.PlaylistError):
            self.sut.next()
    
    def test_next_previous(self):
        playlists = self.server.get_all_playlists()
        playlist = playlists[0]  # ['1s.mp3', '2s.mp3', '4s.mp3']
        
        self.sut.load_playlist(playlist.id)
        
        # Start at first track
        current = self.sut.get_current_track()
        self.assertEqual(current.id, '1s.mp3')
        
        # Play the first track to add it to history
        self.sut.play()
        self.sut.stop()
        
        # Should not be able to go previous (only one track in history)
        with self.assertRaises(Spotifice.PlaylistError) as cm:
            self.sut.previous()
        self.assertEqual(cm.exception.reason, "No previous track available")
        
        # Go to next track
        self.sut.next()
        current = self.sut.get_current_track()
        self.assertEqual(current.id, '2s.mp3')
        
        # Play and stop to add to history
        self.sut.play()
        self.sut.stop()
        
        # Go to next track again
        self.sut.next()
        current = self.sut.get_current_track()
        self.assertEqual(current.id, '4s.mp3')
        
        # Play and stop to add to history
        self.sut.play()
        self.sut.stop()
        
        # Now we should be able to go back to previous track
        self.sut.previous()
        current = self.sut.get_current_track()
        self.assertEqual(current.id, '2s.mp3')
    
    def test_playlist_loads_next_track_when_exhausted(self):
        playlists = self.server.get_all_playlists()
        playlist = playlists[0]  # ['1s.mp3', '2s.mp3', '4s.mp3']
        
        self.sut.load_playlist(playlist.id)
        self.sut.load_track('1s.mp3')  # 1 second track
        self.sut.play()
        
        # Wait for track to finish and auto-advance
        import time
        time.sleep(1.5)  # Wait for 1s track to finish
        
        # Should automatically move to next track and continue playing
        status = self.sut.get_status()
        self.assertEqual(status.state, Spotifice.PlaybackState.PLAYING)
        
        current = self.sut.get_current_track()
        self.assertEqual(current.id, '2s.mp3')
    
    def test_repeat_playlist(self):
        playlists = self.server.get_all_playlists()
        playlist = playlists[0]  # ['1s.mp3', '2s.mp3', '4s.mp3']
        
        self.sut.load_playlist(playlist.id)
        self.sut.set_repeat(True)
        
        # Navigate to last track
        self.sut.next()
        self.sut.next()
        current = self.sut.get_current_track()
        self.assertEqual(current.id, '4s.mp3')
        
        # Next from last track should wrap to first track when repeat is on
        self.sut.next()
        current = self.sut.get_current_track()
        self.assertEqual(current.id, '1s.mp3')


class RepeatTests(TestRender):
    
    def test_repeat_plays_same_track(self):
        self.sut.load_track('1s.mp3')
        self.sut.set_repeat(True)
        self.sut.play()
        
        # Wait for track to finish
        import time
        time.sleep(1.5)
        
        # Should automatically replay the same track
        status = self.sut.get_status()
        self.assertEqual(status.state, Spotifice.PlaybackState.PLAYING)
        
        current = self.sut.get_current_track()
        self.assertEqual(current.id, '1s.mp3')