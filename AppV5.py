import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Scale
import keyboard
import mouse
import json  # Import the json module
import os

# Correct imports for the Siege-Wizard fork
from buttplug import Client, WebsocketConnector
from buttplug.errors import (ClientError, ConnectorError,
                       ButtplugError)


class IntifaceApp:
    def __init__(self, master):
        self.master = master
        master.title("Intiface Haptic Control")
        master.minsize(300, 250)

        self.client = None
        self.device = None
        self.vibrating = False  # Track vibration state

        # Load keybindings from file, or use defaults
        self.load_keybindings()


        # Styling
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 14), padding=10, borderwidth=2)
        self.style.configure('TLabel', font=('Arial', 12))
        self.style.configure('TMenu', font=('Arial', 12))
        self.style.configure('Horizontal.TScale', troughcolor='gray', sliderthickness=20, sliderlength=30)


        # Instructions
        self.instructions_label = ttk.Label(
            master,
            text="Instructions:\n1. Open and connect your device in Intiface Desktop.\n"
                 "2. Press 'Connect to Intiface' below.\n"
                 "3. Press 'Vibrate' button or hold the bound key (default: Spacebar).",
            justify=tk.LEFT,
            wraplength=280
        )
        self.instructions_label.pack(pady=10, padx=10)

        # Menu Bar
        self.menu_bar = tk.Menu(master)
        self.master.config(menu=self.menu_bar)

        self.options_menu = tk.Menu(self.menu_bar, tearoff=0, font=('Arial', 12))
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        self.options_menu.add_command(label="Rebind Vibration Key", command=self.rebind_vibration_key)
        self.options_menu.add_command(label="Rebind Intensity Increase Key", command=self.rebind_increase_key)
        self.options_menu.add_command(label="Rebind Intensity Decrease Key", command=self.rebind_decrease_key)
        self.options_menu.add_command(label="Set Vibration Intensity", command=self.set_intensity)


        # Connect Button
        self.connect_button = ttk.Button(
            master, text="Connect to Intiface", command=self.connect_to_intiface, style='TButton'
        )
        self.connect_button.pack(pady=10, padx=20, fill=tk.X)

        # Vibrate Button (Press and Hold)
        self.vibrate_button = ttk.Button(master, text="Vibrate", style='TButton')
        self.vibrate_button.pack(pady=5, padx=20, fill=tk.X)
        self.vibrate_button.bind("<ButtonPress-1>", self.start_vibration)
        self.vibrate_button.bind("<ButtonRelease-1>", self.stop_vibration)
        self.vibrate_button.config(state=tk.DISABLED)

        # Status Label
        self.status_label = ttk.Label(master, text="Not Connected", style='TLabel')
        self.status_label.pack(pady=5)

        # Quit Button
        self.quit_button = ttk.Button(master, text="Quit", command=self.quit_app, style='TButton')  # Use quit_app
        self.quit_button.pack(pady=10, padx=20, fill=tk.X)

        # Asynchronous event loop handling (for Buttplug)
        self.event_loop = asyncio.new_event_loop()
        self.event_loop_thread = threading.Thread(
            target=self.run_event_loop, daemon=True
        )
        self.event_loop_thread.start()

        # bind close button
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        # Keyboard binding
        self.update_keyboard_binding()

    def run_event_loop(self):
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()

    def connect_to_intiface(self):
        self.connect_button.config(state=tk.DISABLED)
        asyncio.run_coroutine_threadsafe(self.connect_task(), self.event_loop)

    async def connect_task(self):
        """Connects to Intiface and scans for devices."""

        self.status_label.config(text="Connecting...")
        self.client = Client("Haptic Control App")
        connector = WebsocketConnector("ws://localhost:12345")
        try:
            await self.client.connect(connector)
            self.status_label.config(text="Connected.  Scanning...")
            await self.client.start_scanning()
            while not self.client.devices:
                await asyncio.sleep(0.1)
            self.device = list(self.client.devices.values())[0]
            self.status_label.config(text=f"Connected to: {self.device.name}\nIntensity:{self.vibration_intensity}")
            self.vibrate_button.config(state=tk.NORMAL)
            await self.client.stop_scanning()

        except ClientError as e:
            self.status_label.config(text=f"Connection Error: {e}")
            self.connect_button.config(state=tk.NORMAL)
            return
        except Exception as e:
            self.status_label.config(text=f"Error: {e}")
            self.connect_button.config(state=tk.NORMAL)
            return

    def start_vibration(self, event=None):
        """Starts vibration (GUI button)."""
        if self.device and not self.vibrating:
            self.vibrating = True
            asyncio.run_coroutine_threadsafe(self.vibrate_task(self.vibration_intensity), self.event_loop)  # Use stored intensity
            self.vibrate_button.config(text="Vibrating...")

    def stop_vibration(self, event=None):
        """Stops vibration (GUI button)."""
        if self.device and self.vibrating:
            self.vibrating = False
            asyncio.run_coroutine_threadsafe(self.vibrate_task(0.0), self.event_loop)
            self.vibrate_button.config(text="Vibrate")

    async def vibrate_task(self, intensity):
        """Sends vibration commands, handling potential errors."""
        try:
            if not self.device:  # Early exit if no device
                return

            if hasattr(self.device, 'actuators') and self.device.actuators:
                if hasattr(self.device.actuators[0], 'command'):
                    await self.device.actuators[0].command(intensity)
                else:
                    self.status_label.config(text="Actuator does not have a command")
            elif hasattr(self.device, 'linear_actuators') and self.device.linear_actuators:
                if hasattr(self.device.linear_actuators[0], 'command'):
                    await self.device.linear_actuators[0].command(250, intensity)
                else:
                    self.status_label.config(text="Linear Actuator error")
            elif hasattr(self.device, 'rotatory_actuators') and self.device.rotatory_actuators:
                if hasattr(self.device.rotatory_actuators[0], 'command'):
                    await self.device.rotatory_actuators[0].command(intensity, True)
                else:
                    self.status_label.config(text="Rotatory Actuator error")
            else:
                self.status_label.config(text="Device doesn't support vibrate")

        except (ConnectorError, ButtplugError, Exception) as e:
            print(f"Error during vibration: {e}")
            self.status_label.config(text=f"Error: {e}")

    def on_close(self):
        async def close_client():
            if self.client:
                try:
                    if self.device and self.device.connected:
                        await self.device.stop()
                    await self.client.disconnect()
                except Exception:
                    pass  # Ignore errors during close
                finally:
                    self.master.after(0, self.master.destroy)
            else:
                self.master.destroy()

        if self.client:
            asyncio.run_coroutine_threadsafe(close_client(), self.event_loop)
        else:
            self.master.destroy()

    def rebind_vibration_key(self):
        dialog = KeyRebindDialog(self.master, self, "vibration")
        self.master.wait_window(dialog)

    def rebind_increase_key(self):
        dialog = KeyRebindDialog(self.master, self, "increase")
        self.master.wait_window(dialog)

    def rebind_decrease_key(self):
        dialog = KeyRebindDialog(self.master, self, "decrease")
        self.master.wait_window(dialog)

    def set_intensity(self):
        dialog = IntensityDialog(self.master, self)
        self.master.wait_window(dialog)

    def increase_intensity(self, event=None):
        """Increases the vibration intensity by 0.1, up to a maximum of 1.0."""
        self.vibration_intensity = min(1.0, round(self.vibration_intensity + 0.1, 1))
        if self.device:
            self.status_label.config(text=f"Connected to: {self.device.name}\nIntensity:{self.vibration_intensity}")
        if self.vibrating:  # If already vibrating, update the vibration
             asyncio.run_coroutine_threadsafe(self.vibrate_task(self.vibration_intensity), self.event_loop)


    def decrease_intensity(self, event=None):
        """Decreases the vibration intensity by 0.1, down to a minimum of 0.0."""
        self.vibration_intensity = max(0.0, round(self.vibration_intensity - 0.1, 1))
        if self.device:
            self.status_label.config(text=f"Connected to: {self.device.name}\nIntensity:{self.vibration_intensity}")
        if self.vibrating:  # If already vibrating, update the vibration
            asyncio.run_coroutine_threadsafe(self.vibrate_task(self.vibration_intensity), self.event_loop)

    def update_keyboard_binding(self):
        """Updates keyboard/mouse bindings, unhooking previous ones."""
        keyboard.unhook_all()
        mouse.unhook_all()

        if self.vibration_key in ["left", "middle", "right"]:  # Mouse buttons
            if self.vibration_key == "left":
                mouse.on_button(self.start_vibration_mouse, buttons=(mouse.LEFT,), types=(mouse.DOWN,))
                mouse.on_button(self.stop_vibration_mouse, buttons=(mouse.LEFT,), types=(mouse.UP,))
            elif self.vibration_key == "middle":
                mouse.on_button(self.start_vibration_mouse, buttons=(mouse.MIDDLE,), types=(mouse.DOWN,))
                mouse.on_button(self.stop_vibration_mouse, buttons=(mouse.MIDDLE,), types=(mouse.UP,))
            elif self.vibration_key == "right":
                mouse.on_button(self.start_vibration_mouse, buttons=(mouse.RIGHT,), types=(mouse.DOWN,))
                mouse.on_button(self.stop_vibration_mouse, buttons=(mouse.RIGHT,), types=(mouse.UP,))
        else:  # Keyboard keys
            keyboard.on_press_key(self.vibration_key, self.start_vibration_keyboard)
            keyboard.on_release_key(self.vibration_key, self.stop_vibration_keyboard)

        # Bind intensity increase and decrease keys
        keyboard.on_press_key(self.intensity_increase_key, self.increase_intensity)
        keyboard.on_press_key(self.intensity_decrease_key, self.decrease_intensity)

    def start_vibration_keyboard(self, event):
        """Starts vibration (keyboard event)."""
        if self.device and not self.vibrating:
            self.vibrating = True
            asyncio.run_coroutine_threadsafe(self.vibrate_task(self.vibration_intensity), self.event_loop)  # Use intensity
            self.master.after(0, lambda: self.vibrate_button.config(text="Vibrating..."))

    def stop_vibration_keyboard(self, event):
        """Stops vibration (keyboard event)."""
        if self.device and self.vibrating:
            self.vibrating = False
            asyncio.run_coroutine_threadsafe(self.vibrate_task(0.0), self.event_loop)
            self.master.after(0, lambda: self.vibrate_button.config(text="Vibrate"))

    def start_vibration_mouse(self):
        """Starts vibration (mouse event)."""
        if self.device and not self.vibrating:
            self.vibrating = True
            asyncio.run_coroutine_threadsafe(self.vibrate_task(self.vibration_intensity), self.event_loop)  # Use intensity
            self.master.after(0, lambda: self.vibrate_button.config(text="Vibrating..."))

    def stop_vibration_mouse(self):
        """Stops vibration (mouse event)."""
        if self.device and self.vibrating:
            self.vibrating = False
            asyncio.run_coroutine_threadsafe(self.vibrate_task(0.0), self.event_loop)
            self.master.after(0, lambda: self.vibrate_button.config(text="Vibrate"))

    def load_keybindings(self):
        """Loads keybindings from a JSON file."""
        try:
            with open("keybindings.json", "r") as f:
                bindings = json.load(f)
                self.vibration_key = bindings.get("vibration_key", "space")
                self.intensity_increase_key = bindings.get("intensity_increase_key", "+")
                self.intensity_decrease_key = bindings.get("intensity_decrease_key", "-")
                self.vibration_intensity = bindings.get("vibration_intensity", 1.0)
        except FileNotFoundError:
            # Use default values if file not found
            self.vibration_key = "space"
            self.intensity_increase_key = "+"
            self.intensity_decrease_key = "-"
            self.vibration_intensity = 1.0

    def save_keybindings(self):
        """Saves keybindings to a JSON file."""
        bindings = {
            "vibration_key": self.vibration_key,
            "intensity_increase_key": self.intensity_increase_key,
            "intensity_decrease_key": self.intensity_decrease_key,
            "vibration_intensity" : self.vibration_intensity
        }
        with open("keybindings.json", "w") as f:
            json.dump(bindings, f)

    def quit_app(self):
        """Saves keybindings and destroys the application."""
        self.save_keybindings()
        self.master.destroy()



