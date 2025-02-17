import asyncio
import threading
import tkinter as tk
from tkinter import ttk

# Correct imports for the Siege-Wizard fork
from buttplug import Client, WebsocketConnector, Device
from buttplug.errors import (ClientError, ConnectorError,
                       ButtplugError)


class IntifaceApp:
    def __init__(self, master):
        self.master = master
        master.title("Intiface Haptic Control")

        self.client = None
        self.device = None

        # Connect Button
        self.connect_button = ttk.Button(
            master, text="Connect to Intiface", command=self.connect_to_intiface
        )
        self.connect_button.pack(pady=10)

        # Vibrate Button (Press and Hold)
        self.vibrate_button = ttk.Button(master, text="Vibrate")
        self.vibrate_button.pack(pady=10)
        self.vibrate_button.bind("<ButtonPress-1>", self.start_vibration)  # Left mouse button press
        self.vibrate_button.bind("<ButtonRelease-1>", self.stop_vibration)  # Left mouse button release
        self.vibrate_button.config(state=tk.DISABLED)  # Disable initially

        # Status Label
        self.status_label = ttk.Label(master, text="Not Connected")
        self.status_label.pack(pady=5)

        # Quit Button
        self.quit_button = ttk.Button(master, text="Quit", command=master.destroy)
        self.quit_button.pack()

        # Asynchronous event loop handling (for Buttplug)
        self.event_loop = asyncio.new_event_loop()  # Create a separate event loop for Buttplug
        self.event_loop_thread = threading.Thread(
            target=self.run_event_loop, daemon=True
        )  # and run it in a separate thread
        self.event_loop_thread.start()

        #bind close button
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)


    def run_event_loop(self):
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()

    def connect_to_intiface(self):
        #Disable connect button to avoid multiple client
        self.connect_button.config(state=tk.DISABLED)
        #Runs the function connect_task in an asyncio task so it doesn't block the ui.
        asyncio.run_coroutine_threadsafe(self.connect_task(), self.event_loop)


    async def connect_task(self):
        """Connects to the Intiface server and scans for devices."""

        self.status_label.config(text="Connecting...")
        self.client = Client("Haptic Control App")  # Use the correct class name

        connector = WebsocketConnector("ws://localhost:12345") # Use the correct class name
        try:
            await self.client.connect(connector)
            self.status_label.config(text="Connected.  Scanning...")
            await self.client.start_scanning()

             # Wait for a device to be found
            while not self.client.devices:
                await asyncio.sleep(0.1) # Short delay.  Don't lock the GUI thread.

            # Assuming we only want the first device
            self.device = list(self.client.devices.values())[0]
            self.status_label.config(text=f"Connected to: {self.device.name}")
            self.vibrate_button.config(state=tk.NORMAL)  # Enable vibrate button
            await self.client.stop_scanning()

        except ClientError as e:
            self.status_label.config(text=f"Connection Error: {e}")
            self.connect_button.config(state=tk.NORMAL) #Re-enable connect button in-case of failure.
            return
        except Exception as e:
            self.status_label.config(text=f"Error: {e}")
            self.connect_button.config(state=tk.NORMAL)
            return

    def start_vibration(self, event=None):
        """Starts vibration at 100% intensity."""
        if self.device:
            asyncio.run_coroutine_threadsafe(self.vibrate_task(1.0), self.event_loop)

    def stop_vibration(self, event=None):
        """Stops the vibration."""
        if self.device:
            asyncio.run_coroutine_threadsafe(self.vibrate_task(0.0), self.event_loop)

    async def vibrate_task(self, intensity):
        """Sends a vibration command to the device.  Handles potential errors."""
        try:
            if hasattr(self.device, 'actuators') and self.device.actuators:
                if hasattr(self.device.actuators[0], 'command'):
                    await self.device.actuators[0].command(intensity)
                else:
                    print(f"Actuator does not have a command")
                    self.status_label.config(text=f"Actuator does not have a command")
            elif hasattr(self.device, 'linear_actuators') and self.device.linear_actuators:
                if hasattr(self.device.linear_actuators[0], 'command'):
                     await self.device.linear_actuators[0].command(250, intensity) #duration, intensity
                else:
                    print(f"Linear Actuator does not have a command")
                    self.status_label.config(text=f"Linear Actuator does not have a command")
            elif hasattr(self.device, 'rotatory_actuators') and self.device.rotatory_actuators:
                if hasattr(self.device.rotatory_actuators[0], 'command'):
                    await self.device.rotatory_actuators[0].command(intensity, True)  # Assuming clockwise
                else:
                    print(f"Rotatory Actuator does not have a command")
                    self.status_label.config(text=f"Rotatory Actuator does not have a command")

            else:
                print("Device doesn't support vibrate commands")
                self.status_label.config(text=f"Device does not support vibrate commands")

        except ConnectorError as e:
            print(f"Device error: {e}")
            self.status_label.config(text=f"Device Error: {e}")
        except ButtplugError as e:
            print(f"Buttplug error: {e}")
            self.status_label.config(text=f"Buttplug Error: {e}")
        except Exception as e:
            print(f"Unexpected error during vibration: {e}")
            self.status_label.config(text=f"Unexpected Error: {e}")

    def on_close(self):
        async def close_client():
            """Safely disconnects the client and closes the application."""
            if self.client:
                try:
                    if self.device and self.device.connected:
                        await self.device.stop()
                    await self.client.disconnect()
                except Exception as e:
                    print(f"Error during disconnection: {e}")
                finally:
                    #Use after to interact with the GUI, to not block the async task.
                    self.master.after(0, self.master.destroy)
            else:
                self.master.destroy()

        if self.client:
            asyncio.run_coroutine_threadsafe(close_client(), self.event_loop)
        else:
            self.master.destroy()

def main():
    root = tk.Tk()
    app = IntifaceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()