"""Identity evidence from message senders, without an employee directory."""
import re
import unicodedata
import hashlib


def name_key(value):
    value=value.replace('Đ','D').replace('đ','d')
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',value) if not unicodedata.combining(c)).casefold().split())


def exact_name_key(value):
    """Identity matching must distinguish names such as Bảo/Báo or Cẩm/Cầm."""
    return ' '.join(unicodedata.normalize('NFKC', str(value or '')).casefold().split())


def source_quote(alias,text):
    count=len(alias.split())
    words=list(re.finditer(r'\w+',text))
    for index in range(len(words)-count+1):
        quote=text[words[index].start():words[index+count-1].end()]
        if exact_name_key(quote) == exact_name_key(alias):
            return quote
        # An unaccented source alias may be compared to accented text. Never
        # strip tone marks from a name that already specifies its own tone.
        if exact_name_key(alias).isascii() and name_key(quote) == name_key(alias):
            return quote
    return None


def sender_name(value):
    value=unicodedata.normalize('NFKC',str(value or ''))
    value=re.sub(r'\s*\(CTV\)', '', value, flags=re.IGNORECASE)
    parts=re.findall(r'\(([^()]+)\)',value)
    return (parts[-1] if parts else value).strip()


def identity_hints(snapshot):
    found={}
    for message in snapshot:
        name=sender_name(message.get('name'))
        if not name:continue
        entry=found.setdefault(name,{'employee_name':name,'aliases':[], 'source_message_ids':[]})
        words=name.split()
        entry['aliases']=sorted({name,' '.join(words[-2:]),words[-1]})
        entry['source_message_ids'].append(message['message_id'])
    return list(found.values())


def unique_short_name_evidence(name, linked_text, snapshot):
    hints=identity_hints(snapshot)
    target=next((h for h in hints if h['employee_name'].casefold()==name.casefold()),None)
    if not target:return False
    for alias in target['aliases']:
        if not source_quote(alias,linked_text):continue
        matches=[h for h in hints if name_key(alias) in {name_key(a) for a in h['aliases']}]
        if len(matches)==1:return True
    return False


def align_event_identities(events, snapshot):
    """Align derived IDs using sender accounts, never a model ID or name alone.

    The caller retains untouched model output before invoking this function.
    Names from report messages can be resolved against other source senders, but
    only when the quoted alias selects exactly one account in this snapshot.
    A name shared by several accounts needs a matching linked sender account.
    Unresolved names retain their model ID; conflicting unresolved IDs are split
    conservatively without claiming that the people have been identified.
    """
    sources = {m.get('message_id'): m for m in snapshot}
    accounts = {}
    for message in snapshot:
        account = message.get('account_id')
        name = sender_name(message.get('name'))
        if account is None or isinstance(account, bool) or str(account).strip() in {'', '0'} or not name:
            continue
        account = str(account)
        entry = accounts.setdefault(account, {'names': set(), 'aliases': set()})
        entry['names'].add(name)
        words = name.split()
        entry['aliases'].update(exact_name_key(a) for a in (name, ' '.join(words[-2:]), words[-1]))

    def account_for(event):
        name = event.get('employee_name')
        ids = event.get('source_message_ids')
        if not isinstance(name, str) or not isinstance(ids, list) or not ids or any(not isinstance(i, str) or i not in sources for i in ids):
            return None
        name = re.sub(r'\s*\(CTV\)', '', name, flags=re.IGNORECASE).strip()
        key = exact_name_key(name)
        linked = [sources[i] for i in ids]
        text = '\n'.join(str(m.get('body') or '') + '\n' + str(m.get('name') or '') for m in linked)
        exact = {account for account, entry in accounts.items() if key in {exact_name_key(n) for n in entry['names']}}
        direct = {str(m.get('account_id')) for m in linked
                  if str(m.get('account_id')) in accounts and exact_name_key(sender_name(m.get('name'))) == key}
        if len(exact) > 1:
            # Identical names belonging to different senders must stay separate.
            return next(iter(direct)) if len(direct) == 1 else None
        possible = exact or {account for account, entry in accounts.items() if key in entry['aliases']}
        if len(possible) != 1:
            return None
        account = next(iter(possible))
        entry = accounts[account]
        if source_quote(name, text):
            return account
        for alias in entry['aliases']:
            if not source_quote(alias, text):
                continue
            owners = {owner for owner, other in accounts.items() if alias in other['aliases']}
            if owners == {account}:
                return account
        return None

    unresolved = {}
    for event in events:
        # Identity alignment does not repair a malformed model field; leave its
        # type untouched so schema validation can require a source review.
        if not isinstance(event.get('person_id'), str):
            continue
        account = account_for(event)
        if account is not None:
            # Do not depend on the order or batch in which a model saw the name.
            event['person_id'] = 'SRC-A-' + hashlib.sha256(account.encode()).hexdigest()[:16]
            names = accounts[account]['names']
            event['employee_name'] = sorted(names, key=lambda n: (-len(n.split()), n.casefold()))[0]
            continue
        original_id = event.get('person_id')
        name = event.get('employee_name')
        if isinstance(name, str):
            key = exact_name_key(re.sub(r'\s*\(CTV\)', '', name, flags=re.IGNORECASE).strip())
            owners = {owner for owner, entry in accounts.items() if key in entry['aliases']}
            if len(owners) > 1:
                # A source-derived report alias is deliberately team-scoped;
                # it does not claim to be any of the matching sender accounts.
                # Quân OT 4h is independently verifiable even when the room
                # has multiple unrelated senders whose names end in Quân.
                # Do not require a registry ID just to retain the literal OT.
                evidence = event.get('identity_evidence')
                ids = event.get('source_message_ids')
                source_alias = (original_id.startswith('SRC-N-') and
                                isinstance(evidence, str) and bool(evidence.strip()) and
                                isinstance(ids, list) and
                                any(isinstance(i, str) and i in sources and
                                    source_quote(evidence, str(sources[i].get('body') or ''))
                                    for i in ids))
                if not source_alias:
                    event['identity_uncertain'] = True
        if isinstance(original_id, str) and isinstance(name, str):
            # Keep Vietnamese tone marks when grouping unresolved identities.
            # Bảo and Báo must not inherit one model-generated employee ID.
            unresolved.setdefault(original_id, {}).setdefault(exact_name_key(name), []).append(event)
    for original_id, by_name in unresolved.items():
        if len(by_name) <= 1:
            continue
        # A reused model ID cannot combine two different, still-unverified names.
        for key, rows in by_name.items():
            value = original_id + '|' + key
            conservative_id = 'SRC-U-' + hashlib.sha256(value.encode()).hexdigest()[:16]
            for event in rows:
                event['person_id'] = conservative_id
    return events


