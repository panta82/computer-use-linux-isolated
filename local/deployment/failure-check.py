#!/usr/bin/python3
# PANTA: verify loss of input backend/display cannot reach the human session.
import importlib.util, json, pathlib, subprocess, time
spec=importlib.util.spec_from_file_location('check',pathlib.Path(__file__).with_name('mcp-check.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
b=c.base
r=subprocess.run([str(b/'bin/computer-use-linux'),'mcp'],capture_output=True,text=True)
assert r.returncode!=0 and ('SESSION_DIR' in r.stderr or 'environment variable' in r.stderr),r.stderr
print('PASS: direct launch with host environment rejected')
fake=b/'missing-backend';fake.mkdir(exist_ok=True)
marker=fake/'unsafe-backend-called';marker.unlink(missing_ok=True)
f=fake/'ydotool';f.write_text('#!/bin/sh\ntouch "'+str(marker)+'"\nexit 0\n');f.chmod(0o755)
m=c.MCP([str(pathlib.Path.home()/'.local/bin/computer-use-linux-desktop'),'run','/usr/bin/env','PATH='+str(fake),str(b/'bin/computer-use-linux'),'mcp'])
try:
    for name,args in [('click',{'x':100,'y':100}),('type_text',{'text':'MUST NOT REACH HOST'}),('press_key',{'key':'a'}),('scroll',{'x':100,'y':100,'direction':'down'}),('drag',{'start_x':100,'start_y':100,'end_x':200,'end_y':200})]:
        result=m.tool(name,args);assert result['ok'] is False,(name,result)
        print('PASS: missing xdotool fails closed:',name,result['message'])
    assert not marker.exists()
finally:m.close()
m=c.MCP()
try:
    m.tool('doctor')
    subprocess.run(['systemctl','--user','stop','computer-use-linux-desktop.service'],check=True)
    for name,args in [('click',{'x':100,'y':100}),('type_text',{'text':'MUST NOT REACH HOST'})]:
        result=m.tool(name,args);assert result['ok'] is False,(name,result)
        print('PASS: stopped display fails closed:',name)
finally:m.close()
# New MCP launch must start the stopped service and recover its own display.
m=c.MCP()
try:
    doctor=m.tool('doctor');assert doctor['platform']['display']==':199'
    assert doctor['readiness']['can_send_development_input']
    assert doctor['readiness']['can_build_accessibility_tree']
    print('PASS: new MCP process starts stopped service and restores isolated readiness')
finally:m.close()
