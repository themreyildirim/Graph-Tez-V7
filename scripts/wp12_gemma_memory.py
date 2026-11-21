"""GGUF metadata okur; tensor/model yüklemez. v2 bütçesi deneysel garanti değildir."""
from pathlib import Path
import math
import struct

GIB=2**30
MODEL_BLOB=Path('C:/Users/emrey/.ollama/models/blobs/sha256-2f8c3d137f2496dcb4019e17a50f2974b89c1be1a742db3c80cc86f91cafeeef')


def read_metadata(path):
    """64MiB metadata sınırı; tokenizer dizileri atlanır, tensor verisine girilmez."""
    with Path(path).open('rb') as f:
        def raw(n):
            if n<0 or f.tell()+n>64*2**20:raise ValueError('metadata budget')
            b=f.read(n)
            if len(b)!=n:raise ValueError('truncated GGUF')
            return b
        def unpack(fmt):return struct.unpack('<'+fmt,raw(struct.calcsize('<'+fmt)))[0]
        def string(keep):
            n=unpack('Q')
            if keep:return raw(n).decode('utf-8')
            if f.tell()+n>64*2**20:raise ValueError('metadata budget')
            f.seek(n,1)
        def value(t,keep):
            formats={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
            if t==8:return string(keep)
            if t==9:
                item=unpack('I');count=unpack('Q')
                if count>1_000_000 or item==9:raise ValueError('invalid array')
                for _ in range(count):value(item,False)
                return {'array_type':item,'count':count}
            if t not in formats:raise ValueError('unknown GGUF value type')
            return unpack(formats[t])
        if raw(4)!=b'GGUF':raise ValueError('GGUF magic')
        version=unpack('I')
        if version!=3:raise ValueError('only GGUFv3 is validated')
        tensors=unpack('Q');count=unpack('Q');metadata={}
        if count>100_000:raise ValueError('metadata count')
        for _ in range(count):
            key=string(True);t=unpack('I');keep=key.startswith(('general.','gemma3.'))
            v=value(t,keep)
            if keep:
                if key in metadata:raise ValueError('duplicate metadata')
                metadata[key]=v
        return {'version':version,'tensor_count':tensors,'metadata_count':count,
                'metadata_span_bytes':f.tell(),'metadata':metadata,'tensor_data_read':False}


def kv_bytes(meta, context, element_bytes):
    m=meta['metadata']
    if type(context) is not int or context<=0 or element_bytes not in (2,4):raise ValueError('KV inputs')
    # K ve V ayrı boyutlarla; tüm katmanlarda tam context. Sliding-window indirimi YOK.
    return (m['gemma3.block_count']*m['gemma3.attention.head_count_kv']*context*
            (m['gemma3.attention.key_length']+m['gemma3.attention.value_length'])*element_bytes)


def budget(meta):
    weights=MODEL_BLOB.stat().st_size
    kv=kv_bytes(meta,2048,4)
    return {'weights_bytes':weights,'KV_FP16_bytes':kv_bytes(meta,2048,2),'KV_FP32_bytes':kv,
        'KV_assumption':'all26 layers/full2048 context, no sliding-window savings; dtype/layout unmeasured',
        'host_runtime_budget_bytes':int(.5*GIB),'host_staging_margin_bytes':int(.25*GIB),
        'host_reserve_bytes':int(.75*GIB),'GPU_runtime_budget_bytes':int(.5*GIB),
        'GPU_reserve_bytes':int(.5*GIB),
        'host_budget_total_bytes':weights+kv+int(1.5*GIB),
        'GPU_budget_total_bytes':weights+kv+GIB,
        'host_admission_bytes':int(2.5*GIB),'GPU_admission_MiB':2048,
        'commit_available_minimum_bytes':3*GIB,
        'estimated_budgets_not_measured_peak':True,'guaranteed_safe':False}


def admission(host_available_bytes,gpu_free_mib,commit_available_bytes):
    values=(host_available_bytes,gpu_free_mib,commit_available_bytes)
    if not all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) and x>=0 for x in values):return False
    return host_available_bytes>=int(2.5*GIB) and gpu_free_mib>=2048 and commit_available_bytes>=3*GIB
