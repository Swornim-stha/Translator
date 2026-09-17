# Offline Translator

An instant translation tool that works 100% offline without relying on AI models. Based on the original QuickTranslate app but uses only offline translation libraries for privacy and speed.

## Features

- **Instant Offline Translation**: Translate text instantly without internet connection
- **Multiple Languages**: Supports French, Spanish, German, Italian, Portuguese, Dutch, and more
- **Global Hotkeys**: Use keyboard shortcuts to translate selected text anywhere
- **Privacy Focused**: No data leaves your computer - all translation happens locally

## Supported Languages

- English → French
- English → Spanish
- English → German
- English → Italian
- English → Portuguese
- English → Dutch

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install language packages (run once):

   ```bash
   # Update package index
   python -m argostranslate.package update_index
   # Install required language pairs (English → French, Spanish, German, Italian, Portuguese, Dutch)
   python -m argostranslate.package install en_fr
   python -m argostranslate.package install en_es
   python -m argostranslate.package install en_de
   python -m argostranslate.package install en_it
   python -m argostranslate.package install en_pt
   python -m argostranslate.package install en_nl
   ```

## Usage

### Running the Application

```bash
python offline_translator.py
```

### Global Hotkeys

Once the application is running, use these keyboard shortcuts to translate selected text in any application:

- **Ctrl + Shift + T** → Translate to French
- **Ctrl + Shift + S** → Translate to Spanish
- **Ctrl + Shift + G** → Translate to German
- **Ctrl + Shift + I** → Translate to Italian
- **Ctrl + Shift + P** → Translate to Portuguese
- **Ctrl + Shift + D** → Translate to Dutch

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

## How It Works Internally

The offline translator uses [Argos Translate](https://github.com/argosopentech/argos-translate), an open-source offline translation library. It uses:

- **CT2** (CTranslate2) for fast neural machine translation inference
- **SentencePiece** for tokenization
- **Stanford Stanza** for linguistic processing
- **SACREMOSES** for text preprocessing

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Notes

- The first translation may take a moment as the models load into memory
- Subsequent translations are nearly instantaneous
- The application runs in the background and shows a notification when translation completes
- Your privacy is protected as no text is sent to external servers

## License

This project is adapted from the original QuickTranslate app. See the original license for details.

## Acknowledgments

- [Argos Translate](https://github.com/argosopentech/argos-translate) for the offline translation engine
- Original QuickTranslate app for the UI concept and hotkey implementation
