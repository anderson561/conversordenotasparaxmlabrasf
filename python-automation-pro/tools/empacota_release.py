# -*- coding: utf-8 -*-
"""Compacta `dist/nfse_converter_gui/` (a build onedir) em
`dist/nfse_converter_gui.zip`, que é o asset principal do GitHub Release.

O `auto_updater` espera um zip cuja RAIZ seja a pasta `nfse_converter_gui/`,
com o executável dentro dela — é assim que ele localiza o que instalar.
"""
import os
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, 'dist', 'nfse_converter_gui')
DESTINO = os.path.join(RAIZ, 'dist', 'nfse_converter_gui.zip')

if not os.path.isdir(PASTA):
    print('ERRO: %s nao existe — rode a build do onedir antes.' % PASTA)
    sys.exit(1)

if not os.path.exists(os.path.join(PASTA, 'nfse_converter_gui.exe')):
    print('ERRO: nfse_converter_gui.exe nao esta em %s' % PASTA)
    sys.exit(1)

n = 0
total = 0
# ZIP_DEFLATED e' o que o zipfile do Python le' de volta sem dependencia
# externa — o updater descompacta com o mesmo modulo.
with zipfile.ZipFile(DESTINO, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for base, _dirs, arquivos in os.walk(PASTA):
        for nome in arquivos:
            completo = os.path.join(base, nome)
            # Caminho DENTRO do zip, começando por "nfse_converter_gui/".
            interno = os.path.relpath(completo, os.path.dirname(PASTA))
            z.write(completo, interno)
            n += 1
            total += os.path.getsize(completo)

print('nfse_converter_gui.zip: %d arquivos, %.1f MB crus -> %.1f MB compactados'
      % (n, total / 1048576.0, os.path.getsize(DESTINO) / 1048576.0))
