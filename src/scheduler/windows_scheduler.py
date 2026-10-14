"""Verified daily tasks using XML, independent of Windows display language."""
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from .timing import next_run

TASK_NAME='ChamCongChatwork_New_Sync'
NS='http://schemas.microsoft.com/windows/2004/02/mit/task'


class WindowsScheduler:
    def __init__(self,app_path,task_name=TASK_NAME):
        self.app_path=str(Path(app_path).resolve())
        self.exe_path=str(Path(sys.executable).resolve())
        self.script_path=str(Path(self.app_path)/'main.py')
        self.arguments='--sync' if getattr(sys, 'frozen', False) else subprocess.list2cmdline([self.script_path, '--sync'])
        self.task_name=task_name

    def _run_schtasks(self,args):
        try:
            result=subprocess.run(['schtasks']+args,capture_output=True,timeout=30,
                                  creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            def decode(raw):
                if isinstance(raw,str):return raw
                return raw.decode('utf-16' if b'\x00' in raw[:60] else 'utf-8',errors='replace').lstrip('\ufeff')
            return result.returncode==0,decode(result.stdout),decode(result.stderr)
        except (OSError,subprocess.TimeoutExpired):
            return False,'','Không truy cập được Windows Task Scheduler.'

    def _xml(self,hour,minute):
        ET.register_namespace('',NS)
        root=ET.Element('{'+NS+'}Task',version='1.2')
        def child(parent,name,text=None):
            node=ET.SubElement(parent,'{'+NS+'}'+name)
            if text is not None:node.text=str(text)
            return node
        triggers=child(root,'Triggers')
        trigger=child(triggers,'CalendarTrigger')
        child(trigger,'StartBoundary',next_run(hour,minute).isoformat())
        child(trigger,'Enabled','true')
        child(child(trigger,'ScheduleByDay'),'DaysInterval',1)
        principal=child(child(root,'Principals'),'Principal');principal.set('id','User')
        user=os.environ.get('USERNAME',getpass.getuser())
        domain=os.environ.get('USERDOMAIN')
        user_id=(domain+'\\' if domain else '')+user
        child(principal,'UserId',user_id)
        login=child(triggers,'LogonTrigger')
        child(login,'Enabled','true')
        child(login,'UserId',user_id)
        child(login,'Delay','PT30S')
        child(principal,'LogonType','InteractiveToken');child(principal,'RunLevel','LeastPrivilege')
        settings=child(root,'Settings')
        for name,value in [('MultipleInstancesPolicy','IgnoreNew'),('DisallowStartIfOnBatteries','false'),
                           ('StopIfGoingOnBatteries','false'),('StartWhenAvailable','true'),
                           ('RunOnlyIfNetworkAvailable','false'),('Enabled','true'),('ExecutionTimeLimit','PT15M')]:
            child(settings,name,value)
        restart=child(settings,'RestartOnFailure')
        child(restart,'Interval','PT10M')
        child(restart,'Count',144)
        actions=child(root,'Actions');actions.set('Context','User')
        execute=child(actions,'Exec')
        child(execute,'Command',self.exe_path);child(execute,'Arguments',self.arguments)
        child(execute,'WorkingDirectory',self.app_path)
        return ET.tostring(root,encoding='unicode')

    def _register(self,xml):
        with tempfile.NamedTemporaryFile(suffix='.xml',delete=False) as file:
            path=file.name;file.write(xml.encode('utf-16'))
        try:return self._run_schtasks(['/Create','/TN',self.task_name,'/XML',path,'/F'])
        finally:Path(path).unlink(missing_ok=True)

    def get_task_status(self):
        try:
            # schtasks /XML under CREATE_NO_WINDOW uses the ANSI codepage and
            # irreversibly replaces Vietnamese characters. COM keeps Unicode.
            escaped=self.task_name.replace("'","''")
            script="[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); $s=New-Object -ComObject Schedule.Service; $s.Connect(); $t=$s.GetFolder('\\').GetTask('"+escaped+"'); @{xml=$t.Xml;next_run=$t.NextRunTime.ToString('o');status=$t.State;last_result=$t.LastTaskResult}|ConvertTo-Json -Compress"
            result=subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',script],capture_output=True,timeout=15,
                                  creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode!=0:return None
            payload=json.loads(result.stdout.decode('utf-8-sig'))
            xml=payload.pop('xml')
            root=ET.fromstring(xml)
            text=lambda name:root.findtext('.//{'+NS+'}'+name)
            boundary=__import__('datetime').datetime.fromisoformat(text('StartBoundary'))
            command=text('Command') or ''
            info={'exists':True,'task_name':self.task_name,'hour':boundary.hour,'minute':boundary.minute,
                  'start_boundary':boundary.isoformat(),'command':command,'arguments':text('Arguments'),
                  'daily':text('DaysInterval')=='1','start_when_available':text('StartWhenAvailable')=='true',
                  'path_changed':os.path.normcase(os.path.abspath(command))!=os.path.normcase(self.exe_path) or text('Arguments') != self.arguments or os.path.normcase(os.path.abspath(text('WorkingDirectory') or '')) != os.path.normcase(self.app_path),
                  'next_run':None,'xml':xml}
            login=root.find('.//{'+NS+'}LogonTrigger')
            restart=root.find('.//{'+NS+'}RestartOnFailure')
            info['logon_catchup']=bool(login is not None and login.findtext('{'+NS+'}Enabled')=='true')
            info['retry_interval']=restart.findtext('{'+NS+'}Interval') if restart is not None else None
            info['retry_count']=int(restart.findtext('{'+NS+'}Count') or 0) if restart is not None else 0
            info['automatic_recovery']=info['logon_catchup'] and info['retry_interval']=='PT10M' and info['retry_count']==144
            info.update(payload)
            return info
        except (ValueError,TypeError,ET.ParseError,OSError,subprocess.TimeoutExpired):
            return None

    def update_schedule(self,hour,minute):
        xml=self._xml(hour,minute)
        old=self.get_task_status()
        if not Path(self.exe_path).is_file() or (not getattr(sys, 'frozen', False) and not Path(self.script_path).is_file()):
            return {'success':False,'task_name':self.task_name,'applied':self.public_status(old),
                    'message':'Chưa tìm thấy ChamCong.exe tại thư mục hiện tại. Hãy dùng gói portable hoặc build EXE trước khi lưu lịch.'}
        ok,output,error=self._register(xml)
        actual=self.get_task_status() if ok else old
        verified=bool(ok and actual and actual['hour']==hour and actual['minute']==minute and actual['daily']
                      and actual['start_when_available'] and actual.get('automatic_recovery')
                      and actual['arguments']==self.arguments and not actual['path_changed'])
        if not verified and ok:
            if old:self._register(old['xml'])
            else:self.delete_task()
            actual=self.get_task_status()
        return {'success':verified,'task_name':self.task_name,'applied':self.public_status(actual),
                'message':'Đã áp dụng và xác minh lịch Windows.' if verified else 'Chưa áp dụng lịch. Kiểm tra quyền tài khoản và Windows Task Scheduler.'}

    create_task=update_schedule

    @staticmethod
    def public_status(status):
        return {k:v for k,v in status.items() if k!='xml'} if status else None

    def delete_task(self):
        return self._run_schtasks(['/Delete','/TN',self.task_name,'/F'])[0]

    def detect_path_change(self):
        status=self.get_task_status()
        return status['command'] if status and status['path_changed'] else None
