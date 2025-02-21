# MemoCoco
MemoCoco is a fully open-source, privacy-first alternative to proprietary solutions like Microsoft's Windows Recall or Limitless' Rewind.ai. With MemoCoco, you can easily access your digital history, enhancing your memory and productivity without compromising your privacy.

this project is based on https://github.com/openrecall/openrecall openrecall project,Enriched and refined program details.

include those features:
- 1. ocr model migranted to trwebocr,mainly for chinese language and english language.
- 2. search engine replaced by ollama,so you can use any model that ollama support.
- 3. Image storage path optimization with folder slice mode.
- 4. New picture compression function, to ensure that the size of a single picture is less than 200K, it is expected that the size of a single day file is less than 200M.
- 5. Optimize the search function, support through the app option to query the corresponding content.


## OpenRecall Original Features

- **Time Travel**: Revisit and explore your past digital activities seamlessly across Windows, macOS, or Linux.
- **Local-First AI**: OpenRecall harnesses the power of local AI processing to keep your data private and secure.
- **Semantic Search**: Advanced local OCR interprets your history, providing robust semantic search capabilities.
- **Full Control Over Storage**: Your data is stored locally, giving you complete control over its management and security.

## Get Started
- Python 3.11
- MacOSX/Windows/Linux
- Git

To install:
```
python3 -m pip install --upgrade --no-cache-dir git+https://e.coding.net/liuwenwu/projectLiu/memococo.git
```

To run:
```
python3 -m memococo.app
```

visit on browser(recommend install this site as an app):
http://127.0.0.1:8082

storage path:
```
~/.local/share/MemoCoco/
```

## Uninstall instructions

To uninstall memococo and remove all stored data:

1. Uninstall the package:
   ```
   python3 -m pip uninstall memococo
   ```

2. Remove stored data:
   - On Windows:
     ```
     rmdir /s %APPDATA%\MemoCoco
     ```
   - On macOS:
     ```
     rm -rf ~/Library/Application\ Support/MemoCoco
     ```
   - On Linux:
     ```
     rm -rf ~/.local/share/MemoCoco
     ```

Note: If you specified a custom storage path at any time using the `--storage-path` argument, make sure to remove that directory too.

## Contribute

As an open-source project, we welcome contributions from the community. If you'd like to help improve MemoCoco, please submit a pull request or open an issue on our GitHub repository.

## Contact the maintainers
liuawu625@163.com

## License

MemoCoco is released under the [AGPLv3](https://opensource.org/licenses/AGPL-3.0), ensuring that it remains open and accessible to everyone.

**Enjoy this project?** Show your support by starring it! ⭐️ Thank you!