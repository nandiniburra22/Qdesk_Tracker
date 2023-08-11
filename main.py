# main.py
from features.active_windows import get_active_windows
from features.chrome_tabs import get_chrome_tabs
from features.current_active_window import get_current_active_window
from features.screenshot import take_screenshot
from features.screen_recorder import record_screen
from features.camera_recorder import record_camera
from features.log import log_to_csv
from pynput import keyboard
import time
import threading
import sys

# List to store the captured keyboard inputs
captured_keyboard_inputs = []


def on_press(key):
    try:
        # Append the captured key to the list
        captured_keyboard_inputs.append(str(key))
    except Exception as e:
        print(f"Error capturing keyboard input: {e}")


def track_activity():
    print("Script started.")
    log_to_csv("Script started", " ")
    # Store the script start time
    script_start_time = time.time()

    current_window = get_current_active_window()
    if current_window:
        print(
            f"Currently opened window at {time.strftime('%Y-%m-%d %H:%M:%S')}: {current_window}")
        log_to_csv("Currently opened window", current_window)

    prev_active_windows = set(get_active_windows())
    prev_chrome_tabs = set(get_chrome_tabs())

    # Variable to keep track of whether the desktop was displayed
    desktop_displayed = False

    # Dictionary to store the start time for each opened window/tab
    start_times = {}
    # Dictionary to store the number of times a window/tab is visited
    times_visited = {}

    # Flag to track if script start time has been recorded
    script_start_recorded = False

    # Create a listener for keyboard inputs
    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.start()

    try:
        # Start separate threads for taking screenshots, screen recording, and camera recording
        screenshot_thread = threading.Thread(target=take_screenshot)
        screenshot_thread.daemon = True
        screenshot_thread.start()

        screen_record_thread = threading.Thread(target=record_screen)
        screen_record_thread.daemon = True
        screen_record_thread.start()

        camera_record_thread = threading.Thread(target=record_camera)
        camera_record_thread.daemon = True
        camera_record_thread.start()

        while True:
            active_windows = set(get_active_windows())
            new_windows = active_windows - prev_active_windows
            closed_windows = prev_active_windows - active_windows

            for window in closed_windows:
                # Calculate the duration if the window was previously opened
                duration = "-"
                if window in start_times:
                    duration = int(time.time() - start_times[window])
                    del start_times[window]

                if not script_start_recorded:
                    # Record the script's start time as the duration for the first window closed
                    duration = int(time.time() - script_start_time)
                    script_start_recorded = True

                # Log captured keyboard inputs along with the window close event
                keyboard_inputs = ", ".join(captured_keyboard_inputs)
                print(
                    f"Window closed at {time.strftime('%Y-%m-%d %H:%M:%S')}: {window} (Duration: {duration} seconds)")
                log_to_csv("Window closed", window, duration,
                           times_visited.get(window, "-"), keyboard_inputs)
                captured_keyboard_inputs.clear()  # Clear the captured inputs list

            # Check if any window was closed before checking for the desktop display
            if not active_windows:
                # Display the desktop message only if it wasn't displayed before
                if not desktop_displayed:
                    print(
                        f"Displaying desktop at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                    log_to_csv("Displaying desktop", " ")
                    desktop_displayed = True
            else:
                desktop_displayed = False

            for window in new_windows:
                print(
                    f"New window opened at {time.strftime('%Y-%m-%d %H:%M:%S')}: {window}")
                # Increment the number of times a window is visited
                times_visited[window] = times_visited.get(window, 0) + 1
                log_to_csv("New window opened", window,
                           times_visited=times_visited[window])
                # Store the start time when a new window is opened
                start_times[window] = time.time()

            prev_active_windows = active_windows

            chrome_tabs = set(get_chrome_tabs())
            new_tabs = chrome_tabs - prev_chrome_tabs
            closed_tabs = prev_chrome_tabs - chrome_tabs

            for tab in closed_tabs:
                # Calculate the duration if the tab was previously opened
                duration = "-"
                if tab in start_times:
                    duration = int(time.time() - start_times[tab])
                    del start_times[tab]

                print(
                    f"Tab closed at {time.strftime('%Y-%m-%d %H:%M:%S')}: {tab} (Duration: {duration} seconds)")
                log_to_csv("Tab closed", tab, duration)

            for tab in new_tabs:
                print(
                    f"New tab opened at {time.strftime('%Y-%m-%d %H:%M:%S')}: {tab}")
                log_to_csv("New tab opened", tab)
                # Store the start time when a new tab is opened
                start_times[tab] = time.time()

            # Terminate the script if the elapsed time exceeds 300 seconds (5 minutes)
            if time.time() - script_start_time > 300:
                print("Script has run for 300 seconds. Exiting...")
                sys.exit()

            # Wait for a very short period (0 seconds) can increase time to avoid excessive resource usage
            time.sleep(0)
    except KeyboardInterrupt:
        for window in prev_active_windows:
            duration = int(
                time.time() - start_times.get(window, script_start_time))
            log_to_csv("Window/tab closed", window, duration,
                       times_visited.get(window, "-"))
            # Log captured keyboard inputs along with the window close event
            keyboard_inputs = ", ".join(captured_keyboard_inputs)
            log_to_csv("Window closed", window, duration,
                       times_visited.get(window, "-"), keyboard_inputs)
        captured_keyboard_inputs.clear()  # Clear the captured inputs list
        log_to_csv("Activity tracking stopped", " ")
        print("Activity tracking stopped.")


if __name__ == "__main__":
    track_activity