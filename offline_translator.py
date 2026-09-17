#!/usr/bin/env python3
import sys
import time
import platform

from dotenv import load_dotenv
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

APP_NAME = "OfflineTranslator"

# Default language when using the main shortcut
DEFAULT_LANGUAGE = "French"

# Small delay after simulated copy/paste
COPY_DELAY = 0.05
PASTE_DELAY = 0.05


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
# OFFLINE TRANSLATION WORKER
# ============================================================

class TranslationWorker(QObject):

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, text, language):
        super().__init__()

        self.text = text
        self.language = language

    def run(self):
        # Try offline translation via argostranslate
        try:
            import argostranslate.translate

            # Map language names to argostranate codes
            lang_map = {
                "French": "fr",
                "Spanish": "es",
                "German": "de",
                "Italian": "it",
                "Portuguese": "pt",
                "Russian": "ru",
                "Dutch": "nl",
                "Japanese": "ja",
                "Korean": "ko",
                "Chinese": "zh",
                "Polish": "pl",
                "Swedish": "sv",
                "Danish": "da",
                "Norwegian": "no",
                "Finnish": "fi",
                "Greek": "el",
                "Czech": "cs",
                "Hungarian": "hu",
                "Romanian": "ro",
                "Slovak": "sk",
                "Bulgarian": "bg",
                "Croatian": "hr",
                "Lithuanian": "lt",
                "Latvian": "lv",
                "Estonian": "et",
                "Slovenian": "sl",
                "Malay": "ms",
                "Indonesian": "id",
                "Thai": "th",
                "Vietnamese": "vi",
                "Hindi": "hi",
                "Arabic": "ar",
                "Hebrew": "he",
                "Turkish": "tr",
                "Ukrainian": "uk"
            }

            target_code = lang_map.get(self.language)
            if not target_code:
                self.error.emit(f"Language '{self.language}' not supported for offline translation.")
                return

            # Get installed languages
            installed = argostranslate.translate.get_installed_languages()
            from_lang = next((l for l in installed if l.code == "en"), None)
            to_lang = next((l for l in installed if l.code == target_code), None)

            if from_lang and to_lang:
                translation = from_lang.get_translation(to_lang)
                translated_text = translation.translate(self.text)
                translated_text = translated_text.strip()
                if translated_text:
                    print("OFFLINE TRANSLATION:", repr(translated_text))
                    self.finished.emit(translated_text)
                    return
                else:
                    raise ValueError("Empty translation from offline model")
            else:
                # Try to suggest installing language packages
                available_langs = [(lang.name, lang.code) for lang in installed]
                self.error.emit(
                    f"Language packages not installed. "
                    f"Source: English (en), Target: {self.language} ({target_code}). "
                    f"Available languages: {available_langs}"
                )

        except ImportError:
            self.error.emit(
                "Argostranslate library not installed. "
                "Please install it with: pip install argostranslate"
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(f"Translation error: {str(e)}")


# ========================================================
# USER INTERFACE
# ========================================================

class OfflineTranslator(QWidget):

    # Signals
    hotkey_triggered = Signal(str)

    def __init__(self):
        super().__init__()

        # State variables
        self.translation_running = False
        self.original_clipboard = ""
        self.current_language = DEFAULT_LANGUAGE

        # Set up the UI
        self.create_ui()

        # Start global hotkeys
        self.start_global_hotkeys()

        # Connect signals
        self.hotkey_triggered.connect(self.handle_global_hotkey)

    # ========================================================
    # USER INTERFACE
    # ========================================================

    def create_ui(self):

        self.setWindowTitle(APP_NAME)
        self.setFixedSize(400, 600)

        layout = QVBoxLayout()
        layout.setSpacing(8)  # Standard spacing
        layout.setContentsMargins(15, 15, 15, 15)  # Standard margins

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        title = QLabel(
            APP_NAME
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 3px;
            """
        )

        layout.addWidget(
            title
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
        self.input_box.setMinimumHeight(50)  # Minimum height for usability
        self.input_box.setMaximumHeight(100)  # Maximum height to prevent taking too much space

        layout.addWidget(
            self.input_box
        )
        # Make input box expandable
        layout.setStretch(
            layout.indexOf(self.input_box), 1
        )


        # ----------------------------------------------------
        # Language selection
        # ----------------------------------------------------

        language_layout = QHBoxLayout()


        language_label = QLabel(
            "Translate to:"
        )
        language_label.setFixedSize(80, 28)


        self.language_dropdown = QComboBox()
        self.language_dropdown.setFixedSize(120, 28)  # Compact size

        # Add supported languages
        self.language_dropdown.addItems([
            "French", "Spanish", "German", "Italian", "Portuguese",
            "Russian", "Dutch", "Japanese", "Korean", "Chinese",
            "Polish", "Swedish", "Danish", "Norwegian", "Finnish",
            "Greek", "Czech", "Hungarian", "Romanian", "Slovak",
            "Bulgarian", "Croatian", "Lithuanian", "Latvian", "Estonian",
            "Slovenian", "Malay", "Indonesian", "Thai", "Vietnamese",
            "Hindi", "Arabic", "Hebrew", "Turkish", "Ukrainian"
        ])

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
        self.output_box.setMinimumHeight(60)  # Minimum height for usability
        self.output_box.setMaximumHeight(120)  # Maximum height to prevent taking too much space

        layout.addWidget(
            self.output_box
        )
        # Make output box expandable
        layout.setStretch(
            layout.indexOf(self.output_box), 1
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
        button_layout.setSpacing(5)


        self.copy_button = QPushButton(
            "Copy"
        )
        self.copy_button.setFixedSize(60, 28)
        self.copy_button.clicked.connect(
            self.copy_translation
        )


        self.clear_button = QPushButton(
            "Clear"
        )
        self.clear_button.setFixedSize(60, 28)
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
            "⌃ + Shift + T  →  French\n"
            "⌃ + Shift + S  →  Spanish\n"
            "⌃ + Shift + G  →  German\n"
            "⌃ + Shift + I  →  Italian\n"
            "⌃ + Shift + P  →  Portuguese\n"
            "⌃ + Shift + R  →  Russian\n"
            "⌃ + Shift + D  →  Dutch"
        )

        shortcut_label.setAlignment(
            Qt.AlignCenter
        )

        shortcut_label.setStyleSheet(
            """
            color: gray;
            font-size: 11px;
            margin-top: 2px;
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
                "<ctrl>+<shift>+t":
                    lambda:
                    self.hotkey_triggered.emit(
                        "French"
                    ),

                "<ctrl>+<shift>+s":
                    lambda:
                    self.hotkey_triggered.emit(
                        "Spanish"
                    ),

                "<ctrl>+<shift>+g":
                    lambda:
                    self.hotkey_triggered.emit(
                        "German"
                    ),

                "<ctrl>+<shift>+i":
                    lambda:
                    self.hotkey_triggered.emit(
                        "Italian"
                    ),

                "<ctrl>+<shift>+p":
                    lambda:
                    self.hotkey_triggered.emit(
                        "Portuguese"
                    ),

                "<ctrl>+<shift>+r":
                    lambda:
                    self.hotkey_triggered.emit(
                        "Russian"
                    ),

                "<ctrl>+<shift>+d":
                    lambda:
                    self.hotkey_triggered.emit(
                        "Dutch"
                    ),
            }

        else:

            hotkeys = {
                "<ctrl>+<shift>+t":
                    lambda:
                    self.hotkey_triggered.emit(
                        "French"
                    ),

                "<ctrl>+<shift>+s":
                    lambda:
                    self.hotkey_triggered.emit(
                        "Spanish"
                    ),

                "<ctrl>+<shift>+g":
                    lambda:
                    self.hotkey_triggered.emit(
                        "German"
                    ),

                "<ctrl>+<shift>+i":
                    lambda:
                    self.hotkey_triggered.emit(
                        "Italian"
                    ),

                "<ctrl>+<shift>+p":
                    lambda:
                    self.hotkey_triggered.emit(
                        "Portuguese"
                    ),

                "<ctrl>+<shift>+r":
                    lambda:
                    self.hotkey_triggered.emit(
                        "Russian"
                    ),

                "<ctrl>+<shift>+d":
                    lambda:
                    self.hotkey_triggered.emit(
                        "Dutch"
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

if __name__ == "__main__":
    load_dotenv()  # Load .env file (though we don't use API keys)

    app = QApplication(
        sys.argv
    )


    window = OfflineTranslator()


    window.show()


    sys.exit(
        app.exec()
    )