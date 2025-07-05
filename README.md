# Google Calendar Modular Command Platform (MCP)

This project provides a Modular Command Platform (MCP) for interacting with Google Calendar using Python and FastMCP.

## Features
- List, create, update, and delete calendar events
- Search events by keyword
- List all accessible calendars
- Check free/busy times
- Create recurring events
- Re-authenticate and switch Google accounts

## Setup

### 1. Create Google OAuth Credentials
To use this project, you need Google OAuth credentials for the Calendar API:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Under **APIs & Services → Library**, search for and enable **Google Calendar API**.
3. Under **APIs & Services → Credentials**, click **Create Credentials** and select **OAuth client ID**.
4. Choose **Desktop App** as the application type.
5. Download the generated JSON file (e.g., `credentials.json`).
6. Place `credentials.json` in your project directory.

### 2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Or, using [uv](https://github.com/astral-sh/uv) (recommended for modern Python):
   ```bash
   uv pip install -r requirements.txt
   # or, using pyproject.toml
   uv pip install
   ```

### 3. Run the MCP server (FastMCP will handle CLI entry):
   ```bash
   fastmcp server.py
   ```
   For usage with a MCP client, use the following MCP config
   ```
   "gCal": {
      "command": "fastmcp",
      "args": [
        "run",
        "/PATH/TO/FOLDER/server.py"
      ]
    }
   ```

### 4. On first run, authenticate with your Google account in the browser window that opens.

## Usage
- Use the provided MCP tools to interact with your Google Calendar.
- Example operations:
  - List events for a date range
  - Create or update events
  - Check your free/busy status
  - Switch Google accounts with the reauthenticate tool

## Notes
- Requires Python 3.7+
- Make sure `credentials.json` is present for authentication
- Do not call `mcp.run()` explicitly; FastMCP handles it via CLI 
