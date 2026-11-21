"""Bu yeni hazırlığın son kamusal dosya/secret denetimi; inference yoktur."""
import json
from pathlib import Path
import nbformat
import wp12_openai_adapter as a
import wp12_openai_client as client
from wp12_api_security import public_sha,is_private_path,load_key


def main():
    root=a.c.ROOT;qa=a.QA
    old=a.c.read(qa/'previous_public_files_sha256.json')
    expected={'.gitignore','run_status.md'}
    # Eski durumun tam baytları yeni başlığın ardından korunur.
    saved=(qa/'run_status_before.md').read_bytes()
    assert public_sha(qa/'run_status_before.md')==old['run_status.md']
    assert public_sha(qa/'gitignore_before.txt')==old['.gitignore']
    assert (root/'.gitignore').read_bytes().startswith((qa/'gitignore_before.txt').read_bytes())
    header='''# WP12 — Ayrı OpenAI API pilotu çevrimdışı hazır; ilk istek onay bekliyor ·08.11.2026

- gpt-5.4-mini Responses/Structured Outputs kamu belgesi doğrulandı; hesap erişimi ve API adapter çalışma kabulü PENDING. Kimlik doğrulamalı API/inference0; anahtar kullanılabilirliği yalnız VAR/YOK, değer/prefix/hash yok.
- Aynı dondurulmuş S01, DB00199, fiziksel1/6, iki tam alıntı537 karakter. Kaynak metni/19senaryo/44alıntı ve önceki sonuçlar korunur. GemmaV1/V2 FAIL, Qwen NOT_RUN; OpenAI NOT_RUN. reported_in_PDF ile predicted_by_GNN ayrı, insanPENDING.
- 35offline test PASS, ağ soketi testte kapalı; PS5.1 parse0hata ve policy/client pinleri eşit. Env/dotenv güvenliği, özel dosya hash dışlama, geçici Git ignore denetimi, kalıcı tek-attempt ve10çağrı, token/cache/usage/timeout/AppContainer testleri geçti. Gerçek gizli dosya manifestlenmedi.
- maxinput6000/exact server count; output1200(reasoning dahil), effortnone. Resmî standart .75/.075/4.50USD/milyon. Tek inference üst token maliyeti.0099USD; %20payla.01188; sabit inference .02+HTTP.001 rezerv;10+10üstrezerv.21<.24<.25USD. Fiyat kaydı24saat eskirse durur; bakiye kullanıcı beyanı. Retry/Batch/araç/model değiştirme yok.
- Rapor reports/WP12_OPENAI_API_PREPARATION.md; sözleşme docs/plan/WP12_OPENAI_API_ADAPTER_v1.md; notebook notebooks/WP12_OpenAI_API_offline_preparation.ipynb (4çalışmış hücre); QA reports/qa/WP12/openai_api_pilot_v1/. Normal kullanıcı PowerShell komutu raporda; -RunFirstCase yalnız kullanıcı ilk gerçek isteği onayladıktan sonra. Önce S01 sonucu incelenir; başka vaka/19×3/eğitim/yayın/WP13 yok.
- Önceki3709 kamusal dosya denetlendi; yalnız istenen .gitignore ek kuralları ve bu tarihçe başlığı değişti. Eski status ve ignore baytları ayrı arşivde. Detaylı QA public_preservation.json ve evidence_manifest.json içindedir; gizli dosya/anahtar hash'i yok.

---
Önceki run_status (tam baytları korunmuş tarihsel kayıt):

'''
    (root/'run_status.md').write_bytes(header.encode('utf-8')+saved)
    def save_current(name,data):
        assert name in {'public_preservation.json','final_verification.json','evidence_manifest.json'}
        (qa/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    changed=[];missing=[]
    for relative,digest in old.items():
        if is_private_path(relative):raise RuntimeError('PRIVATE_PATH_IN_PUBLIC_BASELINE')
        path=root/relative
        if not path.is_file():missing.append(relative)
        elif public_sha(path)!=digest:changed.append(relative)
    assert not missing and set(changed)==expected
    assert (root/'run_status.md').read_bytes().endswith(saved)
    save_current('public_preservation.json',{'baseline_public_files':len(old),
        'unchanged_public_files':len(old)-len(changed),'missing_public_files':missing,
        'expected_changes_only':changed,'old_status_exact_bytes_retained':True,
        'old_gitignore_exact_prefix_retained':True,'secret_files_not_inventoried_or_hashed':True})

    client.verify_policy() # ağsız: sürüm/fiyat/hash kapısı.
    notebook=nbformat.read(root/'notebooks/WP12_OpenAI_API_offline_preparation.ipynb',as_version=4)
    cells=[x for x in notebook.cells if x.cell_type=='code']
    assert len(cells)==4 and all(x.execution_count for x in cells)
    assert all(y.output_type!='error' for x in cells for y in x.outputs)
    assert not list(client.CONTROL.glob('*.json'))
    # Listeye almadan önce private filtresi: gerçek .env dosyasının adı/içeriği/hash'i kanıt olmaz.
    def current_artifacts():
        # Explicit görev allowlist'i; eski bağımlılık/cache/legacy dizinleri yeni çıktı değildir.
        files=[root/p for p in ['scripts/wp12_api_security.py','scripts/wp12_openai_adapter.py',
            'scripts/wp12_openai_client.py','scripts/wp12_openai_prepare.py','scripts/wp12_openai_offline_evidence.py',
            'scripts/wp12_openai_close_preparation.py','scripts/WP12_OpenAI_UserSingleCase_v1.ps1',
            'tests/test_wp12_openai_pilot.py','configs/WP12_OPENAI_API_PILOT_v1.json',
            'docs/plan/WP12_OPENAI_API_ADAPTER_v1.md','reports/WP12_OPENAI_API_PREPARATION.md',
            'notebooks/WP12_OpenAI_API_offline_preparation.ipynb',
            'reports/figures/WP12/openai_api_pilot_v1/01_cost_reservation_plan.png']]
        files.extend(p for p in qa.iterdir() if not is_private_path(p) and p.is_file()
            and p.name not in {'evidence_manifest.json','evidence_manifest.sha256'})
        assert all(not is_private_path(p) and p.relative_to(root).as_posix() not in old for p in files)
        return files
    new=current_artifacts()
    # Anahtar yalnız RAM'de karşılaştırılır; kendisi/uzunluğu/prefix'i/hash'i çıktı değildir.
    key=load_key(root)
    secret_found=False
    if key:
        secret_found=any(key.encode('utf-8') in path.read_bytes() for path in [*new,root/'.gitignore',root/'run_status.md'])
    assert not secret_found
    save_current('final_verification.json',{'status':'OFFLINE_PREPARATION_PASS_WAIT_USER_APPROVAL',
        'offline_tests':35,'PowerShell_syntax_errors':0,'executed_notebook_code_cells':len(cells),
        'new_public_artifact_secret_value_found':secret_found,'api_key_available':bool(key),
        'no_secret_files_in_hash_inventory':True,'authenticated_API_requests':0,'inference_requests':0,
        'account_model_access':'PENDING','server_schema_acceptance':'PENDING','human_review':'PENDING',
        'prior_experiments_unchanged':True,'WP13':False})
    del key
    artifacts=[root/'.gitignore',root/'run_status.md',*current_artifacts()]
    rows={p.relative_to(root).as_posix():public_sha(p) for p in sorted(set(artifacts))}
    save_current('evidence_manifest.json',{'version':'WP12-OpenAI-offline-preparation-v1',
        'hash_algorithm':'SHA-256','public_files':rows,'secret_files_or_hashes_included':False})
    (qa/'evidence_manifest.sha256').write_text(public_sha(qa/'evidence_manifest.json')+'\n',encoding='utf-8')
    print(json.dumps({'public_baseline':len(old),'unchanged':len(old)-2,'expected_root_changes':2,
        'public_manifest_files':len(rows),'secret_value_found':False,'authenticated_API_calls':0},ensure_ascii=False))


if __name__=='__main__':main()
