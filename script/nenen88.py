TOKET = ''
TOBRUT = ''

from IPython.core.magic import register_line_magic
from IPython.display import display, HTML
from urllib.parse import urlparse
from IPython import get_ipython
from pathlib import Path
from tqdm import tqdm
import subprocess
import threading
import requests
import zipfile
import shlex
import json
import sys
import re
import os
import io

MAGENTA = '\033[35m'
RED = '\033[31m'
CYAN = '\033[36m'
GREEN = '\033[38;5;49m'
YELLOW = '\033[33m'
BLUE = '\033[38;5;69m'
PURPLE = '\033[38;5;177m'
ORANGE = '\033[38;5;208m'
RESET = '\033[0m'

CD = os.chdir
SyS = get_ipython().system
iRON = os.environ

KAGGLE = 'KAGGLE_DATA_PROXY_TOKEN' in iRON

CIVITAI = ['civitai.com', 'civitai.red']

@register_line_magic
def say(line):
    args = re.findall(r'\{[^\{\}]+\}|[^\s\{\}]+', line)
    output = []
    theme = get_ipython().config.get('InteractiveShellApp', {}).get('theme', 'light')
    default_color = 'white' if theme == 'dark' else 'black'

    i = 0
    while i < len(args):
        msg = args[i]
        color = None

        if re.match(r'^\{[^\{\}]+\}$', msg.lower()):
            color = msg[1:-1]
            msg = ''
        else:
            while i < len(args) - 1 and not re.match(r'^\{[^\{\}]+\}$', args[i + 1].lower()):
                i += 1
                msg += ' ' + args[i]

        if color == 'd':
            color = default_color
        elif color is None and i < len(args) - 1:
            if re.match(r'^\{[^\{\}]+\}$', args[i + 1].lower()):
                color = args[i + 1][1:-1]
                i += 1

        span_text = f'<span'
        if color:
            span_text += f" style='color:{color};'"
        span_text += f'>{msg}</span>'
        output.append(span_text)
        i += 1

    display(HTML(' '.join(output)))

@register_line_magic
def download(i):
    args = i.split()
    if not args:
        print('  missing URL, downloading nothing')
        return

    url = args[0]
    path = Path(url).expanduser()
    if url.endswith('.txt') and path.is_file():
        for l in path.read_text(encoding='utf-8').splitlines(): netorare(l)
    else: netorare(i)

def netorare(line):
    fp, fn = None, None

    parts = line.strip().split()
    if not parts: return

    cwd = Path.cwd()
    path = lambda s: '/' in s or '~/' in s
    url = parts[0].replace('\\', '')

    C = any(u in url for u in CIVITAI)
    H = 'huggingface.co' in url
    G = 'github.com' in url
    D = 'drive.google.com' in url

    try:
        if len(parts) >= 3:
            a, b = parts[1], parts[2]

            aa = path(a)
            bb = path(b)

            if bb and not aa: p, f = b, a
            elif aa and not bb: p, f = a, b
            elif Path(b).suffix == '' and Path(a).suffix != '': p, f = b, a
            else: p, f = a, b

            fp = Path(p).expanduser()
            fn = f

            fp.mkdir(parents=True, exist_ok=True)
            CD(fp)

        elif len(parts) == 2:
            a = parts[1]

            if path(a):
                fp = Path(a).expanduser()
                fp.mkdir(parents=True, exist_ok=True)
                CD(fp)
                fn = (None if (C or D) else Path(urlparse(url).path).name)
            else:
                fn = a
                fp = cwd

        else:
            fn = (None if (C or D) else Path(urlparse(url).path).name)
            fp = cwd

        if C or H or G: ariari(url, fp, fn)

        elif D: gdrown(url, fp, fn)

        else:
            cp = (len(parts) == 2 and fp is not None)
            cmd = (
              f"curl -#{'OJL' if len(parts) == 1 or cp else 'JL'} '{url}'" +
              (f" -o '{fn}'" if fn is not None and not cp else "")
            )
            curlly(cmd, fn)

    finally:
        CD(cwd)

def resizer(b, size=512):
    from PIL import Image
    i = Image.open(io.BytesIO(b))
    w, h = i.size
    s = (size, int(h * size / w)) if w > h else (int(w * size / h), size)
    o = io.BytesIO()
    i.resize(s, Image.LANCZOS).save(o, format='PNG')
    o.seek(0)
    return o

