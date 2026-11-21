"""Streamlit AppTest (no browser, model, API or source extraction)."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from streamlit.testing.v1 import AppTest
import wp13_external_reference_v1 as r

def main():
    result=[]
    app=AppTest.from_file(str(ROOT/'apps/drug_safety_explorer_FINAL_v3.py'),default_timeout=30).run()
    assert not app.exception
    app.radio(key='final_v3_area').set_value('Tedizolid dış tahmin deneyi').run()
    assert not app.exception
    result.append({'case':'mode_added_without_breaking_old_view','status':'PASS'})
    for cui,word,quote in [('C0011991','Diyare','SIVEXTRO-v1-p07-498-504'),('C0020517','İlaca aşırı duyarlılık','SIVEXTRO-v1-p06'),('C0040034','trombositopeni','SIVEXTRO-v1-p03'),('C0002792','Çapraz eşleme saptanmadı','')]:
        app.selectbox(key='tedizolid_reference_PT').set_value(cui).run()
        assert not app.exception
        content='\n'.join(str(e.value) for e in app.text)+ '\n'+'\n'.join(str(e.value) for e in app.info)+ '\n'+'\n'.join(str(e.value) for e in app.caption)+'\n'+'\n'.join(str(e.value) for e in app.markdown)
        assert word in content,(cui,word)
        if quote:assert quote in content,(cui,quote)
        else:assert 'Bu PT için kaynak eşleme adayı saptanmadı' in content
        result.append({'case':cui+'_source_alignment','status':'PASS'})
    app.selectbox(key='tedizolid_shap_fold').set_value(5).run()
    assert not app.exception
    assert any('B1 primary model5' in str(e.value) for e in app.markdown)
    result.append({'case':'fifth_model_SHAP_CUI_fold_alignment','status':'PASS'})
    app.radio(key='final_v3_area').set_value('Önceki kayıtlı ilaç demosu').run()
    assert not app.exception
    result.append({'case':'return_to_preserved_previous_demo','status':'PASS'})
    r.dump(r.Q/'Streamlit_AppTest_results.json',{'checks':result,'model_execution':False,'API':False,'source':'actual Streamlit AppTest widget runs'})
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
