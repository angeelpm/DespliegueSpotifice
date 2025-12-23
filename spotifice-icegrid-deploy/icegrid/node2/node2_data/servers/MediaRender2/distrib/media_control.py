#!/usr/bin/env python3

import sys
from time import sleep

import Ice

Ice.loadSlice('-I{} spotifice_v2.ice'.format(Ice.getSliceDir()))
import Spotifice  # type: ignore # noqa: E402


def get_proxy(ic, property, cls):
    proxy = ic.propertyToProxy(property)

    for _ in range(5):
        try:
            proxy.ice_ping()
            break
        except Ice.ConnectionRefusedException:
            sleep(0.5)

    object = cls.checkedCast(proxy)
    if object is None:
        raise RuntimeError(f'Invalid proxy for {property}')

    return object

def print_help():
    print("""
        Available commands:
        playlists                  - List every playlist
        load_playlist <id>         - Load a playlist
        tracks                     - List every track on the server 
        load_track <id>            - Load a specific track
        play                       - Play the current track
        pause                      - Pause playback
        stop                       - Stop playback
        next                       - Next track
        previous                   - Previous track
        repeat [on/off]            - Toggle repeat mode
        status                     - Show current status
        help                       - Show help menu
        exit / quit                - Exit the client
        """)
    
    

def main(ic):
    server = get_proxy(ic, 'MediaServer.Proxy', Spotifice.MediaServerPrx)
    render = get_proxy(ic, 'MediaRender.Proxy', Spotifice.MediaRenderPrx)

    print("=== Spotifice Login ===")
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    try:
        stream_manager = server.authenticate(render, username, password)
        print(f"✓ Authenticated as {username}")
        
        user_info = stream_manager.get_user_info()
        print(f"  Name: {user_info.fullname}")
        print(f"  Email: {user_info.email}")
        print(f"  Premium: {'Yes' if user_info.is_premium else 'No'}\n")
    except Spotifice.AuthError as e:
        print(f"✗ Authentication failed: {e.reason}")
        return
    except Exception as e:
        print(f"✗ Error during authentication: {e}")
        return

    render.bind_media_server(server, stream_manager)
    render.stop()

    print("Welcome to Spotifice")
    print("Type 'help' to see available commands.\n")

    while True:
        try:
            cmd = input("spotifice> ").strip()
            if not cmd:
                continue

            parts = cmd.split()
            command = parts[0].lower()

            if command in ("exit", "quit"):
                print("Exiting Spotifice...")
                try:
                    stream_manager.close()
                except Exception as e:
                    print(f"Error closing session: {e}")
                break

            elif command == "help":
                print_help()

            elif command == "playlists":
                playlists = server.get_all_playlists()
                if not playlists:
                    print("No playlists available.")
                else:
                    print("Available playlists:")
                    for p in playlists:
                        print(f"  {p.id} ({len(p.track_ids)} tracks)")

            elif command == "tracks":
                tracks = server.get_all_tracks()
                if not tracks:
                    print("No tracks available.")
                else:
                    for t in tracks:
                        print(f"- {t.id}: {t.title}")

            elif command == "load_playlist":
                if len(parts) < 2:
                    print("Usage: load_playlist <id>")
                    continue
                playlist_id = parts[1]
                render.load_playlist(playlist_id)
                print(f"Playlist '{playlist_id}' loaded.")

            elif command == "load_track":
                if len(parts) < 2:
                    print("Usage: load_track <id>")
                    continue
                track_id = parts[1]
                render.load_track(track_id)
                print(f"Track '{track_id}' loaded.")

            elif command == "play":
                render.play()
                print("Playing...")

            elif command == "pause":
                render.pause()
                print("Playback paused.")

            elif command == "stop":
                render.stop()
                print("Playback stopped.")

            elif command == "next":
                render.next()
                print("Next track.")

            elif command == "previous":
                render.previous()
                print("Previous track.")

            elif command == "repeat":
                if len(parts) < 2:
                    print("Usage: repeat on/off")
                    continue
                value = parts[1].lower() in ["on", "true", "1"]
                render.set_repeat(value)
                print(f"Repeat mode {'enabled' if value else 'disabled'}.")

            elif command == "status":
                status = render.get_status()
                print(f"State: {status.state.name}")
                print(f"Current track: {status.current_track_id}")
                print(f"Repeat: {'ON' if status.repeat else 'OFF'}")

            else:
                print(f"Unknown command: {command}. Type 'help' to see available commands.")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("Usage: media_control.py <config-file>")

    with Ice.initialize(sys.argv[1]) as communicator:
        main(communicator)
