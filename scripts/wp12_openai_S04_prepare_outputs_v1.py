"""Yalnız offline S04 hazırlık kanıtları; API transport çağırmaz, eski çıktıları ezmez."""
import json
import hashlib
import subprocess
from pathlib import Path
import pandas as pd
import wp12_openai_S04_execution_v1 as budget
import wp12_openai_S04_v1_client as client
from wp12_api_security import public_sha
from wp09_close_wp10_notebooks import execute, INIT

ROOT = budget.ROOT
Q = budget.QA


def save(name, value):
    client.s.old.c.save_new(Q / name, value)


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


def main():
    policy = budget.verify()
    config = json.loads(budget.POLICY.read_text(encoding='utf-8'))
    request = client.s.request('S04')
    frozen = client.s.old.c.read(client.s.QA / 'S04_request_NOT_SENT.json')
    assert request == frozen
    assert not list(budget.CONTROL.iterdir())
    tests = client.s.old.c.read(Q / 'test_summary.json')
    assert tests['returncode'] == 0 and tests['tests'] == 16
    equivalence = {
        'frozen_file_sha256': public_sha(client.s.QA / 'S04_request_NOT_SENT.json'),
        'canonical_request_sha256': canonical_hash(request),
        'canonical_frozen_request_sha256': canonical_hash(frozen),
        'request_object_identical': request == frozen,
        'instructions_UTF8_identical': request['instructions'].encode() == frozen['instructions'].encode(),
        'sources_and_question_identical': request['input'] == frozen['input'],
        'Structured_Outputs_schema_identical': request['text'] == frozen['text'],
        'request_transport_unchanged': True,
        'initial_test_failure': 'File serialization newline comparison failed; parsed payload and UTF-8 prompt were unchanged. Initial log retained.',
        'new_model_method_or_prompt': False,
    }
    save('frozen_request_equivalence.json', equivalence)
    save('execution_authority_change_manifest.json', {
        'version': 'WP12-S04-single-execution-v1',
        'changes_only': ['S04 explicit execution permission', 'separate append-only S04 ledger and output root',
                         'S04-only command and offline tests'],
        'unchanged': ['model', 'frozen question and acceptance criteria', 'source quotes and dependencies',
                      'prompt', 'Structured Outputs schema', 'reasoning and output limit',
                      '30 HTTP / 10 inference / 0.25 USD', '90 second timeout', 'no retry'],
        'previous_S07_outcome_used_to_change_prompt': False,
        'formal_human_decision_written': False,
        'S04_status': 'NOT_RUN', 'new_API_requests': 0,
    })
    _, payload, _, _ = client.s.context('S04')
    rows = [{**x, 'context_count': len(x['required_context_quote_ids']), 'characters': len(x['quote'])}
            for x in payload['sources']]
    pd.DataFrame(rows).to_csv(Q / 'S04_source_dependencies.csv', index=False, encoding='utf-8-sig')
    save('S04_outbound_disclosure_NOT_SENT.json', payload)
    save('S04_status_NOT_RUN.json', {
        'scenario': 'S04', 'execution': 'NOT_RUN', 'HTTP': 'NOT_RUN', 'tokens': None, 'cost_USD': None,
        'technical_validation': 'NOT_RUN', 'agent_source_review': 'NOT_RUN',
        'formal_human_review': 'PENDING', 'automatic_publication': False,
    })
    base = budget.aggregate(policy)
    projected = budget.projected(policy, HTTP=3, inference=1)
    save('budget_before_and_projected.json', {'actual_reservations_before': base,
        'planned_if_three_HTTP_and_one_inference_complete': projected,
        'limits': {'HTTP': 30, 'inference': 10, 'operational_USD': '0.25'},
        'inference_upper_at_6000_input_1200_output_with_margin': client.s.old.estimate_upper(6000, policy),
        'prices_per_million_USD': policy['prices_per_million_USD'],
        'pricing_valid_until_UTC': policy['pricing_valid_until_UTC'],
        'reservation_is_not_actual_cost_or_account_balance': True})
    # Parse only: no wrapper execution or API call.
    ps = ROOT / 'scripts/WP12_OpenAI_S04_SingleCase_v1.ps1'
    command = """$tokens=$null; $parseErrors=$null
$null=[System.Management.Automation.Language.Parser]::ParseFile('%s',[ref]$tokens,[ref]$parseErrors)
@{parser='PowerShell AST';errors=@($parseErrors).Count;executed=$false}|ConvertTo-Json -Compress
""" % str(ps).replace("'", "''")
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                            capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert parsed['errors'] == 0
    save('PowerShell_parse_and_hash.json', {**parsed, 'script_sha256': public_sha(ps),
        'config_sha256': public_sha(budget.POLICY), 'client_sha256': public_sha(ROOT/'scripts/wp12_openai_S04_v1_client.py')})
    # Key is only checked as a boolean; never inventoried, hashed, or serialized.
    save('key_availability_boolean_only.json', {'api_key_available': bool(client.project_key()),
                                              'API_authentication_test': 'NOT_RUN'})
    doc = ROOT / 'docs/plan/WP13_DEMO_SCOPE_v1.md'
    assert doc.exists() and '(ROADMAP_V7.md)' in doc.read_text(encoding='utf-8')
    assert public_sha(ROOT/'docs/plan/ROADMAP_V7.md') == 'c49907813583e6afbb139162ea0d3fc4136fb817947bf11419424d512af5ce6c'
    save('WP13_scope_link_check.json', {'scope_document': str(doc.relative_to(ROOT)),
        'active_roadmap_link_resolves': True, 'roadmap_unchanged': True,
        'implementation': 'NOT_STARTED', 'priority': 'WP12 S04 and scientific pilot review'})
    parts = [
        ('md', '# WP12 — S04 tek istek hazırlığı\n\nBu notebook yalnız gerçek mevcut kaynak ve sayaçları inceler. S04 henüz **NOT_RUN**; token ve yanıt üretmez. S07 öncesi hazırlanmış soru, prompt, üç alıntı, bağlam ve şema aynıdır. Model kalitesine göre yöntem değişikliği yapılmadı.'),
        ('code', INIT + "\nQ=ROOT/'reports/qa/WP12/openai_S04_preparation_v1'\nF=ROOT/'reports/figures/WP12/openai_S04_preparation_v1'\nF.mkdir(parents=True,exist_ok=True)\nread=lambda name: json.loads((Q/name).read_text(encoding='utf-8'))\ndisplay(pd.DataFrame([read('frozen_request_equivalence.json')]).T)"),
        ('md', '**Yorum:** İstek nesnesi, UTF-8 prompt, kaynaklar ve şema eşit. İlk test dosya serileştirme/satır sonu farkını yöntem değişikliği sanmıştı; başarısız ilk kayıt saklandı, içerik ve taşıma biçimini ayrı sınayan test geçti.'),
        ('code', "sources=pd.read_csv(Q/'S04_source_dependencies.csv')\ndisplay(sources[['physical_page','char_start','char_end','characters','kind','qualifier','quote_id','context_count']])\nfor _,r in sources.iterrows():\n    display(pd.DataFrame([{'fiziksel_sayfa':r.physical_page,'quote_ID':r.quote_id,'birebir_kaynak':r.quote,'zorunlu_bağlamlar':r.required_context_quote_ids}]))"),
        ('md', '**Yorum:** Üç alıntı toplam 3803 karakterdir; örtüşen sayfa5/unknown bölümünü kesmedik. Bilinmeyen sıklık alıntısı sayfa5 ve sayfa4 bağlamını taşır. Doğru quote-ID, doğru Türkçe veya doğru anlam kanıtı değildir.'),
        ('code', "b=read('budget_before_and_projected.json')\ntable=pd.DataFrame([{'durum':label,**b[key]} for label,key in [('Gerçek mevcut rezerv','actual_reservations_before'),('S04 tamamlanırsa plan','planned_if_three_HTTP_and_one_inference_complete')]])\ndisplay(table)\nfig,axs=plt.subplots(1,3,figsize=(12,4))\nfor ax,col,cap,title in zip(axs,['HTTP_reservations_total','inference_reservations_total','reserved_USD'],[30,10,.25],['HTTP rezervi','Inference rezervi','Operasyonel rezerv (USD)']):\n    vals=pd.to_numeric(table[col]);ax.bar(['Mevcut','S04 planı'],vals,color=['#447a91','#bc9150']);ax.axhline(cap,color='#963e42',linestyle='--',label='Toplam tavan');ax.set_title(title);ax.set_ylim(0,cap*1.16);ax.legend(fontsize=8)\n    for i,v in enumerate(vals):ax.text(i,v+cap*.025,f'{v:g}',ha='center')\nfig.suptitle('Gerçek sayaçlar ve koşullu plan — API sonucu değildir');plt.tight_layout();plt.savefig(F/'01_actual_reservations_and_conditional_plan.png',dpi=160);plt.show()"),
        ('md', '**Yorum:** Mevcut9HTTP/3inference/.069USD rezervi korunur. ÜçHTTP tamamlanırsa12/4/.092 olur. Bunlar gerçek fatura değildir; 429 dahil eski belirsiz maliyet iade varsayımıyla çıkarılmaz. Her çağrı bütçe/hash kontrolü yapar; inference öncesi exact server token sayımı zorunludur, bağlam kesilmez.'),
        ('code', "display(pd.DataFrame([read('test_summary.json'),read('PowerShell_parse_and_hash.json')]))\nreview=read('human_review_plan_S04.json')\ndisplay(pd.DataFrame({'önceden_dondurulmuş_inceleme_sorusu':review['frozen_plan']['required_review_questions_tr']}))\ndisplay(pd.DataFrame(review['dimensions_kept_separate']))\ndisplay(pd.DataFrame([read('S04_status_NOT_RUN.json')]))"),
        ('md', '**Yorum:** 16 ağsız teknik test PASS, PowerShell yalnız parse edildi. İnceleyici bilinmeyen sıklığı, may/usually/koşulları, tam Türkçeyi ve item atıflarını ayrı değerlendirecek. İnsan kararı ayrı kimlik/rol/tarih/hash kapsamlı olayla yönetilir; burada otomatik onay/reddetme yoktur. S07 kullanıcı değerlendirmesi ayrı beyan olarak korundu; önceki QA değişmedi. WP13 yalnız kapsam belgesidir; uygulama başlamaz.'),
    ]
    execute('WP12_OpenAI_S04_preparation_v1.ipynb', parts)
    report = r'''# WP12 — S04 Erythromycin tek istek hazırlığı v1

S04 **NOT_RUN**. Bu hazırlıkta yeni API isteği, model eğitimi veya yöntem geliştirme yapılmadı. Kullanıcı S07 teknik sonucunu kabul etti; tam Türkçe/atıf kalitesini başarılı saymadı. Beyanı ayrı `S07_user_feedback_NOT_FORMAL_QA.json` kaydındadır; S01/S07 resmî insan QA kararları PENDING olarak korundu.

## Değişmeyen yöntem ve kaynak

S04 soru, kabul ölçütü, prompt ve Structured Outputs şeması S07 sonucu öncesi kaydedilmiş dosyalarla içerik/hash düzeyinde doğrulandı. Yeni sürüm yalnız S04 yürütüm yetkisi, ayrı sayaç/çıktı konumu ve tek komut sağlar. Önceki şema, kaynak alıntısı, prompt veya başarı kriteri değiştirilmedi.

DB00199 Erythromycin PDF fiziksel4–5 kaynakları: üç alıntı, örtüşmeler dahil3803karakter. Unknown alıntısı sayfa5→sayfa4 bağlamını taşır. Tam alıntılar `S04_source_dependencies.csv` ve notebook'ta görünür; API'ye tam PDF veya GNN çıktısı gönderilmez.

GPT-5.4-mini, reasoning=none, max_output_tokens=1200, input cap6000, timeout90s, store=false, tools=[], truncation=disabled; otomatik retry yoktur. Model erişimi ve exact `/responses/input_tokens` kontrolünden sonra yalnız bir inference yapılabilir. Bağlam sığmazsa kesme yerine durur. Kaynak/provider retleri ayrı kaydedilir, başarı sayılmaz.

## Bütçe ve anahtar

Mevcut toplam9HTTP/3inference/.069USD rezervi değişmedi. Üç S04HTTP adımı tamamlanırsa12HTTP/4inference/.092USD rezerv olur; toplam30HTTP/10inference ve.25USD tavan aynı kalır. Önceki429 ve bilinmeyen maliyetler silinmez/iade varsayılmaz. Altı bin input ve1200output üst sınırında uncached maliyet.0099USD, %20payla.01188USD; inference rezervi.02USD'dir. Bu plan gerçek kullanım/fatura/bakiye değildir.

Fiyatlar mevcut dondurulmuş v2 politikada input.75/cached.075/output4.50USD/milyon token olarak korunur ([resmî model belgesi](https://developers.openai.com/api/docs/models/gpt-5.4-mini)). Fiyat geçerlilik tarihi dolarsa yürütücü durur; limitleri kendisi genişletmez. Anahtar yalnız proje.env OPENAI_API_KEY'den alınır; raporda yalnız var/yok, Authorization veya anahtar/hash yoktur. API kimlik doğrulaması bu tur NOT_RUN.

## Doğrulama ve insan incelemesi

16 yeni ağsız test PASS; PowerShell AST sözdizimi hatası0. İlk16 testin birinde dosya serileştirme/satır sonu karşılaştırması başarısızdı. İlk log korundu; istek nesnesi ve prompt içerikleri değişmeden, kontrol serileştirme biçimini içerikten ayıracak şekilde düzeltildi. Test fixture'ları yalnız TEST_ONLY'dir ve model yanıtı diye sunulmaz.

İnceleme boyutları ayrıdır: teknik JSON/ID/bağımlılık; ajan kaynak okuması; tam Türkçe; item düzeyinde atıf; yetkili insan kararı. Bilinmeyen sıklık nadir/yaygın/yüzde veya kesin yokluk yapılamaz. May/usually/high doses/kidney problems gibi mevcut nitelemeler korunmalı; prospektüs uyarısı kişisel tedavi önerisine dönüşmemelidir. S01'e özgü sabit cümle kontrolü genel semantik değerlendirici olarak kullanılmaz. JSON geçişi ve doğruquote-ID tek başına semantik başarı değildir.

Mevcut245 önceki kamusal dosyanın hash'i, frozen19senaryo/44alıntı, PDF'ler, eskiGemmaFAIL/QwenNOT_RUN ve S01/S07 kayıtları doğrulandı. Bu sayım tüm proje dosyalarının yeni taraması değildir; önceki manifestlerden gelen açık allowlist kontrolüdür. Gizli dosyalar envantere/hash'e alınmaz. Gerçek S04 cevabı, token/maliyet ve anlam değerlendirmesi henüz yoktur; NOT_RUN/PENDING korunur.

## Normal kullanıcı PowerShell komutu

```powershell
& "C:\Users\emrey\Downloads\Graph-Tez-V7_SADELESTIRILMIS_CODEX\Graph-Tez-V7\scripts\WP12_OpenAI_S04_SingleCase_v1.ps1" -RunS04
```

Yalnız tek S04 denemesi yetkilidir. Hata/timeout/ret dahil otomatik tekrar yapılmaz. Çıktı `reports/qa/WP12/openai_S04_user_runs_v1/` altında yeni benzersiz klasöre yazılır. Kullanıcı durum satırını ve Evidence_directory yolunu paylaşınca gerçek yanıt ayrıca değerlendirilir. Başka senaryo,19×3 ve otomatik yayın kapalıdır.

## WP13 ile ilişki

`docs/plan/WP13_DEMO_SCOPE_v1.md`, aktif ROADMAP'in mevcutWP13 satırının localhost Streamlit hedefini ayrıntılandırır. ROADMAP baytları ve önceki kabul edilmiş belgeler değiştirilmedi. WP12 S04/küçük pilotun bilimsel değerlendirmesi önceliklidir. WP13 uygulaması, yeni API ve yeni eğitim başlamadı.

Çıktılar: çalıştırılmış `notebooks/WP12_OpenAI_S04_preparation_v1.ipynb`, gerçek sayaç/koşullu plan PNG'si, kaynak bağımlılık CSV'si, yeni yetki/config manifesti,16test logu, PowerShell parse/hash ve ayrı kullanıcı beyanı. Gerçek API sonucu gibi sunulan temsilî veri yoktur.
'''
    report_path = ROOT / 'reports/WP12_OPENAI_S04_PREPARATION_v1.md'
    with report_path.open('x', encoding='utf-8') as f:
        f.write(report)
    prefix = '''# WP12 — S04 tek istek hazır; WP13 yalnız kapsam belgesi ·08.11.2026

- S04 NOT_RUN; yeni API0. S07 öncesi frozen prompt/şema/soru/3alıntı aynı. 16 yeni ağsıztest PASS; ilk serileştirme kontrolü başarısızlık kaydı korundu. PowerShell AST hata0.
- Global9HTTP/3inference/.069USD rezervi aynen; S04 tamamlanırsa12/4/.092 planı. Tavan30HTTP/10inference/.25USD; retry yok. S04 dışında yeni senaryo yetkisi yok.
- S07 kullanıcı tamTürkçe/atıf başarı vermedi; beyan ayrı. S01/S07 resmî insanQA PENDING değişmedi. Teknik geçiş, ajan kaynak okuması ve insan kararı ayrı.
- Önceki245 açık manifest dosyası doğrulandı;19senaryo/44alıntı/PDF/yerelFAIL/QwenNOT_RUN/ilk429/S01/S07 korundu. Gizli dosya hash/envanteri yok.
- Rapor reports/WP12_OPENAI_S04_PREPARATION_v1.md; notebook notebooks/WP12_OpenAI_S04_preparation_v1.ipynb; QA reports/qa/WP12/openai_S04_preparation_v1/. Kullanıcı komutu scripts/WP12_OpenAI_S04_SingleCase_v1.ps1 -RunS04; gerçek çıktı bekleniyor.
- WP13 docs/plan/WP13_DEMO_SCOPE_v1.md PLANNED; aktifROADMAP aynı. Streamlit uygulaması/ekran görüntüsü/API/eğitim NOT_STARTED. Öncelik WP12 S04 ve küçük pilot bilimsel incelemesi.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''
    previous = (Q / 'run_status_before.md').read_bytes()
    assert (ROOT / 'run_status.md').read_bytes() == previous
    (ROOT / 'run_status.md').write_bytes(prefix.encode('utf-8') + previous)
    final = {'protected_prior_public_files': len(config['protected_prior_public_files_sha256']),
             'protected_prior_files_unchanged': True, 'S04_new_control_files': len(list(budget.CONTROL.iterdir())),
             'actual_budget': budget.aggregate(policy), 'S04': 'NOT_RUN', 'new_API_requests': 0,
             'WP13': 'SCOPE_ONLY_IMPLEMENTATION_NOT_STARTED', 'tests': tests,
             'prior_run_status_exact_suffix_preserved': (ROOT/'run_status.md').read_bytes().endswith(previous)}
    budget.verify()
    save('final_verification.json', final)
    # Explicit new public artefacts, never a workspace walk / secret-file hash inventory.
    files = [p for p in Q.iterdir() if p.is_file()]
    files += [budget.POLICY, ps, ROOT/'scripts/wp12_openai_S04_v1_client.py',
              ROOT/'scripts/wp12_openai_S04_execution_v1.py', Path(__file__).resolve(),
              ROOT/'tests/test_wp12_openai_S04_v1.py', report_path, doc, ROOT/'run_status.md',
              ROOT/'notebooks/WP12_OpenAI_S04_preparation_v1.ipynb',
              ROOT/'reports/figures/WP12/openai_S04_preparation_v1/01_actual_reservations_and_conditional_plan.png']
    key = client.project_key()
    assert not key or all(key.encode() not in p.read_bytes() for p in files)
    save('evidence_manifest.json', {str(p.relative_to(ROOT)).replace('\\','/'): public_sha(p) for p in files})
    print(json.dumps(final, ensure_ascii=False))


if __name__ == '__main__':
    main()
