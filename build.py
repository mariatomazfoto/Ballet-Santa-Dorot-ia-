"""Monta a galeria do Ballet Santa Dorotéia a partir de fotos/.

Uso (dentro da pasta do repositório):
    python3 build.py                       # destaques = arquivos com "destaque" no nome
    python3 build.py foto3.jpg foto7.jpg   # destaques escolhidos, nessa ordem
"""
import json, os, re, shutil, sys, zipfile
from PIL import Image, ImageOps

NOME_ZIP = 'Ballet_SantaDoroteia'
EXT = ('.jpg', '.jpeg', '.png', '.webp')


def natural(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


fotos = sorted((f for f in os.listdir('fotos') if f.lower().endswith(EXT)), key=natural)
feat = sys.argv[1:] or [f for f in fotos if 'destaque' in f.lower()]
falta = [f for f in feat if f not in fotos]
if falta:
    sys.exit(f'Destaques não encontrados em fotos/: {falta}')
order = feat + [f for f in fotos if f not in feat]

for d in ('tela', 'mini', 'zip'):
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)

P = []
for i, f in enumerate(order, 1):
    im = ImageOps.exif_transpose(Image.open('fotos/' + f)).convert('RGB')
    t = im.copy(); t.thumbnail((1800, 1800), Image.LANCZOS)
    t.save(f'tela/{i:03d}.jpg', quality=86, optimize=True, progressive=True)
    m = im.copy(); m.thumbnail((900 if f in feat else 640,) * 2, Image.LANCZOS)
    m.save(f'mini/{i:03d}.jpg', quality=80, optimize=True, progressive=True)
    P.append({'f': f, 'n': i, 'w': m.width, 'h': m.height, 'd': 1 if f in feat else 0})
    if im.width < 2000 and im.height < 2000:
        print(f'  aviso: {f} tem só {im.width}x{im.height}px (boa na tela, impressão só pequena)')

# "Baixar todas" em partes de até ~80 MB, sem compressão
groups, size = [[]], 0
for f in order:
    s = os.path.getsize('fotos/' + f)
    if size + s > 80 * 2**20 and groups[-1]:
        groups.append([]); size = 0
    groups[-1].append(f); size += s

btns, a, total = [], 1, 0
for k, g in enumerate(groups, 1):
    path = f'zip/{NOME_ZIP}_parte{k}.zip'
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_STORED) as z:
        for f in g:
            z.write('fotos/' + f, f)
    mb = os.path.getsize(path) / 2**20; total += mb
    b = a + len(g) - 1
    btns.append(f'<a class="btn part" href="{path}" download data-goatcounter-click="ballet/baixar-todas/parte-{k}" '
                f'data-goatcounter-title="ballet: baixar todas, parte {k}">Parte {k} <span>fotos {a}–{b} · {mb:.0f} MB</span></a>')
    a = b + 1

n = len(order)
partes = (f'<p class="hint">As {n} fotos ({total:.0f} MB) estão divididas em {len(groups)} arquivos .zip. '
          f'Baixe cada parte, de preferência no Wi‑Fi.</p>' if len(groups) > 1 else
          f'<p class="hint">As {n} fotos ({total:.0f} MB) em um arquivo .zip. Baixe de preferência no Wi‑Fi.</p>')

html = open('index.html', encoding='utf-8').read()
html = re.sub(r'var P=\[.*?\];', lambda _: 'var P=' + json.dumps(P, ensure_ascii=False, separators=(',', ':')) + ';', html, count=1, flags=re.S)
html = re.sub(r'<span class="count">.*?</span>', f'<span class="count">{n} fotos.</span>', html, count=1)
html = re.sub(r'<!--PARTS-->.*?<!--/PARTS-->', lambda _: '<!--PARTS-->' + partes + ''.join(btns) + '<!--/PARTS-->', html, count=1, flags=re.S)
open('index.html', 'w', encoding='utf-8').write(html)
print(f'{n} fotos ({len(feat)} destaques), {len(groups)} parte(s) de zip, {total:.0f} MB')
