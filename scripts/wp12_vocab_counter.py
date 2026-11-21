"""Kurulu llama.cpp620d2225c ile vocabulary-only token sayımı; decode/context yok.

llama_model_params ABI, aynı commit'in include/llama.h dosyasına göre80 bayttır.
Hiçbir llama_context/sampler oluşturulmaz; vocab_only=True, n_gpu_layers=0.
"""
import ctypes as C
import hashlib
import os
from pathlib import Path
import struct

RUNTIME=Path('C:/Users/emrey/AppData/Local/Programs/Ollama/lib/ollama')
GGUF=Path('C:/Users/emrey/.ollama/models/blobs/sha256-2f8c3d137f2496dcb4019e17a50f2974b89c1be1a742db3c80cc86f91cafeeef')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


class Params(C.Structure):
    _fields_=[('devices',C.c_void_p),('tensor_buft_overrides',C.c_void_p),
        ('n_gpu_layers',C.c_int32),('split_mode',C.c_int32),('load_mode',C.c_int32),
        ('lazy_mode',C.c_int32),('main_gpu',C.c_int32),('tensor_split',C.c_void_p),
        ('progress_callback',C.c_void_p),('progress_callback_user_data',C.c_void_p),('kv_overrides',C.c_void_p),
        ('vocab_only',C.c_bool),('check_tensors',C.c_bool),('use_extra_bufts',C.c_bool),
        ('no_host',C.c_bool),('no_alloc',C.c_bool),('load_mtp',C.c_bool)]


def template_from_gguf(path=GGUF):
    """Yalnız GGUF metadata; tokenizer token dizileri belleğe alınmadan atlanır."""
    with Path(path).open('rb') as f:
        def raw(n):
            if n<0 or f.tell()+n>16*2**20:raise ValueError('GGUF metadata limit')
            b=f.read(n)
            if len(b)!=n:raise ValueError('truncated metadata')
            return b
        def u(fmt):return struct.unpack('<'+fmt,raw(struct.calcsize('<'+fmt)))[0]
        def string(keep):
            n=u('Q')
            if keep:return raw(n).decode('utf-8')
            if f.tell()+n>16*2**20:raise ValueError('metadata limit')
            f.seek(n,1)
        def val(t,keep):
            if t==8:return string(keep)
            if t==9:
                subtype=u('I');count=u('Q')
                if count>1000000 or subtype==9:raise ValueError('invalid metadata array')
                for _ in range(count):val(subtype,False)
                return None
            formats={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
            return u(formats[t])
        if raw(4)!=b'GGUF' or u('I')!=3:raise ValueError('GGUFv3 required')
        u('Q');count=u('Q');out={}
        keys={'tokenizer.chat_template','tokenizer.ggml.bos_token_id','tokenizer.ggml.eos_token_id','tokenizer.ggml.add_bos_token','tokenizer.ggml.add_eos_token'}
        for _ in range(count):
            key=string(True);t=u('I');v=val(t,key in keys)
            if key in keys:out[key]=v
        return out


def render_single_user(content,template):
    from jinja2 import Environment,StrictUndefined
    def refuse(message):raise ValueError(message)
    return Environment(undefined=StrictUndefined).from_string(template).render(
        messages=[{'role':'user','content':content}],bos_token='<bos>',eos_token='<eos>',
        add_generation_prompt=True,raise_exception=refuse)


class VocabCounter:
    def __init__(self,model_path=GGUF,runtime=RUNTIME):
        self.model=None
        if C.sizeof(C.c_void_p)!=8 or C.sizeof(Params)!=80 or Params.vocab_only.offset!=72:
            raise RuntimeError('unsupported native ABI')
        self.directory_handle=os.add_dll_directory(str(runtime))
        self.dll=C.CDLL(str(runtime/'libllama.dll'))
        self.dll.llama_version.restype=C.c_char_p
        self.version=self.dll.llama_version().decode()
        self.dll.llama_model_default_params.restype=Params
        self.dll.llama_model_load_from_file.argtypes=[C.c_char_p,Params]
        self.dll.llama_model_load_from_file.restype=C.c_void_p
        self.dll.llama_model_get_vocab.argtypes=[C.c_void_p];self.dll.llama_model_get_vocab.restype=C.c_void_p
        self.dll.llama_model_free.argtypes=[C.c_void_p]
        self.dll.llama_tokenize.argtypes=[C.c_void_p,C.c_char_p,C.c_int32,C.POINTER(C.c_int32),C.c_int32,C.c_bool,C.c_bool]
        self.dll.llama_tokenize.restype=C.c_int32
        params=self.dll.llama_model_default_params()
        params.vocab_only=True;params.n_gpu_layers=0;params.load_mode=0
        # Sadece vocabulary okunur; backend/context/weights/forward başlatılmaz.
        self.model=self.dll.llama_model_load_from_file(str(model_path).encode('utf-8'),params)
        if not self.model:raise RuntimeError('vocabulary-only load failed; no fallback')
        self.vocab=self.dll.llama_model_get_vocab(self.model)
        if not self.vocab:self.close();raise RuntimeError('no vocabulary')

    def tokens(self,text,add_special=False):
        b=text.encode('utf-8')
        n=self.dll.llama_tokenize(self.vocab,b,len(b),None,0,add_special,True)
        if n==-(2**31):raise ValueError('token overflow')
        size=abs(n)
        buffer=(C.c_int32*max(1,size))()
        count=self.dll.llama_tokenize(self.vocab,b,len(b),buffer,size,add_special,True)
        if count<0:raise RuntimeError('tokenizer buffer mismatch')
        return list(buffer[:count])

    def close(self):
        if self.model:self.dll.llama_model_free(self.model);self.model=None
        if getattr(self,'directory_handle',None):self.directory_handle.close();self.directory_handle=None

    def __enter__(self):return self
    def __exit__(self,*args):self.close()
