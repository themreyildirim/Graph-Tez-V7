"""Anahtar değerini kanıta taşımayan yükleyici ve gizli-dosya sınırı."""
from pathlib import Path
import contextlib
import io
import json
import os
import hashlib


def is_private_path(path):
    p=Path(path);name=p.name.casefold()
    return (name.startswith('.env') or name in {'.netrc','.npmrc','.pypirc','.openai_api_key'}
        or name.endswith(('.pem','.key','.p12','.pfx')) or name.startswith(('credentials','secrets'))
        or any(x.casefold() in {'.git','.ssh','.aws','.secrets'} for x in p.parts))


def public_sha(path):
    if is_private_path(path):raise ValueError('PRIVATE_FILE_EXCLUDED_NO_READ_NO_HASH')
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def load_key(root,environ=None):
    """Yalnız OPENAI_API_KEY. dotenv interpolasyonu/diğer env değişkenleri yok."""
    env=os.environ if environ is None else environ
    key=env.get('OPENAI_API_KEY')
    if not key:
        from dotenv import dotenv_values
        # Parser uyarısı/çıktısı kanıta veya terminale taşınmaz.
        try:
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                values=dotenv_values(Path(root)/'.env',interpolate=False,verbose=False,encoding='utf-8-sig')
        except Exception:return None
        key=values.get('OPENAI_API_KEY')
        values.clear()
    if not isinstance(key,str):return None
    key=key.strip()
    if len(key)<16 or any(ord(x)<33 or ord(x)>126 for x in key):return None
    return key


def key_available(root):return bool(load_key(root))


def git_privacy_state(root):
    import subprocess
    repo=subprocess.run(['git','-C',str(root),'rev-parse','--is-inside-work-tree'],capture_output=True,text=True)
    if repo.returncode!=0:return {'git_repository_present':False,'tracked_private_files_detected':False}
    tracked=subprocess.run(['git','-C',str(root),'ls-files','-z'],capture_output=True)
    if tracked.returncode!=0:raise ValueError('GIT_PRIVACY_CHECK_UNAVAILABLE')
    names=tracked.stdout.decode('utf-8').split('\x00')
    return {'git_repository_present':True,'tracked_private_files_detected':any(is_private_path(n) for n in names if n)}


class SecretBlocked(ValueError):pass


class Evidence:
    """Tüm çalışma kanıtları için secret-aware yazıcı. Secret kendisi hash'lenmez."""
    def __init__(self,folder,key=None):self.folder=Path(folder);self._key=key
    def text(self,name,value):
        if Path(name).name!=name or is_private_path(name):raise ValueError('INVALID_EVIDENCE_FILENAME')
        if self._key and self._key in value:raise SecretBlocked('SECRET_DETECTED_NOT_SAVED')
        if '"authorization"' in value.casefold() or 'bearer ' in value.casefold():
            raise SecretBlocked('AUTHENTICATION_MATERIAL_NOT_SAVED')
        with (self.folder/name).open('x',encoding='utf-8',newline='') as f:f.write(value)
    def json(self,name,value):self.text(name,json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False))


def safe_request_id(value,key):
    import re
    if not isinstance(value,str) or (key and key in value):return None
    return value if re.fullmatch(r'[A-Za-z0-9_-]{1,160}',value) else None


def safe_error_fields(body,key):
    """401 mesajı anahtarı yansıtabilir; raw error/message/header asla yazılmaz."""
    import re
    try:error=json.loads(body).get('error',{})
    except Exception:return {'provider_error_body':'WITHHELD_SECURITY_POLICY'}
    out={'provider_error_body':'WITHHELD_SECURITY_POLICY'}
    for name in ['type','code','param']:
        value=error.get(name)
        if isinstance(value,str) and (not key or key not in value) and re.fullmatch('[A-Za-z0-9_.-]{1,80}',value):out[name]=value
    return out
