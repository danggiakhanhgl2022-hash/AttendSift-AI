"""Cache only this exporter's fixed formulas while preserving their Excel text."""
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET


def cache_generated_totals(workbook, target):
    totals = defaultdict(lambda: [0.0] * 9)
    cached = {2: {}, 3: {}}
    detail = workbook['2_CHAM_CONG']
    for row in range(5, detail.max_row + 1):
        name = detail.cell(row, 6).value
        if not name:
            continue
        for i, column in enumerate([12, 13, 16, 17, 18, 19, 20, 21, 22]):
            totals[name][i] += float(detail.cell(row, column).value or 0)
        for dest, source in [('N', 12), ('O', 13), ('W', 22)]:
            cached[2][f'{dest}{row}'] = float(detail.cell(row, source).value or 0) / 60
    summary = workbook['3_TONG_KET']
    for row in range(5, summary.max_row + 1):
        name = summary.cell(row, 1).value
        if not name:
            continue
        t = totals[name]
        values = [t[0]/60, t[1]/60, t[2], t[3], t[4], t[5], t[6], t[6]/60, t[7], t[8], t[8]/60]
        for col, value in enumerate(values, 3):
            cached[3][summary.cell(row, col).coordinate] = value
    is_stream = hasattr(target, 'seek')
    if is_stream:
        target.seek(0)
        original = target.read()
    else:
        original = Path(target).read_bytes()
    result = BytesIO()
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    with ZipFile(BytesIO(original)) as source, ZipFile(result, 'w') as output:
        for info in source.infolist():
            data = source.read(info.filename)
            for index, values in cached.items():
                if info.filename != f'xl/worksheets/sheet{index}.xml':
                    continue
                xml = ET.fromstring(data)
                for cell in xml.iter(f'{{{ns}}}c'):
                    key = cell.get('r')
                    if key not in values or cell.find(f'{{{ns}}}f') is None:
                        continue
                    value = cell.find(f'{{{ns}}}v')
                    if value is None:
                        value = ET.SubElement(cell, f'{{{ns}}}v')
                    value.text = format(values[key], '.15g')
                    cell.attrib.pop('t', None)
                data = ET.tostring(xml, encoding='utf-8', xml_declaration=True)
            output.writestr(info, data)
    if is_stream:
        target.seek(0)
        target.truncate()
        target.write(result.getvalue())
        target.seek(0)
    else:
        Path(target).write_bytes(result.getvalue())
