import fitz, pytesseract
from PIL import Image

doc = fitz.open(r'L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\062026\NF S - 2026702 - CUIABA.pdf')
text = ''
for page in doc:
    pix = page.get_pixmap()
    img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    text += pytesseract.image_to_string(img, lang='por')

with open('cuiaba_ocr_test.txt', 'w', encoding='utf-8') as f:
    f.write(text)
