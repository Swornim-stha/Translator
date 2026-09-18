# Offline Translator

An instant translation tool that works 100% offline without relying on AI models. Based on the original QuickTranslate app but uses only offline translation libraries for privacy and speed.

## Features

- **Instant Offline Translation**: Translate text instantly without internet connection
- **Multiple Languages**: Supports French, Spanish, German, Italian, Portuguese, Dutch, and more
- **Global Hotkeys**: Use keyboard shortcuts to translate selected text anywhere
- **Privacy Focused**: No data leaves your computer - all translation happens locally
- **Cross-Platform**: Works on both macOS and Windows

## Supported Languages

- English → French
- English → Spanish
- English → German
- English → Italian
- English → Portuguese
- English → Dutch
- *(Additional languages can be installed as needed)*

## Installation

Follow these steps carefully to ensure a successful installation. The process involves creating a virtual environment to isolate dependencies and avoid conflicts.

### Step 1: Clone or Download the Repository

**Option 1: Using Git (Recommended)**
```bash
# Clone the repository
git clone <repository-url>
cd Translator
```

**Option 2: Download ZIP**
1. Download the repository as a ZIP file
2. Extract it to a folder of your choice
3. Open terminal/command prompt and navigate to the extracted folder

### Step 2: Create and Activate Virtual Environment

Creating a virtual environment prevents package conflicts with your system Python installation.

#### On macOS:
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

#### On Windows:
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate
```

You should see `(.venv)` at the beginning of your command prompt, indicating the virtual environment is active.

### Step 3: Install Dependencies

With the virtual environment activated, install the required Python packages:

```bash
pip install -r requirements.txt
```

### Step 4: Install Language Models

The translator uses Argos Translate for offline translation. You need to download the language models for the languages you want to use.

```bash
# Update the package index (ensures you get latest models)
python -m argostranslate.package update_index

# Install language models for English to target languages
# You can install all at once or individually as needed
python -m argostranslate.package install en_fr   # French
python -m argostranslate.package install en_es   # Spanish
python -m argostranslate.package install en_de   # German
python -m argostranslate.package install en_it   # Italian
python -m argostranslate.package install en_pt   # Portuguese
python -m argostranslate.package install en_nl   # Dutch
```

> **Note**: The first installation may take a few minutes as it downloads and extracts the translation models.

### Step 5: Verify Installation

Before running the application, verify that everything is installed correctly:

```bash
# Test argostranslate import
python -c "import argostranslate; print('Argos Translate imported successfully')"

# Test translation functionality
python -c "
import argostranslate.translate
installed = argostranslate.translate.get_installed_languages()
print(f'Number of installed languages: {len(installed)}')
for lang in installed:
    if lang.code == 'en':
        english = lang
    elif lang.code == 'fr':
        french = lang
if 'english' in locals() and 'french' in locals():
    translation = english.get_translation(french)
    result = translation.translate('Hello')
    print(f'Translation test: Hello -> {result}')
else:
    print('Languages not found - check installation')
"
```

If these tests pass without errors, your installation is successful!

## Usage

### Running the Application

With your virtual environment still activated:

```bash
python offline_translator.py
```

The application window should appear, and it will run in the background monitoring for hotkeys.

### Global Hotkeys

Once the application is running, use these keyboard shortcuts to translate selected text in any application:

- **Ctrl + Shift + T** → Translate to French
- **Ctrl + Shift + S** → Translate to Spanish
- **Ctrl + Shift + G** → Translate to German
- **Ctrl + Shift + I** → Translate to Italian
- **Ctrl + Shift + P** → Translate to Portuguese
- **Ctrl + Shift + D** → Translate to Dutch

> **Note**: On macOS, you may need to grant accessibility permissions the first time you run the app. Look for a system prompt asking for permission to control your computer.

### How It Works

1. Select any text in any application
2. Press the corresponding hotkey for your target language
3. The application copies the selected text, translates it offline, and pastes the translation back
4. Your original clipboard content is restored automatically

### Manual Translation

You can also use the application window for manual translation:

1. Enter English text in the input box
2. Select the target language from the dropdown
3. Click "Translate" or press Enter
4. The translation appears in the output box
5. Use "Copy" to copy the translation to clipboard

## Troubleshooting

### Common Issues and Solutions

#### "ModuleNotFoundError: No module named 'argostranslate'"
This usually means the virtual environment isn't activated or packages weren't installed correctly.

**Solution:**
1. Ensure you're in the project directory
2. Activate the virtual environment:
   - macOS: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`
3. Reinstall dependencies: `pip install -r requirements.txt`
4. Reinstall language models: `python -m argostranslate.package install en_fr` (etc.)

#### Broken Symlinks in Virtual Environment
If you see errors like `/path/to/python3.13: No such file or directory`, your virtual environment has broken symlinks.

**Solution:** Recreate the virtual environment:
```bash
# Deactivate if currently active
deactivate

# Remove the broken virtual environment
rm -rf .venv

# Recreate it
python3 -m venv .venv  # macOS
# or
python -m venv .venv   # Windows

# Reactivate and reinstall
source .venv/bin/activate  # macOS
# or
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
python -m argostranslate.package update_index
python -m argostranslate.package install en_fr  # etc.
```

#### Application Doesn't Respond to Hotkeys
1. Ensure the application window is open (it runs in the background but needs to be launched)
2. On macOS: Go to System Settings > Privacy & Security > Accessibility and ensure Python/your terminal is allowed to control your computer
3. On Windows: Try running the application as administrator if hotkeys don't work

#### Slow First Translation
The first translation may take 5-10 seconds as the models load into memory. Subsequent translations will be nearly instantaneous.

#### Language Not Supported Error
If you get an error like "Language 'XX' not supported for offline translation," you need to install that language model:
```bash
python -m argostranslate.package install en_XX  # Replace XX with language code
```

## How It Works Internally

The offline translator uses [Argos Translate](https://github.com/argosopentech/argos-translate), an open-source offline translation library. It uses:

- **CT2** (CTranslate2) for fast neural machine translation inference
- **SentencePiece** for tokenization
- **Stanford Stanza** for linguistic processing
- **SACREMOSES** for text preprocessing

## Requirements

- Python 3.8 or higher
- Approximately 500MB-1GB of disk space for language models (varies by language)
- Internet connection only needed for initial setup (to download models)

## Notes

- The first translation may take a moment as the models load into memory
- Subsequent translations are nearly instantaneous
- The application runs in the background and shows notifications when translation completes
- Your privacy is protected as no text is sent to external servers
- To quit the application, close the window or press Ctrl+C in the terminal where it's running

## License

This project is adapted from the original QuickTranslate app. See the original license for details.

## Acknowledgments

- [Argos Translate](https://github.com/argosopentech/argos-translate) for the offline translation engine
- Original QuickTranslate app for the UI concept and hotkey implementation