# -*- mode: python ; coding: utf-8 -*-
a = Analysis(['main.py'], pathex=[], binaries=[],
    datas=[('templates/index.html','templates'),('templates/template.xlsx','templates'),('static','static')],
    hiddenimports=['flask','werkzeug','jinja2','requests','urllib3','certifi','pytz','openpyxl','sqlite3','msvcrt','webview'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['IPython','matplotlib','pandas','numpy','scipy','torch','tensorflow','PyQt5','PyQt6','PySide2','PySide6'],
    noarchive=False, optimize=0)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='ChamCong',debug=False,
    bootloader_ignore_signals=False,strip=False,upx=False,runtime_tmpdir=None,
    console=False,disable_windowed_traceback=True)
