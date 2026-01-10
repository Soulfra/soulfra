#!/usr/bin/env python3
"""
ASCII Movie Player - Pure Python Stdlib

Terminal-based media player for ASCII art animations using curses.
Like QuickTime/VLC but for ASCII art!

Usage:
    python3 ascii_player.py frame1.bmp frame2.bmp frame3.bmp
    python3 ascii_player.py static/generated/test_*.bmp

Controls:
    Space:    Play/Pause
    ← →:      Previous/Next frame
    [ ]:      Slower/Faster playback
    Q:        Quit
    R:        Restart from beginning

Like:
- iMovie for terminal
- Windows Media Player for ASCII art
- QuickTime but retro

Requires:
- curses (stdlib)
- image_to_ascii.py for conversion
"""

import curses
import time
import sys
import os
import glob


def load_ascii_frames(filepaths, width=80):
    """
    Load image files and convert to ASCII frames

    Args:
        filepaths: List of image file paths
        width: ASCII art width

    Returns:
        list[str]: ASCII art frames
    """
    from image_to_ascii import image_to_ascii

    frames = []

    print("Loading frames...")
    for i, filepath in enumerate(filepaths):
        print(f"  [{i+1}/{len(filepaths)}] {os.path.basename(filepath)}")
        try:
            frame = image_to_ascii(filepath, width=width, charset='detailed')
            frames.append(frame)
        except Exception as e:
            print(f"  ⚠️  Error loading {filepath}: {e}")

    print(f"✅ Loaded {len(frames)} frames")
    return frames


def ascii_player(frames, fps=10):
    """
    Play ASCII art frames in terminal using curses

    Args:
        frames: List of ASCII art strings
        fps: Frames per second (default: 10)

    Controls implemented in curses loop
    """
    if not frames:
        print("❌ No frames to play!")
        return

    def main(stdscr):
        # Setup
        curses.curs_set(0)  # Hide cursor
        stdscr.clear()
        stdscr.nodelay(False)  # Blocking input initially

        # State
        current_frame = 0
        playing = False
        frame_delay = 1.0 / fps

        # UI colors
        try:
            curses.start_color()
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        except:
            pass

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            # Draw current frame
            frame_lines = frames[current_frame].split('\n')

            for i, line in enumerate(frame_lines):
                if i >= height - 4:  # Leave room for UI
                    break
                try:
                    stdscr.addstr(i, 0, line[:width-1])
                except:
                    pass  # Ignore if line too long

            # Draw UI/status bar
            status_y = min(len(frame_lines) + 1, height - 3)

            try:
                # Status line
                status = f" Frame {current_frame + 1}/{len(frames)} "
                if playing:
                    status += "▶ Playing"
                else:
                    status += "⏸ Paused"

                status += f" | FPS: {fps:.1f} "

                stdscr.addstr(status_y, 0, "─" * min(width - 1, 80), curses.A_DIM)
                stdscr.addstr(status_y + 1, 0, status, curses.color_pair(2) | curses.A_BOLD)

                # Controls help
                controls = "Space:Play/Pause  ←→:Prev/Next  []:Speed  R:Restart  Q:Quit"
                stdscr.addstr(status_y + 2, 0, controls, curses.A_DIM)
            except:
                pass

            stdscr.refresh()

            # Handle input
            stdscr.nodelay(playing)  # Non-blocking if playing
            stdscr.timeout(int(frame_delay * 1000) if playing else -1)

            try:
                key = stdscr.getch()
            except:
                key = -1

            # Process key
            if key == ord(' '):  # Space
                playing = not playing

            elif key == curses.KEY_LEFT:  # ← Previous
                current_frame = max(0, current_frame - 1)
                playing = False

            elif key == curses.KEY_RIGHT:  # → Next
                current_frame = min(len(frames) - 1, current_frame + 1)
                playing = False

            elif key == ord('['):  # Slower
                fps = max(1, fps - 1)
                frame_delay = 1.0 / fps

            elif key == ord(']'):  # Faster
                fps = min(30, fps + 1)
                frame_delay = 1.0 / fps

            elif key == ord('r') or key == ord('R'):  # Restart
                current_frame = 0
                playing = False

            elif key == ord('q') or key == ord('Q'):  # Quit
                break

            # Auto-advance if playing
            if playing:
                current_frame = (current_frame + 1) % len(frames)

    # Run curses wrapper
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass


def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("ASCII Movie Player - Pure Python Stdlib")
        print("=" * 60)
        print()
        print("Usage: python3 ascii_player.py <image1> [image2] [image3] ...")
        print()
        print("Examples:")
        print("  python3 ascii_player.py test_shapes.bmp test_gradient.bmp")
        print("  python3 ascii_player.py static/generated/test_*.bmp")
        print("  python3 ascii_player.py frame*.bmp")
        print()
        print("Controls:")
        print("  Space    Play/Pause")
        print("  ← →      Previous/Next frame")
        print("  [ ]      Slower/Faster playback")
        print("  R        Restart from beginning")
        print("  Q        Quit")
        print()
        sys.exit(1)

    # Get file paths (expand globs)
    filepaths = []
    for arg in sys.argv[1:]:
        if '*' in arg or '?' in arg:
            # Glob pattern
            filepaths.extend(glob.glob(arg))
        else:
            filepaths.append(arg)

    # Filter existing files
    filepaths = [f for f in filepaths if os.path.exists(f)]

    if not filepaths:
        print("❌ No valid image files found!")
        sys.exit(1)

    print(f"Found {len(filepaths)} files")
    print()

    # Load frames
    frames = load_ascii_frames(filepaths, width=80)

    if not frames:
        print("❌ Failed to load any frames!")
        sys.exit(1)

    print()
    print("🎬 Starting ASCII Movie Player...")
    print("   Press Space to play, Q to quit")
    print()

    time.sleep(1)  # Give user time to read

    # Play!
    ascii_player(frames, fps=10)

    print()
    print("✅ Thanks for watching!")


if __name__ == '__main__':
    main()
