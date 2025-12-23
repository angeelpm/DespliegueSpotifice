import Ice

from media_server import Spotifice, main

from .icetest import IceTestCase


class TestServer(IceTestCase):
    server_port = 10000

    def setUp(self):
        server_props = {
            'MediaServerAdapter.Endpoints': f'tcp -p {self.server_port}',
            'MediaServer.Content': 'test/media',
            'MediaServer.Playlists': 'test/playlists',
            'MediaServer.UsersFile': 'users.json'
        }
        server_endpoint = f'mediaServer1:default -p {self.server_port} -t 500'
        self.create_server(main, server_props)
        self.sut = self.create_proxy(server_endpoint, Spotifice.MediaServerPrx)


class MusicLibraryTestss(TestServer):
    def test_get_all_tracks(self):
        tracks = self.sut.get_all_tracks()
        self.assertEqual(len(tracks), 4)
        self.assertEqual(tracks[0].id, '1s.mp3')

    def test_get_track_info(self):
        track = self.sut.get_track_info('1s.mp3')
        self.assertEqual(track.id, '1s.mp3')
        self.assertEqual(track.title, '1s')

    def test_get_track_info_wrong_track(self):
        with self.assertRaises(Spotifice.TrackError) as cm:
            self.sut.get_track_info('bad-track-id')

        self.assertEqual(cm.exception.item, 'bad-track-id')
        self.assertEqual(cm.exception.reason, 'Track not found')


class PlaylistManagerTests(TestServer):
    def test_get_all_playlists(self):
        playlists = self.sut.get_all_playlists()
        self.assertEqual(len(playlists), 3)  # test-playlist1, 2, 3
        self.assertEqual(playlists[0].id, 'test-playlist1')
        self.assertEqual(playlists[0].name, 'Test Playlist 1')

    def test_get_all_playlists_returns_sorted(self):
        playlists = self.sut.get_all_playlists()
        # Check that playlists are returned in sorted order
        playlist_ids = [p.id for p in playlists]
        self.assertEqual(playlist_ids, sorted(playlist_ids))

    def test_get_playlist(self):
        playlist = self.sut.get_playlist('test-playlist1')
        self.assertEqual(playlist.id, 'test-playlist1')
        self.assertEqual(playlist.name, 'Test Playlist 1')
        self.assertGreater(len(playlist.track_ids), 0)

    def test_get_playlist_contains_all_fields(self):
        playlist = self.sut.get_playlist('test-playlist1')
        # Verify all playlist fields are present
        self.assertIsNotNone(playlist.id)
        self.assertIsNotNone(playlist.name)
        self.assertIsNotNone(playlist.description)
        self.assertIsNotNone(playlist.owner)
        self.assertIsNotNone(playlist.track_ids)
        self.assertEqual(playlist.owner, 'Test Owner')

    def test_get_playlist_track_ids_are_valid(self):
        playlist = self.sut.get_playlist('test-playlist1')
        # Verify track_ids is a list and contains strings
        self.assertIsInstance(playlist.track_ids, list)
        self.assertGreater(len(playlist.track_ids), 0)
        for track_id in playlist.track_ids:
            self.assertIsInstance(track_id, str)

    def test_get_playlist_wrong_playlist(self):
        with self.assertRaises(Spotifice.PlaylistError) as cm:
            self.sut.get_playlist('non-existent-playlist')

        self.assertEqual(cm.exception.item, 'non-existent-playlist')
        self.assertEqual(cm.exception.reason, 'Playlist not found')

    def test_get_playlist_empty_string(self):
        with self.assertRaises(Spotifice.PlaylistError) as cm:
            self.sut.get_playlist('')

        self.assertEqual(cm.exception.item, '')
        self.assertEqual(cm.exception.reason, 'Playlist not found')

    def test_multiple_playlists_loaded(self):
        # Verify all three playlists can be retrieved
        playlist1 = self.sut.get_playlist('test-playlist1')
        playlist2 = self.sut.get_playlist('test-playlist2')
        playlist3 = self.sut.get_playlist('test-playlist3')
        
        self.assertNotEqual(playlist1.id, playlist2.id)
        self.assertNotEqual(playlist2.id, playlist3.id)
        self.assertNotEqual(playlist1.id, playlist3.id)