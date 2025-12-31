import subprocess
import time
import re
import threading

def getForegroundApp():
    """
    Get the package name of the currently visible/foreground Android app.
    Uses root privileges to run dumpsys command and parse the output.
    Returns the package name as a string, or empty string if not found.
    """
    dumpsys = subprocess.run(
        ['su','-c','dumpsys activity activities'],  # Run dumpsys command with root
        capture_output=True,
        text=True,
        timeout=2
    )

    visible_app_line = ''

    # Search through dumpsys output for the visible activity
    for line in dumpsys.stdout.splitlines():
        if 'VisibleActivityProcess'.lower() in line.lower():
            visible_app_line += line
            break
    
    # Extract package name using regex (pattern: colon followed by package name)
    search = re.search(
        r':([a-zA-Z.]+)',
        visible_app_line
    )

    package = ''
    if search:
        package = search.group(1)  # Get the matched package name
    
    return package

class App:
    """
    Class to represent an application being tracked for time usage.
    Stores timing information and state for each monitored app.
    """
    def __init__(self, package):
        self.package = package  # Android package name (e.g., com.example.app)
        self.start_time = time.time()  # When tracking started for current session
        self.total_time = 0.0  # Total active time accumulated
        self.isActive = False  # Is app currently in foreground?
        self.isDone = False  # Has app exceeded its time limit?
        self.pause_time = 0  # When app was last paused/backgrounded
        self.total_paused = 0  # Total time app has been paused
        self.banned_start_time = 0  # When ban period started
        self.banned_stop_time = '00:10:00'  # Ban duration after time limit (10 mins)
        self.idle_treshold = '00:05:00'  # Idle time before resetting timer (5 mins)
    
    def reset(self):
        """Reset all timing counters for this app"""
        self.start_time = time.time()
        self.total_time = 0.0
        self.pause_time = 0
        self.total_paused = 0

def monitor(app:App, stop_time):
    """
    Thread function to monitor an app's usage time.
    Continuously checks if app has exceeded its allowed time.
    """
    # Handle pause time if app was previously paused
    if app.pause_time > 0:
        app.total_paused += time.time() - app.pause_time

        formatted = time.strftime(
            '%H:%M:%S',
            time.gmtime(app.total_paused)
        )

        # Reset if app was idle beyond threshold
        if formatted >= app.idle_treshold:
            app.reset()

    # Main monitoring loop
    while app.isActive:
        # Calculate current active time (total time minus paused time)
        app.total_time = time.time() - app.start_time - app.total_paused

        # Format time for comparison with stop_time
        formatted = time.strftime(
            '%H:%M:%S',
            time.gmtime(app.total_time)
        )

        # Check if time limit has been reached
        if formatted >= stop_time:
            print(f'\nTime\'s app. Killing {app.package}')
            # Kill the app process
            subprocess.run(
                [
                    'sudo',
                    'pkill',
                    app.package
                ]
            )
            # Show notification to user
            subprocess.run(
                [
                    'termux-toast',
                    '-b',
                    'black',
                    '-c',
                    'white',
                    'Time\'s Up'
                ]
            )

            app.isDone = True  # Mark as time limit reached
            app.banned_start_time = time.time()  # Start ban period
            app.start_time = 0  # Reset start time

            break
        
        # If not done yet, update pause time for idle tracking
        if not app.isDone:
            app.pause_time = time.time()

def loadBlockList() -> list:
    """
    Load list of package names to monitor from block.txt file.
    Each line should contain one package name.
    Returns list of package names.
    """
    result = []
    with open('block.txt','r') as file:
        for line in file:
            pkg = line.strip()  # Remove whitespace/newlines

            if pkg:  # Only add non-empty lines
                result.append(pkg)
    
    return result

if __name__ == '__main__':
    # Dictionary to store App objects keyed by package name
    queue = {}
    
    # Load initial block list
    block_list = loadBlockList()
    
    # Tracking variables
    current_app = None  # Currently foreground app
    tracking_app = None  # App currently being tracked

    try:
        # Main program loop
        while True:
            print(f'Total thread: {threading.active_count()}')

            # Reload block list (allows dynamic updates without restarting)
            block_list = loadBlockList()            

            # Get current foreground app
            current_app = getForegroundApp()

            # Check if current app is in block list
            if current_app in block_list:

                # If app is already in tracking queue
                if current_app in queue:
                    if not tracking_app:
                        # Start tracking if no app is currently being tracked
                        tracking_app = queue[current_app]
                        
                    else:
                        # If there's already a tracking app
                    
                        if tracking_app.isDone:
                            # If previous app reached time limit
                            tracking_app.isActive = False
                            
                            # Calculate how long it's been banned
                            ban_elapsed = time.time() - tracking_app.banned_start_time
                            ban_elapsed = time.strftime(
                                '%H:%M:%S',
                                time.gmtime(ban_elapsed)
                            )

                            print('LOG:' + ban_elapsed)
                            print('\n\n\n')
                            
                            # Check if ban period is over
                            if ban_elapsed >= tracking_app.banned_stop_time:
                                tracking_app.isDone = False  # Unban the app
                            else:
                                # App is still banned, kill it
                                subprocess.run(
                                    [
                                        'sudo',
                                        'pkill',
                                        tracking_app.package
                                    ]
                                )
                                
                                # Notify user app is still banned
                                subprocess.run(
                                    [
                                        'termux-toast',
                                        '-b',
                                        'black',
                                        '-c',
                                        'white',
                                        'Banned for 30 minutes.'
                                    ]
                                )
                                continue  # Skip to next iteration

                    # If current app matches the one being tracked
                    if current_app.strip().lower() == tracking_app.package.strip().lower():
                        if not tracking_app.isActive:
                            # Start/resume tracking this app
                            if tracking_app.start_time == 0:
                                tracking_app.start_time = time.time()

                            # Show notification that tracking is starting
                            subprocess.run(
                                    [
                                        'termux-toast', '-b','black','-c','white','-g','bottom',
                                        f'Starting from {time.strftime(
                                            '%H:%M:%S',time.gmtime(app.total_time) )}'
                                    ]
                                )
                            
                            # TODO - Get stop time from user using termux dialog
                            # Currently hardcoded to 30 minutes
                            tracking_app.isActive = True
                            t = threading.Thread(
                                target=monitor,
                                args=(app,'00:30:00')  # Hardcoded 30 minute limit
                            )
                            t.start()
                    else:
                        # Different app came to foreground, pause current tracking
                        tracking_app.isActive = False
                        tracking_app = queue[current_app]  # Switch to new app
                else:
                    # First time seeing this app, create new App object
                    app = App(current_app)
                    queue[current_app] = app
                    tracking_app = app

                # Display current tracking status
                formatted = time.strftime(
                    '%H:%M:%S',
                    time.gmtime(tracking_app.total_time)
                )
                msg = f'Tracking: {tracking_app.package}\n'
                msg += f'Current time: {formatted}'

                print(f'\n{msg}')
            else:
                # Current app is not in block list, pause any active tracking
                if tracking_app:
                    tracking_app.isActive = False
            
            # Wait before next check
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        print('\n\nQuiting...')