import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import math
from collections import deque
import numpy as np

class SensorMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GasHealth Monitor")
        self.root.geometry("1000x800")
        self.root.configure(bg='#2c3e50')
        
        # --- Serial communication and Threading ---
        self.serial_port_obj = None
        self.serial_thread = None
        self.running = False
        
        # --- Sensor data storage with timestamps and filtering ---
        self.sensor_data = {
            'gas': {
                'value': 0, 
                'raw_value': 0,
                'history': deque(maxlen=80),
                'timestamps': deque(maxlen=80),
                'filtered_history': deque(maxlen=80),
                'filter_buffer': deque(maxlen=5),
                'initial_samples': 0,
                'initial_values': [],
                'calibration_phase': True,
                'calibration_samples': []
            },
            'ldr': {
                'value': 0, 
                'raw_value': 0,
                'history': deque(maxlen=80),
                'timestamps': deque(maxlen=80),
                'filtered_history': deque(maxlen=80),
                'filter_buffer': deque(maxlen=5),
                'initial_samples': 0,
                'initial_values': [],
                'calibration_phase': True,
                'calibration_samples': [],
                'led_state': False
            },
            'voltage': {
                'value': 0, 
                'raw_value': 0,
                'history': deque(maxlen=80),
                'timestamps': deque(maxlen=80),
                'filtered_history': deque(maxlen=80),
                'filter_buffer': deque(maxlen=5),
                'initial_samples': 0,
                'initial_values': [],
                'calibration_phase': True,
                'calibration_samples': []
            }
        }
        
        # --- LED Control States for Manual Mode ---
        self.led_states = {
            'LED1': False,
            'LED2': False,
            'LED3': False
        }

        # Optimized filter parameters
        self.filter_alpha = 0.6
        self.initial_filter_alpha = 0.3
        self.calibration_samples_count = 15
        
        # Visualization types
        self.viz_types = {
            'gas': ['Graph with Time', 'Speed Meter', 'Digital Version'],
            'ldr': ['Graph with Time', 'Speed Meter', 'Digital Version'], 
            'voltage': ['Graph with Time', 'Speed Meter', 'Digital Version']
        }
        
        self.current_viz = {
            'gas': 'Graph with Time',
            'ldr': 'Graph with Time',
            'voltage': 'Graph with Time'
        }
        
        self.start_time = time.time()
        
        # Skip counters for initial noise
        self.skip_counter = {
            'gas': 0,
            'ldr': 0, 
            'voltage': 0
        }
        self.max_skip = 10
        
        self.initialize_dummy_data()
        self.setup_ui()
        
        # Start continuous update loop for graphs
        self.update_visualizations_loop()
        
    def initialize_dummy_data(self):
        """Initialize with some dummy data so graphs show something at startup"""
        current_time = time.time() - self.start_time
        
        for i in range(5):
            time_val = current_time - (4 - i) * 0.5 
            
            # Gas sensor 
            gas_val = 100 + i * 20
            self.sensor_data['gas']['history'].append(gas_val)
            self.sensor_data['gas']['filtered_history'].append(gas_val)
            self.sensor_data['gas']['timestamps'].append(time_val)
            self.sensor_data['gas']['value'] = gas_val
            
            # LDR sensor 
            ldr_val = 1000 + i * 200
            self.sensor_data['ldr']['history'].append(ldr_val)
            self.sensor_data['ldr']['filtered_history'].append(ldr_val)
            self.sensor_data['ldr']['timestamps'].append(time_val)
            self.sensor_data['ldr']['value'] = ldr_val
            
            # Voltage sensor 
            voltage_val = 1.5 + i * 0.1
            self.sensor_data['voltage']['history'].append(voltage_val)
            self.sensor_data['voltage']['filtered_history'].append(voltage_val)
            self.sensor_data['voltage']['timestamps'].append(time_val)
            self.sensor_data['voltage']['value'] = voltage_val
            
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg='#34495e', height=80)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="GASHEALTH MONITOR",
                                 font=('Arial', 20, 'bold'), fg='#ecf0f1', bg='#34495e')
        title_label.pack(expand=True)
        
        # Connection frame
        conn_frame = tk.Frame(self.root, bg='#34495e', relief=tk.RAISED, bd=2)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Port selection
        tk.Label(conn_frame, text="Port:", font=('Arial', 10, 'bold'), 
                 fg='#ecf0f1', bg='#34495e').grid(row=0, column=0, padx=5, pady=10, sticky='w')
        
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, 
                                       width=15, state='readonly')
        self.port_combo.grid(row=0, column=1, padx=5, pady=10)
        
        # Baudrate selection
        tk.Label(conn_frame, text="Baudrate:", font=('Arial', 10, 'bold'), 
                 fg='#ecf0f1', bg='#34495e').grid(row=0, column=2, padx=5, pady=10, sticky='w')
        
        self.baud_var = tk.StringVar(value="115200")
        self.baud_combo = ttk.Combobox(conn_frame, textvariable=self.baud_var, 
                                       values=["9600", "19200", "38400", "57600", "115200"], 
                                       width=10, state='readonly')
        self.baud_combo.grid(row=0, column=3, padx=5, pady=10)
        
        # Connection buttons
        self.connect_btn = tk.Button(conn_frame, text="CONNECT", font=('Arial', 10, 'bold'),
                                     bg='#27ae60', fg='white', relief=tk.RAISED, bd=3,
                                     command=self.toggle_connection, width=10)
        self.connect_btn.grid(row=0, column=4, padx=5, pady=10)
        
        refresh_btn = tk.Button(conn_frame, text="REFRESH PORTS", font=('Arial', 10, 'bold'),
                               bg='#3498db', fg='white', relief=tk.RAISED, bd=3,
                               command=self.refresh_ports)
        refresh_btn.grid(row=0, column=5, padx=5, pady=10)
        
        # Status label
        self.status_label = tk.Label(conn_frame, text="Disconnected", font=('Arial', 10, 'bold'),
                                     fg='#e74c3c', bg='#34495e')
        self.status_label.grid(row=0, column=6, padx=10, pady=10, sticky='e')
        
        # Data display for debugging
        self.data_debug = tk.Label(conn_frame, text="", font=('Arial', 8), 
                                  fg='#bdc3c7', bg='#34495e')
        self.data_debug.grid(row=1, column=0, columnspan=7, padx=5, pady=2)
        
        # --- Main Content: Use ttk.Notebook for Auto/Manual Modes ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Auto Mode Frame (Monitoring)
        self.auto_mode_frame = tk.Frame(self.notebook, bg='#2c3e50')
        self.notebook.add(self.auto_mode_frame, text="📈 Auto Mode (Monitor)")
        self.setup_auto_mode_ui(self.auto_mode_frame)
        
        # Manual Mode Frame (Control)
        self.manual_mode_frame = tk.Frame(self.notebook, bg='#2c3e50')
        self.notebook.add(self.manual_mode_frame, text="⚙️ Manual Mode (Control)")
        self.setup_manual_mode_ui(self.manual_mode_frame)
        
        # Refresh ports on start
        self.refresh_ports()
        
        # Bind tab change event for mode switching
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
    def apply_adaptive_low_pass_filter(self, sensor_type, raw_value):
        """Apply adaptive low-pass filter with improved initial noise handling"""
        # Store calibration samples
        if self.sensor_data[sensor_type]['calibration_phase']:
            self.sensor_data[sensor_type]['calibration_samples'].append(raw_value)
            
            # Check if we have enough calibration samples
            if len(self.sensor_data[sensor_type]['calibration_samples']) >= self.calibration_samples_count:
                # Calculate baseline from calibration samples (median to ignore outliers)
                calibration_data = self.sensor_data[sensor_type]['calibration_samples']
                baseline = np.median(calibration_data)
                
                # End calibration phase
                self.sensor_data[sensor_type]['calibration_phase'] = False
                self.sensor_data[sensor_type]['initial_samples'] = self.calibration_samples_count
                
                # Initialize filter buffer with baseline
                for _ in range(3):
                    self.sensor_data[sensor_type]['filter_buffer'].append(baseline)
                
                return baseline
            else:
                # During calibration, return the current raw value (will be smoothed later)
                return raw_value
        
        # Add new value to buffer
        self.sensor_data[sensor_type]['filter_buffer'].append(raw_value)
        
        # Track initial samples for adaptive filtering
        self.sensor_data[sensor_type]['initial_samples'] += 1
        
        # If we don't have enough data, return raw value
        if len(self.sensor_data[sensor_type]['filter_buffer']) < 3:
            return raw_value
        
        buffer = list(self.sensor_data[sensor_type]['filter_buffer'])
        
        # For the first samples after calibration, use more aggressive filtering
        if self.sensor_data[sensor_type]['initial_samples'] <= self.calibration_samples_count + 10:
            # Use median filter for initial samples to remove outliers
            sorted_buffer = sorted(buffer)
            median_value = sorted_buffer[len(sorted_buffer) // 2]
            
            # Apply exponential smoothing with low alpha
            if len(self.sensor_data[sensor_type]['filtered_history']) > 0:
                last_filtered = self.sensor_data[sensor_type]['filtered_history'][-1]
                filtered_value = self.initial_filter_alpha * median_value + (1 - self.initial_filter_alpha) * last_filtered
            else:
                filtered_value = median_value
                
            return filtered_value
        
        # After stabilization, use faster responding filter
        # Simple moving average for speed
        avg_value = sum(buffer) / len(buffer)
        
        # Final exponential smoothing with higher alpha for faster response
        if len(self.sensor_data[sensor_type]['filtered_history']) > 0:
            last_filtered = self.sensor_data[sensor_type]['filtered_history'][-1]
            final_value = self.filter_alpha * avg_value + (1 - self.filter_alpha) * last_filtered
        else:
            final_value = avg_value
            
        return final_value

    def setup_auto_mode_ui(self, parent_frame):
        """Sets up the sensor monitoring (Auto Mode) UI."""
        
        # Create three equal columns for sensors
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=1)
        parent_frame.columnconfigure(2, weight=1)
        parent_frame.rowconfigure(0, weight=1)
        
        # Gas Sensor Frame
        self.gas_frame = self.create_sensor_frame(parent_frame, "GAS SENSOR", 0, 0, '#2ecc71')
        
        # LDR Sensor Frame  
        self.ldr_frame = self.create_sensor_frame(parent_frame, "LIGHT SENSOR", 0, 1, '#f39c12')
        
        # Temperature Sensor Frame (Voltage in this case)
        self.voltage_frame = self.create_sensor_frame(parent_frame, "TEMPERATURE SENSOR", 0, 2, '#e74c3c')
        
        # Setup visualizations
        self.setup_gas_visualization()
        self.setup_ldr_visualization()
        self.setup_voltage_visualization()

    def setup_manual_mode_ui(self, parent_frame):
        """Sets up the LED control panel (Manual Mode) UI."""
        
        control_panel = tk.Frame(parent_frame, bg='#34495e', padx=20, pady=20, relief=tk.RAISED, bd=3)
        control_panel.pack(pady=50, padx=50)

        tk.Label(control_panel, text="MANUAL LED CONTROL", font=('Arial', 16, 'bold'),
                 fg='#ecf0f1', bg='#34495e').grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # LED 1 Control (Gas LED)
        tk.Label(control_panel, text="Gas LED (LED1)", font=('Arial', 12),
                 fg='#ecf0f1', bg='#34495e').grid(row=1, column=0, padx=10, pady=10, sticky='w')

        self.led1_btn = tk.Button(control_panel, text="OFF", font=('Arial', 12, 'bold'), width=10,
                              command=lambda: self.toggle_led('LED1', self.led1_btn))
        self.led1_btn.grid(row=1, column=1, padx=10, pady=10)
        self.update_led_button_text('LED1', self.led1_btn)
        
        # LED 2 Control (LDR LED)
        tk.Label(control_panel, text="Light LED (LED2)", font=('Arial', 12),
                 fg='#ecf0f1', bg='#34495e').grid(row=2, column=0, padx=10, pady=10, sticky='w')

        self.led2_btn = tk.Button(control_panel, text="OFF", font=('Arial', 12, 'bold'), width=10,
                              command=lambda: self.toggle_led('LED2', self.led2_btn))
        self.led2_btn.grid(row=2, column=1, padx=10, pady=10)
        self.update_led_button_text('LED2', self.led2_btn)

        # LED 3 Control (Voltage LED)
        tk.Label(control_panel, text="Voltage LED (LED3)", font=('Arial', 12),
                 fg='#ecf0f1', bg='#34495e').grid(row=3, column=0, padx=10, pady=10, sticky='w')

        self.led3_btn = tk.Button(control_panel, text="OFF", font=('Arial', 12, 'bold'), width=10,
                              command=lambda: self.toggle_led('LED3', self.led3_btn))
        self.led3_btn.grid(row=3, column=1, padx=10, pady=10)
        self.update_led_button_text('LED3', self.led3_btn)

        # Status indicator
        tk.Label(control_panel, text="Connection Status:", font=('Arial', 10),
                 fg='#ecf0f1', bg='#34495e').grid(row=4, column=0, padx=10, pady=(20, 0), sticky='w')
        self.manual_status_label = tk.Label(control_panel, text="Serial Disconnected", font=('Arial', 10, 'bold'),
                                            fg='#e74c3c', bg='#34495e')
        self.manual_status_label.grid(row=4, column=1, padx=10, pady=(20, 0), sticky='w')

    def update_led_button_text(self, led_id, button):
        """Updates the LED button text and color based on its state."""
        is_on = self.led_states[led_id]
        text = "ON" if is_on else "OFF"
        color = '#27ae60' if is_on else '#e74c3c'
        button.config(text=text, bg=color, fg='white')

    def toggle_led(self, led_id, button):
        """Toggles the LED state and sends command via serial."""
        if not self.running or not self.serial_port_obj or not self.serial_port_obj.is_open:
            messagebox.showerror("Connection Error", "Please connect to a serial port first.")
            return

        # Toggle state
        self.led_states[led_id] = not self.led_states[led_id]
        new_state = self.led_states[led_id]
        
        # Send command
        command = f"{led_id}_{'ON' if new_state else 'OFF'}\n"
        
        try:
            self.serial_port_obj.write(command.encode('utf-8'))
            print(f"Sent command: {command.strip()}")
            
            # Update button appearance
            self.update_led_button_text(led_id, button)
            
        except Exception as e:
            messagebox.showerror("Serial Write Error", f"Failed to send command: {e}")
            # Revert state on error
            self.led_states[led_id] = not new_state
            self.update_led_button_text(led_id, button)

    def change_mode(self, mode):
        """Change between auto and manual mode"""
        if not self.running or not self.serial_port_obj or not self.serial_port_obj.is_open:
            messagebox.showerror("Connection Error", "Please connect to a serial port first.")
            return
            
        command = f"MODE_{mode}\n"
        try:
            self.serial_port_obj.write(command.encode('utf-8'))
            self.log_message(f"Switching to {mode} mode")
        except Exception as e:
            messagebox.showerror("Serial Write Error", f"Failed to send mode command: {e}")

    def reset_manual_leds(self):
        """Reset all LED states to OFF and update buttons when switching to Manual mode"""
        # Reset all LED states to OFF
        for led_id in ['LED1', 'LED2', 'LED3']:
            self.led_states[led_id] = False
        
        # Update all button appearances
        self.update_led_button_text('LED1', self.led1_btn)
        self.update_led_button_text('LED2', self.led2_btn)
        self.update_led_button_text('LED3', self.led3_btn)
        
        # Send OFF commands to all LEDs
        if self.running and self.serial_port_obj and self.serial_port_obj.is_open:
            for led_id in ['LED1', 'LED2', 'LED3']:
                command = f"{led_id}_OFF\n"
                try:
                    self.serial_port_obj.write(command.encode('utf-8'))
                    print(f"Sent command: {command.strip()}")
                except Exception as e:
                    print(f"Error sending {command}: {e}")

    def on_tab_changed(self, event):
        """Handle tab changes to switch between auto and manual modes"""
        if not self.running or not self.serial_port_obj:
            return
            
        current_tab = self.notebook.tab(self.notebook.select(), "text")
        if "Auto Mode" in current_tab:
            self.change_mode("AUTO")
        elif "Manual Mode" in current_tab:
            self.change_mode("MANUAL")
            # Reset all LEDs to OFF state when switching to Manual mode
            self.reset_manual_leds()

    def update_visualizations_loop(self):
        """The main loop to update all active visualizations with faster refresh."""
        try:
            self.update_warnings()

            # Update value displays
            self.gas_raw_label_text.set(f"Value: {self.sensor_data['gas']['value']:.0f} PPM")
            self.ldr_raw_label_text.set(f"Value: {self.sensor_data['ldr']['value']:.0f}")
            self.voltage_raw_label_text.set(f"Value: {self.sensor_data['voltage']['value']:.2f}V")

            # Update visualizations based on current view type
            if self.current_viz['gas'] == 'Graph with Time':
                self.update_gas_time_graph()
            elif self.current_viz['gas'] == 'Speed Meter':
                self.update_gas_speed_meter()
            elif self.current_viz['gas'] == 'Digital Version':
                self.update_gas_digital_version()

            if self.current_viz['ldr'] == 'Graph with Time':
                self.update_ldr_time_graph()
            elif self.current_viz['ldr'] == 'Speed Meter':
                self.update_ldr_speed_meter()
            elif self.current_viz['ldr'] == 'Digital Version':
                self.update_ldr_digital_version()

            if self.current_viz['voltage'] == 'Graph with Time':
                self.update_voltage_time_graph()
            elif self.current_viz['voltage'] == 'Speed Meter':
                self.update_voltage_speed_meter()
            elif self.current_viz['voltage'] == 'Digital Version':
                self.update_voltage_digital_version()
            
            # Re-schedule the update with faster refresh rate
            self.root.after(100, self.update_visualizations_loop)
            
        except Exception as e:
            print(f"Error in update loop: {e}")
            # Still reschedule even if there's an error
            self.root.after(100, self.update_visualizations_loop)

    # --- SERIAL COMMUNICATION METHODS ---

    def refresh_ports(self):
        """Finds and updates the list of available serial ports."""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_var.set(port_list[-1])

    def toggle_connection(self):
        """Connects or disconnects the serial port."""
        if self.running:
            self.stop_serial()
        else:
            self.start_serial()

    def start_serial(self):
        """Starts the serial connection and data reading thread."""
        port = self.port_var.get()
        baudrate = self.baud_var.get()

        if not port:
            messagebox.showerror("Connection Error", "Please select a serial port.")
            return

        try:
            self.serial_port_obj = serial.Serial(port, int(baudrate), timeout=0.05)
            self.running = True
            
            # Reset filter states and enable calibration when starting new connection
            for sensor in ['gas', 'ldr', 'voltage']:
                self.sensor_data[sensor]['filter_buffer'].clear()
                self.sensor_data[sensor]['initial_samples'] = 0
                self.sensor_data[sensor]['initial_values'] = []
                self.sensor_data[sensor]['calibration_phase'] = True
                self.sensor_data[sensor]['calibration_samples'] = []
            
            # Reset skip counters when starting new connection
            self.skip_counter = {'gas': 0, 'ldr': 0, 'voltage': 0}
            
            self.serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
            self.serial_thread.start()
            
            self.connect_btn.config(text="DISCONNECT", bg='#e74c3c')
            self.status_label.config(text=f"Connected to {port}", fg='#2ecc71')
            self.manual_status_label.config(text=f"Connected to {port}", fg='#2ecc71')
            
            messagebox.showinfo("Connection Status", f"Successfully connected to {port} at {baudrate} bps.")

        except serial.SerialException as e:
            self.running = False
            self.serial_port_obj = None
            messagebox.showerror("Connection Error", f"Failed to connect to {port}: {e}")
            self.connect_btn.config(text="CONNECT", bg='#27ae60')
            self.status_label.config(text="Disconnected", fg='#e74c3c')
            self.manual_status_label.config(text="Serial Disconnected", fg='#e74c3c')
    
    def stop_serial(self):
        """Stops the serial reading thread and closes the port."""
        self.running = False
        if self.serial_thread and self.serial_thread.is_alive():
            pass 
        
        if self.serial_port_obj and self.serial_port_obj.is_open:
            self.serial_port_obj.close()
            self.serial_port_obj = None
            
        self.connect_btn.config(text="CONNECT", bg='#27ae60')
        self.status_label.config(text="Disconnected", fg='#e74c3c')
        self.manual_status_label.config(text="Serial Disconnected", fg='#e74c3c')
        messagebox.showinfo("Connection Status", "Disconnected successfully.")

    def read_serial_data(self):
        """Target function for the serial thread to continuously read and process data."""
        buffer = ""
        while self.running:
            try:
                if self.serial_port_obj and self.serial_port_obj.in_waiting > 0:
                    # Read all available data at once for better performance
                    data = self.serial_port_obj.read(self.serial_port_obj.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    
                    lines = buffer.split('\n')
                    buffer = lines[-1]  # Keep incomplete line in buffer
                    
                    # Process all complete lines
                    for line in lines[:-1]:
                        if line.strip():
                            self.parse_sensor_data(line.strip())
                            
                time.sleep(0.005)  # Reduced sleep for faster response
            except Exception as e:
                print(f"Serial Read Error: {e}")
                time.sleep(0.05)

    def parse_sensor_data(self, line):
        """Parse sensor data in the new format"""
        try:
            current_time = time.time() - self.start_time
            self.data_debug.config(text=f"Last: {line}")
            
            if line.startswith('GAS:'):
                # Format: "GAS:value,dangerLevel"
                parts = line[4:].split(',')
                if len(parts) == 2:
                    raw_gas_value = float(parts[0])
                    
                    # Skip first few values for this sensor
                    if self.skip_counter['gas'] < self.max_skip:
                        self.skip_counter['gas'] += 1
                        return  # Skip this data point
                    
                    # Apply adaptive filter with calibration
                    filtered_gas_value = self.apply_adaptive_low_pass_filter('gas', raw_gas_value)
                    
                    # Update gas sensor data
                    self.sensor_data['gas']['raw_value'] = raw_gas_value
                    self.sensor_data['gas']['value'] = filtered_gas_value
                    self.sensor_data['gas']['history'].append(raw_gas_value)
                    self.sensor_data['gas']['filtered_history'].append(filtered_gas_value)
                    self.sensor_data['gas']['timestamps'].append(current_time)
                    
            elif line.startswith('LDR:'):
                # Format: "LDR:time,value"  
                parts = line[4:].split(',')
                if len(parts) == 2:
                    raw_ldr_value = float(parts[1])
                    
                    # Skip first few values for this sensor
                    if self.skip_counter['ldr'] < self.max_skip:
                        self.skip_counter['ldr'] += 1
                        return  # Skip this data point
                    
                    # Apply adaptive filter with calibration
                    filtered_ldr_value = self.apply_adaptive_low_pass_filter('ldr', raw_ldr_value)
                    
                    # Update LDR sensor data
                    self.sensor_data['ldr']['raw_value'] = raw_ldr_value
                    self.sensor_data['ldr']['value'] = filtered_ldr_value
                    self.sensor_data['ldr']['history'].append(raw_ldr_value)
                    self.sensor_data['ldr']['filtered_history'].append(filtered_ldr_value)
                    self.sensor_data['ldr']['timestamps'].append(current_time)
                    
                    # Update LDR LED state
                    self.update_ldr_led_state(filtered_ldr_value)
                    
            elif line.startswith('VOLT:'):
                # Format: "VOLT:min,value,max"
                parts = line[5:].split(',')
                if len(parts) == 3:
                    raw_volt_value = float(parts[1])
                    
                    # Skip first few values for this sensor
                    if self.skip_counter['voltage'] < self.max_skip:
                        self.skip_counter['voltage'] += 1
                        return  # Skip this data point
                    
                    # Apply adaptive filter with calibration
                    filtered_volt_value = self.apply_adaptive_low_pass_filter('voltage', raw_volt_value)
                    
                    # Update voltage sensor data
                    self.sensor_data['voltage']['raw_value'] = raw_volt_value
                    self.sensor_data['voltage']['value'] = filtered_volt_value
                    self.sensor_data['voltage']['history'].append(raw_volt_value)
                    self.sensor_data['voltage']['filtered_history'].append(filtered_volt_value)
                    self.sensor_data['voltage']['timestamps'].append(current_time)
                    
            elif line.startswith('LED_STATUS:'):
                # Format: "LED_STATUS:gas,ldr,volt"
                parts = line[11:].split(',')
                if len(parts) == 3:
                    gas_led = int(parts[0])
                    ldr_led = int(parts[1])
                    volt_led = int(parts[2])
                    # Update LED status display if needed
                    
            elif line.startswith('MODE_CHANGED:'):
                mode = line.split(':')[1]
                self.log_message(f"Mode changed to: {mode}")
                
            elif line.startswith('LED') and ':' in line:
                # LED command confirmation like "LED1:ON"
                led, state = line.split(':', 1)
                self.log_message(f"{led} turned {state}")
                
        except Exception as e:
            print(f"Error parsing data: {e}")

    def create_sensor_frame(self, parent, title, row, col, color):
        frame = tk.Frame(parent, bg='#34495e', relief=tk.RAISED, bd=2)
        frame.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=1)
        
        # Title
        title_frame = tk.Frame(frame, bg=color, height=40)
        title_frame.grid(row=0, column=0, sticky='ew', padx=2, pady=(2, 0))
        title_frame.grid_propagate(False)
        
        tk.Label(title_frame, text=title, font=('Arial', 12, 'bold'), 
                 fg='white', bg=color).pack(expand=True)
        
        # Visualization selector
        viz_frame = tk.Frame(frame, bg='#34495e')
        viz_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=(10, 5))
        
        tk.Label(viz_frame, text="View Type:", font=('Arial', 9, 'bold'),
                 fg='#ecf0f1', bg='#34495e').pack(side=tk.LEFT, padx=(0, 5))
        
        viz_var = tk.StringVar()
        if 'GAS' in title:
            viz_values = self.viz_types['gas']
            sensor_type = 'gas'
        elif 'LIGHT' in title:
            viz_values = self.viz_types['ldr']
            sensor_type = 'ldr'
        elif 'TEMPERATURE' in title:
            viz_values = self.viz_types['voltage']
            sensor_type = 'voltage'
        else:
            viz_values = self.viz_types['gas']
            sensor_type = 'unknown'

        viz_combo = ttk.Combobox(viz_frame, textvariable=viz_var, 
                                 values=viz_values, state="readonly", width=15)
        viz_combo.pack(side=tk.LEFT)
        
        # Value Display
        raw_frame = tk.Frame(frame, bg='#34495e')
        raw_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=(0, 5))

        raw_label_text = tk.StringVar(value="Value: N/A")
        raw_label = tk.Label(raw_frame, textvariable=raw_label_text, font=('Arial', 9),
                             fg='#bdc3c7', bg='#34495e')
        raw_label.pack(side=tk.LEFT, fill=tk.X)
        
        # Warning label for each sensor
        warning_frame = tk.Frame(frame, bg='#34495e')
        warning_frame.grid(row=4, column=0, sticky='ew', padx=10, pady=(0, 5))
        
        warning_label = tk.Label(warning_frame, text="", font=('Arial', 9, 'bold'),
                                 fg='#e74c3c', bg='#34495e', wraplength=250)
        warning_label.pack(fill=tk.X)
        
        # Visualization container
        viz_container = tk.Frame(frame, bg='#2c3e50', relief=tk.SUNKEN, bd=1)
        viz_container.grid(row=3, column=0, sticky='nsew', padx=10, pady=(0, 10))
        viz_container.columnconfigure(0, weight=1)
        viz_container.rowconfigure(0, weight=1)
        
        # Store references
        if sensor_type == 'gas':
            self.gas_viz_var = viz_var
            self.gas_viz_container = viz_container
            self.gas_warning_label = warning_label
            self.gas_raw_label_text = raw_label_text
            viz_combo.bind('<<ComboboxSelected>>', lambda e: self.change_visualization('gas'))
        elif sensor_type == 'ldr':
            self.ldr_viz_var = viz_var
            self.ldr_viz_container = viz_container
            self.ldr_warning_label = warning_label
            self.ldr_raw_label_text = raw_label_text
            viz_combo.bind('<<ComboboxSelected>>', lambda e: self.change_visualization('ldr'))
        elif sensor_type == 'voltage':
            self.voltage_viz_var = viz_var
            self.voltage_viz_container = viz_container
            self.voltage_warning_label = warning_label
            self.voltage_raw_label_text = raw_label_text
            viz_combo.bind('<<ComboboxSelected>>', lambda e: self.change_visualization('voltage'))
        
        return frame

    def setup_gas_visualization(self):
        self.gas_viz_var.set('Graph with Time')
        self.create_gas_time_graph()
        
    def setup_ldr_visualization(self):
        self.ldr_viz_var.set('Graph with Time')
        self.create_ldr_time_graph()
        
    def setup_voltage_visualization(self):
        self.voltage_viz_var.set('Graph with Time')
        self.create_voltage_time_graph()
        
    def change_visualization(self, sensor_type):
        viz_type = getattr(self, f'{sensor_type}_viz_var').get()
        self.current_viz[sensor_type] = viz_type
        
        container = getattr(self, f'{sensor_type}_viz_container')
        for widget in container.winfo_children():
            widget.destroy()
        
        if viz_type == 'Graph with Time':
            getattr(self, f'create_{sensor_type}_time_graph')()
        elif viz_type == 'Speed Meter':
            getattr(self, f'create_{sensor_type}_speed_meter')()
        elif viz_type == 'Digital Version':
            getattr(self, f'create_{sensor_type}_digital_version')()
            
    # Update warning messages based on sensor values and LED states
    def update_warnings(self):
        # Gas sensor warning
        gas_value = self.sensor_data['gas']['value']
        if gas_value > 350:
            self.gas_warning_label.config(text="⚠️ If sensor read upper than 350, Gas cooker not healthy.")
        else:
            self.gas_warning_label.config(text="")
            
        # Temperature sensor warning
        temp_value = min(self.sensor_data['voltage']['value'] * 100, 300)
        if temp_value > 200:
            self.voltage_warning_label.config(text="⚠️ If maximum temperature upper than 200°C, Gas cooker not healthy.")
        else:
            self.voltage_warning_label.config(text="")
            
        # LDR sensor warning - based on LED state (pin 26)
        ldr_led_state = self.sensor_data['ldr']['led_state']
        if ldr_led_state:
            self.ldr_warning_label.config(text="⚠️ LDR LED is ON - Gas cooker not healthy.")
        else:
            self.ldr_warning_label.config(text="")
            
    # Update LDR LED state based on Arduino logic (LDR value > 1500)
    def update_ldr_led_state(self, ldr_value):
        self.sensor_data['ldr']['led_state'] = (ldr_value > 1500)
        
    def log_message(self, message):
        """Add message to log"""
        print(f"LOG: {message}")

    # ==================== OPTIMIZED VISUALIZATION METHODS ====================
    
    def create_gas_time_graph(self):
        canvas = tk.Canvas(self.gas_viz_container, bg='#2c3e50', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.gas_time_canvas = canvas
        canvas.bind('<Configure>', lambda e: self.update_gas_time_graph())
        
    def update_gas_time_graph(self):
        if not hasattr(self, 'gas_time_canvas') or not self.gas_time_canvas.winfo_exists():
            return

        # Use filtered history for display
        history = list(self.sensor_data['gas']['filtered_history'])
        timestamps = list(self.sensor_data['gas']['timestamps'])
        self.gas_time_canvas.delete("all")
        
        width = self.gas_time_canvas.winfo_width()
        height = self.gas_time_canvas.winfo_height()
        
        if width < 50 or height < 50:
            return
        
        if len(history) > 0:
            graph_width = width - 80
            graph_height = height - 100
            
            # Draw axes
            self.gas_time_canvas.create_line(60, 40, 60, 40 + graph_height, fill='#7f8c8d', width=2)
            self.gas_time_canvas.create_line(60, 40 + graph_height, 60 + graph_width, 40 + graph_height, 
                                             fill='#7f8c8d', width=2)
            
            # Set gas sensor range to 0-1000
            max_val = 1000
            min_val = 0
            val_range = max_val - min_val if max_val != min_val else 1
            
            # Optimized: Draw fewer points for better performance
            points = []
            step = max(1, len(history) // 50)  # Show max 50 points for performance
            for i in range(0, len(history), step):
                val = history[i]
                x = 60 + (i / max(1, len(history)-1)) * graph_width
                # Cap values at 1000 for display
                display_val = min(val, max_val)
                y = 40 + graph_height - ((display_val - min_val) / val_range) * graph_height
                points.append((x, y))
            
            # Draw trend line - use simple line instead of smooth for performance
            if len(points) > 1:
                self.gas_time_canvas.create_line(points, fill='#2ecc71', width=2)
            elif len(points) == 1:
                x, y = points[0]
                self.gas_time_canvas.create_oval(x-2, y-2, x+2, y+2, fill='#2ecc71', outline='#2ecc71')
            
            # Draw danger level line
            danger_y = 40 + graph_height - ((350 - min_val) / val_range) * graph_height
            if 40 <= danger_y <= 40 + graph_height:
                self.gas_time_canvas.create_line(60, danger_y, 60 + graph_width, danger_y,
                                                 fill='#f1c40f', width=2, dash=(5, 2))
                self.gas_time_canvas.create_text(55, danger_y, text="350", anchor='e',
                                                 font=('Arial', 8), fill='#f1c40f')
            
            # Draw current value
            if history:
                current_val = min(history[-1], max_val)  # Cap current value at 1000
                self.gas_time_canvas.create_text(width/2, 20, 
                                                 text=f"Current: {current_val:.0f} PPM", 
                                                 font=('Arial', 12, 'bold'), fill='#ecf0f1')
            
            # Labels
            self.gas_time_canvas.create_text(width/2, height-20, text="Time →", 
                                             font=('Arial', 10), fill='#bdc3c7')
            self.gas_time_canvas.create_text(20, height/2, text="Gas Level", angle=90,
                                             font=('Arial', 10), fill='#bdc3c7')
            
            # Y-axis labels for gas sensor (0-1000) - reduced number for performance
            for i in range(0, 1001, 250):
                y_pos = 40 + graph_height - ((i - min_val) / val_range) * graph_height
                if 40 <= y_pos <= 40 + graph_height:
                    self.gas_time_canvas.create_text(50, y_pos, text=str(i), anchor='e',
                                                    font=('Arial', 8), fill='#bdc3c7')
        else:
            self.gas_time_canvas.create_text(width/2, height/2, 
                                             text="No data available\nConnect to device", 
                                             font=('Arial', 12), fill='#bdc3c7')

    def create_ldr_time_graph(self):
        canvas = tk.Canvas(self.ldr_viz_container, bg='#2c3e50', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.ldr_time_canvas = canvas
        canvas.bind('<Configure>', lambda e: self.update_ldr_time_graph())
        
    def update_ldr_time_graph(self):
        if not hasattr(self, 'ldr_time_canvas') or not self.ldr_time_canvas.winfo_exists():
            return

        # Use filtered history for display
        history = list(self.sensor_data['ldr']['filtered_history'])
        timestamps = list(self.sensor_data['ldr']['timestamps'])
        self.ldr_time_canvas.delete("all")
        
        width = self.ldr_time_canvas.winfo_width()
        height = self.ldr_time_canvas.winfo_height()
        
        if width < 50 or height < 50:
            return
        
        if len(history) > 0:
            graph_width = width - 80
            graph_height = height - 100
            
            self.ldr_time_canvas.create_line(60, 40, 60, 40 + graph_height, fill='#7f8c8d', width=2)
            self.ldr_time_canvas.create_line(60, 40 + graph_height, 60 + graph_width, 40 + graph_height, 
                                             fill='#7f8c8d', width=2)
            
            # Set LDR sensor range to 0-3000
            max_val = 3000
            min_val = 0
            val_range = max_val - min_val if max_val != min_val else 1
            
            # Optimized: Draw fewer points
            points = []
            step = max(1, len(history) // 50)
            for i in range(0, len(history), step):
                val = history[i]
                x = 60 + (i / max(1, len(history)-1)) * graph_width
                # Cap values at 3000 for display
                display_val = min(val, max_val)
                y = 40 + graph_height - ((display_val - min_val) / val_range) * graph_height
                points.append((x, y))
            
            if len(points) > 1:
                self.ldr_time_canvas.create_line(points, fill='#f39c12', width=2)
            elif len(points) == 1:
                x, y = points[0]
                self.ldr_time_canvas.create_oval(x-2, y-2, x+2, y+2, fill='#f39c12', outline='#f39c12')
            
            threshold_y = 40 + graph_height - ((1500 - min_val) / val_range) * graph_height
            if 40 <= threshold_y <= 40 + graph_height:
                self.ldr_time_canvas.create_line(60, threshold_y, 60 + graph_width, threshold_y,
                                                 fill='#3498db', width=2, dash=(5, 2))
                self.ldr_time_canvas.create_text(55, threshold_y, text="1500", anchor='e',
                                                 font=('Arial', 8), fill='#3498db')
            
            if history:
                current_val = min(history[-1], max_val)  # Cap current value at 3000
                status = "HIGH" if current_val > 1500 else "LOW"
                color = '#e74c3c' if current_val > 1500 else '#f39c12'
                self.ldr_time_canvas.create_text(width/2, 20, 
                                                 text=f"Current: {current_val:.0f} ({status})", 
                                                 font=('Arial', 12, 'bold'), fill=color)
            
            self.ldr_time_canvas.create_text(width/2, height-20, text="Time →", 
                                             font=('Arial', 10), fill='#bdc3c7')
            self.ldr_time_canvas.create_text(20, height/2, text="Light Level", angle=90,
                                             font=('Arial', 10), fill='#bdc3c7')
            
            # Y-axis labels for LDR sensor (0-3000) - reduced number
            for i in range(0, 3001, 750):
                y_pos = 40 + graph_height - ((i - min_val) / val_range) * graph_height
                if 40 <= y_pos <= 40 + graph_height:
                    self.ldr_time_canvas.create_text(50, y_pos, text=str(i), anchor='e',
                                                    font=('Arial', 8), fill='#bdc3c7')
        else:
            self.ldr_time_canvas.create_text(width/2, height/2, 
                                             text="No data available\nConnect to device", 
                                             font=('Arial', 12), fill='#bdc3c7')

    def create_voltage_time_graph(self):
        canvas = tk.Canvas(self.voltage_viz_container, bg='#2c3e50', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.voltage_time_canvas = canvas
        canvas.bind('<Configure>', lambda e: self.update_voltage_time_graph())
        
    def update_voltage_time_graph(self):
        if not hasattr(self, 'voltage_time_canvas') or not self.voltage_time_canvas.winfo_exists():
            return

        # Use filtered history for display
        history_volt = list(self.sensor_data['voltage']['filtered_history'])
        timestamps = list(self.sensor_data['voltage']['timestamps'])
        self.voltage_time_canvas.delete("all")
        
        width = self.voltage_time_canvas.winfo_width()
        height = self.voltage_time_canvas.winfo_height()
        
        if width < 50 or height < 50:
            return
        
        if len(history_volt) > 0:
            history_temp = [min(v * 100, 300) for v in history_volt]
            
            graph_width = width - 80
            graph_height = height - 100
            
            self.voltage_time_canvas.create_line(60, 40, 60, 40 + graph_height, fill='#7f8c8d', width=2)
            self.voltage_time_canvas.create_line(60, 40 + graph_height, 60 + graph_width, 40 + graph_height, 
                                             fill='#7f8c8d', width=2)
            
            max_val = 300 
            min_val = 0
            val_range = max_val - min_val if max_val != min_val else 1
            
            # Optimized: Draw fewer points
            points = []
            step = max(1, len(history_temp) // 50)
            for i in range(0, len(history_temp), step):
                temp = history_temp[i]
                x = 60 + (i / max(1, len(history_temp)-1)) * graph_width
                y = 40 + graph_height - ((temp - min_val) / val_range) * graph_height
                points.append((x, y))
            
            if len(points) > 1:
                self.voltage_time_canvas.create_line(points, fill='#e74c3c', width=2)
            elif len(points) == 1:
                x, y = points[0]
                self.voltage_time_canvas.create_oval(x-2, y-2, x+2, y+2, fill='#e74c3c', outline='#e74c3c')
            
            danger_y = 40 + graph_height - ((200 - min_val) / val_range) * graph_height
            if 40 <= danger_y <= 40 + graph_height:
                self.voltage_time_canvas.create_line(60, danger_y, 60 + graph_width, danger_y,
                                                 fill='#f1c40f', width=2, dash=(5, 2))
                self.voltage_time_canvas.create_text(55, danger_y, text="200", anchor='e',
                                                 font=('Arial', 8), fill='#f1c40f')
            
            if history_temp:
                current_val = history_temp[-1]
                self.voltage_time_canvas.create_text(width/2, 20, 
                                                 text=f"Current: {current_val:.1f}°C", 
                                                 font=('Arial', 12, 'bold'), fill='#ecf0f1')
            
            self.voltage_time_canvas.create_text(width/2, height-20, text="Time →", 
                                             font=('Arial', 10), fill='#bdc3c7')
            self.voltage_time_canvas.create_text(20, height/2, text="Temperature (°C)", angle=90,
                                             font=('Arial', 10), fill='#bdc3c7')
        else:
            self.voltage_time_canvas.create_text(width/2, height/2, 
                                             text="No data available\nConnect to device", 
                                             font=('Arial', 12), fill='#bdc3c7')

    # ==================== SPEED METER VISUALIZATIONS ====================
    
    def create_gas_speed_meter(self):
        canvas = tk.Canvas(self.gas_viz_container, bg='#2c3e50', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.gas_speed_canvas = canvas
        canvas.bind('<Configure>', lambda e: self.update_gas_speed_meter())
        
    def update_gas_speed_meter(self):
        if not hasattr(self, 'gas_speed_canvas') or not self.gas_speed_canvas.winfo_exists():
            return
            
        # Use filtered value for display
        value = min(self.sensor_data['gas']['value'], 1000)  # Cap at 1000
        self.gas_speed_canvas.delete("all")
        
        width = self.gas_speed_canvas.winfo_width()
        height = self.gas_speed_canvas.winfo_height()
        
        if width < 10 or height < 10:
            return
        
        center_x, center_y = width/2, height/2 + 20
        radius = min(width, height) / 3
        
        start_angle = 135
        extent = 270
        
        # Set gas sensor range to 0-1000
        max_val = 1000
        min_val = 0
        
        # Color zones for gas sensor (0-1000 range)
        safe_end = 350/max_val * extent
        danger_end = extent - safe_end

        # Draw the gauge background
        self.gas_speed_canvas.create_arc(center_x-radius, center_y-radius, center_x+radius, center_y+radius,
                                         start=start_angle, extent=safe_end, outline='#27ae60', width=15, style=tk.ARC)
        self.gas_speed_canvas.create_arc(center_x-radius, center_y-radius, center_x+radius, center_y+radius,
                                         start=start_angle+safe_end, extent=danger_end, outline='#e74c3c', width=15, style=tk.ARC)
        
        # Draw needle
        needle_angle = start_angle + (min(max(value, min_val), max_val) / max_val) * extent
        rad_angle = math.radians(needle_angle)
        needle_x = center_x + (radius-10) * math.cos(rad_angle)
        needle_y = center_y - (radius-10) * math.sin(rad_angle)
        
        self.gas_speed_canvas.create_line(center_x, center_y, needle_x, needle_y, fill='#ffffff', width=4)
        
        # Draw center circle
        self.gas_speed_canvas.create_oval(center_x-10, center_y-10, center_x+10, center_y+10,
                                         fill='#34495e', outline='#ffffff', width=2)
        
        # Draw value and label
        self.gas_speed_canvas.create_text(width/2, 40, text=f"{value:.0f} PPM", 
                                         font=('Arial', 16, 'bold'), fill='#ecf0f1')
        self.gas_speed_canvas.create_text(width/2, 70, text="Gas Level", 
                                         font=('Arial', 12), fill='#bdc3c7')
        
        # Draw scale marks (0-1000 range) - reduced number for performance
        for i in range(0, 1001, 250):
            mark_angle = start_angle + (i / max_val) * extent
            rad_mark = math.radians(mark_angle)
            
            inner_radius = radius - 20
            outer_radius = radius
            inner_x = center_x + inner_radius * math.cos(rad_mark)
            inner_y = center_y - inner_radius * math.sin(rad_mark)
            outer_x = center_x + outer_radius * math.cos(rad_mark)
            outer_y = center_y - outer_radius * math.sin(rad_mark)
            
            self.gas_speed_canvas.create_line(inner_x, inner_y, outer_x, outer_y, fill='#ecf0f1', width=2)
            
            label_radius = radius - 35
            label_x = center_x + label_radius * math.cos(rad_mark)
            label_y = center_y - label_radius * math.sin(rad_mark)
            self.gas_speed_canvas.create_text(label_x, label_y, text=str(i),
                                             font=('Arial', 8), fill='#bdc3c7')

    def create_ldr_speed_meter(self):
        canvas = tk.Canvas(self.ldr_viz_container, bg='#2c3e50', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.ldr_speed_canvas = canvas
        canvas.bind('<Configure>', lambda e: self.update_ldr_speed_meter())
        
    def update_ldr_speed_meter(self):
        if not hasattr(self, 'ldr_speed_canvas') or not self.ldr_speed_canvas.winfo_exists():
            return
            
        # Use filtered value for display
        value = self.sensor_data['ldr']['value']
        self.ldr_speed_canvas.delete("all")
        
        width = self.ldr_speed_canvas.winfo_width()
        height = self.ldr_speed_canvas.winfo_height()
        
        if width < 10 or height < 10:
            return
        
        center_x, center_y = width/2, height/2 + 20
        radius = min(width, height) / 3
        
        start_angle = 135
        extent = 270
        
        max_val = 4095
        
        # Color zones for LDR
        dark_end = 1500 / max_val * extent
        bright_end = extent - dark_end
        
        self.ldr_speed_canvas.create_arc(center_x-radius, center_y-radius, center_x+radius, center_y+radius,
                                         start=start_angle, extent=dark_end, outline='#3498db', width=15, style=tk.ARC)
        self.ldr_speed_canvas.create_arc(center_x-radius, center_y-radius, center_x+radius, center_y+radius,
                                         start=start_angle+dark_end, extent=bright_end, outline='#e74c3c', width=15, style=tk.ARC)
        
        needle_angle = start_angle + (min(max(value, 0), max_val) / max_val) * extent
        rad_angle = math.radians(needle_angle)
        needle_x = center_x + (radius-10) * math.cos(rad_angle)
        needle_y = center_y - (radius-10) * math.sin(rad_angle)
        
        self.ldr_speed_canvas.create_line(center_x, center_y, needle_x, needle_y, fill='#ffffff', width=4)
        
        self.ldr_speed_canvas.create_oval(center_x-10, center_y-10, center_x+10, center_y+10,
                                         fill='#34495e', outline='#ffffff', width=2)
        
        self.ldr_speed_canvas.create_text(width/2, 40, text=f"{value:.0f}", 
                                         font=('Arial', 16, 'bold'), fill='#ecf0f1')
        self.ldr_speed_canvas.create_text(width/2, 70, text="Light Level", 
                                         font=('Arial', 12), fill='#bdc3c7')
        
        # Reduced number of marks for performance
        for i in [0, 1024, 2048, 3072, 4095]:
            mark_angle = start_angle + (i / max_val) * extent
            rad_mark = math.radians(mark_angle)
            
            inner_radius = radius - 20
            outer_radius = radius
            inner_x = center_x + inner_radius * math.cos(rad_mark)
            inner_y = center_y - inner_radius * math.sin(rad_mark)
            outer_x = center_x + outer_radius * math.cos(rad_mark)
            outer_y = center_y - outer_radius * math.sin(rad_mark)
            
            self.ldr_speed_canvas.create_line(inner_x, inner_y, outer_x, outer_y, fill='#ecf0f1', width=2)
            
            label_radius = radius - 35
            label_x = center_x + label_radius * math.cos(rad_mark)
            label_y = center_y - label_radius * math.sin(rad_mark)
            self.ldr_speed_canvas.create_text(label_x, label_y, text=str(i),
                                             font=('Arial', 8), fill='#bdc3c7')

    def create_voltage_speed_meter(self):
        canvas = tk.Canvas(self.voltage_viz_container, bg='#2c3e50', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.voltage_speed_canvas = canvas
        canvas.bind('<Configure>', lambda e: self.update_voltage_speed_meter())
        
    def update_voltage_speed_meter(self):
        if not hasattr(self, 'voltage_speed_canvas') or not self.voltage_speed_canvas.winfo_exists():
            return

        # Use filtered value for display
        value_volt = self.sensor_data['voltage']['value']
        value_temp = min(value_volt * 100, 300)
        
        self.voltage_speed_canvas.delete("all")
        
        width = self.voltage_speed_canvas.winfo_width()
        height = self.voltage_speed_canvas.winfo_height()
        
        if width < 10 or height < 10:
            return
        
        center_x, center_y = width/2, height/2 + 20
        radius = min(width, height) / 3
        
        start_angle = 135
        extent = 270
        max_val = 300
        
        # Color zones for temperature
        safe_end = 100/max_val * extent
        warning_end = (200/max_val * extent) - safe_end
        danger_end = extent - (safe_end + warning_end)

        self.voltage_speed_canvas.create_arc(center_x-radius, center_y-radius, center_x+radius, center_y+radius,
                                         start=start_angle, extent=safe_end, outline='#27ae60', width=15, style=tk.ARC)
        self.voltage_speed_canvas.create_arc(center_x-radius, center_y-radius, center_x+radius, center_y+radius,
                                         start=start_angle+safe_end, extent=warning_end, outline='#f1c40f', width=15, style=tk.ARC)
        self.voltage_speed_canvas.create_arc(center_x-radius, center_y-radius, center_x+radius, center_y+radius,
                                         start=start_angle+safe_end+warning_end, extent=danger_end, outline='#e74c3c', width=15, style=tk.ARC)
        
        needle_angle = start_angle + (min(max(value_temp, 0), max_val) / max_val) * extent
        rad_angle = math.radians(needle_angle)
        needle_x = center_x + (radius-10) * math.cos(rad_angle)
        needle_y = center_y - (radius-10) * math.sin(rad_angle)
        
        self.voltage_speed_canvas.create_line(center_x, center_y, needle_x, needle_y, fill='#ffffff', width=4)
        
        self.voltage_speed_canvas.create_oval(center_x-10, center_y-10, center_x+10, center_y+10,
                                         fill='#34495e', outline='#ffffff', width=2)
        
        self.voltage_speed_canvas.create_text(width/2, 40, text=f"{value_temp:.1f}°C", 
                                         font=('Arial', 16, 'bold'), fill='#ecf0f1')
        self.voltage_speed_canvas.create_text(width/2, 70, text="Temperature", 
                                         font=('Arial', 12), fill='#bdc3c7')
        
        # Reduced number of marks for performance
        for i in range(0, 301, 100):
            mark_angle = start_angle + (i / max_val) * extent
            rad_mark = math.radians(mark_angle)
            
            inner_radius = radius - 20
            outer_radius = radius
            inner_x = center_x + inner_radius * math.cos(rad_mark)
            inner_y = center_y - inner_radius * math.sin(rad_mark)
            outer_x = center_x + outer_radius * math.cos(rad_mark)
            outer_y = center_y - outer_radius * math.sin(rad_mark)
            
            self.voltage_speed_canvas.create_line(inner_x, inner_y, outer_x, outer_y, fill='#ecf0f1', width=2)
            
            label_radius = radius - 35
            label_x = center_x + label_radius * math.cos(rad_mark)
            label_y = center_y - label_radius * math.sin(rad_mark)
            self.voltage_speed_canvas.create_text(label_x, label_y, text=str(i),
                                             font=('Arial', 8), fill='#bdc3c7')

    # ==================== DIGITAL VERSION VISUALIZATIONS ====================
    
    def create_gas_digital_version(self):
        canvas = tk.Canvas(self.gas_viz_container, bg='#2c3e50', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.gas_digital_canvas = canvas
        canvas.bind('<Configure>', lambda e: self.update_gas_digital_version())
        
    def update_gas_digital_version(self):
        if not hasattr(self, 'gas_digital_canvas') or not self.gas_digital_canvas.winfo_exists():
            return
            
        # Use filtered value for display
        value = min(self.sensor_data['gas']['value'], 1000)  # Cap at 1000
        self.gas_digital_canvas.delete("all")
        
        width = self.gas_digital_canvas.winfo_width()
        height = self.gas_digital_canvas.winfo_height()
        
        if width < 10 or height < 10:
            return
        
        # Draw digital display background
        self.gas_digital_canvas.create_rectangle(20, height/2-60, width-20, height/2+60,
                                                 fill='#1a1a1a', outline='#2ecc71', width=3)
        
        # Draw large digital value
        self.gas_digital_canvas.create_text(width/2, height/2-10,
                                            text=f"{value:04.0f}", font=('Arial', 48, 'bold'),
                                            fill='#2ecc71')
        
        # Draw unit label
        self.gas_digital_canvas.create_text(width/2, height/2+35,
                                            text="PPM", font=('Arial', 16, 'bold'),
                                            fill='#2ecc71')
        
        # Draw status indicator
        status = "DANGER" if value > 350 else "NORMAL"
        color = '#ff0000' if value > 350 else '#2ecc71'
        self.gas_digital_canvas.create_text(width/2, 40,
                                            text=status, font=('Arial', 18, 'bold'),
                                            fill=color)
        
        # Draw threshold info
        self.gas_digital_canvas.create_text(width/2, height-30,
                                            text=f"Danger level: 350 PPM", 
                                            font=('Arial', 12),
                                            fill='#bdc3c7')

    def create_ldr_digital_version(self):
        canvas = tk.Canvas(self.ldr_viz_container, bg='#2c3e50', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.ldr_digital_canvas = canvas
        canvas.bind('<Configure>', lambda e: self.update_ldr_digital_version())
        
    def update_ldr_digital_version(self):
        if not hasattr(self, 'ldr_digital_canvas') or not self.ldr_digital_canvas.winfo_exists():
            return

        # Use filtered value for display
        value = self.sensor_data['ldr']['value']
        self.ldr_digital_canvas.delete("all")
        
        width = self.ldr_digital_canvas.winfo_width()
        height = self.ldr_digital_canvas.winfo_height()
        
        if width < 10 or height < 10:
            return
        
        self.ldr_digital_canvas.create_rectangle(20, height/2-60, width-20, height/2+60,
                                                 fill='#1a1a1a', outline='#f39c12', width=3)
        
        self.ldr_digital_canvas.create_text(width/2, height/2-10,
                                            text=f"{value:04.0f}", font=('Arial', 48, 'bold'),
                                            fill='#f39c12')
        
        self.ldr_digital_canvas.create_text(width/2, height/2+35,
                                            text="ADC", font=('Arial', 16, 'bold'),
                                            fill='#f39c12')
        
        status = "BRIGHT" if value > 1500 else "DARK"
        color = '#e74c3c' if value > 1500 else '#3498db'
        self.ldr_digital_canvas.create_text(width/2, 40,
                                            text=status, font=('Arial', 18, 'bold'),
                                            fill=color)
        
        self.ldr_digital_canvas.create_text(width/2, height-30,
                                            text=f"LED Threshold: 1500 ADC",
                                            font=('Arial', 12),
                                            fill='#bdc3c7')

    def create_voltage_digital_version(self):
        canvas = tk.Canvas(self.voltage_viz_container, bg='#2c3e50', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.voltage_digital_canvas = canvas
        canvas.bind('<Configure>', lambda e: self.update_voltage_digital_version())
        
    def update_voltage_digital_version(self):
        if not hasattr(self, 'voltage_digital_canvas') or not self.voltage_digital_canvas.winfo_exists():
            return

        # Use filtered value for display
        value_volt = self.sensor_data['voltage']['value']
        value_temp = min(value_volt * 100, 300)
        
        self.voltage_digital_canvas.delete("all")
        
        width = self.voltage_digital_canvas.winfo_width()
        height = self.voltage_digital_canvas.winfo_height()
        
        if width < 10 or height < 10:
            return
        
        self.voltage_digital_canvas.create_rectangle(20, height/2-60, width-20, height/2+60,
                                                 fill='#1a1a1a', outline='#e74c3c', width=3)
        
        self.voltage_digital_canvas.create_text(width/2, height/2-10,
                                            text=f"{value_temp:05.1f}", font=('Arial', 48, 'bold'),
                                            fill='#e74c3c')
        
        self.voltage_digital_canvas.create_text(width/2, height/2+35,
                                            text="°C", font=('Arial', 16, 'bold'),
                                            fill='#e74c3c')
        
        status = "CRITICAL" if value_temp > 200 else "NORMAL"
        color = '#ff0000' if value_temp > 200 else '#2ecc71'
        self.voltage_digital_canvas.create_text(width/2, 40,
                                            text=status, font=('Arial', 18, 'bold'),
                                            fill=color)
        
        self.voltage_digital_canvas.create_text(width/2, height-30,
                                            text=f"Max safe temp: 200.0°C",
                                            font=('Arial', 12),
                                            fill='#bdc3c7')

    # --- Cleanup ---
    def on_closing(self):
        """Called when the window is closed."""
        self.stop_serial()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SensorMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()