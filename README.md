# DJI Tello Navigation System

A comprehensive Object-Oriented Programming (OOP) based navigation system for DJI Tello drone that enables manual waypoint mapping and autonomous navigation between waypoints using Python.

## Features

### 🚁 Core Functionality
- **Manual Mapping Mode**: Real-time keyboard control to create waypoints
- **Autonomous Navigation**: Navigate between any two created waypoints
- **JSON Path Storage**: Save and load navigation paths for future use
- **Battery Monitoring**: Real-time battery level tracking with low battery warnings
- **Keep-Alive System**: Prevents drone auto-landing during extended operations

### 🎮 Controls (Mapping Mode)
- **WASD**: Move drone in X/Y plane 
- **Up**: Move Up 
- **Down**: Move Down 
- **Left**: Rotate counter clockwise
- **Right**: Rotate clockwise
- **X**: Create waypoint at current position
- **q**: Finish mapping and save navigation data and exit

## Requirements

### System Requirements
- **Operating System**: Linux or macOS (Unix-based systems)
  - **Windows**: WSL2 (Windows Subsystem for Linux) required
  - **Not supported**: Native Windows (due to `termios`, `tty`, `select` dependencies)
- **Python**: 3.7 or higher (required for dataclasses and advanced typing features)
- **Hardware**: DJI Tello drone
- **Network**: WiFi connection to Tello-XXXXXX network

### Installation

1. **Clone or download the project files**

2. **Verify Python version** (must be 3.7+):
```bash
python3 --version
# Should show Python 3.7.0 or higher
```

3. **Install Python dependencies**:
```bash
pip3 install -r requirements.txt
```
   or if using a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/macOS
pip install -r requirements.txt
```

4. **System dependencies** (automatically available on Linux/macOS):
   - `termios`, `select`, `tty` modules - Terminal I/O control (standard library)
   - All other dependencies are standard Python library modules

### Platform-Specific Setup

#### Linux Users
- All dependencies should work out of the box
- Ensure your user has access to network interfaces

#### macOS Users  
- All dependencies should work out of the box
- May need to allow Python network access in System Preferences

#### Windows Users
- **Install WSL2** (Windows Subsystem for Linux):
  1. Open PowerShell as Administrator
  2. Run: `wsl --install`
  3. Restart computer
  4. Install Ubuntu or preferred Linux distribution
  5. Run the project inside WSL2 terminal

### Dependencies

#### External Package
- `djitellopy==2.5.0` - DJI Tello drone SDK (only external dependency)

#### Python Standard Library (included with Python)
- `json` - JSON data handling
- `time` - Time operations and delays  
- `threading` - Multi-threading support
- `uuid` - Unique identifier generation
- `sys` - System-specific parameters
- `os` - Operating system interface
- `glob` - File pattern matching
- `argparse` - Command-line argument parsing
- `traceback` - Error traceback handling
- `datetime` - Date and time operations
- `typing` - Type hints (Dict, List, Optional, Tuple)
- `dataclasses` - Data class decorators (Python 3.7+)
- `enum` - Enumeration support

#### Platform-Specific Standard Library (Linux/Unix only)
- `select` - I/O multiplexing for real-time input
- `termios` - Terminal control for keyboard input
- `tty` - Terminal mode control

**Note**: The platform-specific modules are why this system requires Linux/macOS or WSL2 on Windows.

## Usage

### Setup and Connection

1. **Power on your DJI Tello drone**
2. **Connect to Tello WiFi network**:
   - Look for network named `Tello-XXXXXX`
   - No password required
3. **Run the application**:
```bash
python main.py
```

### Operation Modes

#### 1. Mapping Mode
Create waypoints by manually controlling the drone:

1. Select "1" for Mapping Mode from the main menu
2. Drone will take off automatically to 80cm altitude
3. Use keyboard controls to move the drone:
   - WASD keys for horizontal movement 
   - Up/Down for vertical movement 
   - Left/Right for rotation movement
4. Press **X** to create waypoints at desired locations
5. Press **q** when finished to save navigation data
6. Drone will automatically land and save `drone_movements_YYYYMMDD_HHMMSS.json`

#### 2. Navigation Mode
Navigate between previously created waypoints:

1. Select "2" for Navigation Mode from the main menu
2. Choose a JSON file containing waypoint data
3. Select navigation options:
4. Drone will execute autonomous navigation between waypoints

## Project Structure

The system uses modular OOP design with the following main components:

- **`main.py`**: Main application entry point and mode selection
- **`realtime_drone_control.py`**: Manual control and waypoint creation
- **`navigation_interface.py`**: User interface for navigation mode
- **`waypoint_navigation.py`**: Autonomous navigation logic

## File Outputs

### JSON Navigation Data
The system creates timestamped JSON files (e.g., `drone_movements_20250703_135143.json`) containing:
- All recorded movements during mapping
- Waypoint positions and movement sequences
- Data needed for autonomous navigation


## Safety Features

- **Battery Monitoring**: Continuous battery level checking with automatic landing at <10%
- **Keep-Alive Commands**: Prevents Tello auto-landing during extended operations
- **Emergency Landing**: Immediate landing with Esc key
- **Movement Validation**: All movements validated before execution
- **Error Handling**: Comprehensive error handling with user feedback

## Troubleshooting

### WSL2 Users
- Ensure WSL2 has access to WiFi (Windows 11 required for WiFi passthrough)
- If WiFi issues persist, consider using Windows Python installation with alternatives to `termios`/`tty`
- Test basic connectivity: `ping 192.168.10.1` (Tello's default IP)

### macOS Users
- If you encounter permission issues, try running with `sudo python3 main.py`
- Ensure Python has network access permissions in System Preferences > Security & Privacy

### Python Version Issues
- **Minimum Python 3.7 required** for `dataclasses` and advanced typing features
- Check version: `python3 --version`
- If using older Python, upgrade via package manager or download from python.org

### Battery Life
- Tello battery lasts ~10-13 minutes of flight time
- System automatically monitors and forces landing at low battery
- Plan mapping sessions accordingly