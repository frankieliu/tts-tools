# TTS Tools - Installation Guide

## Quick Setup

### 1. Add to PATH

Add the tools directory to your PATH by adding this line to your shell configuration file:

**For bash (~/.bashrc):**
```bash
export PATH="$HOME/Library/CloudStorage/Box-Box/Work/bg/tts-tools/bin:$PATH"
```

**For zsh (~/.zshrc):**
```bash
export PATH="$HOME/Library/CloudStorage/Box-Box/Work/bg/tts-tools/bin:$PATH"
```

### 2. Reload Shell Configuration

```bash
# For bash
source ~/.bashrc

# For zsh
source ~/.zshrc
```

### 3. Verify Installation

Test that tools are accessible:

```bash
tts-pipeline --help
tts-download --help
tts-generate-pdf --help
```

You should see help text for each command.

## First Run

The first time you run any tool, it will automatically:
1. Create necessary Python virtual environments
2. Install required dependencies
3. Set up the workspace

This may take a minute or two. Subsequent runs will be instant.

## Testing the Pipeline

Try a quick test with a small mod:

```bash
# Create a test directory
mkdir -p ~/tts-test
cd ~/tts-test

# Run the pipeline
tts-pipeline 3162057688
```

This will download the Evenfall mod and generate a complete deck PDF.

## Troubleshooting

### Command Not Found

If you get "command not found" errors:

1. Verify PATH is set correctly:
   ```bash
   echo $PATH | grep tts-tools
   ```

2. Check that files are executable:
   ```bash
   ls -l ~/Library/CloudStorage/Box-Box/Work/bg/tts-tools/bin/
   ```
   All files should have `-rwxr-xr-x` permissions.

### Virtual Environment Errors

If you encounter venv errors, manually create the environments:

```bash
# Steam Workshop tools
cd ~/Work/bg/steam_workshop
uv venv
uv pip install -r requirements.txt

# Asset downloader
cd ~/Library/CloudStorage/Box-Box/Work/bg/tts-mod-download
uv venv
uv pip install -r requirements.txt

# PDF generator
cd ~/Library/CloudStorage/Box-Box/Work/bg/tts-mods
uv venv
uv pip install .
```

### SSL Certificate Errors

Some users may encounter SSL errors when downloading. Use `--no-verify`:

```bash
tts-pipeline 3162057688 --no-verify
```

## Next Steps

See [README.md](README.md) for:
- Usage examples
- Individual tool documentation
- Customization options
- Advanced workflows
