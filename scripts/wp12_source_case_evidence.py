"""Ağsız hazırlık raporu/notebook; yalnız mevcut QA okur, LLM çalıştırmaz."""
from pathlib import Path
import json
import sys

sys.dont_write_bytecode=True
from wp12_source_case import ROOT,QA,CONFIG,read,sha,save_new
from wp09_close_wp10_notebooks import execute


def new_text(path,text):
    with Path(path).open('x',encoding='utf-8') as f:f.write(text)


def main():
    cfg=read(CONFIG);proof=read(QA/'package/offline_token_proof.json')
    sources=read(QA/'package/context.json');mem=read(QA/'preparation_memory_snapshot.json')
    full=(QA/'test_source_single_case_final.log').read_text(encoding='utf-8-sig')
    release=(QA/'test_source_single_case_release.log').read_text(encoding='utf-8-sig')
    contract=(QA/'test_existing_llm_contract.log').read_text(encoding='utf-8-sig')
    assert 'Ran 30 tests' in full and full.rstrip().endswith('OK')
    assert 'Ran 25 tests' in release and 'OK (skipped=1)' in release
    assert 'Ran 24 tests' in contract and contract.rstrip().endswith('OK')
    ast=read(QA/'powershell_5_1_release_syntax.json')
    assert ast['runner_sha256']==sha(ROOT/cfg['runner']) and ast['parse_error_count']==0
    checks={'stage':'S01_R1_PREPARED_NOT_RUN','full_preparation_tests_passed':30,
        'existing_source_contract_tests_passed':24,'final_release_tests_passed':25,
        'final_release_skipped_groups':1,'final_release_skipped_native_tests':5,
        'skip_reason':'VOCAB_ONLY_UTILITY_RAM_GUARD; never force utility or inference',
        'initial_test_failures':2,'initial_failure_cause':'Test assertions: native Jinja external trim and first-slot WAIT_FIRST_CASE_REVIEW status; fixture assertions corrected, original log retained',
        'PowerShell_5_1_parse_errors':0,'generation_AST_call_sites':ast['generation_call_AST_count'],
        'input_tokens':proof['input_token_count'],'input_limit':1536,'actual_LLM_generation_calls':0,
        'models_downloaded':0,'new_training':False,'semantic_review':'NOT_PERFORMED_NO_REAL_OUTPUT',
        'automatic_release':False,'stage2_enabled':False,'source_quotes':44,'frozen_scenarios':19,
        'first_scenario':'S01','first_repeat':1,'runner_sha256':cfg['runner_sha256']}
    save_new(QA/'preparation_checks.json',checks)
    save_new(QA/'first_case_human_review_template.json',{
        'status':'AWAITING_ACTUAL_USER_OUTPUT','scenario_id':'S01','repeat':1,
        'actual_run_directory':None,'raw_response_sha256':None,'structural_result':None,
        'reviewer':None,'reviewed_at':None,'semantic_success':None,'automatic_release':False,
        'frozen_question':sources['scenario']['question_tr'],
        'frozen_acceptance':sources['scenario']['acceptance_criteria_tr'],
        'human_checks':{'Turkish_and_faithful_to_quote':None,'identity_vs_formulation_preserved':None,
            'no_parent_product_equivalence_claim':None,'no_new_adverse_event_label_or_score':None,
            'all_claims_cited_with_correct_scope_kind':None,'nothing_published':None}})
    figures=ROOT/'reports/figures/WP12/source_single_case_v1';figures.mkdir(parents=True,exist_ok=True)
    init=r'''from pathlib import Path
import sys,json,pandas as pd,matplotlib.pyplot as plt
from IPython.display import display
ROOT=Path.cwd()
while not (ROOT/'AGENTS.md').exists(): ROOT=ROOT.parent
QA=ROOT/'reports/qa/WP12/source_single_case_v1'
F=ROOT/'reports/figures/WP12/source_single_case_v1'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
cfg=read(ROOT/'configs/WP12_SOURCE_SINGLE_CASE_v1.json')
ctx=read(QA/'package/context.json');proof=read(QA/'package/offline_token_proof.json')
pd.set_option('display.max_colwidth',600);pd.set_option('display.max_columns',12)
'''
    execute('WP12_source_single_case_preparation.ipynb',[
        ('md','''# WP12 — İlk gerçek kaynaklı açıklama için S01-R1 hazırlığı

Bu notebook **LLM çalıştırmaz**. Sabit kaynak, tam prompt token ölçümü, çalıştırıcı kontrolleri ve bekleyen insan incelemesini gösterir. Kullanıcı teknik echo testini kabul etti; gerçek kaynaklı açıklama henüz üretilmedi. Tek vaka frozen19 listesinin ilk kaydıdır; başarıya bakılarak seçilmedi. Yeni eğitim, PDF/model indirmesi, WP13 veya 57 çağrı yoktur.'''),
        ('code',init+'''
display(pd.DataFrame([{'model':cfg['model'],'API_digest':cfg['API_model_digest'],
 'Ollama_sürümü':cfg['server_version_pinned'],'vaka':'S01-R1',
 'gerçek_üretim_isteği':0,'otomatik_yayın':False,'ikinci_aşama':False}]))
display(pd.DataFrame([ctx['scenario']])[['scenario_id','question_tr','acceptance_criteria_tr']])
'''),
        ('md','''**Yorum:** S01 ürün kimliği/formülasyon açıklamasıdır; SIDER etiketi veya tahmin skoru değildir. İlaç ana kimliği ile belgeye özgü ürün/formülasyon eşdeğerliği kurulamaz. API digest, yerel wrapper dosya SHA'sından ayrı doğrulanır. Eski Qwen/Gemma kayıtları korunur.

## Gerçek PDF alıntıları'''),
        ('code','''
display(pd.DataFrame(ctx['sources'])[['physical_page','scope','kind','quote_id','quote']])
'''),
        ('md','''**Yorum:** Erythromycin fiziksel sayfa1 ve6'dan iki alıntı toplam537 Unicode karakterdir. Satır sonları dahil ham kaynak metni korunur. Cümle/sayfa/aralık bilgisi çıktıdaki quote-ID'den trusted wrapper ile eklenir; LLM bu alanları yazmaz. Kimlik, tuz ve formülasyon bilgileri yeni model girdisi olmaz.

## Karakter tahmini yerine gerçek tokenizer'''),
        ('code','''
display(pd.DataFrame([{k:proof[k] for k in ['input_token_count','input_token_limit','output_reserve','safety_reserve','context','admitted','weights_loaded','context_or_decode_created']}]))
labels=['Tam prompt','Çıktı rezervi','Güvenlik','Kullanılmayan']
values=[proof['input_token_count'],384,128,2048-proof['input_token_count']-384-128]
fig,ax=plt.subplots(figsize=(11,3));left=0
for label,value,color in zip(labels,values,['#3b718a','#92b8ab','#e4bc72','#dddddd']):
 ax.barh([0],[value],left=left,label=f'{label}: {value}',color=color)
 ax.text(left+value/2,0,str(value),ha='center',va='center');left+=value
ax.set(xlim=(0,2048),yticks=[],xlabel='Token',title='S01: kaynaklar ve JSON Schema dahil gerçek token bütçesi')
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.3),ncol=2)
plt.tight_layout();plt.savefig(F/'01_actual_prompt_token_budget.png',dpi=160,bbox_inches='tight');plt.show()
display(pd.DataFrame([read(QA/'tokenizer_smoke_alignment_probe.json')]))
'''),
        ('md','''**Yorum:** Kurulu Ollama'nın aynı GGUF sözlüğü ve Jinja şablonu, tensor yüklemeyen `vocab_only` kipinde kullanıldı. 919 token; sınır1536, çıktı384, güvenlik128. Şema, yönerge, soru ve tam alıntılar sayıya dahildir. Geçmiş gerçek echo'nun41 token sayısı bu yolla41; ikinci BOS eklenirse42 olur. Bu hizalama yeni gerçek kaynak yanıtının doğru olacağını kanıtlamaz. Sunucunun yeni yanıttaki `prompt_eval_count` sayısı ayrıca919 ile karşılaştırılacak; fark varsa otomatik düzeltme/tekrar yapılmayacak. Uzun test prompt'u kesilmeden reddedildi. Üretim/context/decode oluşturulmadı.

## Bellek, testler ve bekleyen aşama'''),
        ('code','''
mem=read(QA/'preparation_memory_snapshot.json');checks=read(QA/'preparation_checks.json')
display(pd.DataFrame([mem]));display(pd.DataFrame([checks]).T.rename(columns={0:'doğrulama'}))
fig,axes=plt.subplots(1,2,figsize=(11,4))
axes[0].bar(['Ölçülen RAM','RAM giriş eşiği'],[mem['available_RAM_GiB'],2.5],color=['#b36c6c','#6d8798'])
axes[1].bar(['Ölçülen VRAM','VRAM giriş eşiği'],[3935/1024,2],color=['#7f9f8b','#6d8798'])
axes[0].set(ylabel='GiB',title='Tek hazırlık anı — RAM kapısı geçmiyor')
axes[1].set(ylabel='GiB',title='Tek GPU anlık ölçümü; tepe kullanım değildir')
plt.tight_layout();plt.savefig(F/'02_preparation_memory_snapshot.png',dpi=160);plt.show()
critical=read(QA/'critical_scenario_review_materials_NOT_RUN.json')
display(pd.DataFrame([{'senaryo':k,'inceleme':v['review_focus'],'soru':v['frozen_scenario']['question_tr'],
 'gerçek_kaynak_sayısı':len(v['actual_sources']),'LLM_durumu':v['LLM_status']} for k,v in critical.items()]))
'''),
        ('md','''**Yorum:** 30 testlik tam tur ve mevcut24 sözleşme testi geçti. Son güvenlik düzenlemesinden sonra25 test geçti;5 tokenizer testi ayrı sınıf kapısında o anki RAM nedeniyle atlandı. Önceki başarılı native ölçüm kaydı korunur. İki ilk test beklentisi hatası da ilk logda saklanır; bunlar LLM başarısızlıkları değildir. PS5.1 sözdizimi hatası0, tek üretim çağrı noktası1.

Güncel RAM ölçümü2,5GiB kapısını geçmiyor. Kullanıcının çalışma anında yeniden ölçüm zorunludur; şu anki GPU boşluğu çalışabilirlik garantisi değildir. Bellek yetersizse model yüklenmez. RAM/commit için5 kararlı ölçüm, son RAM/GPU kontrolü,60s timeout ve1GiB çalışma uyarısı korunur.

**Durdurma noktası:** Normal PowerShell'de yalnız S01-R1; her yanıt/ret/hata ham saklanır. JSON Schema geçişi semantik başarı değildir. İnsan gerçek çıktıyı kaynaklarla karşılaştırmadan 19×3 aşaması açılmaz. İlk kayıt aynı model/prompt/ayarlarla kabul edilirse57 yuvanın biri sayılır,56 kalır. Toplu çalıştırıcı bu aşamada verilmez. S04/S06/S07/S17 için gerçek kanıt ve inceleme odağı hazır; LLM sonuçları NOT_RUN. BUN istisnası, sınıf atfı ve bilinmeyen sıklık korunmalıdır.''')])

    command=f'& "{ROOT / cfg["runner"]}" -RunFirstCase'
    report=f'''# WP12 — Kaynaklı tek-vaka pilot hazırlığı v1

08.11.2026 · **S01-R1 kullanıcı çalıştırması bekleniyor. Gerçek açıklama üretilmedi.**

AGENTS.md, aktif ROADMAP WP12 ve `WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md` korundu. Kullanıcı kabul ettiği teknik echo ardından gerçek PDF açıklamasını normal PowerShell'de tek istekle sınayacak. Codex AppContainer'dan Ollama API'ye bağlanılmadı; kısıt aşılmadı. İndirme, yeni eğitim, servis kapatma, güvenlik değişikliği veya WP13 yok.

## 1. Değişmeyen kaynak ve ilk vaka

- Frozen19 listesinin ilk vakası **S01**; seçim sonuç başarısına bağlı değil. Soru: “{sources['scenario']['question_tr']}”
- Kabul ölçütü aynen: “{sources['scenario']['acceptance_criteria_tr']}”
- Erythromycin kullanıcı PDF'sinin fiziksel sayfa1 ve6'sından `E_identity` ve `E_formulation`; iki tam alıntı toplam537 karakter. Ham PDF hash'leri,44 alıntının sayfa/aralık/hash'i ve bağlam bağımlılıkları doğrulandı. Yeni PDF çıkarımı yapılmadı.
- `package/context.json` kaynak metinlerini, `package/request.json` gönderilecek sabit isteği taşır. Tam prompt, kaynak quote-ID/metin/sayfa/scope/kind/qualifier ve v1'in yalnız bu vaka için daraltılmış geçerli JSON Schema alt kümesini içerir. Eski v1 şeması değişmez. Sayfa/aralık/ham SHA çıktıya trusted wrapper ile eklenir.
- Model **{cfg['model']}**; API/source digest **{cfg['API_model_digest']}**. Yerel wrapper `313f48e3…` ayrı dosya SHA'sıdır, API digest ile karıştırılmaz. Önceki teknik identity helper aynen kullanılır. GGUF tensor dosyasının SHA'sı ayrıca kontrol edilir.

## 2. Gerçek token bütçesi ve sınırları

Kurulu Ollama0.40.6 için genel `/api/tokenize` uç noktasına güvenilmedi. Aynı kurulu libllama/ggml DLL hash'leri ve model GGUF `tokenizer.chat_template` sabitlendi. Küçük Python ctypes adaptörü, mevcut native build620d2225c ABI'sinde `vocab_only=True`, GPU layers0 ile **yalnız sözlük** okur; tensor/context/decode/sampler veya model inference oluşturmaz. Paket kurulmadı. GGUF metadatası16MiB üst sınırla okunur; model dosyası bütünlük hash'i1MiB bloklarla alınır, belleğe bütünüyle yüklenmez.

| Alan | Değer |
|---|---:|
| S01 yönerge + JSON Schema + soru + tam alıntı + özgün chat şablonu | **919 token** |
| İzinli giriş |1536|
| Çıktı rezervi |384|
| Güvenlik rezervi |128|
| Toplam context |2048|
|919+384+128 sonrası boşluk|617|

Geçmiş gerçek smoke'un41 `prompt_eval_count` değeri aynı offline yolla41 bulundu; ikinci BOS eklense42 olur. Şablonun kendi dış boşluk temizliği kaynak kesmek değildir; JSON içindeki ham alıntılar değişmez. Bu geçmiş hizalama gelecekteki gerçek istekte token eşitliğini garanti etmez: **yeni yanıttaki sunucu sayısı919 ile ayrıca karşılaştırılır; fark varsa TOKEN_COUNT_ALIGNMENT_FAILED ve insan incelemesi gerekir**. Karakter/token oranı tahmini veya sessiz kesme yok. `truncate=false`, `shift=false`;1536 üzeri tam prompt'ta üretim yapılmaz. Şema ayrıca prompt'ta olduğundan grammar için görünmeyen metin varsayılmaz. Büyük sahte test eki yalnız testte kullanıldı; gerçek kaynak veya frozen vaka değiştirilmedi.

Resmî uygulama dayanakları: [Ollama0.40.6 routes](https://github.com/ollama/ollama/blob/v0.40.6/server/routes.go), [API tipleri](https://github.com/ollama/ollama/blob/v0.40.6/api/types.go), [tokenizer köprüsü](https://github.com/ollama/ollama/blob/v0.40.6/llm/llama_server.go), [kurulu native commit ABI](https://github.com/ggml-org/llama.cpp/blob/620d2225c/include/llama.h). Bu yerel adaptör tam bu hash/sürümle sınırlıdır; runtime değişirse işlem durur, tahmini sayıya dönmez.

## 3. İstek kapıları ve kayıtlar

Onaylı v2 eşikler değişmedi: başlangıç RAM≥2,5GiB, boş GPU≥2GiB, commit alanı≥3GiB; RAM/commit için5 örnek/4 saniye ve gönderim öncesi RAM/GPU yeniden kontrolü. HTTP timeout60s, çalışma RAM uyarısı1GiB. Hazırlık anlık ölçümü RAM **{mem['available_RAM_GiB']:.3f}GiB**: model başlatma kapısı **geçmedi**. GPU3935MiB boştu; bu tepe ölçümü veya çalışma garantisi değildir. Kullanıcı uygulamalarını kendi kararıyla kapatıp komutu çalıştırdığında kapılar tekrar ölçülür. Betik uygulama/servis kapatmaz; eşik düşürmez.

Teknik echo'dan farklı gerçek kaynaklı üretim bütçesi mevcut açıklama sözleşmesiyle2048context/384output/batch32/temperature0/seed20261108/thinkfalse/streamfalse/keep_alive0 olarak kilitlidir. Üretim bir kez `/api/chat`; retry, en iyi tekrar seçimi veya fallback yok. Önce version/tags/ps salt okunur metadata; tam kimlik/helper/source/native/PDF hash ve gerçek tokenizer kapısı; sonra kararlı bellek ve tek üretim. Başka yüklü model varsa otomatik unload yerine durur. AppContainer algılanırsa üretim yok.

Her kullanıcı çalıştırması benzersiz `reports/qa/WP12/source_single_case_user_runs/<zaman_GUID>/` klasörü açar. `run_record.json`, metadata, token bütçesi, tam prompt/request, kaynak bağlamı, ham yanıt, Python stdout/stderr, bellek örnekleri, süre/HTTP/hata ve dosya hash'leri saklanır. Timeout'ta sunucunun durmuş olduğu iddia edilmez; HTTP iptali süreç sonlandırmaz. `inference_attempts` gönderim teşebbüsüdür; yerel istemci kaydı sunucudaki başka istemciler için global ağ kanıtı değildir. Ham HTTP hata gövdesi de korunur; hata veya ret başarıya çevrilmez.

## 4. Yapısal ve semantik değerlendirme ayrı

JSON Schema, tamamlanma/stop, doğru model, token sayısı, seçilmiş quote-ID, kaynak scope/kind, bağlam bağımlılıkları kontrol edilir. Eksik kaynak, fazla skor alanı, yanlış kimlik, eksik çıktı, length stop ve duplicate JSON anahtarları reddedilir. Geçerli aday bile **SOURCE_CANDIDATE_PENDING_HUMAN_REVIEW**, semantic_success=null, automatic_release=false kalır. Ret **MODEL_REFUSAL_RECORDED**; başarı değildir. Yanlış Türkçe cümle doğru quote-ID ile yapısal kapıyı geçebilir; bu sınırlama testte gösterildi. İnsan alıntıyı, ürünü, formülasyonu, belirsizliği ve kaynak dışı iddiayı karşılaştırmadan açıklama kabul edilmez.

`reported_in_PDF` gerçek kaynak cümlesi/sayfasıyla ayrı; `predicted_by_GNN` trusted wrapper'da NOT_REQUESTED/null. Model skoru, SHAP, Δz veya MedDRA üretimi ve otomatik yayın yok. Bu çalışma klinik risk veya nedensellik doğrulaması değildir. `first_case_human_review_template.json` henüz boş/kararsız inceleme formudur; gerçek model çıktısı değildir.

## 5. Gelecek ikinci aşama — bu tur kapalı

`stage2_plan_NOT_EXECUTABLE.json` frozen19×3=57 yuvayı aynen kaydeder; bulk executor verilmedi. S01-R1 yalnız aynı prompt/model/ayar hash'leriyle insan kabulü alırsa ilk yuva olarak sayılabilir; kalan56. İlk yanıt kötü/ret/eksik olursa otomatik devam yok; yeni sonuç seçimi veya sessiz prompt ayarı yok. Bellek/API/source/token kapıları ileride her istekten önce yeniden gerekir. Bütçe reddi veya kaynak eksikliği olan yuva kayıtlı ret/NOT_RUN kalabilir;57 gerçek generation garantisi verilmez.

Özellikle S04 Erythromycin bilinmeyen sıklık/sayfa4–5 bağlamı, S06 tetracycline sınıf listesi, S07 BUN sınıf ifadesi ve doxycycline istisnasının tam bağlamı, S17 kaynak dışı skor/etiket talebi için gerçek kanıtlar `critical_scenario_review_materials_NOT_RUN.json` içindedir. Kaynaklar/kriterler değişmedi; bu vakalar çalıştırılmadı. Uyarı, etkileşim, sınıf ve doğrudan ilaç ifadeleri tek kanıt gibi birleştirilmeyecek.

## 6. QA ve korunma kanıtı

- İlk turda2 test beklentisi hatası vardı: özgün Jinja dış trim'i ve ilk-yuva bekleme durumu. Test beklentileri düzeltildi, ilk başarısız log korundu. Kaynak veya yöntem bu nedenle değişmedi.
- Tam tur **30/30** geçti; gerçek native41/919 sayımı ve aşırı context reddi dahil. Eski saf kaynak sözleşmesi **24/24** geçti.
- Son çalıştırıcı güvenlik düzenlemesinden sonra **25 test geçti;5 native test**, kendi1,5GiB yalnız-sözlük utility guard'ında o anki RAM nedeniyle sınıf olarak atlandı. Bu, gerçek model için2,5GiB kapısını değiştirmez. Başarılı önceki native test/tam sayım kanıtı saklıdır; son atlama gizlenmez.
- Windows PowerShell **{ast['powershell_parser']}** parser:0 hata; AST'de1 PostAsync. Betik çalıştırılmadı. Son hash: `{cfg['runner_sha256']}`. Geliştirme parser logları da korunur; güncel hash `powershell_5_1_release_syntax.json` içindedir.
- Önceki **3503** dosyanın tamamı güncelleme öncesi aynı SHA ile doğrulandı. WP00–11/GNN/SHAP/PPI/model/QA, PDF ve frozen19 korunur. Kapanış manifesti yeni dosyaları kapsar. Sadece güncel run_status yeni bölüm ekler; önceki baytlar `run_status_before.md` ve dosyanın tarihsel devamında korunur.

## 7. Kullanıcı komutu ve durma noktası

Normal kullanıcı PowerShell'inde, RAM kapısının yeniden ölçülmesine izin vererek **yalnız bir kez**:

```powershell
{command}
```

ExecutionPolicy değiştirme veya yönetici çalıştırma talimatı yoktur. Komutun yazdığı `Evidence directory` klasörü ilk gerçek yanıtın bağımsız incelemesi için paylaşılmalıdır. Bu aşamada yalnız S01-R1 hazırlandı; kullanıcı çıktısı bekleniyor.19×3 çalıştırılmadı, WP13 başlatılmadı.

Çıktılar: `notebooks/WP12_source_single_case_preparation.ipynb` çalıştırılmış Türkçe öğretici notebook; `reports/figures/WP12/source_single_case_v1/` gerçek token/bellek PNG'leri; `reports/qa/WP12/source_single_case_v1/` test, kaynak/prompt, plan ve manifest kanıtları; `configs/WP12_SOURCE_SINGLE_CASE_v1.json` sabit politika; modüler Python dosyaları kaynak/token/yanıt doğrulayıcılarıdır.
'''
    new_text(ROOT/'reports/WP12_SOURCE_SINGLE_CASE_PREPARATION.md',report)
    before=(QA/'run_status_before.md').read_bytes()
    assert (ROOT/'run_status.md').read_bytes()==before
    prefix=f'''# WP12 — Kaynaklı S01-R1 tek-vaka betiği hazır; kullanıcı çıktısı bekleniyor ·08.11.2026

- Normal kullanıcı PowerShell'i için scripts/WP12_SourceSingleCase_v1.ps1 -RunFirstCase hazırlandı. Tek gerçek PDF açıklama vakası; bu tur API/inference/indirme/eğitim0.19×3 ve WP13 kapalı.
- Frozen19,44 alıntı ve bütün eski3503 dosyanın SHA'sı doğrulandı. Yeni prompt919 gerçek token;1536 giriş/384 çıktı/128 güvenlik/2048context. Aynı yerel native vocabulary-only tokenizer geçmiş41-token smoke ile hizalandı; tensor/context/decode yüklenmedi. Sunucu sayısı gerçek yanıtta ayrıca kontrol edilecek.
- v2 RAM2,5GiB/GPU2GiB/commit3GiB/timeout60s değişmedi. Hazırlık ölçümü RAM{mem['available_RAM_GiB']:.3f}GiB: kapı geçmedi, model çalıştırılmadı. Kullanıcı betiği çalışma anında tekrar ölçer, koşul yoksa durur.
-30 tam test ve24 mevcut sözleşme testi geçti. Son kontrol25 geçti;5 native test RAM utility guard nedeniyle atlandı. İlk2 test beklentisi hatası ve tüm loglar saklı. PS5.1 parser0hata, tek PostAsync; güncel hash{cfg['runner_sha256']}.
- Yapısal geçiş insan anlam onayı değildir; semantic_success null, otomatik yayınfalse. İlk gerçek yanıt incelenmeden ikinci aşama açılmaz. Rapor reports/WP12_SOURCE_SINGLE_CASE_PREPARATION.md; notebook notebooks/WP12_source_single_case_preparation.ipynb; QA reports/qa/WP12/source_single_case_v1/.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''.encode('utf-8')
    (ROOT/'run_status.md').write_bytes(prefix+before)
    prior=read(QA/'prior_artifacts_sha256.json')
    changed=[p for p,h in prior.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    assert changed==['run_status.md'],changed
    assert sha(QA/'run_status_before.md')==prior['run_status.md']
    assert (ROOT/'run_status.md').read_bytes().endswith(before)
    save_new(QA/'prior_artifacts_preservation.json',{'prior_files':len(prior),
        'unchanged_at_original_path':len(prior)-1,'only_updated_path':'run_status.md',
        'previous_status_archived_exactly':True,'previous_status_retained_as_exact_suffix':True,
        'changed_accepted_source_or_result_files':0,'actual_inference_calls':0})
    print('Executed notebook + Turkish report + new status; first actual user output pending.')


if __name__=='__main__':main()
