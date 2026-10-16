"""Create the fixed attendance workbook from the application's clean resource."""
from collections import Counter
from math import ceil
from copy import copy
from datetime import datetime
from pathlib import Path
import openpyxl
import re
from ..services.event_policy import is_annual_leave_text_only, is_ctv_text_only, reason_from_source
from ..services.paid_break_policy import is_paid_break_event
from .message_cleaning import deduplicate_copied_sender_header
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError
from openpyxl.formula.translate import Translator
from openpyxl.styles import PatternFill, Border, Side

SHEETS = ['1_TIN_NHAN_GOC','2_CHAM_CONG','3_TONG_KET','4_CAN_KIEM_TRA']
WIDTHS = [8,26,13,7]


def needs_excel_review(event):
    """Unverified facts remain inspectable, but never influence payroll totals.

    The snapshot/source sheet is always preserved. A confirmed row with newly
    detected validation problems is still held back until checked again.
    """
    if event.get('is_excluded') or event.get('source_only'):
        return False
    # Fatal validation problems cannot be overridden by an earlier confirmation.
    if event.get('validation_errors'):
        return True
    # A manual confirmation clears non-fatal review flags; it does not excuse
    # unknown personnel classification or broken source validation.
    if event.get('review_state') == 'confirmed' and event.get('classification') != 'unresolved':
        return False
    return bool(event.get('review_state') == 'pending' or
                event.get('validation_warnings') or event.get('needs_review') or
                event.get('identity_uncertain') or event.get('classification') == 'unresolved')


def builtin_workbook_path():
    from ..app.paths import RESOURCE_PATH
    return Path(RESOURCE_PATH) / 'templates' / 'template.xlsx'


def verify_workbook(path):
    try:
        workbook = openpyxl.load_workbook(path, data_only=False)
        try:
            if workbook.sheetnames not in (SHEETS, SHEETS + ['5_CTV']):
                raise ValueError('Mẫu Excel phải có đúng bốn sheet chuẩn.')
            for sheet, width in zip(workbook, WIDTHS):
                if not sheet.cell(4,1).value or not sheet.cell(4,width).value:
                    raise ValueError('Tiêu đề mẫu Excel phải ở dòng 4.')
            if workbook[SHEETS[1]]['A4'].value != 'Event ID' or workbook[SHEETS[1]]['W4'].value != 'Giờ OT tính lương':
                raise ValueError('Mapping cột Excel không hợp lệ.')
            return True
        finally:
            workbook.close()
    except (OSError,KeyError,BadZipFile,ParseError,openpyxl.utils.exceptions.InvalidFileException) as error:
        raise ValueError('Không đọc được mẫu Excel hợp lệ.') from error


def safe_cell(cell,value):
    if isinstance(value,str) and len(value)>32767:
        raise ValueError('Nội dung vượt giới hạn một ô Excel; không được cắt mất dữ liệu.')
    cell.value=value
    # Source strings must never become spreadsheet formulas.
    if isinstance(value,str):cell.data_type='s'


