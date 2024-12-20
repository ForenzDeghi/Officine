[app]
# (str) Titolo dell'applicazione
title = Etichette Da Terminale

# (str) Nome del pacchetto
package.name = etichette_da_terminale

# (str) Dominio del pacchetto (identifica unicamente l'app)
package.domain = org.deghi.etichette

# (str) Directory del codice sorgente
source.dir = .

# (str) Main script file
source.include_exts = py,png,ttf,ini,jpg
source.include_dirs = assets

# (str) Punto d'entrata per l'applicazione (starter)
source.main = main

# (str) Versione dell'applicazione
version = 1.2

# (str) Android API version to target (usually leave this default)
android.api = 31

# (str) Api minima supportata per Android
android.minapi = 21

# (list) Permessi richiesti dall'applicazione
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (list) Features richieste dall'app
# android.features = android.hardware.touchscreen

# (list) Dependenze (moduli Python) -------> 
requirements = python3,kivy,pillow,requests,fpdf,configparser,cython

# (str) Supporto orientamento schermo
orientation = portrait

# (str) Schermo intero
fullscreen = 1

# (str) Icona dell'applicazione
#icon.filename = assets/icon.png

# (str) Libreria Java .jar or .aar addizionali da includere
# Leave this empty unless you're including custom Java libraries
android.add_jars =

# (str) Immagine all'avvio (startup image)
#presplash.filename = assets/presplash.png

# (list) Presplash background color (rgba)
presplash.color = [1, 1, 1, 1]

# (str) Nome pacchetto per la classe Java
android.package_name = org.deghi.totem

# (str) The path to a key for signing your app. If left empty, Buildozer generates one.
# android.keystore = 

# (str) Keystore password (leave empty if generating automatically)
# android.keystore_password = 

# (str) Alias for the key
# android.keyalias = 

# (str) Password for the alias (leave empty if generating automatically)
# android.keyalias_password = 

# (bool) Indicate whether the screen should stay on
android.keep_screen_on = True

# (str) Internal storage path for the app (leave default)
android.private_storage = True

# (list) Files to exclude from the build
exclude_patterns = *.spec,*.pyc,*.pyo,*.bak

# (bool) Include SQLite3 support (useful if the app uses local databases)
android.sqlite3 = False

# (list) Any additional libraries to include
android.add_libs_armeabi_v7a = 

# (list) Libraries for x86 architecture
android.add_libs_x86 = 

# (list) Additional env variables
android.env_vars = 

# (bool) Automatically accept SDK licenses
android.accept_sdk_license = True

# (str) Your app's unique identifier (leave default)
package.unique_id = totem_prezzi

# (str) Name of the application
app.name = Etichette da Terminale

# (list) Custom build commands
build_commands = 

# (bool) Disable usage analytics
disable_usage_analytics = False

# (bool) Enable buildozer logs
log.enable = True

# (str) List of architectures to support (default includes all)
android.archs = arm64-v8a

[buildozer]
# (str) Whether to build the APK (for Android) or not
build_type = release

# (bool) Automatically clean the build environment
auto_clean = True

# (str) Path to the output APK
output.apk = bin/

[log]
# (bool) Enable verbose logging
log_level = 2
verbose = True