class KeyRebindDialog(Toplevel):
    def __init__(self, parent, app_instance, key_type):
        super().__init__(parent)
        self.app = app_instance
        self.key_type = key_type  # 'vibration', 'increase', or 'decrease'
        self.title(f"Rebind {key_type.capitalize()} Key")
        self.geometry("300x200")
        self.minsize(500, 175)

        if key_type == "vibration":
            self.label = ttk.Label(self, text="Press the new key or choose a mouse button:", font=('Arial', 12))
            self.label.pack(pady=20)
             # Mouse buttons
            self.mouse_button_frame = ttk.Frame(self)
            self.mouse_button_frame.pack()

            self.left_button = ttk.Button(self.mouse_button_frame, text="Left Mouse", command=lambda: self.set_mouse_button("left"))
            self.left_button.pack(side=tk.LEFT, padx=5)

            self.middle_button = ttk.Button(self.mouse_button_frame, text="Middle Mouse", command=lambda: self.set_mouse_button("middle"))
            self.middle_button.pack(side=tk.LEFT, padx=5)

            self.right_button = ttk.Button(self.mouse_button_frame, text="Right Mouse", command=lambda: self.set_mouse_button("right"))
            self.right_button.pack(side=tk.LEFT, padx=5)
        else:
            self.label = ttk.Label(self, text=f"Press the new key for {key_type.capitalize()}:", font=('Arial', 12))
            self.label.pack(pady=20)
            self.mouse_button_frame = None


        



        self.grab_set()
        self.focus_set()
        self.bind("<Key>", self.key_pressed)
        self.new_key = None


    def set_mouse_button(self, button_name):
        """Sets the vibration key to a mouse button."""
        self.app.vibration_key = button_name
        self.app.update_keyboard_binding()
        messagebox.showinfo("Key Rebound", f"Vibration rebound to: {button_name.capitalize()} Mouse Button", parent=self)
        self.destroy()

    def key_pressed(self, event):
        """Handles key press events within the dialog."""
        try:
            key_name = event.keysym
            if key_name.lower() == "escape":
                self.destroy()
                return

            # Check if the pressed key is already in use
            if self.key_type == "vibration" and key_name == self.app.vibration_key:
                messagebox.showinfo("Same Key", "You are already using this key for vibration.", parent=self)
                return
            elif self.key_type == "increase" and key_name == self.app.intensity_increase_key:
                messagebox.showinfo("Same Key", "You are already using this key for intensity increase.", parent=self)
                return
            elif self.key_type == "decrease" and key_name == self.app.intensity_decrease_key:
                messagebox.showinfo("Same Key", "You are already using this key for intensity decrease.", parent=self)
                return

            # Map Tkinter keysyms to keyboard names
            if key_name == "Shift_L":      key_name = "left shift"
            elif key_name == "Shift_R":    key_name = "right shift"
            elif key_name == "Control_L":  key_name = "left ctrl"
            elif key_name == "Control_R":  key_name = "right ctrl"
            elif key_name == "Alt_L":      key_name = "left alt"
            elif key_name == "Alt_R":      key_name = "right alt"
            elif key_name == "Return":     key_name = "enter"
            elif key_name == "plus":       key_name = "+"  # Handle +
            elif key_name == "minus":      key_name = "-"  # Handle -


            keyboard.parse_hotkey(key_name)

            if self.key_type == "vibration":
                self.app.vibration_key = key_name
            elif self.key_type == "increase":
                self.app.intensity_increase_key = key_name
            elif self.key_type == "decrease":
                self.app.intensity_decrease_key = key_name

            self.app.update_keyboard_binding()
            messagebox.showinfo("Key Rebound", f"{self.key_type.capitalize()} key rebound to: {key_name}", parent=self)
            self.destroy()

        except ValueError:
            messagebox.showerror("Invalid Key", "Invalid key entered.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self)
        finally:
            self.grab_release()


class IntensityDialog(Toplevel):
    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app = app_instance
        self.title("Set Vibration Intensity")
        self.geometry("300x150")
        self.minsize(300, 180)

        self.label = ttk.Label(self, text="Adjust Vibration Intensity:", font=('Arial', 12))
        self.label.pack(pady=10)

        self.intensity_var = tk.DoubleVar(value=self.app.vibration_intensity)  # Use DoubleVar
        self.scale = Scale(self, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL,
                           variable=self.intensity_var, command=self.update_intensity, length=250,
                           sliderlength=20)

        self.scale.pack(pady=5)

        self.ok_button = ttk.Button(self, text="OK", command=self.close_dialog)
        self.ok_button.pack(pady=10)

        self.grab_set()
        self.focus_set()


    def update_intensity(self, value):
        # No need to do anything here, the variable is already updated
        pass

    def close_dialog(self):
        self.app.vibration_intensity = self.intensity_var.get()  # Update the main app's value
        if self.app.device:
            self.app.status_label.config(text=f"Connected to: {self.app.device.name}\nIntensity:{self.app.vibration_intensity}")
        self.destroy()

def main():
    root = tk.Tk()
    app = IntifaceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()