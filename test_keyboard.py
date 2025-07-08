#!/usr/bin/env python3
import json
import time
import threading
import uuid
import sys
import select
import termios
import tty
from datetime import datetime
from djitellopy import Tello


class RealTimeDroneController:
    def __init__(self):
        """Initialize the drone controller with recording capabilities."""
        self.tello = Tello()
        self.is_connected = False
        self.is_flying = False
        self.movement_speed = 30  # cm/s
        self.rotation_speed = 30  # degrees/s
        
        # Movement tracking
        self.current_movement = None
        self.waypoints = []
        self.current_waypoint_movements = []
        self.waypoint_counter = 0
        
        # Control flags
        self.active_keys = set()
        self.add_movement = False
        
        # JSON file for storing movement data
        self.data_file = f"drone_movements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
    def connect_drone(self):
        """Connect to the Tello drone."""
        try:
            print("Connecting to Tello drone...")
            self.tello.RESPONSE_TIMEOUT = 7
            self.tello.connect(wait_for_state=False)
            print("Drone connected successfully!")

            try:
                battery_response = self.tello.send_command_with_return("battery?", timeout=5)
                print(f"✅ Battery: {battery_response}%")
            except Exception as e:
                print(f"❌ Battery command failed: {e}")

            # print(f"Battery level: {self.tello.get_battery()}%")
            
            self.is_connected = True
            print("Successfully connected to drone!")
            return True
        except Exception as e:
            print(f"Failed to connect to drone: {e}")
            return False
    
    def takeoff(self):
        """Take off the drone and mark starting waypoint."""
        if not self.is_connected:
            print("Drone not connected!")
            return False
            
        try:
            print("Taking off...")
            self.tello.takeoff()
            self.is_flying = True
            time.sleep(2)  # Wait for stabilization
            
            # Mark starting waypoint automatically
            self.mark_waypoint("START", auto_generated=True)
            print("Drone ready for control!")
            return True
        except Exception as e:
            print(f"Takeoff failed: {e}")
            return False
    
    def land(self):
        """Land the drone safely."""
        if self.is_flying:
            try:
                print("Landing drone...")
                self.tello.land()
                self.is_flying = False
                print("Drone landed successfully!")
            except Exception as e:
                print(f"Landing failed: {e}")
    
    def get_drone_state(self):
        """Get current drone state including position and yaw."""
        try:
            state = {}

            # Get yaw (facing direction)
            try:
                attitude_str = self.tello.send_command_with_return("attitude?", timeout=3)
                print(f"Raw attitude response: '{attitude_str}'")  # Debug line
                
                # Parse attitude string like "pitch:0;roll:0;yaw:45;"
                state['yaw'] = 0  # Default value
                if attitude_str and ':' in attitude_str:
                    attitude_parts = attitude_str.split(';')
                    for part in attitude_parts:
                        if part.strip() and 'yaw:' in part:
                            try:
                                yaw_value = part.split(':')[1].strip()
                                if yaw_value:
                                    state['yaw'] = int(yaw_value)
                                    break
                            except (ValueError, IndexError) as e:
                                print(f"⚠️  Failed to parse yaw from '{part}': {e}")
                                continue
            except Exception as e:
                print(f"⚠️  Attitude query failed: {e}")
                state['yaw'] = 0

            # Get height
            try:
                height_str = self.tello.send_command_with_return("height?", timeout=3)
                # Height returns like "10dm" (decimeters), convert to cm
                height_dm = int(height_str.replace('dm', ''))
                state['height'] = height_dm * 10  # Convert dm to cm
            except Exception as e:
                print(f"⚠️  Height query failed: {e}")
                state['height'] = 0
            
            # Get battery level
            try:
                battery_str = self.tello.send_command_with_return("battery?", timeout=3)
                state['battery'] = int(battery_str)
            except Exception as e:
                print(f"⚠️  Battery query failed: {e}")
                state['battery'] = 0
            

            return state
        except Exception as e:
            print(f"Error getting drone state: {e}")
            return {'height': 0, 'yaw': 0, 'battery': 0}

    def start_movement(self, direction, movement_type="move"):
        """Start a movement in the specified direction."""
        print(f"🚀 start_movement called: {movement_type} {direction}")  # Debug
        
        if self.current_movement is not None:
            print("⚠️  Already moving, ignoring new movement")
            return  # Already moving
        
        try: 
            drone_state = self.get_drone_state()
            start_yaw = drone_state.get('yaw', 0)  # Default to 0 if not available
        except Exception as e:
            print(f"Error getting drone state: {e}")
            start_yaw = 0

        self.current_movement = {
            'type': movement_type,
            'direction': direction,
            'start_time': time.time(),
            'start_yaw': start_yaw,
        }
        
        print(f"📝 Created movement record: {self.current_movement}")  # Debug
        
        # Start the actual drone movement
        try:
            if movement_type == "move":
                self.add_movement = True

                print(f"📡 Sending RC control for {direction}")  # Debug
                if direction == "forward":
                    self.tello.send_rc_control(0, self.movement_speed, 0, 0)
                elif direction == "backward":
                    self.tello.send_rc_control(0, -self.movement_speed, 0, 0)
                elif direction == "left":
                    self.tello.send_rc_control(-self.movement_speed, 0, 0, 0)
                elif direction == "right":
                    self.tello.send_rc_control(self.movement_speed, 0, 0, 0)
                print(f"✅ RC control sent for {direction}")  # Debug
                    
            elif movement_type == "lift":
                self.add_movement = True

                print(f"📡 Sending RC control for lift {direction}")  # Debug
                if direction == "up":
                    self.tello.send_rc_control(0, 0, self.movement_speed, 0)
                elif direction == "down":
                    self.tello.send_rc_control(0, 0, -self.movement_speed, 0)
                print(f"✅ RC control sent for lift {direction}")  # Debug
                    
            elif movement_type == "rotate":
                self.add_movement = False

                print(f"📡 Sending RC control for rotate {direction}")  # Debug
                if direction == "anticlockwise":
                    self.tello.send_rc_control(0, 0, 0, -self.rotation_speed)
                elif direction == "clockwise":
                    self.tello.send_rc_control(0, 0, 0, self.rotation_speed)
                print(f"✅ RC control sent for rotate {direction}")  # Debug
                    
        except Exception as e:
            print(f"❌ Error starting movement: {e}")
            import traceback
            traceback.print_exc()
            self.current_movement = None
    
    def stop_movement(self):
        """Stop current movement and record the event."""
        if self.current_movement is None:
            return
        
        if not self.add_movement:
            print("Stopping rotation movement...")
            # Stop drone rotation
            try:
                self.tello.send_rc_control(0, 0, 0, 0)
            except Exception as e:
                print(f"Error stopping rotation movement: {e}")
                
            self.current_movement = None
            return
        
        # Stop drone movement
        try:
            self.tello.send_rc_control(0, 0, 0, 0)
        except Exception as e:
            print(f"Error stopping movement: {e}")
        
        # Calculate movement duration and distance
        end_time = time.time()
        duration = end_time - self.current_movement['start_time']
        
        # Calculate distance moved
        distance = self.movement_speed * duration  # cm
        
        # Create movement event record
        movement_event = {
            'id': str(uuid.uuid4()),
            'type': self.current_movement['type'],
            'direction': self.current_movement['direction'],
            'distance': round(distance, 2),
            'start_yaw': self.current_movement['start_yaw'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to current waypoint movements
        self.current_waypoint_movements.append(movement_event)
        
        print(f"Recorded {movement_event['type']} {movement_event['direction']} at {movement_event['start_yaw']} degree(s): "
              f"{movement_event['distance']:.1f}cm")
        
        self.current_movement = None
    
    def mark_waypoint(self, name=None, auto_generated=False):
        """Mark a waypoint and save current movement cluster."""
        if not auto_generated and not name:
            name = input("Enter waypoint name: ").strip()
            if not name:
                name = f"Waypoint_{self.waypoint_counter + 1}"
        
        self.waypoint_counter += 1
        waypoint_id = f"WP_{self.waypoint_counter:03d}"
        
        waypoint = {
            'id': waypoint_id,
            'name': name or f"Waypoint_{self.waypoint_counter}",
            'movements_to_here': self.current_waypoint_movements.copy()
        }
        
        self.waypoints.append(waypoint)
        
        print(f"Waypoint marked: {waypoint['name']} (ID: {waypoint_id})")
        print(f"Movements recorded: {len(self.current_waypoint_movements)} events")
        
        # Reset movements for next waypoint cluster
        self.current_waypoint_movements = []
    
    def save_to_json(self):
        """Save all waypoints and movements to JSON file."""
        processed_waypoints = []
        for waypoint in self.waypoints: 
            processed_movements = []

            # Movement type is either 'move', or 'lift' only
            for movement in waypoint['movements_to_here']:
                if movement['type'] == 'move':
                    yaw = movement['start_yaw']
                    if movement['direction'] == 'forward':
                        yaw += 0
                    elif movement['direction'] == 'backward':
                        yaw += 180
                    elif movement['direction'] == 'left':
                        yaw -= 90
                    elif movement['direction'] == 'right':
                        yaw += 90
                    
                    # Normalize yaw to -180 to 180 range
                    if yaw > 180: 
                        yaw -= 360
                    elif yaw < -180:
                        yaw += 360
                    
                    processed_movement = {
                        'id': movement['id'],
                        'type': movement['type'],
                        'yaw': yaw, 
                        'distance': movement['distance'],
                        'timestamp': movement['timestamp']
                    }

                    processed_movements.append(processed_movement)
                
                else: 
                    # For 'lift' movements, we can just record the type distance and direction
                    processed_movement = {
                        'id': movement['id'],
                        'type': movement['type'],
                        'direction': movement['direction'],
                        'distance': movement['distance'],
                        'timestamp': movement['timestamp']
                    }
                    processed_movements.append(processed_movement)

            processed_waypoint = {
                'id': waypoint['id'],
                'name': waypoint['name'],
                'movements_to_here': processed_movements
            }

            processed_waypoints.append(processed_waypoint)

        data = {
            'session_info': {
                'total_waypoints': len(self.waypoints),
                'total_movements': sum(len(wp['movements_to_here']) for wp in self.waypoints)
            },
            'waypoints': processed_waypoints
        }
        
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Data saved to {self.data_file}")
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def get_key(self):
        """Get a single key press without blocking."""
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1).lower()
        return None

    def handle_keypress(self):
        """Handle keyboard input for drone control using termios."""
        if not self.is_flying:
            return
        
        # Save original terminal settings
        old_settings = termios.tcgetattr(sys.stdin)
        
        try:
            # Set terminal to raw mode for immediate key detection
            tty.setraw(sys.stdin)
            
            activeMovementKey = None
            x_pressed = False
            last_battery_check = 0
            
            print("🎮 Keyboard controls active!")
            print("W/A/S/D to move, X for waypoint, Q or ESC to exit")
            
            while self.is_flying:
                # Battery check every 5 seconds
                current_time = time.time()
                if current_time - last_battery_check > 5:
                    try:
                        battery_str = self.tello.send_command_with_return("battery?", timeout=5)
                        battery = int(battery_str)
                        if battery < 20:
                            print(f"\r⚠️  Low battery ({battery}%)               ")
                            if battery < 10:
                                print("\r❗ CRITICAL: Battery too low, landing...")
                                break
                        last_battery_check = current_time
                    except Exception as e:
                        print(f"\rError checking battery: {e}")
                
                # Get key input
                key = self.get_key()
                
                if key:
                    print(f"\r🎮 Key: '{key}'                    ")
                    
                    if key == 'q' or key == '\x1b':  # 'q' or ESC
                        print("\r--- Finishing mapping session ---")
                        break
                    elif key == 'x' and not x_pressed:
                        if self.current_movement:
                            self.stop_movement()
                        activeMovementKey = None
                        print("\r--- Marking Waypoint ---")
                        self.mark_waypoint()
                        x_pressed = True
                    elif key in ['w', 'a', 's', 'd']:
                        if activeMovementKey != key:
                            # Stop previous movement
                            if activeMovementKey:
                                self.stop_movement()
                            
                            # Start new movement
                            activeMovementKey = key
                            print(f"\r🚀 Starting movement: {key}        ")
                            
                            if key == 'w':
                                self.start_movement('forward', 'move')
                            elif key == 's':
                                self.start_movement('backward', 'move')
                            elif key == 'a':
                                self.start_movement('left', 'move')
                            elif key == 'd':
                                self.start_movement('right', 'move')
                    else:
                        # Stop current movement on space or other keys
                        if activeMovementKey:
                            print(f"\r🛑 Stopping movement              ")
                            self.stop_movement()
                            activeMovementKey = None
                        x_pressed = False
                else:
                    # No key pressed - reset x_pressed flag
                    x_pressed = False
                
                time.sleep(0.05)  # Fast responsive loop
                
        except Exception as e:
            print(f"\rError in keyboard handling: {e}")
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            print("\r🎮 Keyboard controls ended            ")
    
    def display_controls(self):
        """Display control instructions."""
        print("\n" + "="*50)
        print("REAL-TIME DRONE CONTROL")
        print("="*50)
        print("MOVEMENT CONTROLS:")
        print("  W Key          - Move Forward")
        print("  S Key          - Move Backward")
        print("  A Key          - Move Left")
        print("  D Key          - Move Right")
        print("  ↑ Arrow Key    - Move Up")
        print("  ↓ Arrow Key    - Move Down") 
        print("  ← Arrow Key    - Rotate Left (Anticlockwise)")
        print("  → Arrow Key    - Rotate Right (Clockwise)")
        print("\nWAYPOINT CONTROLS:")
        print("  X Key          - Mark Waypoint")
        print("  ESC Key        - Finish & Land")
        print("\nNOTES:")
        print("- Hold key to move, release to stop")
        print("- Only one movement/action at a time")
        print("- All movements are recorded automatically")
        print("="*50)
        print()
    
    def run(self):
        """Main control loop."""
        self.display_controls()
        
        # Connect and takeoff
        if not self.connect_drone():
            print("Failed to connect to drone. Exiting...")
            return
        
        if not self.takeoff():
            print("Failed to take off. Exiting...")
            return
        
        # Set up keyboard listener
        print("Starting keyboard control... Press ESC to exit")
        
        try:
            self.handle_keypress()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
        
        finally:
            # Cleanup
            print("🧹 Starting cleanup...")
            
            if self.current_movement:
                self.stop_movement()
            
            # Mark final waypoint if there are pending movements
            if self.current_waypoint_movements:
                self.mark_waypoint("END", auto_generated=True)
            
            print("Landing drone...")
            self.land()

            try:
                self.tello.end()
            except:
                pass

            # Save data to JSON file
            self.save_to_json()
                
            print(f"\nSession complete! Data saved to: {self.data_file}")
            print("✅ Program finished - safe to close terminal")


def main():
    """Main function to start the drone control system."""
    controller = RealTimeDroneController()
    
    try:
        controller.run()
    except Exception as e:
        print(f"Error during execution: {e}")
        if controller.is_flying:
            controller.land()


if __name__ == "__main__":
    main()


'''
You're absolutely correct! The keyboard.is_pressed() function needs to access the raw input devices (/dev/input/event*), not terminal input. Let me run some diagnostics to see what's blocking it.

Interesting! The /dev/input/ directory doesn't exist on your system. This explains why keyboard.is_pressed() isn't working. Let me check what input system your Linux distribution uses:

Aha! You're running on WSL2 (Windows Subsystem for Linux)! This is why keyboard.is_pressed() doesn't work. WSL2 doesn't have direct access to hardware input devices like /dev/input/event* because it's running inside Windows.

'''