def get_civdom(url):
    try: return next((d for d in CIVITAI if d in urlparse(url).netloc.lower()), None)
    except: return None

def civitai_headers():
    return {'User-Agent': 'CivitaiLink:Automatic1111'}

def civitai_preview(j, p, fn, versionId=None):
    v = get_civitai(j, versionId)
    if not v: return

    images = v.get('images', [])
    name = fn or v.get('files', [{}])[0].get('name')
    if not name: return

    path = Path(p) / f'{Path(name).stem}.preview.png'
    if path.exists(): return

    preview = next((img.get('url', '') for img in images if not img.get('url', '').lower().endswith(('.mp4', '.gif'))), None)
    if not preview: return

    r = requests.get(preview, headers=civitai_headers()).content
    resized = resizer(r)

    if KAGGLE:
        from melon00 import image_encryption
        image_encryption(resized, path)
    else:
        path.write_bytes(resized.read())

def civitai_infotags(j, p, fn, versionId=None):
    v = get_civitai(j, versionId)
    if not v: return

    modelId = j.get('id') or v.get('modelId')
    name = fn or v.get('files', [{}])[0].get('name')
    if not name: return

    info = Path(p) / f'{Path(name).stem}.json'
    if info.exists(): return

    baseList = {
        'SD 1': 'SD1',
        'SD 1.5': 'SD1',
        'SD 2': 'SD2',
        'SD 3': 'SD3',
        'SDXL': 'SDXL',
        'Pony': 'SDXL',
        'Illustrious': 'SDXL',
        'Anima': 'Anima',
        'ZImageBase': 'ZImageBase',
        'ZImageTurbo': 'ZImageTurbo',
    }

    data = {
        'activation text': ', '.join(v.get('trainedWords', [])),
        'sd version': next((s for k, s in baseList.items() if k in v.get('baseModel', '')), ''),
        'modelId': modelId,
        'modelVersionId': v.get('id'),
        'sha256': v.get('files', [{}])[0].get('hashes', {}).get('SHA256')
    }

    info.write_text(json.dumps(data, indent=4))

def civitai_earlyAccess(j, versionId=None, civitai=None):
    v = get_civitai(j, versionId)
    if not v: return False

    if v.get('availability') == 'EarlyAccess' or v.get('earlyAccessEndsAt'):
        modelId = j.get('id') or v.get('modelId')
        modelVersionId = v.get('id')
        page = f'https://{civitai}/models/{modelId}?modelVersionId={modelVersionId}'
        print(f'{page}\n-> The model version is in early access and requires payment for downloading.')
        return True

    return False

def civitai_file(j, versionId=None):
    v = get_civitai(j, versionId)
    if not v: return None, None

    f = next((f for f in v.get('files', []) if f.get('downloadUrl')), None)
    n = ((f.get('name') if f else None) or v.get('name'))

    return f, n

def get_json(api_url, headers):
    try:
        r = requests.get(api_url, headers=headers, timeout=15)
        if r.status_code != 200: return None
        return r.json()
    except:
        return None

def get_civitai(j, versionId=None):
    v = None

    if versionId:
        if 'modelVersions' in j: v = next((mv for mv in j['modelVersions'] if str(mv.get('id')) == str(versionId)), None)
        if not v and str(j.get('id')) == str(versionId) and 'files' in j: v = j

    if not v:
        if 'modelVersions' in j: v = j['modelVersions'][0]
        else: v = j

    return v

