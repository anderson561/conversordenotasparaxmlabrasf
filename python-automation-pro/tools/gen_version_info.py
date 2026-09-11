# -*- coding: utf-8 -*-
"""Gera `version_info.txt` — o recurso VERSIONINFO que o Windows lê nas
propriedades do .exe — a partir de `src/version.py`.

Existe por dois motivos:

1. O `flet pack` escrevia esse recurso num diretório temporário de nome
   ALEATÓRIO a cada execução. Como o `version=` do spec mudava sempre, o passo
   EXE do PyInstaller nunca era reaproveitado do cache: toda build era
   completa. Aqui o caminho é fixo e o conteúdo só muda quando a versão muda.

2. O recurso que o `flet pack` gravava trazia a versão do FLET (0.21.2), não a
   do aplicativo. Agora as propriedades do arquivo mostram o APP_VERSION real.

Roda sozinho a partir do build.bat, antes do PyInstaller.
"""
import io
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from src.version import APP_VERSION  # noqa: E402

partes = [int(p) for p in APP_VERSION.split('.')]
while len(partes) < 4:
    partes.append(0)
quadra = ', '.join(str(p) for p in partes[:4])

MODELO = """# Gerado por tools/gen_version_info.py — NÃO editar à mão.
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({quadra}),
    prodvers=({quadra}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '041604B0',
        [StringStruct('CompanyName', 'Norte Contabil'),
        StringStruct('FileDescription', 'Conversor NFS-e / Contratos para XML ABRASF 2.01'),
        StringStruct('FileVersion', '{versao}'),
        StringStruct('InternalName', 'nfse_converter_gui'),
        StringStruct('OriginalFilename', 'nfse_converter_gui.exe'),
        StringStruct('ProductName', 'Conversor NFS-e para ABRASF XML'),
        StringStruct('ProductVersion', '{versao}')])
      ]),
    VarFileInfo([VarStruct('Translation', [1046, 1200])])
  ]
)
"""

destino = os.path.join(RAIZ, 'version_info.txt')
novo = MODELO.format(quadra=quadra, versao=APP_VERSION)

# Só reescreve se mudou — reescrever com o mesmo conteúdo mexeria no mtime e
# faria o PyInstaller refazer o passo EXE à toa, que é justamente o que este
# arquivo existe para evitar.
antigo = io.open(destino, encoding='utf-8').read() if os.path.exists(destino) else None
if antigo == novo:
    print('version_info.txt: inalterado (%s)' % APP_VERSION)
else:
    io.open(destino, 'w', encoding='utf-8', newline='\n').write(novo)
    print('version_info.txt: gravado (%s)' % APP_VERSION)
