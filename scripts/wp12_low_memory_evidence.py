"""Deneysel düşük bellek hazırlığının gerçek gözlem/test raporu; LLM yok."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import wp12_source_case as c
import wp12_source_low_memory as low
from wp09_close_wp10_notebooks import execute


def text_new(path,value):
    with Path(path).open('x',encoding='utf-8') as f:f.write(value)


def main():
    p=c.read(low.POLICY);m=c.read(low.QA/'current_measurements.json')
    stable=c.read(low.QA/'read_only_stability_samples.json')['memory']
    ast=c.read(low.QA/'powershell_5_1_syntax.json')
    assert all(x['error_count']==0 for x in ast['files'])
    assert ast['files'][0]['sha256']==p['runner_sha256']
    for name,count in [('test_low_memory.log',25),('test_existing_contract.log',24)]:
        log=(low.QA/name).read_text(encoding='utf-8-sig')
        assert f'Ran {count} tests' in log and log.rstrip().endswith('OK')
    prior=c.read(low.QA/'previous_files_sha256.json')
    changed=[name for name,h in prior.items() if c.sha(c.ROOT/name)!=h];assert not changed,changed
    native_log=(c.QA/'test_source_single_case_final.log').read_text(encoding='utf-8-sig')
    # Kaydedilmiş gerçek GGUF metadata satırları; yeni model yüklemesi yok.
    import re
    keys=['gemma3.block_count','gemma3.embedding_length','gemma3.attention.head_count_kv',
          'gemma3.attention.key_length','gemma3.attention.value_length']
    dims={k:int(re.search(re.escape(k)+r'\s+u32\s+= (\d+)',native_log).group(1)) for k in keys}
    kv_bytes=dims['gemma3.block_count']*2048*dims['gemma3.attention.head_count_kv']*(dims['gemma3.attention.key_length']+dims['gemma3.attention.value_length'])*2
    blob_size=c.GGUF.stat().st_size
    evidence={'scope':'PREPARATION_ONLY_NO_INFERENCE','memory_policy':p['version'],
        'measurement_at':m['memory']['at'],'initial_gate_passed_at_observation':low.entry_gate(m['memory'],m['GPU'],p),
        'all_5_host_commit_OS_samples_passed':all(low.entry_gate(x,m['GPU'],p) for x in stable),
        'GPU_measurement_single_snapshot_not_runtime_peak':True,'available_RAM_GiB':m['memory']['available_bytes']/2**30,
        'available_commit_GiB':m['memory']['commit_available_bytes']/2**30,'GPU_free_MiB':m['GPU']['free_MiB'],
        'OS_low_memory_notification':m['memory']['low_memory_notification'],'is_appcontainer':m['is_appcontainer'],
        'model_blob_bytes':blob_size,'GGUF_architecture_from_previous_real_vocab_log':dims,
        'hypothetical_full_context_FP16_KV_bytes':kv_bytes,
        'KV_estimate_is_not_measured_runtime_usage':True,'runtime_overhead_or_cpu_gpu_placement':'UNKNOWN_UNTIL_USER_RUN',
        'input_token_count_from_unchanged_prompt':919,'max_generation_requests':1,
        'actual_API_calls_this_preparation':0,'actual_generation_calls_this_preparation':0,
        'new_tests_passed':25,'existing_contract_tests_passed':24,'PowerShell_5_1_syntax_errors':0,
        'runner_sha256':p['runner_sha256'],'prior_files_unchanged_before_status_update':len(prior),
        'semantic_review':'NOT_PERFORMED_NO_REAL_OUTPUT','safety_guarantee':False}
    c.save_new(low.QA/'preparation_checks.json',evidence)
    F=c.ROOT/'reports/figures/WP12/experimental_low_memory_v1';F.mkdir(parents=True,exist_ok=True)
    init=r'''from pathlib import Path
import json,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists(): ROOT=ROOT.parent
Q=ROOT/'reports/qa/WP12/experimental_low_memory_v1'
F=ROOT/'reports/figures/WP12/experimental_low_memory_v1'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
p=read(ROOT/'configs/WP12_EXPERIMENTAL_LOW_MEMORY_v1.json');m=read(Q/'current_measurements.json')
checks=read(Q/'preparation_checks.json')
pd.set_option('display.max_colwidth',600)
'''
    execute('WP12_experimental_low_memory_single_case.ipynb',[
        ('md','''# WP12 — EXPERIMENTAL_LOW_MEMORY_v1

Kullanıcı yalnız bu tek gerçek PDF açıklaması için daha düşük giriş limitlerini açıkça onayladı. Eski2,5GiB politika, smoke kayıtları ve önceki kaynaklı pilot hazırlığı değişmez. Bu notebook **sadece gerçek ölçüm ve hazır betiği belgeler; inference/API yoktur**. Normal kullanıcı PowerShell'inde S01-R1 bekleniyor. Ölçümler çalışabilirlik veya güvenlik garantisi değildir.'''),
        ('code',init+'''
display(pd.DataFrame([{'politika':p['version'],'RAM_GiB':p['RAM_floor_bytes']/2**30,
 'VRAM_GiB':p['GPU_floor_MiB']/1024,'commit_GiB':p['commit_floor_bytes']/2**30,
 'runtime_RAM_GiB':p['runtime_RAM_floor_bytes']/2**30,'runtime_commit_GiB':p['runtime_commit_floor_bytes']/2**30,
 'HTTP_timeout_s':p['HTTP_timeout_seconds'],'otomatik_tekrar':p['automatic_retry']}]))
display(pd.DataFrame([m['memory']]).assign(GPU_free_MiB=m['GPU']['free_MiB']))
'''),
        ('md','''**Yorum:** Başlangıç≥1,5GiB RAM,≥1GiB VRAM,≥3GiB commit ve Windows düşük bellek sinyali=false. Commit bir fiziksel RAM rezervi değildir. Çalışmada RAM<0,75GiB, commit<1GiB veya OS düşük bellek sinyali varsa kayıt ve HTTP istemci iptali; sunucunun anında durması garanti edilmez. Eksik ölçümde devam edilmez. Eski2,5GiB RAM kapısı önceki politikalarda hâlâ geçerlidir.

## Gerçek ölçüm ve beş kararlı örnek'''),
        ('code','''
samples=pd.DataFrame(read(Q/'read_only_stability_samples.json')['memory'])
display(samples)
fig,axes=plt.subplots(1,2,figsize=(11,4))
ram=samples.available_bytes/2**30;commit=samples.commit_available_bytes/2**30
axes[0].plot(range(1,6),ram,marker='o',label='Ölçülen boş RAM')
axes[0].axhline(2.5,color='gray',ls='--',label='Eski v2 giriş')
axes[0].axhline(1.5,color='#b08a43',ls='--',label='Deneysel giriş')
axes[0].axhline(.75,color='#b35c5c',ls=':',label='Çalışma uyarısı')
axes[0].set(xlabel='Gerçek örnek',ylabel='GiB',title='RAM: eski ve deneysel kapılar ayrı');axes[0].legend(fontsize=8)
axes[1].plot(range(1,6),commit,marker='o',color='#568b78',label='Boş sistem commit')
axes[1].axhline(3,color='#b08a43',ls='--',label='Deneysel giriş3GiB')
axes[1].axhline(1,color='#b35c5c',ls=':',label='Çalışma uyarısı1GiB')
axes[1].set(xlabel='Gerçek örnek',ylabel='GiB',title='Commit: RAM ile aynı ölçü değildir');axes[1].legend(fontsize=8)
plt.tight_layout();plt.savefig(F/'01_actual_memory_samples_and_separate_thresholds.png',dpi=160);plt.show()
display(pd.DataFrame([checks]).T.rename(columns={0:'gerçek_kayıt'}))
'''),
        ('md','''**Yorum:** Beş örneğin RAM/commit/OS koşulları geçti; GPU ayrı anlık3935MiB ölçümüdür, beş eşzamanlı GPU ölçümü veya tepe değildir. Bu hazırlıkta AppContainer=true olduğu için API'ye hiç başvurulmadı. Kullanıcı betiği her kapıyı yeniden ölçer ve AppContainer'da metadata isteğinden bile önce durur.

Model dosyası yaklaşık769MiB; önceki gerçek GGUF metadatasıyla26 katman,1 KVhead,256 key/256value ve2048context için varsayımsal tam FP16 KV52MiB. Runtime/aktivasyon/sürücü/CPU-GPU kopyaları buna dahil değildir. Bunlar resident/peak ölçümü değildir;1GiB GPU veya1,5GiB RAM modelin sığacağını garanti etmez.

## Değişmeyen gerçek kaynak ve yöntem'''),
        ('code','''
ctx=read(ROOT/'reports/qa/WP12/source_single_case_v1/package/context.json')
display(pd.DataFrame([ctx['scenario']])[['scenario_id','question_tr','acceptance_criteria_tr']])
display(pd.DataFrame(ctx['sources'])[['physical_page','scope','kind','quote_id','quote']])
display(pd.DataFrame([{'tam_prompt_token':919,'giriş_limiti':1536,'çıktı':384,'güvenlik':128,
 'context':2048,'gerçek_üretim':0,'semantik_inceleme':'GERÇEK_YANIT_BEKLENİYOR','otomatik_yayın':False}]))
'''),
        ('md','''**Yorum:** S01-R1 Erythromycin ürün/formülasyon sorusudur; fiziksel sayfa1 ve6'nın iki tam alıntısı537 karakterdir. Frozen senaryo/soru/kabul kriteri, model digest, prompt, JSON Schema ve generation ayarları değişmedi. Yalnız ayrı bellek politikası ve ölçüm koşulları eklendi.919 token önceki gerçek sözlük-only hesabıdır; kullanıcı isteğinden önce aynı tokenizer ile yeniden sayılır. Tam alıntı/bağlam sığmazsa CONTEXT_BUDGET; kesme/fallback yok.

25 yeni deneysel test ve24 mevcut kaynak sözleşmesi testi geçti. PS5.1 parser0hata, tek generation çağrı noktası. Eksik ölçüm, düşük RAM/GPU/commit ve OS basıncı sınandı; hiç optimizer/LLM inference yapılmadı. Geçerli JSON/quote-ID semantik başarı değildir. `reported_in_PDF` ile `predicted_by_GNN` ayrıdır; sonuncu NOT_REQUESTED/null kalır. Gerçek açıklama ilk kullanıcı çıktısından sonra insan tarafından incelenecek.57 çağrı, otomatik tekrar/yayın ve WP13 kapalıdır.''')])
    command=f'& "{c.ROOT / p["runner"]}" -RunFirstCase'
    report=f'''# WP12 — EXPERIMENTAL_LOW_MEMORY_v1 tek-vaka hazırlığı

08.11.2026 · **Yalnız normal kullanıcı PowerShell'inde S01-R1 için hazır. Gerçek LLM isteği gönderilmedi.**

Kullanıcı1,68GiB civarı RAM koşulunda mevcut Gemma1B ile kontrollü tek denemeyi açıkça onayladı. Bu onay yalnız ayrı deneysel politika içindir. Eski2,5GiB politika/smoke/başarısızlıklar/QA,19 senaryo ve44 kaynak alıntısı değiştirilmedi. Aktif AGENTS/ROADMAP/output sözleşmesi geçerlidir; WP13 yoktur.

## Politika ve gerçek ölçüm

| Koşul | Deneysel giriş | Çalışma uyarısı |
|---|---:|---:|
| Kullanılabilir fiziksel host RAM |≥1,5GiB|<0,75GiB|
| Boş GPU belleği |≥1GiB|Başlangıç/son ölçümü; sürekli GPU peak iddiası yok|
| Sistem commit boşluğu |≥3GiB|<1GiB|
| Windows LowMemoryResourceNotification |false ve okunabilir olmalı|true veya ölçüm hatası|

Commit girişte önceki3GiB marjını korur;1GiB çalışma kritik sınırı ayrı açık politikadır. Bu sınırlar performansa göre seçilmedi ve güvenlik garantisi değildir. Commit alanı fiziksel RAM ile eşdeğer değildir; paging veya sistem yavaşlamasını önlediği iddia edilemez. Başlangıç5 RAM/commit/OS örneği yaklaşık4 saniye, gönderim öncesi RAM/GPU/commit/OS tekrar kontrolü; çalışma örnekleme250ms. Kısa süreli basınç örnekler arasında kaçabilir. Runtime uyarısında HTTP istemcisi iptal edilir, yeni istek/tekrar yoktur; başlamış sunucu inference'ının hemen durduğu varsayılmaz. Ölçüm eksikse işlem durur.

Gerçek salt okunur ölçüm **{m['memory']['at']}**: RAM **{evidence['available_RAM_GiB']:.3f}GiB**, toplamRAM{m['memory']['total_bytes']/2**30:.3f}GiB; GTX1650Ti4096MiB toplam/**3935MiB boş**, commit **{evidence['available_commit_GiB']:.3f}GiB**, OS düşük bellek **false**. Bu an yeni giriş kapısını geçti; eski2,5GiB kapısını geçmedi. Sonraki5 örnek de RAM/commit/OS koşullarını geçti; GPU o aralık için tek snapshot'tır. Bunlar kullanıcı komutunun çalışma anına taşınan garanti değildir; her şey tekrar ölçülür.

Windows OS sinyali [CreateMemoryResourceNotification](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-creatememoryresourcenotification) ve [QueryMemoryResourceNotification](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-querymemoryresourcenotification) ile okunur. Yalnız bu gözlem için alınmış notification handle kapatılır; uygulama veya servis sonlandırılmaz. Commit hesabı [PERFORMANCE_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-performance_information) üzerinden `(CommitLimit−CommitTotal)×PageSize`dır. API hatası false sinyal gibi yorumlanmaz.

## Donanım gerekçesi ve bilinmeyenler

Mevcut onaylı GGUF dosyası **{blob_size}bayt ({blob_size/2**20:.2f}MiB)**; bu dosya boyutudur, process resident veya GPU yükleme boyutu değildir. Önceki gerçek vocabulary-only logunda26 katman,1 KVhead, key256/value256 kayıtlıdır.2048context veFP16 varsayımıyla üstten tam KV dizisi hesabı `26×2048×1×(256+256)×2`=**{kv_bytes/2**20:.0f}MiB**. Gemma'nın sliding/local attention uygulaması veya cache tipi bunu değiştirebilir; gerçek runtime KV ölçümü yapılmadı.

Bu nedenle1GiB GPU giriş eşiği ancak deneysel alt sınırdır. DLL/runtime, aktivasyonlar, scratch, sürücü ve CPU/GPU kopyaları bilinmiyor. Mevcut3,84GiB boş GPU alanı gözlemsel bir marj sağlar; GPU offload yerleşimi veya peak hostRAM garantisi değildir.1,5GiB başlangıç ve0,75GiB uyarısı arasındaki alan dar olduğundan ilk yanıt/timeout/çalışma bellek kayıtları görülmeden daha fazla istek açılmaz.

## Değişmeyen vaka, kimlik ve token politikası

- Tek vaka **S01-R1**: frozen19 listesinin ilk kaydı, Erythromycin ürün ve formülasyon açıklaması; başarıya göre seçilmedi. Fiziksel sayfa1+6, iki tam alıntı537 karakter; soru/ölçüt/quote-ID/ham metin aynıdır.
- Model **{p['model']}**, API/source digest **{p['API_model_digest']}**. Yerel wrapper SHA313f… ayrı kalır. Eski identity helper ve onaylı kaynak manifesti doğrulanır; yeni indirme/etiket/model yok.
- Prompt, v1 daraltılmış JSON Schema ve tüm generation ayarları önceki tek-vaka paketinin aynısı:2048context/384output/batch32/temp0/seed20261108/thinkfalse/streamfalse/keep_alive0; HTTP60s değişmez.
- Tam prompt **919 gerçek token**, önceki vocabulary-only ölçümü; her kullanıcı çalıştırmasında aynı GGUF sözlüğü/şablonuyla yeniden hesaplanır.1536 giriş+384output+128safety; tam kaynak/zorunlu bağlam sığmazsa **CONTEXT_BUDGET**. Sessiz kesme yok. Tensor/context/decode başlatmayan token sayacı yalnız düşük-bellek adaptörünün açık1,5GiB kapısından sonra çalışır; eski modülün2,5GiB kapısı değiştirilmedi.
- Native dosya, model blob, PDF,19 senaryo,44 alıntı, bağımlılık/kaynak ve kod hash'leri kontrol edilir. Sunucunun `prompt_eval_count` değeri offline sayıyla eşit değilse inceleme başarısızdır; otomatik yeniden deneme yoktur.

## İstemci ve kayıt sınırları

`scripts/WP12_ExperimentalLowMemorySingleCase_v1.ps1` tek PostAsync içerir. AppContainer algılanırsa **API metadata isteğinden önce** durur. Bu hazırlıkta AppContainer=true; API0/inference0. Kullanıcının kendi normal PowerShell'inde version/tags/ps metadatası okunur; kimlik/JSON Schema/token/bellek kapıları geçmeden kaynaklı chat gönderilmez. Başka model yüklüyse otomatik unload yerine durur. Süreç sonlandırma, servis/güvenlik ayarı, yetki yükseltme veya model indirme kodu yoktur.

Her deneme `reports/qa/WP12/experimental_low_memory_user_runs_v1/<zaman_GUID>/` altında ham request/response, tam prompt ve token proof, quote bağlamı, kaynak/kod/model hash'leri, RAM/commit/OS örnekleri, giriş/sonGPU, süre/HTTP/istisna, Python logları, run_record ve dosya hash manifestini saklar. Timeout/istemci hatasında server_completion UNKNOWN kalır. Tek `inference_attempts` kaydı istemci gönderim teşebbüsüdür; global sunucu trafiği denetimi değildir. Üretimden önce durulursa ham yanıt olmaması açıkça anlaşılır; sahte yanıt üretilmez.

## Anlam incelemesi ve QA

JSON Schema ve kaynak-ID/scope/kind kontrolü insan semantik incelemesinden ayrıdır. Geçerli aday `SOURCE_CANDIDATE_PENDING_HUMAN_REVIEW`, semantic_success=null, automatic_release=false; ret ve düşük kaliteli/eksik yanıtlar saklanır. Kaynağa aykırı Türkçe iddia otomatik başarı sayılmaz. `reported_in_PDF` ile `predicted_by_GNN` alanları ayrıdır; yeni skor/SHAP/Δz/MedDRA veya klinik risk iddiası yoktur.

**25 yeni test +24 mevcut sözleşme testi geçti.** Sınır değerler, eksik/bozuk ölçüm, OS basıncı, RAM/GPU/commit düşüşü, tek çağrı, AppContainer izolasyonu, no-retry ve eski2,5GiB/prompt/hash korunması doğrulandı. PS5.1({ast['parser']}) parser:iki dosyada0hata; runner1, observer0 generation çağrı noktası. Runner SHA-256 **{p['runner_sha256']}**. Betik gerçek inference için bu ortamda çalıştırılmadı.

Önceki **{len(prior)}** dosya güncelleme öncesi aynı SHA ile doğrulandı. Eski smoke, iki başarısız deneme, B0/B1/B2/GNN/SHAP/PPI/PDF/senaryo/kabul kriterleri korunur. Sadece güncel `run_status.md` yeni bölüm alır; önceki tam baytları yeni QA'da arşivlenir ve dosyanın devamında korunur. Önceki hazırlık manifestinde mutable run_status girdisinin eski hash'i bu arşivle doğrulanır; eski manifest değiştirilmez.

## Kullanıcı komutu — yalnız bir kez

Normal kullanıcı PowerShell'inde:

```powershell
{command}
```

Bu komut kendi kapılarını yeniden ölçer. Koşul sağlanmazsa durur; otomatik tekrar yapmaz. Yazdırdığı **Evidence directory** klasörünü paylaşın; ilk gerçek yanıtı kaynak sadakati ve teknik sonuç bakımından inceleyeceğiz. Tek denemeden sonra durulacak;19×3 veya WP13 başlatılmayacak.

Dosyalar: `configs/WP12_EXPERIMENTAL_LOW_MEMORY_v1.json` yalnız bu deneyin politikası; `scripts/wp12_source_low_memory.py` eski modülü değiştirmeyen adaptör; `scripts/WP12_LowMemoryObservation_v1.ps1` salt okunur OS ölçümü; `notebooks/WP12_experimental_low_memory_single_case.ipynb` çalıştırılmış Türkçe açıklamalar; `reports/figures/WP12/experimental_low_memory_v1/` gerçek ölçüm PNG'si; `reports/qa/WP12/experimental_low_memory_v1/` test/gözlem/korunma/manifest kanıtları.
'''
    text_new(c.ROOT/'reports/WP12_EXPERIMENTAL_LOW_MEMORY_v1.md',report)
    before=(low.QA/'run_status_before.md').read_bytes();assert (c.ROOT/'run_status.md').read_bytes()==before
    prefix=f'''# WP12 — EXPERIMENTAL_LOW_MEMORY_v1 tek-vaka kullanıcı çıktısı bekleniyor ·08.11.2026

- Kullanıcının açık kararıyla yalnız S01-R1 için ayrı deneysel politika: başlangıç RAM≥1,5GiB/GPU≥1GiB/commit≥3GiB, OS düşük bellekfalse; runtime RAM<0,75GiB veya commit<1GiB veya OS basıncında kayıt/istemci iptali/no-retry. Sunucunun hemen duracağı ve güvenlik garanti edilmez. Eski2,5GiB politika değiştirilmedi.
- Gerçek gözlem RAM{evidence['available_RAM_GiB']:.3f}GiB/GPU3935MiB/commit{evidence['available_commit_GiB']:.3f}GiB/OSfalse;5 RAM-commit-OS örneği geçti. AppContainer=true; API ve inference0. Kullanıcı betiği çalışma anında yeniden ölçer.
- scripts/WP12_ExperimentalLowMemorySingleCase_v1.ps1 -RunFirstCase yalnız1 kaynaklı istek. Frozen S01/44 alıntı/19 vaka/model9755…/prompt919token/generation ayarları korunur.25 yeni+24 eski test geçti; PS5.1 iki dosyada0hata, tek PostAsync. SHA{p['runner_sha256']}.
- Önceki{len(prior)} dosya doğrulandı; yalnız status yeni bölümle güncellendi ve eski baytları arşivlendi. Yapısal geçiş semantik başarı değil; ham kullanıcı yanıtı ve insan kaynak incelemesi bekleniyor.19×3, yeni indirme/eğitim, otomatik yayın ve WP13 yok.
- Rapor reports/WP12_EXPERIMENTAL_LOW_MEMORY_v1.md; notebook notebooks/WP12_experimental_low_memory_single_case.ipynb; QA reports/qa/WP12/experimental_low_memory_v1/.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''.encode('utf-8')
    (c.ROOT/'run_status.md').write_bytes(prefix+before)
    changed=[name for name,h in prior.items() if c.sha(c.ROOT/name)!=h]
    assert changed==['run_status.md'],changed
    assert c.sha(low.QA/'run_status_before.md')==prior['run_status.md']
    c.save_new(low.QA/'previous_artifacts_preservation.json',{'previous_files':len(prior),
        'unchanged_at_original_path':len(prior)-1,'only_updated_path':'run_status.md',
        'old_status_archived_exactly':True,'old_status_retained_as_exact_suffix':(c.ROOT/'run_status.md').read_bytes().endswith(before),
        'changed_previous_source_or_result_files':0})
    print('Experimental policy/report/executed notebook ready; user actual response pending.')


if __name__=='__main__':main()