def get_url(url, fn):
    civitai = get_civdom(url)

    if 'github.com' in url:
        return url.replace('/blob/', '/raw/'), None, None, fn

    elif 'huggingface.co' in url:
        url = url.split('?')[0]

        headers = {
            'User-Agent': 'Mozilla/5.0',
            **({'Authorization': f'Bearer {TOBRUT}'} if TOBRUT else {})
        }

        ext = ['.safetensors', '.pt', '.pth']
        j, versionId = None, None

        if fn and Path(fn).suffix.lower() in ext:
            try:
                raw_url = re.sub(r'/(resolve|blob)/', '/raw/', url)
                res = requests.get(raw_url, headers=headers, timeout=15)

                t = re.search(r'oid sha256:([a-fA-F0-9]{64})', res.text)
                if t:
                    sha256 = t.group(1).lower()

                    for c in CIVITAI:
                        try:
                            api_url = f'https://{c}/api/v1/model-versions/by-hash/{sha256}'
                            j_try = get_json(api_url, civitai_headers())
                            if not j_try: continue

                            r = next((f for f in j_try.get('files', []) if f.get('hashes', {}).get('SHA256', '').lower() == sha256), None)
                            if r:
                                j = j_try
                                break

                        except Exception: continue

            except Exception: pass

        url = url.replace('/blob/', '/resolve/')
        return url, j, versionId, fn

    elif civitai in url:
        input_url = url
        url = url.split('?token=')[0]

        if f'{civitai}/api/download/models/' in url:
            versionId = url.split('models/')[1].split('/')[0].split('?')[0]
            api_url = f'https://{civitai}/api/v1/model-versions/{versionId}'

            j = get_json(api_url, civitai_headers())
            if not j: return url, None, None, None

            f, cfn = civitai_file(j, versionId)
            if not f: return url, None, None, None

            return url, j, versionId, (fn or cfn)

        elif f'{civitai}/models/' in url:
            versionId = None
            modelId = url.split('models/')[1].split('/')[0].split('?')[0]

            if '?modelVersionId=' in url: versionId = url.split('?modelVersionId=')[1].split('&')[0]

            api_url = f'https://{civitai}/api/v1/models/{modelId}'
            j = get_json(api_url, civitai_headers())
            if not j or civitai_earlyAccess(j, versionId, civitai): return None, None, None, None

            f, cfn = civitai_file(j, versionId)
            if not f:
                print(f'Unable to find download URL for\n-> {input_url}\n')
                return None, None, None, None

            return f['downloadUrl'], j, versionId, (fn or cfn)

    return url, None, None, fn

def ariari(url, fp, fn):
    url, j, versionId, fn = get_url(url, fn)
    if not url: return

    civitai = get_civdom(url)

    headers = {'User-Agent': (civitai_headers()['User-Agent'] if civitai else 'Mozilla/5.0')}

    if TOKET and f'{civitai}/api/download/models/' in url:
        headers['Authorization'] = f'Bearer {TOKET}'

        try:
            r = requests.get(url, headers=headers, allow_redirects=True, stream=True, timeout=30)
            if r.url and r.url != url: url = r.url
            r.close()

        except Exception as e:
            print(f'  Preflight failed: {e}')
            print('  Falling back to aria2 with Authorization header.')

    cmd = [
        'aria2c',
        f"--header=User-Agent: {headers['User-Agent']}",
        '--allow-overwrite=true', '--console-log-level=error', '--stderr=true',
        '-c', '-x16', '-s16', '-k1M', '-j5' 
    ]

    if TOBRUT and 'huggingface.co' in url: cmd.append(f'--header=Authorization: Bearer {TOBRUT}')
    if fn: cmd += ['-o', fn]

    cmd.append(url)

    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        aria2_output, bl, error_code, error_line = '', False, [], []

        while True:
            lines = p.stderr.readline()

            if lines == '' and p.poll() is not None: break

            if lines:
                aria2_output += lines

                for prog in lines.splitlines():
                    if 'errorCode' in prog or 'Exception' in prog:
                        error_code.append(prog)

                    if '|' in prog and 'error_line' in prog:
                        prog = re.sub(r'(\|\s*)(error_line)(\s*\|)', f'\\1{RED}\\2{RESET}\\3', prog)
                        first, _, last = prog.rpartition('|')
                        last = re.sub(r'/', f'{CYAN}/{RESET}', last)
                        prog = f'{first}|{last}'
                        error_line.append(prog)

                    m = re.match(
                        r'\[#\w+\s+'
                        r'(?:(\d+(?:\.\d+)?\w+/\d+(?:\.\d+)?\w+))?'
                        r'\((\d+%)\)'
                        r'.*?DL:(\d+(?:\.\d+)?\w+)'
                        r'(?:.*?ETA:(\d+\w+))?',
                        prog
                    )

                    if m:
                        sizes, percent, speed, eta = m.groups()

                        percent = re.sub(r'(\d+)(%)', f'\\1{PURPLE}\\2{RESET}', percent)
                        parts = [f'{MAGENTA}({RESET}{percent}{MAGENTA}){RESET}']

                        if sizes:
                            current, total = sizes.split('/')
                            current = re.sub(r'(\d+(?:\.\d+)?)(\w+)', f'\\1{PURPLE}\\2{RESET}', current)
                            total = re.sub(r'(\d+(?:\.\d+)?)(\w+)', f'\\1{PURPLE}\\2{RESET}', total)
                            parts.append(f'{current}' f'{CYAN}/{RESET}' f'{total}')

                        speed = re.sub(r'(\d+(?:\.\d+)?)(\w+)', f'\\1{PURPLE}\\2{RESET}', speed)
                        parts.append(f'{CYAN}DL{RESET}:' f'{speed}')

                        if eta:
                            parts.append(f'{CYAN}ETA{RESET}:' f'{YELLOW}{eta}{RESET}')

                        body = ' '.join(parts)

                        r = (
                            f'{fn} '
                            #f'{MAGENTA}【{RESET}'
                            f'{body}'
                            #f'{MAGENTA}】{RESET}'
                        )

                        print(f"\r{' '*300}\r  {RED}●{RESET} {r}", end='')
                        sys.stdout.flush()

                        bl = True
                        break

        civitai = None
        error = error_code + error_line
        for lines in error: print(f'  {lines}')

        for lines in aria2_output.splitlines():
            if '|' in lines and 'OK' in lines:
                pipe = [p.strip() for p in lines.split('|')]

                if len(pipe) >= 4:
                    saved = pipe[3]
                    saved = re.sub(r'/', f'{ORANGE}/{RESET}', saved)
                    print(f"\r{' '*300}\r  {GREEN}●{RESET} {saved}")
                    sys.stdout.flush()
                    bl = False

        bl and print()
        p.wait()

        if j:
            civitai_infotags(j, fp, fn, versionId)
            threading.Thread(
                target=civitai_preview,
                args=(j, fp, fn, versionId),
                daemon=True
            ).start()

    except KeyboardInterrupt:
        print(f'\n{"":>2}^ Canceled')

