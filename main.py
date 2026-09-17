
import sys
import os
import time
import platform
import traceback

from dotenv import load_dotenv
from google import genai
import pyperclip

from pynput import keyboard
from pynput.keyboard import Key, Controller

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QComboBox,
)

from PySide6.QtCore import (
    Qt,
    QObject,
    Signal,
    QThread,
)


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "QuickTranslate"

# Default language when using the main shortcut
DEFAULT_LANGUAGE = "French"

# Gemini model
GEMINI_MODEL = "gemini-3.6-flash"

# Small delay after simulated copy/paste
COPY_DELAY = 0.15
PASTE_DELAY = 0.15


# ============================================================
# GEMINI SETUP
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found in .env file"
    )

client = genai.Client(
    api_key=api_key
)


# ============================================================
# KEYBOARD CONTROLLER
# ============================================================

keyboard_controller = Controller()


# ============================================================
# PLATFORM HELPERS
# ============================================================

IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"


def get_copy_hotkey():
    """
    Returns the correct copy shortcut for the OS.
    """

    if IS_MAC:
        return [Key.cmd, "c"]

    return [Key.ctrl, "c"]


def get_paste_hotkey():
    """
    Returns the correct paste shortcut for the OS.
    """

    if IS_MAC:
        return [Key.cmd, "v"]

    return [Key.ctrl, "v"]


def press_hotkey(keys):
    """
    Simulate a keyboard shortcut.
    """

    modifier = keys[0]
    key = keys[1]

    keyboard_controller.press(modifier)
    keyboard_controller.press(key)

    keyboard_controller.release(key)
    keyboard_controller.release(modifier)


# ============================================================
# CLIPBOARD FUNCTIONS
# ============================================================

def read_clipboard():
    """
    Read current clipboard text.
    """

    try:
        return pyperclip.paste()
    except Exception:
        return ""


def write_clipboard(text):
    """
    Write text to clipboard.
    """

    try:
        pyperclip.copy(text)
        return True
    except Exception:
        return False


# ============================================================
# GEMINI TRANSLATION WORKER
# ============================================================

class TranslationWorker(QObject):

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, text, language):
        super().__init__()

        self.text = text
        self.language = language


    def run(self):

        prompt = f"""
Translate the following English text into
professional {self.language}.

This is a real-time desktop translation tool.

STRICT RULES:

- Return ONLY the translation.
- Do not explain anything.
- Do not add commentary.
- Do not summarize.
- Do not omit anything.
- Preserve the exact meaning.
- Preserve the original paragraph structure.
- Preserve line breaks whenever possible.
- Preserve punctuation where appropriate.
- Preserve names exactly.
- Preserve company names exactly.
- Preserve invoice numbers exactly.
- Preserve reference numbers exactly.
- Preserve amounts exactly.
- Preserve currencies exactly.
- Preserve dates exactly.
- Preserve times exactly.
- Preserve email addresses exactly.
- Preserve URLs exactly.
- Preserve product names exactly.
- Preserve codes and identifiers exactly.
- Do not convert numbers unnecessarily.
- Use natural professional business language.
- Do not make the translation more formal than necessary.
- Do not add information that is not present in the source.

English text:

{self.text}
"""

        try:

            stream = client.models.generate_content_stream(
                model=GEMINI_MODEL,
                contents=prompt
            )

            translated_text = ""

            for chunk in stream:
                if hasattr(chunk, 'text'):
                    translated_text += chunk.text


            translated_text = translated_text.strip()

            if not translated_text:

                self.error.emit(
                    "Gemini returned an empty translation."
                )

                return

            print("GEMINI TRANSLATION:", repr(translated_text))
            self.finished.emit(
                translated_text
            )


        except Exception as e:
            import traceback
            traceback.print_exc()

            self.error.emit(
                str(e)
            )


# ============================================================
# QUICKTRANSLATE
# ============================================================

