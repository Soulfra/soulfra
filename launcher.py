#!/usr/bin/env python3
"""
Soulfra GUI Launcher

Cross-platform desktop launcher with GUI.
Works on Mac, Windows, and Linux.

Usage:
    python3 launcher.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import webbrowser
import os
import sys
import signal
from pathlib import Path

class SoulframaLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Soulfra Ghost Writer Platform")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # Server process
        self.server_process = None
        self.server_running = False

        # Get working directory
        self.working_dir = Path(__file__).parent

        # Setup UI
        self.setup_ui()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """Create the GUI interface"""

        # Header
        header_frame = tk.Frame(self.root, bg="#667eea", height=80)
        header_frame.pack(fill=tk.X)

        title_label = tk.Label(
            header_frame,
            text="SOULFRA",
            font=("Helvetica", 24, "bold"),
            bg="#667eea",
            fg="white"
        )
        title_label.pack(pady=10)

        subtitle_label = tk.Label(
            header_frame,
            text="AI-Powered Ghost Writing Platform",
            font=("Helvetica", 12),
            bg="#667eea",
            fg="white"
        )
        subtitle_label.pack()

        # Status frame
        status_frame = tk.Frame(self.root, padx=20, pady=15)
        status_frame.pack(fill=tk.X)

        tk.Label(status_frame, text="Status:", font=("Helvetica", 11, "bold")).pack(anchor=tk.W)

        self.status_label = tk.Label(
            status_frame,
            text="⚫ Server not running",
            font=("Helvetica", 10),
            fg="gray"
        )
        self.status_label.pack(anchor=tk.W, pady=5)

        self.url_label = tk.Label(
            status_frame,
            text="",
            font=("Helvetica", 10),
            fg="blue",
            cursor="hand2"
        )
        self.url_label.pack(anchor=tk.W)
        self.url_label.bind("<Button-1>", lambda e: self.open_browser())

        # Buttons frame
        buttons_frame = tk.Frame(self.root, padx=20, pady=10)
        buttons_frame.pack(fill=tk.X)

        self.start_button = ttk.Button(
            buttons_frame,
            text="▶ Start Server",
            command=self.start_server,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            buttons_frame,
            text="⏹ Stop Server",
            command=self.stop_server,
            state=tk.DISABLED,
            width=20
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.browser_button = ttk.Button(
            buttons_frame,
            text="🌐 Open Browser",
            command=self.open_browser,
            state=tk.DISABLED,
            width=20
        )
        self.browser_button.pack(side=tk.LEFT, padx=5)

        # Logs frame
        logs_frame = tk.Frame(self.root, padx=20, pady=10)
        logs_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(logs_frame, text="Server Logs:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)

        self.log_text = scrolledtext.ScrolledText(
            logs_frame,
            wrap=tk.WORD,
            width=70,
            height=15,
            font=("Courier", 9),
            bg="black",
            fg="lightgreen"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Footer
        footer_frame = tk.Frame(self.root, bg="#f0f0f0", height=30)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        footer_label = tk.Label(
            footer_frame,
            text="Soulfra v1.0.0 | localhost:5001",
            font=("Helvetica", 8),
            bg="#f0f0f0",
            fg="gray"
        )
        footer_label.pack(pady=5)

    def log(self, message, color=None):
        """Add message to log window"""
        self.log_text.insert(tk.END, message + "\n")
        if color:
            # Color the last line
            self.log_text.tag_add("colored", "end-2l", "end-1l")
            self.log_text.tag_config("colored", foreground=color)
        self.log_text.see(tk.END)
        self.root.update()

    def start_server(self):
        """Start the Flask server"""

        if self.server_running:
            return

        self.log("=" * 60, "yellow")
        self.log("Starting Soulfra server...", "cyan")
        self.log("=" * 60, "yellow")

        # Check Python
        try:
            result = subprocess.run(
                [sys.executable, "--version"],
                capture_output=True,
                text=True
            )
            self.log(f"✓ Python: {result.stdout.strip()}", "green")
        except Exception as e:
            self.log(f"✗ Python check failed: {e}", "red")
            return

        # Check database
        db_path = self.working_dir / "soulfra.db"
        if not db_path.exists():
            self.log("⚠️  Database not found. Please run install.py first", "yellow")
            if not messagebox.askyesno("Database Not Found", "Database not initialized. Continue anyway?"):
                return

        # Start server in background thread
        def run_server():
            try:
                self.server_process = subprocess.Popen(
                    [sys.executable, "app.py"],
                    cwd=self.working_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                self.server_running = True

                # Update UI
                self.root.after(0, lambda: self.start_button.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.stop_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.browser_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.status_label.config(
                    text="🟢 Server running",
                    fg="green"
                ))
                self.root.after(0, lambda: self.url_label.config(
                    text="http://localhost:5001 (click to open)"
                ))

                self.root.after(0, lambda: self.log("✓ Server started successfully!", "green"))
                self.root.after(0, lambda: self.log("URL: http://localhost:5001", "cyan"))

                # Stream output
                for line in self.server_process.stdout:
                    if line.strip():
                        self.root.after(0, lambda l=line: self.log(l.strip()))

            except Exception as e:
                self.root.after(0, lambda: self.log(f"✗ Error starting server: {e}", "red"))
                self.server_running = False

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()

    def stop_server(self):
        """Stop the Flask server"""

        if not self.server_running:
            return

        self.log("=" * 60, "yellow")
        self.log("Stopping server...", "cyan")

        if self.server_process:
            try:
                # Terminate gracefully
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.log("✓ Server stopped", "green")
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                self.server_process.kill()
                self.log("✓ Server force-stopped", "yellow")
            except Exception as e:
                self.log(f"✗ Error stopping server: {e}", "red")

        self.server_running = False
        self.server_process = None

        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.browser_button.config(state=tk.DISABLED)
        self.status_label.config(text="⚫ Server stopped", fg="gray")
        self.url_label.config(text="")

    def open_browser(self):
        """Open browser to Soulfra"""
        if self.server_running:
            webbrowser.open("http://localhost:5001")
            self.log("→ Opened browser", "cyan")
        else:
            messagebox.showwarning("Server Not Running", "Please start the server first")

    def on_closing(self):
        """Handle window close"""
        if self.server_running:
            if messagebox.askyesno("Stop Server?", "Server is running. Stop it before closing?"):
                self.stop_server()
                self.root.destroy()
            else:
                # Let server keep running
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """Launch the GUI"""
    root = tk.Tk()

    # Set window icon (if exists)
    icon_path = Path(__file__).parent / "static" / "favicon.ico"
    if icon_path.exists():
        try:
            root.iconbitmap(icon_path)
        except:
            pass  # Icon not critical

    app = SoulframaLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