def curlly(cmd, fn):
    try:
        p = subprocess.Popen(
            shlex.split(cmd), cwd=str(Path.cwd()),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1
        )

        prog = re.compile(r'(\d+\.\d+)%')
        curl_output = ''

        with tqdm(
            total=100, desc=f'{fn.ljust(58):>{58 + 2}}', initial=0,
            bar_format='{desc} 【{bar:20}】【{percentage:3.0f}%】',
            ascii='▷▶', file=sys.stdout
        ) as pbar:
            for line in iter(p.stderr.readline, ''):
                if line.strip():
                    match = prog.search(line)
                    if match:
                        progress = float(match.group(1))
                        pbar.update(progress - pbar.n)
                        pbar.refresh()

                curl_output += line
            pbar.close()
        p.wait()

        if p.returncode != 0:
            if 'curl: (23)' in curl_output:
                print(
                    f"{'':>2}^ File already exists; download skipped. "
                    "Append a custom name after the URL or PATH to overwrite."
                )
            elif 'curl: (3)' in curl_output:
                print('')
            else:
                print(f"{'':>2}^ Error: {curl_output}")
        else:
            pass

    except KeyboardInterrupt:
        print(f"{'':>2}^ Canceled")

def gdrown(url, fp=None, fn=None):
    folder = 'drive.google.com/drive/folders' in url
    cmd = ['gdown', '--fuzzy']

    if folder: cmd.append('--folder')
    cmd.append(url)

    name = fn or None
    saved = None

    if fp:
        fp = Path(fp).expanduser()
        fp.mkdir(parents=True, exist_ok=True)

        if fn:
            fn = fp / fn
            cmd += ['-O', str(fn)]

        cwd = str(fp)

    else:
        cwd = None

        if fn: cmd += ['-O', fn]

    try:
        p = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        bl = False

        while True:
            prog = p.stdout.readline()

            if prog == '' and p.poll() is not None: break
            if not prog: continue

            prog = prog.strip()
            if not prog: continue

            if prog.startswith('To: '):
                try:
                    saved = prog[4:].strip()
                    name = Path(saved).name
                except: pass
                continue

            if '%' in prog and '/' in prog:
                prog = re.sub(r'(\d+)(%)', f'\\1{PURPLE}\\2{RESET}', prog)
                prog = re.sub(r'(\d+(?:\.\d+)?[KMG]B/s)', f'{CYAN}\\1{RESET}', prog)
                print(f"\r{' '*300}\r  {RED}●{RESET} {name} {prog}", end='')

                sys.stdout.flush()
                bl = True

            else:
                skip = (
                    'Downloading...' in prog or
                    'From (original):' in prog or
                    'From (redirected):' in prog
                )

                if skip: continue
                if bl: print()

                print(f'  {GREEN}●{RESET} {prog}')
                bl = False

        p.wait()

        if saved:
            saved = re.sub(r'/', f'{ORANGE}/{RESET}', saved)
            print(f"\r{' '*300}\r  {GREEN}●{RESET} {saved}")

    except KeyboardInterrupt:
        try: p.terminate()
        except: pass
        print(f'\n{"":>2}^ Canceled')

