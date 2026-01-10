#!/usr/bin/env python3
"""Centralized Logging - See WTF Is Happening"""
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

def log_info(category, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"{timestamp} | INFO | {category:15} | {message}"
    print(log_line)
    with open(LOG_DIR / 'activity.log', 'a') as f:
        f.write(log_line + '\n')

def log_error(category, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"{timestamp} | ERROR | {category:15} | {message}"
    print(f"\033[91m{log_line}\033[0m")
    with open(LOG_DIR / 'errors.log', 'a') as f:
        f.write(log_line + '\n')

def log_upload(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"{timestamp} | UPLOAD | {message}"
    print(f"\033[92m{log_line}\033[0m")
    with open(LOG_DIR / 'upload.log', 'a') as f:
        f.write(log_line + '\n')

if __name__ == '__main__':
    log_info("TEST", "Logger working!")
    print(f"✅ Logs at: {LOG_DIR}")
