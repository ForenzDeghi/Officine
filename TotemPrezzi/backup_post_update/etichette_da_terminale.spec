block_cipher = None

a = Analysis(
    ['etichette_da_terminale.py'],  # Script principale
    pathex=['.'],  # Percorso base (radice del progetto)
    binaries=[],  # Non sono necessari binari aggiuntivi
    datas=[
        ('assets/label_template.png', 'assets/'),  # Aggiunge il template etichetta
        ("assets/font", "assets/font"), # Include i file presenti in font
        ('assets/config.ini', 'assets/')  
    ],
    hiddenimports=[],  # Aggiungi eventuali moduli nascosti, se necessario
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='etichette_da_terminale',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Imposta False se non vuoi la finestra della console
    icon=None,  # Puoi specificare un'icona personalizzata qui
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='etichette_da_terminale',
)
