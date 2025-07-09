#!/usr/bin/env python3
import os
import glob
import sys
from typing import Optional

import select
from typing import Optional
from waypoint_navigation import WaypointNavigationManager

class NavigationInterface:
    """User interface for waypoint navigation."""
    
    def __init__(self):
        self.nav_manager = WaypointNavigationManager()
        self.is_running = True
    
    def run(self, drone_instance=None, vertical_factor=1.0):
        """Run the navigation interface."""
        try:
            if drone_instance is None:
                print("❌ No drone instance provided. Please initialize the drone first.")
                return
            
            print("\n🧭 WAYPOINT NAVIGATION SYSTEM")
            print("=" * 50)
            
            # Load waypoint file
            if not self._load_waypoint_file(drone_instance=drone_instance):
                return
            
            # Main navigation loop
            self._navigation_loop(drone_instance=drone_instance, vertical_factor=vertical_factor)
            
        except KeyboardInterrupt:
            print("\n🛑 Navigation interrupted by user")
        except Exception as e:
            print(f"\n❌ Navigation error: {e}")
        finally:
            drone_instance.send_rc_control(0, 0, 0, 0)  # Stop any ongoing movement
            print("\n👋 Navigation system closed")
    
    def _load_waypoint_file(self, drone_instance=None) -> bool:
        """Load waypoint file with user selection."""
        # Find available waypoint files
        waypoint_files = self._find_waypoint_files()
        
        if not waypoint_files:
            print("❌ No waypoint files found. Please run mapping mode first.")
            return False
        
        if len(waypoint_files) == 1:
            # Only one file, load it automatically
            selected_file = waypoint_files[0]
            print(f"📁 Found waypoint file: {selected_file}")
        else:
            # Multiple files, let user choose
            selected_file = self._select_waypoint_file(waypoint_files, drone_instance=drone_instance)
            if not selected_file:
                return False
        
        return self.nav_manager.load_waypoint_file(selected_file)
    
    def _find_waypoint_files(self) -> list:
        """Find all available waypoint JSON files."""
        pattern = "drone_movements_*.json"
        files = glob.glob(pattern)
        return sorted(files, reverse=True)  # Newest first
    
    def _select_waypoint_file(self, files: list, drone_instance=None) -> Optional[str]:
        """Let user select which waypoint file to use."""
        print(f"\n📁 Found {len(files)} waypoint files:")
        print("-" * 50)
        
        for i, file in enumerate(files, 1):
            # Extract timestamp from filename for better display
            timestamp = file.replace('drone_movements_', '').replace('.json', '')
            print(f"  {i}. {file} (Created: {timestamp})")
        
        while True:
            try:
                try:
                    battery_str = drone_instance.send_command_with_return("battery?", timeout=5)
                    battery = int(battery_str)
                    if battery < 20:
                        print(f"\r⚠️  Low battery ({battery}%)               ")
                        if battery < 10:
                            print("\r❗ CRITICAL: Battery too low, landing...")
                            return None
                except Exception as e:
                    print(f"\rError checking battery: {e}")
                    return None
                
                prompt = f"\nSelect waypoint file (1-{len(files)}) or 'q' to quit: "

                print(prompt, end='', flush=True)

                # Wait for input with 5-second timeout
                ready, _, _ = select.select([sys.stdin], [], [], 5)

                if ready:
                    choice = sys.stdin.readline().strip().lower()
                    if choice == 'q':
                        return None
                    
                    try: 
                        file_index = int(choice) - 1
                        if 0 <= file_index < len(files):
                            return files[file_index]
                        else:
                            print(f"❌ Invalid choice. Please enter 1-{len(files)}")
                    except ValueError:
                        print("❌ Invalid input. Please enter a valid option.")
                else:
                    # No input received within timeout
                    print("\r" + " " * 50 + "\r", end='')
                    continue
                    
            except Exception as e:
                print(f"❌ Error reading input: {e}")
                return None
    
    def _navigation_loop(self, drone_instance=None, vertical_factor=1.0):
        """Main navigation interaction loop."""
        loop_count = 0
        while self.is_running:
            try:
                # Show current position and options
                destinations = self.nav_manager.print_navigation_options()
                
                if not destinations:
                    print("ℹ️  No other waypoints to navigate to.")
                    break
                
                # Get user choice
                choice = self._get_navigation_choice(destinations, loop_count, drone_instance=drone_instance)
                
                if choice == 'quit':
                    break
                elif choice == 'reload':
                    if self._load_waypoint_file(drone_instance=drone_instance):
                        continue
                    else:
                        break
                elif isinstance(choice, str):
                    # Navigate to selected waypoint
                    success = self.nav_manager.navigate_to_waypoint(choice, drone_instance=drone_instance, vertical_factor=vertical_factor)
                    if success:
                        print(f"\n🎯 Navigation completed!")
                        loop_count += 1
                    else:
                        print(f"\n❌ Navigation failed!")
                        break
                
            except Exception as e:
                print(f"❌ Error in navigation loop: {e}")
                break
    
    def _get_navigation_choice(self, destinations: list, loopCount: int, drone_instance=None) -> str:
        """Get navigation choice from user."""
        print(f"\n🎮 NAVIGATION OPTIONS:")
        print("-" * 30)
        
        for i, (wp_id, wp_name) in enumerate(destinations, 1):
            print(f"  {i}. Navigate to '{wp_name}' ({wp_id})")
        
        print(f"  r. Reload waypoint file")
        print(f"  q. Quit navigation")
        
        while True:
            try:
                try:
                    battery_str = drone_instance.send_command_with_return("battery?", timeout=5)
                    battery = int(battery_str)
                    if battery < 20:
                        print(f"\r⚠️  Low battery ({battery}%)               ")
                        if battery < 10:
                            print("\r❗ CRITICAL: Battery too low, landing...")
                            return 'quit'
                except Exception as e:
                    print(f"\rError checking battery: {e}")
                    return 'quit'

                if loopCount == 0:
                    prompt = f"\nEnter your choice (1-{len(destinations)}, r, q): "
                else: 
                    prompt = f"\nEnter your choice (1-{len(destinations)}, q): "

                print(prompt, end='', flush=True)

                # Wait for input with 5-second timeout
                ready, _, _ = select.select([sys.stdin], [], [], 5)

                if ready:
                    choice = sys.stdin.readline().strip().lower()
                    if choice == 'q':
                        return 'quit'
                    elif choice == 'r':
                        if loopCount == 0: 
                            print("❗ Reloading waypoint file...")
                            return 'reload'
                        else: 
                            print("❗ You can only reload the waypoint file at the start of navigation.")
                            continue
                    else:
                        # Try to parse as waypoint selection
                        try:
                            waypoint_index = int(choice) - 1
                            if 0 <= waypoint_index < len(destinations):
                                return destinations[waypoint_index][0]  # Return waypoint ID
                            else:
                                print(f"❌ Invalid choice. Please enter 1-{len(destinations)}")
                        except ValueError:
                            print("❌ Invalid input. Please enter a valid option.")
                
                else: 
                    # No input received within timeout
                    print("\r" + " " * 50 + "\r", end='')
                    continue
                        
            except KeyboardInterrupt:
                return 'quit'
            except Exception as e:
                print(f"❌ Error reading input: {e}")
                return 'quit'