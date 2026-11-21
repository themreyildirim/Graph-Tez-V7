"""Düzeltilmiş hesap hazırlığının offline QA/notebook'u; gerçek API çağırmaz."""
import json
import re
import subprocess
import sys
from pathlib import Path
import wp12_openai_corrected_account_v1 as n
from wp12_api_security import public_sha,is_private_path
from wp09_close_wp10_notebooks import execute,INIT


def main():
    base,config=n.verify()
    proc=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','discover','-s','tests',
        '-p','test_wp12_openai_corrected_account_v1.py','-v'],cwd=n.ROOT,capture_output=True,text=True,encoding='utf-8')
    with (n.QA/'offline_tests.log').open('x',encoding='utf-8') as f:f.write(proc.stdout+proc.stderr)
    tests=int(re.search(r'Ran (\d+) tests',proc.stderr).group(1))
    n.original.c.save_new(n.QA/'test_summary.json',{'tests':tests,'returncode':proc.returncode,
        'status':'PASS' if proc.returncode==0 else 'FAIL','real_API_requests':0,'fixtures':'TEST_ONLY; socket disabled'})
    assert proc.returncode==0
    ps=r'''$tokens=$null;$errors=$null
$null=[System.Management.Automation.Language.Parser]::ParseFile((Join-Path (Get-Location) 'scripts/WP12_OpenAI_CorrectedAccount_S01_v1.ps1'),[ref]$tokens,[ref]$errors)
[pscustomobject]@{syntax_error_count=@($errors).Count;version=$PSVersionTable.PSVersion.ToString();executed=$false}|ConvertTo-Json -Compress
'''
    p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],cwd=n.ROOT,capture_output=True,text=True,encoding='utf-8')
    assert p.returncode==0
    parse=json.loads(p.stdout)
    runner=n.ROOT/'scripts/WP12_OpenAI_CorrectedAccount_S01_v1.ps1'
    parse['policy_client_pins_match']=re.findall(r"-cne '([0-9a-f]{64})'",runner.read_text(encoding='utf-8'))==[
        public_sha(n.POLICY),public_sha(n.ROOT/'scripts/wp12_openai_corrected_account_v1.py')]
    parse['script_sha256']=public_sha(runner)
    assert parse['syntax_error_count']==0 and parse['policy_client_pins_match']
    n.original.c.save_new(n.QA/'PowerShell_parse_and_hash.json',parse)
    import pandas as pd
    source=n.original.c.read(n.ROOT/'reports/qa/WP12/gemma_v2_review_qwen_preparation_v1/real_comparison_v1_v2_Qwen_NOT_RUN.json')
    rows=[{'experiment':r['model_method'],'status':r['experiment_status'],
        'detail':r.get('pipeline_terminal_status'),'semantic_result':r.get('actual_language_agent'),'human_review':r.get('human_review')}
        for r in source['rows']]
    rows.extend([
        {'experiment':'OpenAI S01 / first account','status':'API_BILLING_BLOCKED_NO_MODEL_OUTPUT','detail':'HTTP429 credit_balance_exhausted',
            'semantic_result':'NOT_EVALUABLE_NO_OUTPUT','human_review':'PENDING_NO_OUTPUT'},
        {'experiment':'OpenAI S01 / corrected account v1','status':'NOT_RUN','detail':'USER_EXECUTOR_READY',
            'semantic_result':'NOT_RUN','human_review':'PENDING'}])
    n.original.c.save_new(n.QA/'comparison_real_and_NOT_RUN.json',{'rows':rows,'synthetic_tests_are_not_experimental_results':True})
    pd.DataFrame(rows).to_csv(n.QA/'comparison_real_and_NOT_RUN.csv',index=False,encoding='utf-8-sig')
    execute('WP12_OpenAI_corrected_account_S01_preparation.ipynb',[
        ('md','''# WP12 — Kullanıcının hesap düzeltmesi sonrası ayrı S01 denemesi

Bu notebook yalnız çevrimdışı hazırlıktır. Kullanıcı önceki429 hatasını yanlış hesap anahtarına bağladı; bu neden kullanıcı beyanıdır, hesap API'sinden bağımsız doğrulanmadı. Önceki başarısız deneme, ham veriler ve bütün rezervler korunur. Yeni açıklama **NOT_RUN**; test fixture'ları sonuç değildir.'''),
        ('code',INIT+r'''
Q=ROOT/'reports/qa/WP12/openai_corrected_account_preparation_v1'
F=ROOT/'reports/figures/WP12/openai_corrected_account_preparation_v1';F.mkdir(parents=True,exist_ok=True)
ready=json.loads((Q/'readiness_NOT_RUN.json').read_text(encoding='utf-8'))
display(pd.read_csv(Q/'comparison_real_and_NOT_RUN.csv'))
display(pd.DataFrame([{'alan':'Proje .env anahtarı VAR/YOK','sonuç':ready['project_dotenv_key_available']},
 {'alan':'Yeni gerçek API isteği','sonuç':0},{'alan':'Kredili hesabın doğrulanması','sonuç':'PENDING; offline hesap sorgusu yok'}]))
'''),('md','''**Yorum:** Eski Gemma başarısızlıkları, Qwen NOT_RUN ve OpenAI429 kaydı ayrı kalır. Yeni model, prompt veya kaynak geliştirmesi yapılmadı. Aynı S01 tekrarının amacı hesap/kimlik altyapısını düzeltmektir; bağımsız genelleme kanıtı değildir. Yeni yürütücü süreç ortamındaki olası eski key yerine yalnız proje .env alanını okur. Anahtar değeri/uzunluğu/prefix'i/hash'i gösterilmez.

## 1. Aynı dondurulmuş gerçek kaynak'''),('code',r'''
import wp12_openai_adapter as a
sources=a.source_payload()['sources']
with pd.option_context('display.max_colwidth',None):
    display(pd.DataFrame(sources)[['physical_page','kind','quote_id','quote']])
print('Tam iki alıntı:',sum(len(x['quote']) for x in sources),'karakter; model:',a.build_request()['model'])
'''),('md','''**Yorum:** DB00199, fiziksel1/6 ve iki özgün alıntı değişmemiştir. İstenen çıktı Türkçe, yalnız PDF kaynağına dayalıdır. Ürün/tuz/formülasyon eşdeğerliği veya GNN/PT/skor üretme yetkisi yoktur. reported_in_PDF ve predicted_by_GNN ayrımı korunur.

## 2. Eski ve yeni denemenin ortak bütçesi'''),('code',r'''
budget=pd.DataFrame([{'durum':'Eski başarısız hesap / korunmuş rezerv','HTTP':3,'inference_rezerv':1,'USD':.023},
    {'durum':'Yeni3HTTP+1inference olursa toplam / PLAN','HTTP':6,'inference_rezerv':2,'USD':.046}])
display(budget)
fig,ax=plt.subplots(figsize=(10,4.5))
bars=ax.barh(budget.durum,budget.USD,color=['#9f6b5b','#527e9c'])
ax.bar_label(bars,labels=[f'${x:.3f}' for x in budget.USD],padding=4)
ax.axvline(.24,color='#626262',linestyle='--',label='Değişmeyen operasyonel rezerv tavanı $0,24')
ax.set(xlim=(0,.275),xlabel='USD — rezerv/plan; gerçek fatura değildir',title='Eski rezerv sıfırlanmadan tek yeni deneme')
ax.legend(loc='lower right');plt.tight_layout();plt.savefig(F/'01_preserved_and_projected_reservations.png',dpi=160);plt.show()
'''),('md','''**Yorum:** İlk hesabın UNKNOWN gerçek maliyeti sıfır varsayılmaz; tam rezerv taşınır. Aynı pilotun10 toplam HTTP/10 inference ve<$0,25 sınırı her çağrı öncesi bütün ledger'lar üzerinden denetlenir. Yeni deneme tam ilerlerse toplam6 HTTP/2 inference rezervi=$0,046 olur. Yeni key bütçe sıfırlama anlamına gelmez. Eski dört-vaka HTTP planına fazladan üç çağrı eklenmesi kalan kapasiteyi azaltır; diğer senaryolar bu yürütücüde açılmaz.

## 3. Teknik kanıt ve durma noktası'''),('code',r'''
display(pd.DataFrame([json.loads((Q/'test_summary.json').read_text(encoding='utf-8'))]))
display(pd.DataFrame([json.loads((Q/'PowerShell_parse_and_hash.json').read_text(encoding='utf-8'))]))
display(pd.DataFrame([{'kontrol':k,'gerçek_yeni_durum':'NOT_RUN / insan PENDING'} for k in
    ['JSON Schema','Türkçe açıklama','PDF kaynak sadakati','quote-ID/sayfa','token/usage/maliyet','tam model snapshot/request-ID']]))
'''),('md','''**Karar:** Yeni scope proje-geneli tek-attempt atomik kilit taşır; aynı komut ikinci üretim isteği gönderemez. Eski billing-stop ve slotlar değişmeden durur. V1 client/adaptör aynen kullanılır; yalnız credential kaynağı, yeni çıktı scope'u ve tüm-hesap bütçe kapısı eklenir. Normal kullanıcı PowerShell'i gerçek çalışmayı yapar. Kaynaklı çıktı alınırsa şema/uygulama/dil/kaynak sadakati ve gerçek usage ayrı değerlendirilecektir; insan semantik incelemesi olmadan yayın yoktur. Yeni API isteği,19×3, eğitim veya WP13 bu notebook'ta yoktur.

Resmî değişmeyen fiyat/model bilgisi: [OpenAI Docs](https://developers.openai.com/api/docs/models/gpt-5.4-mini).''')])
    report='''# WP12 — Doğru hesap için ayrı S01 yürütücüsü hazır

08.11.2026 — **NOT_RUN / kullanıcı normal PowerShell çıktısı bekleniyor.**

Kullanıcı önceki `credit_balance_exhausted` hatasının yanlış hesaptan oluşturulmuş key nedeniyle olduğunu bildirdi. Bu açıklama yeni ayrı kayıt olarak saklandı; önceki hata/QA/billing-stop/rezervler düzeltilmedi veya silinmedi. Hesap kimliği/bakiyesi bağımsız olarak sorgulanmadı. Proje .env içindeki OPENAI_API_KEY kullanılabilirliği yalnız **VAR** olarak doğrulandı; doğru hesabın kredisi için offline garanti verilmez.

**Aynı kalanlar:** gpt-5.4-mini; aynı V2 kaynak promptu ve API adapter v1 JSON Schema; S01 sorusu/kabul kriteri; DB00199; fiziksel1/6; iki tam537-karakter alıntı; 6000 input/1200 output sınırı, reasoning none;90s timeout; aynı kaynak/hash doğrulamaları; sınırlı dil uyarısı ve zorunlu insan semantik incelemesi. Yeni yöntem veya en iyi çıktı seçimi yoktur. Eski request byte/hash ve semantik bileşenler korunur.

**Açık teknik değişiklik:** Yeni yürütücü yalnız proje .env içindeki OPENAI_API_KEY alanını okur (`environ={}`); süreç ortamında kalmış eski key tercih edilmez. Anahtar değeri, prefix, uzunluk, fingerprint/hash, Authorization header veya gizli dosya hash'i kaydedilmez. Kimlik kaynağı değişikliği ayrı sürümlenmiştir. Eski client/security/adapter ve maliyet konfigürasyonu değiştirilmez.

**Eski blok ve yeni tek-deneme yetkisi:** Kullanıcı hesap düzeltmesi sonrası bir ek denemeyi açıkça yetkilendirdi. V1 billing-stop dosyası ve S01_attempt01 hâlâ salt okunur korunur; V1 yürütücüsü bloklu kalır. Yeni sürüm ayrı corrected-account scope'unda kendi atomik tek-attempt kilidini kullanır. İkinci çalıştırma ağ göndermez. Bu yeni deneme, başarısız v1 kaydının otomatik retry'si veya sıfırlanması değildir; insan tarafından yetkilendirilmiş ayrı altyapı-düzeltme denemesidir.

**Ortak bütçe:** Eski ve yeni ledger'lar her gerçek HTTP öncesi birlikte sayılır. Eski3 HTTP/1 inference rezervi ve$0,023 aynen taşınır. Yeni3 HTTP/1 inference tam giderse toplam6 HTTP/2 inference rezervi ve$0,046 olur. Bu rezerv gerçek ücret değildir; önceki gerçek maliyet UNKNOWN kalır. Aynı10 toplamHTTP/10inference, $0,24 operasyonel tavan ve<$0,25 hedef değişmez. Eski denemeye para iadesi varsayılmaz. İlk dört-vaka planının toplam HTTP kapasitesi artık daha azdır; kalan senaryolara otomatik izin verilmez.

Resmî standart fiyatlar tekrar doğrulandı ve aynı: input$0,75/cached$0,075/output$4,50/milyon. 6000+1200 en kötü token maliyeti$0,0099; %20 payla$0,01188. Eski konfigürasyonun24saat fiyat geçerliliği uzatılmadı; eskirse ağ öncesi durur. [OpenAI Docs model/fiyat](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

**Doğrulama:**18 yeni offline regresyon testi PASS. Eski dosyaların değişmezliği, global iki-scope bütçesi, `.env` tek-kaynak seçimi, AppContainer engeli, bir inference sınırı, ikinci çalıştırma blokajı, timeout/429 gizlemeden saklama, token sınırı ve key yansıtması kontrolleri kapsandı. Fake model yanıtları yalnız TEST_ONLY fixture'dır, gerçek başarı sonucu değildir. PowerShell parser ve policy/client hash pinleri QA'da doğrulanır. Önceki66 kamusal kabul edilmiş artifact/kayıt/control hash'i korunur; gerçek gizli dosyalar bu listeye alınmaz. Önceki35 ve9 test logları değiştirilmez.

**Kullanılacak yeni komut** (.env güncellendikten sonra normal kullanıcı PowerShell'i):

```powershell
& "C:\\Users\\emrey\\Downloads\\Graph-Tez-V7_SADELESTIRILMIS_CODEX\\Graph-Tez-V7\\scripts\\WP12_OpenAI_CorrectedAccount_S01_v1.ps1" -RunS01
```

Yeni çıktı dizini `reports/qa/WP12/openai_corrected_account_user_runs_v1/` olur. Flag olmadan yalnız key VAR/YOK offline durumudur. Codex gerçek API çağırmadı; AppContainer ağ kısıtını aşma yoktur. Kontroller geçerse yalnız bir kaynaklı üretim isteği gönderilir, otomatik tekrar yoktur. Ham yanıt, request-ID/model-ID, HTTP/completion, quote/prompt/hash, schema, kullanım ve maliyet dosyaları aynı v1 güvenlik yazıcısıyla saklanır; ayrıca global bütçe ve gerçek transport-attempt kayıtları eklenir.

Gerçek cevap henüz olmadığı için yeni Türkçe/kaynak sadakati/ücret sonuçları NOT_RUN; önceki GemmaV1/V2 FAIL ve QwenNOT_RUN aynı kalır. JSON geçişi semantik başarı değildir. İlk gerçek çıktı klasörü geldikten sonra kaynak/PDF, Türkçe, ret/kapsam, yapı, token/cache/reasoning ve maliyet ayrı raporlanacak; insan incelemesi PENDING kalacak.19×3, otomatik yayın, yeni eğitim ve WP13 yoktur.
'''
    with (n.ROOT/'reports/WP12_OPENAI_CORRECTED_ACCOUNT_S01_READY.md').open('x',encoding='utf-8') as f:f.write(report)
    before=(n.QA/'run_status_before.md').read_bytes()
    assert (n.ROOT/'run_status.md').read_bytes()==before
    prefix=f'''# WP12 — Kullanıcı düzeltmesi sonrası ayrı hesap S01 hazır ·08.11.2026

- Önceki429 nedenini kullanıcı yanlış hesap key'i olarak bildirdi; eski hamrun/QA/billing-stop/rezervler66kamusal hash ile aynı. Yeni key yalnız proje.env'den; kullanılabilirlik VAR/YOK, değer/hash/header kaydı yok. Hesap kredisi bağımsız doğrulanmadı.
- Model/prompt/şema/DB00199/537karakter/1-6sayfa/6000-1200token/timeout/fiyat aynı. Yeni scope tek-attempt; eski+yeni ledger birlikte≤10HTTP/10inference,<.25USD. Eski.023rezerv taşınır; yeni3çağrıtamamlanırsa toplam.046rezerv. Gerçek ücret bilinmiyorsaUNKNOWN; eski kilitler sıfırlanmaz.
-{tests} yeni offline test PASS; PS parser/hash QA. Gerçek yeni API/inference0. scripts/WP12_OpenAI_CorrectedAccount_S01_v1.ps1 -RunS01 normal kullanıcıPowerShell'de bir deneme; çıktı openai_corrected_account_user_runs_v1 altında. Kullanıcı yeni denemeyi bu mesajıyla yetkilendirdi; tekrar onay istenmez. Eski komut kullanılmaz.
- Rapor reports/WP12_OPENAI_CORRECTED_ACCOUNT_S01_READY.md; notebook notebooks/WP12_OpenAI_corrected_account_S01_preparation.ipynb; QA reports/qa/WP12/openai_corrected_account_preparation_v1/. Yeni denemeNOT_RUN; eskiGemmaFAIL/QwenNOT_RUNaynı. İnsan semantikPENDING;19×3/yayın/eğitim/WP13 yok.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''
    (n.ROOT/'run_status.md').write_bytes(prefix.encode('utf-8')+before)
    n.verify_public_inputs(config)
    assert not list(n.CONTROL.glob('*.json'))
    files=[n.ROOT/p for p in ['scripts/wp12_openai_corrected_account_v1.py','scripts/wp12_openai_corrected_account_evidence.py',
        'scripts/WP12_OpenAI_CorrectedAccount_S01_v1.ps1','tests/test_wp12_openai_corrected_account_v1.py',
        'configs/WP12_OPENAI_CORRECTED_ACCOUNT_S01_v1.json','reports/WP12_OPENAI_CORRECTED_ACCOUNT_S01_READY.md',
        'notebooks/WP12_OpenAI_corrected_account_S01_preparation.ipynb',
        'reports/figures/WP12/openai_corrected_account_preparation_v1/01_preserved_and_projected_reservations.png','run_status.md']]
    files.extend(p for p in n.QA.iterdir() if not is_private_path(p) and p.is_file())
    key=n.project_key();available=bool(key);leaked=available and any(key.encode('utf-8') in p.read_bytes() for p in files)
    assert not leaked
    n.original.c.save_new(n.QA/'final_verification.json',{'tests_passed':tests,'PowerShell_syntax_errors':parse['syntax_error_count'],
        'prior_public_files_unchanged':len(config['protected_prior_public_files_sha256']),
        'api_key_available':bool(key),'secret_value_found':leaked,'secret_files_inventoried_or_hashed':False,
        'new_API_requests':0,'new_inference_requests':0,'status':'READY_USER_SINGLE_S01_EXECUTION',
        'original_status_bytes_retained':(n.ROOT/'run_status.md').read_bytes().endswith(before)})
    del key
    files.append(n.QA/'final_verification.json')
    manifest={p.relative_to(n.ROOT).as_posix():public_sha(p) for p in files}
    n.original.c.save_new(n.QA/'evidence_manifest.json',manifest)
    print(json.dumps({'status':'READY_USER_SINGLE_S01_EXECUTION','tests':tests,'protected_files':len(config['protected_prior_public_files_sha256']),
        'api_key_available':available,'new_API_requests':0}))


if __name__=='__main__':main()