@register_line_magic
def clone(i):
    import concurrent.futures
    p = Path(i).expanduser()

    def proc(line):
        line = line.strip()
        if line.startswith('git clone'):
            line = line[len('git clone '):].strip()
        return line

    if p.suffix == '.txt' and p.is_file():
        urls = [proc(line) for line in p.read_text().splitlines() if line.strip()]
    elif isinstance(i, str):
        urls = [proc(i)] if i.strip() else []
    else:
        urls = [proc(l) for l in i if l.strip()]

    def clone_one(url_or_cmd):
        tokens = shlex.split(url_or_cmd)
        url = next((t for t in tokens if t.startswith('http://') or t.startswith('https://')), None)
        if not url:
            return
        
        other_args = [t for t in tokens if t != url and not t.startswith('-')]
        target_name = other_args[0] if other_args else ""
        
        cmd = ['git', 'clone', '--depth', '1', '--recurse-submodules', url]
        if target_name:
            cmd.append(target_name)
            
        repo_display = target_name if target_name else url.split('/')[-1].replace('.git', '')
        print(f"  [SMFactory] Cloning {repo_display}...")
        
        proc_git = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output, _ = proc_git.communicate()
        if proc_git.returncode == 0:
            print(f"  {GREEN}✓{RESET} {repo_display} cloned successfully.")
        else:
            print(f"  {RED}✗{RESET} {repo_display} clone failed: {output.strip()}")

    if urls:
        print(f"[SMFactory] Cloning {len(urls)} repositories in parallel (Max Workers: 5)...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(clone_one, urls)

def download_list(downloads, load_from_drive=False, parallel=False, max_workers=3):
    import threading
    import shutil
    cwd = Path.cwd()
    resolved_downloads = []
    
    gdrive_mounted = Path('/content/drive/MyDrive').exists()
    
    def get_drive_path(local_path):
        local_path = Path(local_path).resolve()
        d_base = Path('/content/drive/MyDrive/SMFactory')
        p_str = str(local_path).lower()
        if 'ckpt' in p_str or 'stable-diffusion' in p_str:
            return d_base / 'checkpoint'
        elif 'lora' in p_str:
            return d_base / 'lora'
        elif 'vae' in p_str:
            return d_base / 'vae'
        elif 'embeddings' in p_str:
            return d_base / 'embeddings'
        elif 'extensions' in p_str or 'custom_nodes' in p_str:
            return d_base / 'extensions'
        elif 'upscale' in p_str or 'esrgan' in p_str:
            return d_base / 'upscalers'
        elif 'unet' in p_str:
            return d_base / 'flux_unet'
        elif 'clip' in p_str or 'text_encoder' in p_str:
            return d_base / 'flux_clip'
        else:
            return d_base / local_path.name

    for url_line, local_dir in downloads:
        url_line = url_line.strip()
        if not url_line:
            continue
        
        parts = url_line.split()
        url = parts[0].replace('\\', '')
        fn = parts[1] if len(parts) > 1 else None
        
        resolved_url, j, versionId, fn = get_url(url, fn)
        if not resolved_url:
            continue
            
        local_dir = Path(local_dir).expanduser()
        local_dir.mkdir(parents=True, exist_ok=True)
        
        if not fn:
            fn = Path(urlparse(resolved_url).path).name
            if not fn:
                fn = "downloaded_file"
                
        local_file = local_dir / fn
        drive_dir = None
        drive_file = None
        skip = False
        
        if load_from_drive and gdrive_mounted:
            drive_dir = get_drive_path(local_dir)
            drive_dir.mkdir(parents=True, exist_ok=True)
            drive_file = drive_dir / fn
            
            if drive_file.exists():
                print(f"[SMFactory] File found in Google Drive: {fn}. Skipping download.")
                if local_file.exists() or local_file.is_symlink():
                    try:
                        if local_file.is_symlink() or local_file.is_file():
                            local_file.unlink()
                        elif local_file.is_dir():
                            shutil.rmtree(local_file)
                    except Exception:
                        pass
                try:
                    local_file.symlink_to(drive_file)
                except Exception as e:
                    print(f"Error creating symlink: {e}")
                
                stem = Path(fn).stem
                for ext in ['.json', '.preview.png']:
                    sidecar_drive = drive_dir / f"{stem}{ext}"
                    sidecar_local = local_dir / f"{stem}{ext}"
                    if sidecar_drive.exists():
                        if sidecar_local.exists() or sidecar_local.is_symlink():
                            try:
                                sidecar_local.unlink()
                            except Exception:
                                pass
                        try:
                            sidecar_local.symlink_to(sidecar_drive)
                        except Exception:
                            pass
                skip = True
        
        resolved_downloads.append({
            'original_url_line': url_line,
            'url': resolved_url,
            'local_dir': local_dir,
            'filename': fn,
            'drive_dir': drive_dir,
            'drive_file': drive_file,
            'local_file': local_file,
            'skip': skip,
            'j': j,
            'versionId': versionId
        })
        
    to_download = [d for d in resolved_downloads if not d['skip']]
    if not to_download:
        print("[SMFactory] All files are already loaded or skipped.")
        return
        
    if not parallel:
        for d in to_download:
            print(f"[SMFactory] Downloading sequentially: {d['filename']}")
            target_dir = d['drive_dir'] if (load_from_drive and gdrive_mounted) else d['local_dir']
            os.chdir(target_dir)
            try:
                ariari(d['url'], target_dir, d['filename'])
                if load_from_drive and gdrive_mounted:
                    if d['local_file'].exists() or d['local_file'].is_symlink():
                        try:
                            d['local_file'].unlink()
                        except Exception:
                            pass
                    d['local_file'].symlink_to(d['drive_file'])
                    
                    stem = Path(d['filename']).stem
                    for ext in ['.json', '.preview.png']:
                        side_drive = d['drive_dir'] / f"{stem}{ext}"
                        side_local = d['local_dir'] / f"{stem}{ext}"
                        if side_drive.exists():
                            if side_local.exists() or side_local.is_symlink():
                                try:
                                    side_local.unlink()
                                except Exception:
                                    pass
                            try:
                                side_local.symlink_to(side_drive)
                            except Exception:
                                pass
            finally:
                os.chdir(cwd)
    else:
        queue_file = Path('/tmp/aria2_queue.txt')
        queue_content = []
        
        for d in to_download:
            target_dir = d['drive_dir'] if (load_from_drive and gdrive_mounted) else d['local_dir']
            civitai = get_civdom(d['url'])
            ua = civitai_headers()['User-Agent'] if civitai else 'Mozilla/5.0'
            
            queue_content.append(f"{d['url']}")
            queue_content.append(f"  dir={target_dir}")
            queue_content.append(f"  out={d['filename']}")
            queue_content.append(f"  header=User-Agent: {ua}")
            if TOBRUT and 'huggingface.co' in d['url']:
                queue_content.append(f"  header=Authorization: Bearer {TOBRUT}")
            if TOKET and f'{civitai}/api/download/models/' in d['url']:
                queue_content.append(f"  header=Authorization: Bearer {TOKET}")
                
        queue_file.write_text("\n".join(queue_content))
        
        cmd = [
            'aria2c',
            '-i', str(queue_file),
            '--allow-overwrite=true',
            '--console-log-level=error',
            '-c',
            '-x16', '-s16', '-k1M',
            f'-j{max_workers}'
        ]
        
        print(f"[SMFactory] Starting parallel download of {len(to_download)} files (Max Workers: {max_workers})...")
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            aria2_output = ''
            
            while True:
                line = p.stderr.readline()
                if line == '' and p.poll() is not None:
                    break
                if line:
                    aria2_output += line
                    for prog in line.splitlines():
                        m = re.match(
                            r'\[#\w+\s+'
                            r'(?:(\d+(?:\.\d+)?\w+/\d+(?:\.\d+)?\w+))?'
                            r'\((\d+%)\)'
                            r'.*?DL:(\d+(?:\.\d+)?\w+)'
                            r'(?:.*?ETA:(\d+\w+))?',
                            prog
                        )
                        if m:
                            sizes, percent, speed, eta = m.groups()
                            gid_match = re.search(r'\[#(\w+)', prog)
                            gid = gid_match.group(1) if gid_match else "Parallel"
                            
                            percent_val = percent
                            parts = [f"({percent_val})"]
                            if sizes:
                                parts.append(sizes)
                            parts.append(f"DL:{speed}")
                            if eta:
                                parts.append(f"ETA:{eta}")
                            
                            body = ' '.join(parts)
                            print(f"\r【#{gid} {body}】", end='', flush=True)
            p.wait()
            print()
            
            for d in to_download:
                target_dir = d['drive_dir'] if (load_from_drive and gdrive_mounted) else d['local_dir']
                target_file = target_dir / d['filename']
                
                if target_file.exists():
                    print(f"  {GREEN}✓{RESET} {d['filename']} downloaded successfully.")
                    if load_from_drive and gdrive_mounted:
                        if d['local_file'].exists() or d['local_file'].is_symlink():
                            try:
                                d['local_file'].unlink()
                            except Exception:
                                pass
                        d['local_file'].symlink_to(d['drive_file'])
                    
                    if d['j']:
                        civitai_infotags(d['j'], target_dir, d['filename'], d['versionId'])
                        t = threading.Thread(
                            target=civitai_preview,
                            args=(d['j'], target_dir, d['filename'], d['versionId']),
                            daemon=True
                        )
                        t.start()
                        t.join(5)
                        
                        if load_from_drive and gdrive_mounted:
                            stem = Path(d['filename']).stem
                            for ext in ['.json', '.preview.png']:
                                side_drive = d['drive_dir'] / f"{stem}{ext}"
                                side_local = d['local_dir'] / f"{stem}{ext}"
                                if side_drive.exists():
                                    if side_local.exists() or side_local.is_symlink():
                                        try:
                                            side_local.unlink()
                                        except Exception:
                                            pass
                                    try:
                                        side_local.symlink_to(side_drive)
                                    except Exception:
                                        pass
                else:
                    print(f"  {RED}✗{RESET} {d['filename']} download failed or file not found.")
                    
        except KeyboardInterrupt:
            print("\n[SMFactory] Parallel download canceled by user.")
        finally:
            if queue_file.exists():
                queue_file.unlink()

@register_line_magic
def pull(line):
    inputs = line.split()
    if len(inputs) < 3: return

    subs = subprocess.run
    repo, tarfold, despath = inputs[:3]
    branch = inputs[3] if len(inputs) == 4 else None

    print(
        f"\n{'':>2}{'pull':<4} : {tarfold}",
        f"\n{'':>2}{'from':<4} : {repo}",
        f"\n{'':>2}{'into':<4} : {despath}",
        end=''
    )

    if branch: print(f"\n{'':>2}{'branch':<4} : {branch}")
    print('\n')

    fp = Path(despath).expanduser()
    opts = {'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE, 'check': True}
    cmd1 = f'git clone -n --depth=1 --filter=tree:0'
    if branch: cmd1 += f' --branch {branch}'
    cmd1 += f' {repo}'
    subs(shlex.split(cmd1), cwd=str(fp), **opts)

    repofold = fp / Path(repo).name.rstrip('.git')

    cmd2 = f'git sparse-checkout set --no-cone {tarfold}'
    subs(shlex.split(cmd2), cwd=str(repofold), **opts)

    cmd3 = 'git checkout'
    subs(shlex.split(cmd3), cwd=str(repofold), **opts)

    zipin = repofold / 'config' / tarfold
    zipout = fp / f'{tarfold}.zip'
    with zipfile.ZipFile(str(zipout), 'w') as zipf:
        for root in zipin.rglob('*'):
            if root.is_file():
                arcname = str(root.relative_to(zipin))
                zipf.write(str(root), arcname=arcname)

    cmd4 = f'unzip -o {str(zipout)}'
    subs(shlex.split(cmd4), cwd=str(fp), **opts)
    zipout.unlink()

    cmd5 = f'rm -rf {str(repofold)}'
    subs(shlex.split(cmd5), cwd=str(fp), **opts)

@register_line_magic
def tempe(line=''):
    try:
        from KANDANG import TEMPPATH
        TMP = Path(TEMPPATH)
    except ImportError:
        TMP = Path('/tmp')

    DIRS = [
        'ckpt',
        'lora',
        'controlnet',
        'svd',
        'z123',
        'clip',
        'clip_vision',
        'diffusers',
        'diffusion_models',
        'text_encoders',
        'unet'
    ]

    for SUB in DIRS: Path(f'{TMP}/{SUB}').mkdir(parents=True, exist_ok=True)
