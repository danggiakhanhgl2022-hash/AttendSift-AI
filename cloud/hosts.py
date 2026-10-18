"""Exact host allowlist from administrator and trusted deployment configuration."""
import re


def allowed_hosts(env):
    hosts = {host.strip().lower() for host in
             env.get('CHAMCONG_ALLOWED_HOSTS', '').split(',') if host.strip()}
    # Only trust platform metadata on Vercel, never incoming proxy headers.
    if env.get('VERCEL') == '1':
        for key in ('VERCEL_URL', 'VERCEL_BRANCH_URL', 'VERCEL_PROJECT_PRODUCTION_URL'):
            host = env.get(key, '').strip().lower()
            if (len(host) <= 253 and re.fullmatch(
                    r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?'
                    r'(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*', host)
                    and all(len(label) <= 63 for label in host.split('.'))):
                hosts.add(host)
    if not hosts:
        raise RuntimeError('Cần CHAMCONG_ALLOWED_HOSTS; không mặc định mở dữ liệu nhân viên ra Internet.')
    return hosts
