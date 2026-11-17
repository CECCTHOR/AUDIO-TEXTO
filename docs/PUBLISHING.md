# Publishing this folder on GitHub

Publish the contents of `AUDIO-TEXTO_FOR_GITHUB` as your repository root. Do not upload
the parent `AUDIO-TEXTO` directory, its recordings, or its existing virtual environment.
The public repository is [CECCTHOR/AUDIO-TEXTO](https://github.com/CECCTHOR/AUDIO-TEXTO).
The project uses the [MIT License](../LICENSE), copyright (c) 2026 CECCTHOR.

## Recommended: use a separate working folder

This distribution may be inside another Git workspace. Copy this prepared folder to
a separate location before initializing a standalone repository. This keeps the audio
archive and unrelated projects outside the new repository.

1. Copy the prepared folder to your chosen repository location.
2. Open a terminal in that copied folder.
3. Create an empty repository on GitHub. Do not pre-create a README or `.gitignore`
   if you plan to push these local files as the initial commit.
4. Review the project name and retain the included `LICENSE` file.
5. Run the tests described in the README.
6. Initialize and inspect the local repository:

```bash
git init -b main
git add LICENSE README.md CHANGELOG.md requirements.txt transcribe_translate.py setup_environment.py run.ps1 run.sh .gitignore .gitattributes .github docs tests examples input/.gitkeep output/.gitkeep
git status --short
git diff --cached --stat
git diff --cached
```

The explicit list above avoids blindly staging recordings or a local test environment.
Still inspect the staged changes for personal information before committing.

7. Commit and connect your empty remote (replace the placeholder URL):

```bash
git commit -m "Add portable audio transcription and translation workflow"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

For an existing repository, copy these files into the intended working tree and
review its changes instead of running `git init` or replacing its remotes. Resolve
README/license conflicts deliberately. Do not overwrite an existing repository's
license without deciding that its terms are appropriate.

## After publishing

- The initial six Windows, macOS, and Linux jobs passed. See the
  [verification record](VERIFICATION.md) for the run and scope of those checks.
- Check the Actions tab for the Windows, macOS, and Linux jobs.
- Treat remote CI as pending until those jobs actually pass.
- Download or clone a fresh copy and follow the README on another supported machine.
- Keep recordings and results local. The empty `input/` and `output/` directories
  are placeholders for users' own data; the explicitly selected Audio 46 sample is
  published separately in `examples/audio46`.
- Never commit `.venv`, cached model weights, credentials, or personal transcripts.

## Publish a version

Use the program version from `transcribe_translate.py`, update `CHANGELOG.md`, and
push the reviewed changes to `main`. Wait for all six CI jobs for that exact commit
to pass, then create an annotated tag such as `v1.0.0` and push it. Create the GitHub
release from that existing tag, with the changes, example details, verification run,
and known limitations in its notes. GitHub supplies source ZIP and tar archives.

Release tags do not start another copy of the matrix: branch pushes to `main`, pull
requests, and manual dispatch remain the workflow triggers. Dependabot proposals
require review and successful tests; they are not automatically merged.
PyAV versions 19 and above are ignored until the transcription dependency supports
their decoder API. Revisit this exclusion when upgrading faster-whisper.

See the official [GitHub import instructions](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).
