#!/usr/bin/python3
# PANTA: guest-only modal and native popup checks.
import importlib.util,pathlib,json
s=importlib.util.spec_from_file_location('d',pathlib.Path(__file__).with_name('drive-test.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
print(json.dumps(d.mcp([['type_text',{'window_id':4194308,'text':'modalagent'}]])))
d.human_type('modalhuman');r=d.checkpoint('html-modal-input');assert r['chrome']['modalInput']=='modalagent';assert 'physicalmorerestartmodalhuman' in r['gtk']
print(json.dumps(d.mcp([['click',{'window_id':4194308,'x':556,'y':382}],['click',{'window_id':4194308,'x':292,'y':350}]])))
d.human_type('popup');d.checkpoint('native-select-popup');d.qmp('screendump',{'filename':str(d.base/'popup.ppm')})