def repair_identity_evidence(event, snapshot):
    """Repair derived quotes only when the actual linked sources support the name."""
    sources={m['message_id']:m for m in snapshot}
    ids=event.get('source_message_ids')
    name=event.get('employee_name')
    if not isinstance(name,str) or not isinstance(ids,list) or not ids or any(not isinstance(i,str) or i not in sources for i in ids):return
    text='\n'.join(str(sources[i].get('body',''))+'\n'+str(sources[i].get('name','')) for i in ids)
    def plain(value):
        return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',value.replace('Đ','D').replace('đ','d')) if not unicodedata.combining(c)).casefold().split())
    candidates=[h['employee_name'] for h in identity_hints(snapshot) if plain(h['employee_name'])==plain(name)]
    if len(candidates)==1 and (candidates[0].casefold() in text.casefold() or unique_short_name_evidence(candidates[0],text,snapshot)):
        name=candidates[0]
        event['employee_name']=name
    # Discard an unsupported surname rather than inventing a full identity.
    all_text='\n'.join(str(m.get('name',''))+'\n'+str(m.get('body','')) for m in snapshot)
    if name.casefold() not in all_text.casefold() and not unique_short_name_evidence(name,text,snapshot):
        words=name.split()
        for short in [' '.join(words[-2:]),words[-1]] if words else []:
            if short.casefold() in {'anh','chị','em','ctv','team'}:continue
            matches=[h for h in identity_hints(snapshot) if short.casefold() in {a.casefold() for a in h['aliases']}]
            if len(matches)>1:continue
            literal=source_quote(short,text)
            if literal:
                name=literal;event['employee_name']=name;break
    aliases=[name]
    if unique_short_name_evidence(name,text,snapshot):
        aliases+=next(h['aliases'] for h in identity_hints(snapshot) if h['employee_name'].casefold()==name.casefold())
    quote=None
    for alias in aliases:
        pattern=r'(?<!\w)'+r'\s+'.join(re.escape(w) for w in alias.split())+r'(?!\w)'
        match=re.search(pattern,text,re.IGNORECASE)
        if match:
            quote=match.group();break
        if unique_short_name_evidence(name,text,snapshot):
            quote=source_quote(alias,text)
            if quote:break
    if not quote:return
    # A short display name must not conceal known namesakes.
    candidates=[h for h in identity_hints(snapshot) if name.casefold() in {a.casefold() for a in h['aliases']}]
    ambiguous=len({h['employee_name'].casefold() for h in candidates})>1
    evidence=event.get('identity_evidence')
    if not isinstance(evidence,str) or not evidence.strip() or evidence not in text:
        event['identity_evidence']=quote
    if not ambiguous and isinstance(event.get('person_id'),str) and not event['person_id'].strip():
        reporters=sorted({str(sources[i].get('account_id') or sources[i].get('name') or '') for i in ids})
        event['person_id']='SRC-'+hashlib.sha256((name.casefold()+'|'+ '|'.join(reporters)).encode()).hexdigest()[:16]
    reason=str(event.get('review_reason') or '')
    registry_only=re.search(r'registry|registered|danh mục|person_id chính thức|mã định danh|mã nhân viên|họ tên đầy đủ|định danh đầy đủ|xác định danh tính.*ngữ cảnh',reason,re.IGNORECASE)
    reason_for_conflict=re.sub(r'chưa rõ mã định danh[^,;]*','',reason,flags=re.IGNORECASE)
    reason_for_conflict=re.sub(r'chưa rõ họ tên đầy đủ[^,;]*','',reason_for_conflict,flags=re.IGNORECASE)
    reason_for_conflict=re.sub(r'chưa rõ định danh đầy đủ[^,;]*','',reason_for_conflict,flags=re.IGNORECASE)
    conflict=re.search(r'trùng|mơ hồ|chưa rõ|không nhất quán|ambiguous|conflict|multiple|unclear|\b(date|time|duration|minutes)\b',reason_for_conflict,re.IGNORECASE)
    if registry_only and not conflict and not ambiguous:
        # Confidence penalized solely for a nonexistent registration requirement
        # is superseded by the verified literal source; the raw AI score is retained.
        confidence=event.get('confidence')
        if isinstance(confidence,(int,float)) and not isinstance(confidence,bool) and 0.5<=confidence<0.85:
            event['confidence']=0.85
        event['needs_review']=False
        event['identity_uncertain']=False
        event['review_reason']=None
