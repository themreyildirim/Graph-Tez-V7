from streamlit.testing.v1 import AppTest
from pathlib import Path
import sys,json
sys.path.insert(0,'scripts')
from wp12_api_security import public_sha
root=Path.cwd();app=AppTest.from_file(str(root/'apps/drug_safety_explorer_v1_1.py'),default_timeout=15).run()
assert len(app.exception)==0
assert len(app.dataframe[0].value)==34
key=app.dataframe[0].key
app.session_state[key]={'selection':{'rows':[1],'columns':[],'cells':[]}}
app.run()
assert any(x.value=='#### Bayılma' for x in app.markdown)
app.selectbox[0].select('Doxycycline · monohydrate kapsül').run()
assert len(app.exception)==0 and len(app.dataframe[0].value)==34
app.radio[0].set_value('EXPERIMENTAL_UPLOAD').run()
assert len(app.exception)==0
print(json.dumps({'status':'PASS','default_rows':34,'row_selection':'PASS','Doxycycline_rows':34,'experimental_no_upload':'PASS','new_API':0}))
