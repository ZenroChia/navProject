import sys
import select
import termios
import tty
import time
from djitellopy import Tello

def get_key():
        """Get a single key press without blocking."""
        if select.select([sys.stdin], [], [], 0.5) == ([sys.stdin], [], []):
            # Read a single character from stdin
            key = sys.stdin.read(1).lower()
            
            if key == '\x1b':

                time.sleep(0.03)  # Allow time for escape sequence
                if select.select([sys.stdin], [], [], 0.1)[0]: 
                    bracket = sys.stdin.read(1)
                    if bracket == '[' and select.select([sys.stdin], [], [], 0.1)[0]:
                        arrow = sys.stdin.read(1)
                        arrow_map = {
                            'A': 'up',  # Up arrow
                            'B': 'down',  # Down arrow
                            'C': 'right',  # Right arrow
                            'D': 'left'   # Left arrow
                        }
                        return arrow_map.get(arrow, 'unknown_key')
                return 'incomplete'  
            elif key == '[': 
                # Ignore the alphebet key character that follows
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    sys.stdin.read(1)
                return 'ignored_key'  
            else: 
                return key  # Regular key press
        return None

def test_alternative_keyboard():
    print("Testing alternative keyboard input...")
    print("Press 'w' key - you should see detection")
    print("Press 'q' to quit")
    
    # Save original terminal settings
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        # Set terminal to raw mode for immediate key detection
        tty.setraw(sys.stdin)
        
        while True:
            # Check if key is available (non-blocking)
            key = get_key()
                
            if key == 'w':
                print("\rW key detected! ✅             ")
            elif key == 'q':
                print("\rQ key detected - exiting       ")
                break
            elif key == '\x1b':  # ESC
                print("\rESC detected - exiting         ")
                break
            elif key == 'up': 
                print("\rUp arrow detected! ⬆️          ")
            elif key == 'down':
                print("\rDown arrow detected! ⬇️        ")
            elif key == 'left':
                print("\rLeft arrow detected! ⬅️        ")
            elif key == 'right':
                print("\rRight arrow detected! ➡️       ")
            else:
                print(f"\rKey pressed: '{key}'           ")
        else:
            # Show that we're listening
            print("\rListening for keys...          ", end='', flush=True)
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        print("\nTest complete!")

def main(): 
    tello = Tello()
    try:
        print("Connecting to Tello drone...")
        tello.RESPONSE_TIMEOUT = 7
        tello.connect(wait_for_state=False)
        print("Drone connected successfully!")

        try:
            battery_response = tello.send_command_with_return("battery?", timeout=5)
            print(f"✅ Battery: {battery_response}%")
        except Exception as e:
            print(f"❌ Battery command failed: {e}")
        
        print("Successfully connected to drone!")
        
    except Exception as e:
        print(f"Failed to connect to drone: {e}")
        return False
    
    print("Taking off...")
    tello.takeoff()
    time.sleep(2)  # Give time for takeoff to complete
    
    print("Moving up 30cm...")
    tello.move_up(118)  # Fix: Use 30cm instead of 5cm
    time.sleep(2)
    
    print("Moving forward 50cm...")
    tello.move_forward(50)  # Fix: Use 50cm instead of 10cm
    time.sleep(2)
    
    print("Rotating 180 degrees...")
    tello.rotate_clockwise(180)
    time.sleep(2)
    
    print("Moving forward 50cm...")
    tello.move_forward(50)  # Fix: Use 50cm instead of 10cm
    time.sleep(2)
    
    print("Landing...")
    tello.land()

if __name__ == "__main__":
    main()


'''
OK now that the basic mapping functionality is done, what about playback? Like since I have the processed json file now for each waypoint, any ideas on how do I kickstart my playback by reading the json file and storing it in memory first so that I could use it let the drone naviate from any waypoint to any selected waypoint. My idea is that I need to have something (probably a class instance) to store the drone's location in its current context (current waypoints json file, since different json file probably mean different space's waypoints, the drone's location could be identified as the id in the current waypoint json file's context with a reference to their own names). The drone always starts at the "id": "WP_001", "name": "START", which indicates the starting point at each waypoint file (always will be). And then once the waypoint file is read, it will then store it structurally in memory for quick access. Then according to the waypoint names we have in the waypoint file, display a list of waypoints (execpt for the current waypoint the drone is at) that the drone could navigate to and let the user select which one to let the drone navigate to. After that, when the user selects a waypoint, the drone then acknowledges this and according to the memory, read all the individual navigation movements from the current waypoint (where the drone is at) to the selected waypoint. If the reading direction from the current waypoint to the selected waypoint is in a normal order (top-down order) (note that the waypoint files lists the waypoints in a topdown order, and that each waypoint on the top comes before the waypoints below, so in order for the drone to navigate to a selected waypoint located at the bottom part of the file from the waypoint located at the top part of the file, the drone needs to read all the movements to go to the next bottom waypoint to go to that waypoint first before moving on to the next waypoint until the selected destination waypoint is reached. no shortcuts.), the drone follows the instruction accordingly; if it is in a reverse order (bottom-up order, where the drone has to navigate from the waypoints located at the bottom part of the waypoints file to the waypoints located at the top of the waypoints file), the movement instructions would have to be in reversed direction (both type move and lift), for the move, reverse the yaw angle and for the lift, reverse the lift direction. And then once it execeutes successfully and reaches the intended destination, it prints a successful message and then list down all the waypoints (execpt for the new current waypoint the drone is at) the drone could move to from that waypoint.'''