class QuickTranslate(QWidget):

    # Signals from global keyboard listener
    hotkey_triggered = Signal(str)

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            APP_NAME
        )

        self.setFixedSize(
            500,
            520
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # The window is NOT always-on-top.
        # ----------------------------------------------------

        self.translation_running = False

        self.original_clipboard = ""

        self.current_language = (
            DEFAULT_LANGUAGE
        )

        self.create_ui()

        # Connect global hotkey signal
        self.hotkey_triggered.connect(
            self.handle_global_hotkey
        )

        # Start global keyboard listener
        self.start_global_hotkeys()


    # ========================================================
    # USER INTERFACE
    # ========================================================

    def create_ui(self):

        layout = QVBoxLayout()


        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        title = QLabel(
            "QuickTranslate"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
            """
        )

        layout.addWidget(
            title
        )


        # ----------------------------------------------------
        # Description
        # ----------------------------------------------------

        description = QLabel(
            "Select text anywhere and use the keyboard shortcut."
        )

        description.setAlignment(
            Qt.AlignCenter
        )

        description.setStyleSheet(
            "color: gray;"
        )

        layout.addWidget(
            description
        )


        # ----------------------------------------------------
        # English input
        # ----------------------------------------------------

        input_label = QLabel(
            "English"
        )

        layout.addWidget(
            input_label
        )


        self.input_box = QTextEdit()

        self.input_box.setPlaceholderText(
            "Enter English text here..."
        )

        layout.addWidget(
            self.input_box
        )


        # ----------------------------------------------------
        # Language selection
        # ----------------------------------------------------

        language_layout = QHBoxLayout()


        language_label = QLabel(
            "Translate to:"
        )


        self.language_dropdown = QComboBox()

        self.language_dropdown.addItems(
            [
                "French",
                "Dutch",
                "German"
            ]
        )


        self.language_dropdown.setCurrentText(
            DEFAULT_LANGUAGE
        )


        self.language_dropdown.currentTextChanged.connect(
            self.language_changed
        )


        language_layout.addWidget(
            language_label
        )

        language_layout.addWidget(
            self.language_dropdown
        )


        layout.addLayout(
            language_layout
        )


        # ----------------------------------------------------
        # Manual clipboard button
        # ----------------------------------------------------

        self.paste_button = QPushButton(
            "Paste from Clipboard"
        )

        self.paste_button.clicked.connect(
            self.paste_from_clipboard
        )

        layout.addWidget(
            self.paste_button
        )


        # ----------------------------------------------------
        # Translate button
        # ----------------------------------------------------

        self.translate_button = QPushButton(
            "Translate"
        )

        self.translate_button.clicked.connect(
            self.translate_manual
        )

        layout.addWidget(
            self.translate_button
        )


        # ----------------------------------------------------
        # Output
        # ----------------------------------------------------

        output_label = QLabel(
            "Translation"
        )

        layout.addWidget(
            output_label
        )


        self.output_box = QTextEdit()

        self.output_box.setReadOnly(
            True
        )

        self.output_box.setPlaceholderText(
            "Translation will appear here..."
        )

        layout.addWidget(
            self.output_box
        )


        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self.status_label = QLabel(
            "Ready"
        )

        self.status_label.setAlignment(
            Qt.AlignCenter
        )

        self.status_label.setStyleSheet(
            "color: gray;"
        )

        layout.addWidget(
            self.status_label
        )


        # ----------------------------------------------------
        # Bottom buttons
        # ----------------------------------------------------

        button_layout = QHBoxLayout()


        self.copy_button = QPushButton(
            "Copy"
        )

        self.copy_button.clicked.connect(
            self.copy_translation
        )


        self.clear_button = QPushButton(
            "Clear"
        )

        self.clear_button.clicked.connect(
            self.clear_text
        )


        button_layout.addWidget(
            self.copy_button
        )

        button_layout.addWidget(
            self.clear_button
        )


        layout.addLayout(
            button_layout
        )


        # ----------------------------------------------------
        # Shortcut information
        # ----------------------------------------------------

        shortcut_label = QLabel(
            "⌘ + Shift + T  →  French\n"
            "⌘ + Shift + D  →  Dutch\n"
            "⌘ + Shift + G  →  German"
        )

        shortcut_label.setAlignment(
            Qt.AlignCenter
        )

        shortcut_label.setStyleSheet(
            """
            color: gray;
            font-size: 11px;
            margin-top: 5px;
            """
        )

        layout.addWidget(
            shortcut_label
        )


        self.setLayout(
            layout
        )


    # ========================================================
    # LANGUAGE CHANGED
    # ========================================================

    def language_changed(self, language):

        self.current_language = language


    # ========================================================
    # START GLOBAL HOTKEYS
    # ========================================================

    def start_global_hotkeys(self):

        if IS_MAC:

            hotkeys = {
                "<cmd>+<shift>+t":
                    lambda:
                    self.hotkey_triggered.emit(
                        "French"
                    ),

                "<cmd>+<shift>+d":
                    lambda:
                    self.hotkey_triggered.emit(
                        "Dutch"
                    ),

                "<cmd>+<shift>+g":
                    lambda:
                    self.hotkey_triggered.emit(
                        "German"
                    ),
            }

        else:

            hotkeys = {
                "<ctrl>+<shift>+t":
                    lambda:
                    self.hotkey_triggered.emit(
                        "French"
                    ),

                "<ctrl>+<shift>+d":
                    lambda:
                    self.hotkey_triggered.emit(
                        "Dutch"
                    ),

                "<ctrl>+<shift>+g":
                    lambda:
                    self.hotkey_triggered.emit(
                        "German"
                    ),
            }


        self.hotkey_listener = (
            keyboard.GlobalHotKeys(
                hotkeys
            )
        )

        self.hotkey_listener.start()


    # ========================================================
    # GLOBAL HOTKEY HANDLER
    # ========================================================

    def handle_global_hotkey(
        self,
        language
    ):
        print("HOTKEY DETECTED:", language)
        # Don't allow another translation
        # while one is already running.
        if self.translation_running:

            return


        self.current_language = language


        # Update UI language selector
        self.language_dropdown.setCurrentText(
            language
        )


        # ----------------------------------------------------
        # IMPORTANT:
        #
        # We DO NOT activate/show our window here.
        #
        # The user's current application must remain focused
        # so that Cmd+C copies the selected text.
        # ----------------------------------------------------

        self.capture_selected_text(
            language
        )


    # ========================================================
    # CAPTURE SELECTED TEXT
    # ========================================================

    def capture_selected_text(
        self,
        language
    ):

        self.translation_running = True

        self.status_label.setText(
            "Capturing selected text..."
        )


        # ----------------------------------------------------
        # Save existing clipboard
        # ----------------------------------------------------

        self.original_clipboard = (
            read_clipboard()
        )


        # ----------------------------------------------------
        # Copy selected text
        # ----------------------------------------------------

        try:

            copy_keys = (
                get_copy_hotkey()
            )

            press_hotkey(
                copy_keys
            )

        except Exception as e:

            self.translation_failed(
                f"Could not copy selected text:\n{e}"
            )

            return


        # Give the source application
        # a moment to update clipboard.
        time.sleep(
            COPY_DELAY
        )


        # ----------------------------------------------------
        # Read selected text
        # ----------------------------------------------------

        selected_text = read_clipboard()
        print("SELECTED TEXT:", repr(selected_text))
        
        


        if not selected_text.strip():

            self.translation_failed(
                "No text was selected."
            )

            return


        # ----------------------------------------------------
        # Start background translation
        # ----------------------------------------------------

        self.start_translation(
            selected_text,
            language,
            automatic=True
        )


    # ========================================================
    # START TRANSLATION
    # ========================================================

    def start_translation(
        self,
        text,
        language,
        automatic=False
    ):

        self.status_label.setText(
            "Translating..."
        )


        # ----------------------------------------------------
        # Show our window only for manual translation.
        #
        # For automatic translation we keep the source
        # application in focus.
        # ----------------------------------------------------

        if not automatic:

            self.show()
            self.raise_()
            self.activateWindow()


        # ----------------------------------------------------
        # Create worker
        # ----------------------------------------------------

        self.thread = QThread()

        self.worker = TranslationWorker(
            text,
            language
        )


        self.worker.moveToThread(
            self.thread
        )


        # ----------------------------------------------------
        # Signals
        # ----------------------------------------------------

        self.thread.started.connect(
            self.worker.run
        )


        self.worker.finished.connect(
            self.translation_finished
        )


        self.worker.error.connect(
            self.translation_failed
        )


        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.error.connect(
            self.thread.quit
        )


        self.thread.finished.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )


        # Start background thread
        self.thread.start()


    # ========================================================
    # TRANSLATION FINISHED
    # ========================================================

    def translation_finished(
        self,
        translated_text
    ):

        self.output_box.setPlainText(
            translated_text
        )


        self.status_label.setText(
            "Translation complete."
        )


        # ----------------------------------------------------
        # Automatic replacement
        # ----------------------------------------------------

        if self.translation_running:

            self.replace_selected_text(
                translated_text
            )

        else:

            self.translation_running = False


    # ========================================================
    # REPLACE SELECTED TEXT
    # ========================================================

    def replace_selected_text(
        self,
        translated_text
    ):

        # ----------------------------------------------------
        # Put translation into clipboard
        # ----------------------------------------------------

        if not write_clipboard(
            translated_text
        ):

            self.translation_failed(
                "Could not write translation to clipboard."
            )

            return


        # ----------------------------------------------------
        # Paste into the original application
        #
        # IMPORTANT:
        # The source application is still supposed to have
        # focus because we never activated QuickTranslate.
        # ----------------------------------------------------

        time.sleep(
            PASTE_DELAY
        )


        try:

            paste_keys = (
                get_paste_hotkey()
            )

            press_hotkey(
                paste_keys
            )

        except Exception as e:

            self.translation_failed(
                f"Could not paste translation:\n{e}"
            )

            return


        # ----------------------------------------------------
        # Restore original clipboard
        #
        # We wait briefly so the paste operation has time
        # to complete first.
        # ----------------------------------------------------

        time.sleep(
            0.2
        )


        if self.original_clipboard:

            write_clipboard(
                self.original_clipboard
            )


        self.status_label.setText(
            "Text replaced successfully."
        )


        self.translation_running = False


    # ========================================================
    # TRANSLATION FAILED
    # ========================================================

    def translation_failed(
        self,
        message
    ):

        self.translation_running = False

        self.status_label.setText(
            "Translation failed."
        )


        self.output_box.setPlainText(
            "Error:\n\n"
            + message
        )


        # Show window so the user can see the error.
        self.show()
        self.raise_()
        self.activateWindow()


    # ========================================================
    # MANUAL TRANSLATION
    # ========================================================

    def translate_manual(self):

        text = (
            self.input_box.toPlainText()
        )


        if not text.strip():

            self.output_box.setPlainText(
                "Please enter some English text."
            )

            return


        self.start_translation(
            text,
            self.language_dropdown.currentText(),
            automatic=False
        )


    # ========================================================
    # PASTE FROM CLIPBOARD
    # ========================================================

    def paste_from_clipboard(self):

        text = read_clipboard()


        if text:

            self.input_box.setPlainText(
                text
            )


    # ========================================================
    # COPY TRANSLATION
    # ========================================================

    def copy_translation(self):

        text = (
            self.output_box.toPlainText()
        )


        if text:

            write_clipboard(
                text
            )


            self.status_label.setText(
                "Translation copied."
            )


    # ========================================================
    # CLEAR
    # ========================================================

    def clear_text(self):

        self.input_box.clear()

        self.output_box.clear()

        self.status_label.setText(
            "Ready"
        )


    # ========================================================
    # CLOSE EVENT
    # ========================================================

    def closeEvent(self, event):

        try:

            self.hotkey_listener.stop()

        except Exception:

            pass


        event.accept()


# ============================================================
# APPLICATION START
# ============================================================

app = QApplication(
    sys.argv
)


window = QuickTranslate()


# ------------------------------------------------------------
# IMPORTANT:
# The application starts normally, but it does NOT stay
# always-on-top.
# ------------------------------------------------------------

window.show()


sys.exit(
    app.exec()
)
