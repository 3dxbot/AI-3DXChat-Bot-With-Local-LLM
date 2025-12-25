# ChatBot-Assistant

**ChatBot-Assistant** is a desktop Python application for automating chat interactions in games. It uses computer vision (OCR with pytesseract), browser automation (Playwright), and input control tools (pyautogui) to scan chat, recognize messages, and generate responses through an external service (e.g., AI).

The project is optimized for maximum stability, speed, and fault tolerance: asynchronous code based on asyncio, detailed error handling, state synchronization, and efficient resource usage.

## 🚀 Key Features

- **Automatic Chat Scanning**: The bot continuously monitors a specified screen area, recognizes text using OCR, and analyzes new messages.
- **Nickname Management**: Support for lists of ignored and tracked nicks with fuzzy matching for reliable recognition.
- **Response Generation**: Browser integration for sending requests to an external service (AI) and receiving responses that are then sent to the game.
- **Flexible Responses**: Automatic message processing with action conversion to commands (/me) and sending to the game.
- **Pose Recognition**: Automatic detection and acceptance of pose changes, with user-assisted naming for unknown poses.
- **Intuitive GUI**: Simple Tkinter interface for managing the bot, nick lists, and logs.
- **Hotkeys**: Quick control via F2 (start/pause scanning), F3 (hide/show UI), F4 (clear chat), and Ctrl+language (change translation language).

## 🔧 Requirements and Installation

### Requirements
- Python 3.12+ (3.12.3 recommended for library compatibility).
- Installed Tesseract OCR (specify path in `utils.py` or `config.py`).
- Google Chrome (for Playwright).
- Libraries: Install via `pip install -r requirements.txt` (create file with the following):
  ```
  playwright
  pytesseract
  pillow
  pyautogui
  keyboard
  pyperclip
  pygetwindow
  pywin32
  rapidfuzz  # For optimized fuzzy matching
  numpy  # For image processing in OCR
  opencv-python  # For image preprocessing
  customtkinter  # For modern UI design
  langdetect  # For automatic language detection
  ```

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/your-repo/ChatBot-Assistant.git
   cd ChatBot-Assistant
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```
   playwright install
   ```
4. Configure Tesseract: Specify path in `utils.py` (e.g., `TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`).
5. Run the application:
   ```
   python main.py
   ```

## ⌨️ Controls (Hotkeys)

- **F2**: Start/Pause chat scanning.
- **F3**: Hide/Show bot window.
- **F4**: Clear chat history in browser and bot memory.
- **Ctrl + E**: Change language to English.
- **Ctrl + R**: Change language to Russian.
- **Ctrl + F**: Change language to French.
- **Ctrl + S**: Change language to Spanish.

## 🎭 Pose Management

The bot includes advanced pose recognition and management:

- **Automatic Pose Detection**: Scans for pose change requests and accepts known poses automatically.
- **Unknown Pose Handling**: When an unknown pose is detected, the bot sends a customizable message to the user asking for a description/name.
- **User-Assisted Database Expansion**: Users can provide names for unknown poses, which are then saved to the pose database for future recognition.
- **Language-Specific Messages**: Unknown pose messages can be customized separately for English/other languages and Russian.
- **Pose Notifications**: After accepting poses, the bot notifies the AI service of pose changes for contextual responses.

## ⚙️ First Launch and Setup

On first launch, the bot is in pause mode for setup:

1. **Browser Authorization**: Open browser, log into AI service account.
2. **Area Setup**:
   - Click "Setup Areas" in UI or use F2 for step-by-step setup:
     - Step 1: Hover over top-left chat corner → F2.
     - Step 2: Hover over bottom-right chat corner → F2.
     - Step 3: Click in game text input field → F2.
3. **Game Window Name**: Specify in UI (e.g., "World of Warcraft") for focusing.
4. **Save Settings**: Saved to `chatbot_settings.json`.
5. **Launch**: Press F2 to start scanning.

## 📁 Project Structure

- `main.py`: Entry point, launches UI.
- `src/ui_*.py`: Graphical interface on Tkinter/CustomTkinter.
- `src/bot.py`: Main bot logic (scanning, processing, sending).
- `src/browser.py`: Browser management via Playwright (AI integration).
- `src/chat_processor.py`: Chat processing (nick recognition, fuzzy matching, message formatting).
- `src/utils.py`: Utilities for OCR and text normalization.
- `src/config.py`: Constants (URLs, selectors, paths).
- `README.md`: This file.

## 🛠️ Optimizations and Improvements

- **Asynchrony**: Main loop on asyncio to avoid blocking.
- **Fault Tolerance**: Specific exception handling (TimeoutError, FileNotFoundError, etc.), automatic page reload on errors.
- **Performance**: Optimized fuzzy matching with rapidfuzz, asynchronous browser waits.
- **Security**: Browser sessions saved in `storage_state.json` for reuse.
- **Logging**: Detailed logs in UI and files (`logs/`).

## ⚠️ Important Notes

- **No Runtime Internet**: No package installation in runtime; all dependencies pre-installed.
- **OCR Accuracy**: Depends on screenshot quality; configure language in `utils.py` (e.g., 'rus+eng').
- **License**: MIT (or specify your own).
- **Limitations**: Works only on Windows (due to pywin32 and win32gui); adapt for other OS.

## 🤝 Contributing

PRs for improvements welcome! If you find a bug, create an issue.

## 📧 Contacts

- Author: [Your Name or GitHub]
- Email: anonymicus.anon@gmail.com (from code example)
