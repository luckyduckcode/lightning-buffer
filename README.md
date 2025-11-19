# Lightning Buffer ⚡

A lightweight, native Windows FastAPI service that acts as an orchestration layer between Telegram bots and Dockerized code-generation engines.

## Overview

Lightning Buffer is designed to be a **single source of truth** that manages:
- Internal Automation API connections (localhost:3000)
- API key management
- File system operations for automation scripts
- Path translation between host and container environments

## Features

- **FastAPI Backend**: High-performance async API with automatic documentation
- **GUI Interface**: Built-in Tkinter GUI for easy monitoring and control
- **Hybrid File Handling**: 
  - Generation & saving via Docker container
  - Listing, reading, deleting via direct Windows file system access
- **Security**: Path traversal protection and optional API key authentication
- **User-Friendly**: Automatic filename generation with timestamps

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/generate` | Generate code and optionally save |
| POST | `/generate-and-run` | Generate, save, and execute immediately |
| POST | `/run` | Execute an existing script |
| GET | `/list` | List all saved automations |
| POST | `/get` | Return the content of a script |
| POST | `/delete` | Delete a script |
| GET | `/health` | Status check for buffer and Docker API |

## Installation

1. Clone the repository:
```bash
git clone https://github.com/luckyduckcode/lightning-buffer.git
cd lightning-buffer
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your `.env` file:
```env
AUTOMATION_API_URL=http://localhost:3000
AUTOMATION_API_KEY=your_api_key_here
AUTOMATIONS_HOST_DIR=D:\AI-Automations
BUFFER_PORT=8000
BUFFER_API_KEY=supersecret123
DEFAULT_MODEL=deepseek-coder:6.7b
MAX_FILENAME_LENGTH=100
```

## Usage

### Development Mode
```bash
start-dev.bat
```
or
```bash
uvicorn main:app --reload --port 8000
```

### Production Mode
```bash
start-prod.bat
```
or
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### GUI Mode
```bash
python gui.py
```

## Project Structure

```
lightning-buffer/
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── utils.py             # Utility functions
├── gui.py               # Tkinter GUI interface
├── .env                 # Environment variables (not in repo)
├── requirements.txt     # Python dependencies
├── start-dev.bat        # Development server script
├── start-prod.bat       # Production server script
└── build_app.bat        # Build standalone executable
```

## Building Standalone Executable

To build a standalone Windows executable:
```bash
build_app.bat
```

The executable will be created in the `dist/` folder.

## Security

- All file operations are validated to prevent directory traversal attacks
- Optional API key authentication between Telegram bot and buffer
- Environment variables for sensitive configuration
- Only allows operations within the configured automations directory

## Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
