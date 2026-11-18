# Audio Texto: guía rápida en español

[Referencia completa en inglés](README.md) | [Ejemplo y resultados del audio 46](examples/audio46/README.md)

Audio Texto convierte audio o video en texto mediante faster-whisper, usando la CPU
de tu equipo. También puede traducir el texto al español mediante Google Translate.
El idioma de origen predeterminado es inglés. Los mensajes del programa están en inglés.

Necesitas Python de 64 bits, versión 3.10 o posterior, y una plataforma compatible
con sus dependencias. Las comprobaciones automáticas cubren Windows, macOS y Linux
con Python 3.12 y 3.14; la transcripción real del ejemplo se verificó en Windows.
Consulta los detalles de [compatibilidad y verificación](docs/VERIFICATION.md).

## 1. Descarga el proyecto

Descarga el [ZIP de la rama principal](https://github.com/CECCTHOR/AUDIO-TEXTO/archive/refs/heads/main.zip)
y extráelo. También puedes clonarlo con Git:

```bash
git clone https://github.com/CECCTHOR/AUDIO-TEXTO.git
cd AUDIO-TEXTO
```

Abre una terminal dentro de la carpeta que contiene `setup_environment.py` y
`transcribe_translate.py`. Si descargaste el ZIP, normalmente se llama `AUDIO-TEXTO-main`.

## 2. Prepara el entorno

En Windows PowerShell:

```powershell
py --version
py setup_environment.py
```

Si `py` no está disponible, prueba `python --version` y `python setup_environment.py`.

En macOS o Linux:

```bash
python3 --version
python3 setup_environment.py
```

El instalador crea `.venv` dentro del proyecto e instala las dependencias de
`requirements.txt`. Necesita internet. Crea este entorno en cada equipo en el que
vayas a usar el programa. En Linux puede ser necesario instalar el paquete `venv`
de tu distribución. Espera a que aparezca el mensaje `Setup complete`.

## 3. Prueba el audio incluido

Esta primera prueba transcribe el audio 46 sin enviar el texto a un traductor.

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe transcribe_translate.py examples/audio46/audio46.ogg --no-translate --output-dir output/audio46
```

macOS o Linux:

```bash
.venv/bin/python transcribe_translate.py examples/audio46/audio46.ogg --no-translate --output-dir output/audio46
```

La primera ejecución descarga el modelo `small.en`; puede tardar y requiere internet.
Después de guardarlo en la caché, añade `--local-files-only` al comando anterior para
exigir procesamiento local sin descargas. El tiempo de transcripción depende de tu equipo.

Para usar una grabación propia, colócala en `input/` y sustituye
`examples/audio46/audio46.ogg` por su ruta, por ejemplo `"input/mi audio.mp3"`.
Elige una carpeta de salida distinta para conservar los resultados de cada grabación.

## Dónde están los resultados

Abre `output/audio46/`. La prueba anterior crea estos cinco archivos:

| Archivo | Contenido |
| --- | --- |
| `audio46.transcript.en.txt` | Transcripción en inglés |
| `audio46.transcript.en.timestamps.txt` | La misma transcripción con tiempos |
| `audio46.translation.es.txt` | Estado de la traducción o texto traducido |
| `audio46.translation.es.timestamps.txt` | Lo mismo con tiempos |
| `audio46.metadata.json` | Segmentos, opciones y estados para reanudar el trabajo |

Como usamos `--no-translate`, los archivos de traducción muestran
`[TRANSLATION SKIPPED]`: significa que se omitió la traducción deliberadamente.
Los resultados de referencia con traducción al español están en
[examples/audio46/expected](examples/audio46/expected).

## Añade la traducción al español, si la necesitas

Puedes traducir la transcripción guardada sin repetir el reconocimiento del audio.
Este paso envía el texto a Google y necesita internet; el audio se procesa localmente.
El comando actualiza los cinco archivos de resultados de esa carpeta.

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe transcribe_translate.py --resume output/audio46/audio46.metadata.json --overwrite
```

macOS o Linux:

```bash
.venv/bin/python transcribe_translate.py --resume output/audio46/audio46.metadata.json --overwrite
```

Google Translate es un servicio no oficial en este programa y puede imponer límites
temporales. Si falla, la transcripción queda guardada y puedes reintentar más tarde
con el mismo comando. Revisa la transcripción y la traducción antes de utilizarlas.

## Si aparece un problema

- Si los resultados ya existen, usa otra carpeta de salida. `--overwrite` sirve
  para sustituirlos cuando esa sea tu intención.
- Si el equipo tiene poca memoria, prueba `--model tiny.en` o `--model base.en`
  para audio en inglés; el resultado puede ser menos preciso.
- Para audio en español u otro idioma, usa un modelo multilingüe y el idioma adecuado,
  como `--model small --language es`. Un modelo terminado en `.en` solo reconoce inglés.
- Consulta la [guía de problemas frecuentes en inglés](docs/TROUBLESHOOTING.md) o abre
  el [formulario para reportar un error](https://github.com/CECCTHOR/AUDIO-TEXTO/issues/new?template=bug_report.yml).

Puedes escribir el reporte en español o inglés. Incluye tu sistema operativo,
versión de Python, comando utilizado y lo ocurrido. Los reportes son públicos:
comparte información de diagnóstico sin datos personales, credenciales ni contenido
privado de tus grabaciones.

El código y la documentación usan la [licencia MIT](LICENSE). El audio de ejemplo
y su contenido tienen un [aviso de derechos separado](examples/audio46/NOTICE.md).
