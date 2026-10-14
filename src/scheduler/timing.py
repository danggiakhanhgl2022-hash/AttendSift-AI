from datetime import datetime, timedelta
import pytz

TZ = pytz.timezone('Asia/Ho_Chi_Minh')


def next_run(hour,minute,now=None):
    if type(hour) is not int or type(minute) is not int or not 0<=hour<=23 or not 0<=minute<=59:
        raise ValueError('Giờ đồng bộ không hợp lệ.')
    now=now or datetime.now(TZ)
    now=TZ.localize(now) if now.tzinfo is None else now
    now=now.astimezone(TZ)
    target=now.replace(hour=hour,minute=minute,second=0,microsecond=0)
    return target if target>now else target+timedelta(days=1)


def due_slot(schedule,last_success=None,now=None):
    now=now or datetime.now(TZ)
    hour,minute=schedule.get('hour',13),schedule.get('minute',0)
    slot=next_run(hour,minute,now)-timedelta(days=1)
    effective=schedule.get('effective_from')
    if effective and slot<datetime.fromisoformat(effective):return None
    if last_success and datetime.fromisoformat(last_success)>=slot:return None
    return slot.isoformat()
