#!/usr/bin/python3
# PANTA: guest-only restart and modal tests, with application readback.
import importlib.util,pathlib,json
s=importlib.util.spec_from_file_location('d',pathlib.Path(__file__).with_name('drive-test.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
before=d.state()
for number in range(3):
 result=d.mcp([['list_windows',{}],['type_text',{'window_id':4194308,'text':'r'}]])
 assert result[-1]['ok'],result[-1]
 after=d.state();assert (before['pointer_id'],before['keyboard_id'],before['primary_focus'])==(after['pointer_id'],after['keyboard_id'],after['primary_focus'])
assert d.browser()['input']=='agentrrr',d.browser()
d.human_type('restart');d.checkpoint('three-mcp-restarts')
print(json.dumps(d.mcp([['click',{'window_id':4194308,'x':130,'y':350}]])))
assert d.browser()['modal'],d.browser()
d.checkpoint('chrome-modal-open')
d.qmp('screendump',{'filename':str(d.base/'modal.ppm')})
