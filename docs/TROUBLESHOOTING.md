# Troubleshooting

## Python or pip is not found

On Windows try `py --version`; on macOS/Linux try `python3 --version`. Install a
64-bit Python distribution and restart your terminal after installation. Always run
pip as `PATH_TO_ENV_PYTHON -m pip` so it installs into the intended environment.

## A package has no compatible wheel

Upgrade pip inside `.venv`. Check the package's platform/Python support. Use a supported
64-bit Python version and recreate `.venv` if needed. Native dependencies may not
support every CPU or operating system. The requirements pin the tested top-level
package, not a universal binary bundle or a full transitive lock file.

## Access denied or a script will not run

Use the direct environment Python command instead of the PowerShell wrapper.
Check file permissions and security software. If running in an application sandbox,
use its permission controls. A sandbox access error does not by itself mean Python
or the model is broken. Do not change system-wide policies just to run this project.

## Model download fails

Check connectivity to Hugging Face and any proxy settings. Use a model already cached
with `--local-files-only`, or supply a local converted faster-whisper model directory
using `--model`. Ordinary Whisper checkpoint files are not interchangeable with a
converted CTranslate2 directory.

## Slow transcription or insufficient memory

Try `--model tiny.en` or `--model base.en` for English. Use `tiny` or `base` for other
languages. Smaller models trade accuracy for speed and memory. Close other memory-heavy
applications. CPU processing can take longer than the recording's duration.

## Invalid or empty audio

Verify that the original file plays and contains audible speech. Some containers,
codecs, encrypted media, or corrupt recordings cannot be decoded. VAD retries without
filtering when no segments are detected; this does not guarantee meaningful text.

## Translation failed or returned HTTP 429

The endpoint may be temporarily unavailable or rate limited. The transcript remains
saved. Wait before retrying with `--resume output/NAME.metadata.json --overwrite`.
Changing `--timeout` can help a slow connection; it does not bypass provider limits.
Use `--no-translate` if you want transcription without an external translation service.

## Results already exist

Choose another output directory or add `--overwrite` after confirming replacement is
intended. Resume in the same directory also requires `--overwrite`. Do not use several
processes to write the same output set.

## The translation or a name is inaccurate

Compare with the recording. Proper names, numbers, accents, music, and speech overlap
can produce errors. Trying a larger model may help. Identical source/translation text
is not automatically a failure: names and some words are legitimately unchanged.
The status records provider success, not linguistic correctness.
