#!/usr/bin/env python3
"""
DJI Tello Navigation System
===========================

A comprehensive OOP-based navigation system for DJI Tello drone that enables:
- Manual control with keyboard input
- Waypoint creation and management
- Automatic navigation between waypoints
- JSON-based path storage and retrieval
- Return to origin functionality

Author: Assistant
Date: June 2025
"""

import os
import sys
import time
import threading
from typing import Optional
from djitellopy import Tello

# Added current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from realtime_drone_control import RealTimeDroneController
from navigation_interface import NavigationInterface


class TelloNavigationApp:
    """Main application class for Tello navigation system."""
    
    def __init__(self, simulate: bool = False):
        """
        Initialize the navigation application.
        
        Args:
            simulate: If True, runs in simulation mode without actual drone
        """
        self.simulate = simulate
        self.drone_controller = RealTimeDroneController()
        self.nav_interface = NavigationInterface()
        self.tello = Tello()
        
        # Application state
        self.is_connected = False
        self.is_flying = False
        self.is_mapping_mode = False
        self.is_navigation_mode = False
        self.is_running = False
        self.movement_thread: Optional[threading.Thread] = None
        self.current_movement_direction: Optional[str] = None
    
    def run(self):
        """Run the main application."""
        try:
            self._show_welcome()
            
            # Get user choice for mode
            mode = self._get_startup_mode()
            
            if mode == "mapping":
                self._run_mapping_mode()
            elif mode == "navigation":
                self._run_navigation_mode()
            elif mode == "quit":
                return
            
        except KeyboardInterrupt:
            print("\n🛑 Application interrupted by user")
        except Exception as e:
            print(f"\n❌ Application error: {e}")
        finally:
            self._cleanup()
    
    def _show_welcome(self):
        """Show welcome message and application info."""
        welcome_text = """
╔══════════════════════════════════════════════════════════════╗
║              🚁 TELLO NAVIGATION SYSTEM v1.0                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  A comprehensive OOP-based navigation system for DJI Tello   ║
║                                                              ║
║  Features:                                                   ║
║  • Manual drone control with keyboard input                  ║
║  • Real-time waypoint creation and tracking                  ║
║  • Automatic navigation between waypoints                    ║
║  • JSON-based path storage and retrieval                     ║
║  • Return to origin functionality                            ║
║  • 3D coordinate system with cm precision                    ║                                
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(welcome_text)
        
        if self.simulate:
            print("🔧 Running in SIMULATION MODE - no actual drone required")
        else:
            print("🚁 Real drone mode - ensure Tello is powered on and connected")
    
    def _get_startup_mode(self) -> str:
        """Get the startup mode from user."""
        while True:
            print("\n📋 Select operation mode:")
            print("1. Mapping Mode - Create new waypoints")
            print("2. Navigation Mode - Use existing waypoints")
            print("3. Quit")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                return "mapping"
            elif choice == "2":
                # Check if navigation file exists
                navigation_files = self._find_navigation_files()
                if navigation_files:
                    return "navigation"
                else:
                    print("❌ No navigation data found. Please run mapping mode first.")
                    continue
            elif choice == "3":
                return "quit"
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
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
        print("  q Key        - Finish & Land")
        print("\nNOTES:")
        print("- Hold key to move, release to stop")
        print("- Only one movement/action at a time")
        print("- All movements are recorded automatically")
        print("="*50)
        print()
    
    def _run_mapping_mode(self):
        """Run the application in mapping mode."""
        print("\n🗺️  MAPPING MODE ACTIVATED")
        print("You will create waypoints by manually controlling the drone.")
        
        self.display_controls()

        if not self.connect_drone():
            print("Failed to connect to drone. Exiting...")
            return
        
        if not self.takeoff():
            print("Failed to take off. Exiting...")
            return
        
        self.is_mapping_mode = True
        self.is_running = True
    
        print("Use keyboard controls to move drone and create waypoints.")
        
        # Start user interface
        try:
            self.drone_controller.run(drone_instance=self.tello)
        except Exception as e:
            print(f"Error during execution: {e}")
            return
        finally:
            self.is_mapping_mode = False
            self.is_running = False

    def _find_navigation_files(self) -> list: 
        # Find all navigation data files creatred by realtime_drone_control.py
        import glob
        pattern = "drone_movements_*.json"
        files = glob.glob(pattern)
        return sorted(files, reverse=True)
    
    def _run_navigation_mode(self):
        """Run the application in navigation mode."""
        print("\n🧭 NAVIGATION MODE ACTIVATED")
        
         # Connect and takeoff
        if not self.connect_drone():
            print("Failed to connect to drone. Exiting...")
            return
        
        if not self.takeoff():
            print("Failed to take off. Exiting...")
            return
        
        self.is_navigation_mode = True
        self.is_running = True
        
        try: 
            self.nav_interface.run(drone_instance=self.tello)
        except Exception as e:
            print(f"Error during navigation: {e}")
        finally: 
            self.is_navigation_mode = False
            self.is_running = False
    
    def connect_drone(self):
        """Connect to the Tello drone."""
        try:
            print("Connecting to Tello drone...")
            self.tello.RESPONSE_TIMEOUT = 7
            self.tello.connect(wait_for_state=False)
            print("Drone connected successfully!")

            self.is_connected = True

            try:
                battery_response = self.tello.send_command_with_return("battery?", timeout=5)
                print(f"✅ Battery: {battery_response}%")
            except Exception as e:
                print(f"❌ Battery command failed: {e}")
            
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
            print("Drone is airborne! 🛫")
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
    
    def _cleanup(self):
        """Cleanup resources and land drone."""
        print("\n🧹 Cleaning up...")

        if self.is_flying:
            try: 
                print("Landing drone...")
                self.tello.land()
                self.is_flying = False
            except Exception as e:
                print(f"Error during landing: {e}")
        
        if self.is_connected:
            try:
                print("Disconnecting from drone...")
                self.tello.end()
                self.is_connected = False
            except Exception as e:
                print(f"Error during disconnection: {e}")

        print("👋 Application closed successfully")


def main():
    """Main entry point of the application."""
    import argparse
    
    parser = argparse.ArgumentParser(description='DJI Tello Navigation System')
    parser.add_argument('--simulate', action='store_true', 
                       help='Run in simulation mode without actual drone')
    
    args = parser.parse_args()
    
    app = TelloNavigationApp(simulate=args.simulate)
    app.run()

if __name__ == "__main__":
    main()
