"""Create a clean Windows handoff ZIP from an EXE and tracked source files."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', '-c', 'safe.directory=' + ROOT.as_posix(),
                                    '-C', str(ROOT), *args])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verification', type=Path, required=True)
    args = parser.parse_args()
    executable = args.exe.read_bytes()
    if executable[:2] != b'MZ':
        raise SystemExit('Expected a Windows PE executable.')
    verification = json.loads(args.verification.read_text(encoding='utf-8-sig'))
    if verification.get('runtime_passed') is not True or verification.get('tests_passed') is not True:
        raise SystemExit('Runtime and source checks must pass before packaging.')
    files = [p for p in git('ls-files', '-z').decode('utf-8').split('\0') if p]
    # Never copy the workspace wholesale: only reviewed, tracked source is included.
    for name in files:
        path = Path(name)
        if any(part in {'data','logs','outputs','backups','config','.git','.venv','release'} for part in path.parts):
            raise SystemExit('Blocked runtime path: ' + name)
        if path.name == '.env' or path.name.startswith('.env.') and path.name != '.env.example':
            raise SystemExit('Blocked environment file.')
        if path.suffix in {'.db','.sqlite','.sqlite3','.credentials','.exe','.zip','.log','.csv'}:
            raise SystemExit('Blocked artifact: ' + name)
        if path.suffix == '.xlsx' and name != 'templates/template.xlsx':
            raise SystemExit('Blocked spreadsheet: ' + name)
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    bundle = 'AttendSift-AI_Windows_' + version
    manifest = {'application':'ChamCongChatwork / AttendSift-AI', 'version':version,
                'department':'Bộ phận AI', 'author':'Đặng Gia Khánh',
                'platform':'Windows 10/11 x64', 'source_commit':git('rev-parse','HEAD').decode().strip(),
                'exe_sha256':hashlib.sha256(executable).hexdigest(),
                'exe_size_bytes':len(executable), 'verification':verification,
                'python_required_on_target':False, 'credentials_included':False,
                'employee_data_included':False, 'code_signed':False}
    guide = (ROOT / 'docs/CHUYEN_MAY_WINDOWS.md').read_text(encoding='utf-8')
    page = '''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bắt đầu — AttendSift-AI</title><style>body{font:16px/1.7 "Segoe UI",sans-serif;margin:0;background:#07121b;color:#eaf2f8}main{max-width:1040px;margin:auto;padding:48px 24px}h1{font-size:36px;margin:8px 0}h2{color:#b9dfed}p{color:#bed0dc}section{background:#122331;padding:24px;border-radius:18px;margin:20px 0}code{background:#06121c;padding:3px 7px;border-radius:5px}a{color:#b9dfed}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.8 "Segoe UI",sans-serif}.tag{color:#9bc9dd}</style><main>
<div class="tag">Bộ phận AI · Đặng Gia Khánh</div><h1>AttendSift-AI cho Windows</h1><p>Bản portable: giải nén toàn bộ ZIP rồi chạy, không cần cài Python.</p>
<section><h2>1. Mở ứng dụng</h2><ol><li>Giải nén vào Documents hoặc ổ D có quyền ghi.</li><li>Mở <code>BAT_DAU.bat</code> hoặc <code>UngDung/ChamCong.exe</code>.</li><li>Đợi cửa sổ ứng dụng hoặc trình duyệt local mở.</li></ol></section>
<section><h2>2. Kết nối và xuất công</h2><ol><li>Thiết lập → nhập token Chatwork, kiểm tra và chọn nhóm.</li><li>Chọn Google Gemini / OpenAI / Claude, nhập API key và kiểm tra.</li><li>Đồng bộ → Xuất công → chọn tháng → kiểm tra các dòng → xuất Excel 4 sheet vào Downloads.</li></ol><p>Máy mới cần nhập lại API. Gói này không chứa khóa hoặc dữ liệu nhân viên.</p></section>
<section><h2>3. Bạn muốn dùng dữ liệu cloud?</h2><p>Mở <code>MO_BAN_WEB.url</code> hoặc <a href="https://attend-sift-ai.vercel.app">attend-sift-ai.vercel.app</a>. Dùng mật khẩu quản trị website. Dữ liệu Windows và Neon không tự đồng bộ với nhau.</p></section>
<section><h2>4. Các tệp trong gói</h2><ul><li><code>KIEM_TRA.bat</code>: kiểm tra thư viện và mẫu Excel của EXE.</li><li><code>CHAY_CONG_KHAC.bat</code>: mở cổng 8767 nếu cần.</li><li><code>HUONG_DAN_CHUYEN_MAY.md</code>: quy trình chuyển dữ liệu và xử lý sự cố.</li><li><code>THONG_TIN_GOI.json</code>: phiên bản, hash EXE và kết quả kiểm tra.</li><li><code>MaNguon/ChamCongChatwork</code>: toàn bộ mã nguồn được theo dõi bằng Git, dành cho kỹ thuật.</li></ul></section>
<details><summary>Đọc toàn bộ hướng dẫn chuyển máy và vận hành</summary><section><pre>''' + html.escape(guide) + '</pre></section></details></main></html>'
    entries = {'UngDung/ChamCong.exe':executable,
               'DOC_TRUOC_KHI_CHAY.html':page.encode('utf-8'),
               'HUONG_DAN_CHUYEN_MAY.md':guide.encode('utf-8'),
               'THONG_TIN_GOI.json':json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'),
               'MO_BAN_WEB.url':b'[InternetShortcut]\r\nURL=https://attend-sift-ai.vercel.app\r\n',
               'BAT_DAU.bat':b'@echo off\r\ncd /d "%~dp0"\r\nstart "" "%~dp0UngDung\\ChamCong.exe"\r\n',
               'CHAY_CONG_KHAC.bat':b'@echo off\r\ncd /d "%~dp0"\r\nstart "" "%~dp0UngDung\\ChamCong.exe" --port 8767\r\n',
               'KIEM_TRA.bat':b'@echo off\r\ncd /d "%~dp0"\r\n"%~dp0UngDung\\ChamCong.exe" --check-runtime "%~dp0KIEM_TRA_MOI_TRUONG.json"\r\nif errorlevel 1 (echo CHECK FAILED. Read the JSON report.) else (echo CHECK PASSED.)\r\ntype "%~dp0KIEM_TRA_MOI_TRUONG.json"\r\npause\r\n'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name, value in entries.items():
            archive.writestr(bundle + '/' + name, value)
        for name in files:
            archive.write(ROOT / name, bundle + '/MaNguon/ChamCongChatwork/' + name)
    with zipfile.ZipFile(args.output) as archive:
        if archive.testzip() is not None:
            raise SystemExit('ZIP integrity failed.')
        print(f'PASS: {len(archive.namelist())} entries, {args.output.stat().st_size} bytes.')
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix('.zip.sha256').write_text(digest + '  ' + args.output.name + '\n',encoding='ascii')
    print('ZIP SHA256: ' + digest)


if __name__ == '__main__':
    main()