def export_to_excel(results,session_info,output_path,template_path=None):
    if template_path is None:
        template_path=builtin_workbook_path()
    verify_workbook(template_path)
    wb=openpyxl.load_workbook(template_path)
    prototypes={}
    for sheet in wb:
        prototypes[sheet.title]=[copy(sheet.cell(5,col)) for col in range(1,sheet.max_column+1)]
        for row in sheet.iter_rows(min_row=5):
            for cell in row:cell.value=None
    # Use explicit cell fills as well as table stripes: Excel may remove a
    # table style while repairing a workbook, and rows may exceed template refs.
    stripe_blue = PatternFill(fill_type='solid', fgColor='CDEEF8')
    stripe_white = PatternFill(fill_type='solid', fgColor='FFFFFF')
    row_rule = Border(bottom=Side(style='thin', color='BCD8E3'))

    def put(sheet_name,row,values,formulas=None):
        sheet=wb[sheet_name]
        for col,value in enumerate(values,1):
            cell=sheet.cell(row,col)
            prototype=prototypes[sheet_name][col-1]
            cell._style=copy(prototype._style)
            cell.alignment=copy(prototype.alignment)
            cell.number_format=prototype.number_format
            # Every alternate data row is blue, separated by a fine rule.
            # Do not depend on template tables to do this formatting.
            cell.fill = stripe_blue if (row-5) % 2 == 0 else stripe_white
            cell.border = row_rule
            if (sheet_name == SHEETS[0] and col == 5 or
                sheet_name == SHEETS[1] and col == 26 or
                sheet_name == SHEETS[3] and col == 7):
                alignment = copy(cell.alignment)
                alignment.wrap_text = True
                alignment.vertical = 'top'
                cell.alignment = alignment
            safe_cell(cell,value)
        for col,formula in (formulas or {}).items():sheet.cell(row,col).value=formula
        # Source text can contain many lines.  Allocate enough visible height
        # for ordinary notes; unusually long messages still keep all cell text.
        if sheet_name == SHEETS[0]:
            content = str(values[4] or '')
            wrapped_lines = sum(max(1, ceil(len(line) / 72)) for line in content.split('\n'))
            sheet.row_dimensions[row].height = min(165, max(32, 16 * wrapped_lines + 12))
        elif sheet_name == SHEETS[1]:
            sheet.row_dimensions[row].height = 42
        elif sheet_name == SHEETS[3]:
            # Review issues and evidence must remain readable in the workbook.
            details = '\n'.join(str(x or '') for x in (values[4], values[6]))
            lines = sum(max(1, ceil(len(line) / 76)) for line in details.split('\n'))
            sheet.row_dimensions[row].height = min(165, max(48, lines * 15 + 10))
        else:
            sheet.row_dimensions[row].height = 31
    month,year=session_info['month'],session_info['year']
    wb[SHEETS[0]]['F4'] = f'Có sự kiện T{month}/{year}?'
    prefix='BẢN TẠM — ' if session_info.get('is_draft') else ''
    wb[SHEETS[1]]['A1']=f'{prefix}CHI TIẾT CHẤM CÔNG – THÁNG {month:02d}/{year}'
    wb[SHEETS[2]]['A1']=f'{prefix}TỔNG KẾT CHẤM CÔNG – THÁNG {month:02d}/{year}'
    if session_info.get('is_draft'):
        for sheet in wb:
            sheet['A2']=str(sheet['A2'].value or '')+' BẢN TẠM: chưa xác nhận đủ dữ liệu kỳ. Phiên '+str(session_info.get('session_id',''))
    import json
    settings = session_info.get('ai_settings') or {}
    if isinstance(settings, str): settings = json.loads(settings)
    personnel_mode = 'employee_registry' in settings or any('classification' in e for e in results)
    source={m['message_id']:m for m in session_info.get('snapshot',[])}
    information_ids={i for r in results if r.get('source_only') for i in r.get('source_message_ids',[])}
    # When the only OT reported is My (CTV), there is intentionally no payroll
    # row; label its original message as informational rather than 'Không'.
    information_ids.update(m['message_id'] for m in source.values()
                           if is_annual_leave_text_only(m.get('body')))
    information_ids.update(m['message_id'] for m in source.values()
                           if re.search(r'(?<!\w)my\s*\(\s*ctv\s*\)\s+OT\b',
                                        str(m.get('body') or ''), re.IGNORECASE))
    # One-click export: separate verified payroll rows from unverified AI
    # suggestions. The latter go exclusively to 4_CAN_KIEM_TRA.
    reportable = [e for e in results if not e.get('is_excluded') and not e.get('source_only')]
    pending = [e for e in reportable if needs_excel_review(e) or
               (personnel_mode and e.get('classification') not in {'official','contractor'})]
    verified = [e for e in reportable if e not in pending]
    contractors = [e for e in verified if e.get('classification') == 'contractor']
    kept = [e for e in verified if e.get('classification') == 'official'] if personnel_mode else [
        e for e in verified if not is_ctv_text_only(e, list(source.values()))]
    # Keep the snapshot as-is; it is evidence rather than model output.
    wb[SHEETS[3]]['A2'] = (str(wb[SHEETS[3]]['A2'].value or '') +
        f' {len(pending)} dòng chưa xác minh: chưa tính vào chấm công, tổng kết hoặc CTV.')
    kept=[{**r, 'reason': reason_from_source(r, list(source.values()))} for r in kept]
    identity_names={r.get('person_id',r.get('employee_name')):r.get('employee_name','') for r in kept}
    counts=Counter(identity_names.values())
    labels={identity:name+(f' [{identity}]' if counts[name]>1 else '') for identity,name in identity_names.items()}
    # Source sheet preserves complete evidence, including context outside the month.
    row=5
    for message in source.values():
        linked=[r for r in (reportable if personnel_mode else kept) if message['message_id'] in r.get('source_message_ids',[])]
        dt=datetime.fromisoformat(message['send_time'])
        body=deduplicate_copied_sender_header(message['body'],message.get('name'));parts=[body[i:i+32000] for i in range(0,len(body),32000)] or ['']
        for part in parts:
            put(SHEETS[0],row,[message['message_id'],dt.replace(tzinfo=None,hour=0,minute=0,second=0,microsecond=0),dt.strftime('%H:%M'),message.get('name'),part,('Có' if any(e in verified for e in linked) else 'Cần kiểm tra') if linked else ('Thông tin' if message['message_id'] in information_ids else 'Không'),', '.join(sorted({str(r.get('event_date') or '') for r in linked})),len(linked)])
            row+=1
    source_last_row=row-1
    person_rows={}
    for row,event in enumerate(kept,5):
        if str(event['event_date'])[:7]!=f'{year}-{month:02d}':
            raise ValueError('Không được xuất sự kiện ngoài tháng.')
        identity=event.get('person_id',event.get('employee_name'))
        person_rows.setdefault(identity,[]).append(row)
        ids=event.get('source_message_ids',[])
        messages=[source[i] for i in ids if i in source]
        dt=datetime.fromisoformat(messages[0]['send_time']) if messages else None
        kind=event.get('event_type'); leave=event.get('event_subtype')
        ot=event.get('ot_minutes',0) if kind in {'Tăng ca','OT'} else 0
        reserved=event.get('ot_used_minutes',0) if ot else 0
        credit=event.get('ot_credit_date') or ''
        # Show the actual OT consumed even when it was earned in a prior month.
        # Salary subtraction stays on the corresponding OT event (reserved), once only.
        used=event.get('ot_used_minutes',0) if not ot else 0
        compensation=event.get('hours_compensation','')
        # Excel attendance uses the Chatwork message body, not an AI summary.
        # Only duplicated copied author headings at the start are collapsed.
        # A group report still has identical readable content on every OT row.
        raw='\n\n'.join(deduplicate_copied_sender_header(m['body'],m.get('name')) for m in messages)
        if len(raw)>32767:raw=raw[:32000]+'\n[Nội dung đầy đủ được nối theo thứ tự các dòng cùng ID tại sheet 1_TIN_NHAN_GOC.]'
        leave_days=event.get('leave_days',0) or 0
        values=[event.get('event_id'),', '.join(ids),dt.replace(tzinfo=None,hour=0,minute=0,second=0,microsecond=0) if dt else '',dt.strftime('%H:%M') if dt else '',datetime.fromisoformat(event['event_date']),labels[identity],kind,leave,event.get('reason'),compensation,
                'Có' if event.get('minutes_compensated',0) else 'Không',event.get('minutes_not_compensated',0),event.get('minutes_compensated',0),'','',leave_days if kind=='Nghỉ' and leave=='Phép năm' else 0,
                leave_days if kind=='Nghỉ' and leave in {'Không lương','Nghỉ không lương'} else 0,int(kind in {'Về sớm','Nghỉ sớm'} and not is_paid_break_event(event)),int(kind=='Đi trễ'),ot,used,ot-reserved,'',event.get('review_reason') or '', 'Đã xác nhận' if event.get('review_state')=='confirmed' else '',raw]
        put(SHEETS[1],row,values,{14:f'=L{row}/60',15:f'=M{row}/60',23:f'=V{row}/60'})
    end=max(2000,len(kept)+5)
    for row,(identity,detail_rows) in enumerate(sorted(person_rows.items(), key=lambda item: labels[item[0]].casefold()),5):
        leave_notes='; '.join(f'{r["event_date"]}: {r.get("leave_days",0)} ngày {r.get("event_subtype","")} – {r.get("reason","")}' for r in kept if r.get('person_id',r.get('employee_name'))==identity and r.get('event_type')=='Nghỉ')
        formulas={}
        for col,source_col,divisor in [(3,'L','/60'),(4,'M','/60'),(5,'P',''),(6,'Q',''),(7,'R',''),(8,'S',''),(9,'T',''),(11,'U',''),(12,'V','')]:
            formulas[col]=f'=SUMIFS(\'2_CHAM_CONG\'!${source_col}$5:${source_col}${end},\'2_CHAM_CONG\'!$F$5:$F${end},$A{row}){divisor}'
        formulas.update({10:f'=I{row}/60',13:f'=L{row}/60'})
        put(SHEETS[2],row,[labels[identity],leave_notes]+['']*11,formulas)
    review_row=5
    for event in results:
        if not personnel_mode and is_ctv_text_only(event, list(source.values())):continue
        if event.get('source_only'):continue
        if event in pending or event.get('review_state')=='confirmed' or event.get('is_excluded'):
            ids=event.get('source_message_ids')
            ids=[i for i in ids if isinstance(i,str)] if isinstance(ids,list) else []
            messages=[source[i] for i in ids if i in source]
            raw='\n\n'.join(deduplicate_copied_sender_header(m['body'],m.get('name')) for m in messages)
            if len(raw)>32767:raw=raw[:32000]+'\n[Xem toàn bộ tại sheet 1_TIN_NHAN_GOC.]'
            issues = [str(item) for item in [event.get('review_reason'),
                      *(event.get('validation_errors') or []),
                      *(event.get('validation_warnings') or [])] if item]
            if event.get('classification') == 'unresolved':
                issues.append('Chưa xác định đúng nhân sự/ID')
            if not issues and event in pending:
                issues.append('Thiếu bằng chứng hoặc cần xác nhận thủ công')
            state = ('Đã loại' if event.get('is_excluded') else
                     'Cần kiểm tra (chưa tính công)' if event in pending else 'Đã xác nhận')
            put(SHEETS[3],review_row,[', '.join(ids),messages[0]['send_time'] if messages else '',
                str(event.get('event_date') or ''),str(event.get('employee_name') or ''),
                ' | '.join(dict.fromkeys(issues)),state,raw])
            review_row+=1
    from openpyxl.workbook.properties import CalcProperties
    from openpyxl.workbook.views import BookView
    wb.calculation = CalcProperties(fullCalcOnLoad=True)
    if not wb.views:
        wb.views = [BookView()]
    wb.active = SHEETS.index('3_TONG_KET')
    for name, last_row, color in [
        ('1_TIN_NHAN_GOC', source_last_row, '7C8793'),
        ('2_CHAM_CONG', len(kept) + 4, '4A75AB'),
        ('3_TONG_KET', len(person_rows) + 4, '1D6B5C'),
        ('4_CAN_KIEM_TRA', review_row - 1, 'C78D31'),
    ]:
        sheet = wb[name]
        sheet.freeze_panes = 'B5' if name == '3_TONG_KET' else 'A5'
        end_row = max(5, last_row)
        # Remove unused sample rows, including their inherited row heights.
        if sheet.max_row > end_row:
            sheet.delete_rows(end_row + 1, sheet.max_row - end_row)
        for unused_row in list(sheet.row_dimensions):
            if unused_row > end_row:
                del sheet.row_dimensions[unused_row]
        sheet.print_area = f'A1:{openpyxl.utils.get_column_letter(sheet.max_column)}{end_row}'
        table_range = f'A4:{openpyxl.utils.get_column_letter(sheet.max_column)}{end_row}'
        sheet.auto_filter.ref = table_range
        # The template's four structured Excel tables previously stayed at
        # A4:H193 etc., even if the export had fewer or more rows.
        for excel_table in sheet.tables.values():
            excel_table.ref = table_range
            if excel_table.autoFilter is not None:
                excel_table.autoFilter.ref = table_range
            if excel_table.tableStyleInfo is not None:
                excel_table.tableStyleInfo.showRowStripes = True
        sheet.sheet_properties.tabColor = color
        sheet.sheet_view.tabSelected = name == '3_TONG_KET'
    if personnel_mode:
        from .personnel_excel import append_personnel_sheets
        append_personnel_sheets(wb, kept, contractors, source, month, year)
    wb.save(output_path)
    from .formula_cache import cache_generated_totals
    cache_generated_totals(wb, output_path)
    wb.close()
    verify_workbook(output_path)
    return output_path


class ExcelExporter:
    def __init__(self,template_path=None):self.template_path=template_path
    def create_workbook(self,results,session_info,output_path):
        return export_to_excel(results,session_info,output_path,self.template_path)
