import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (REPO_ROOT / 'gateway/templates/default.conf.template').read_text()
COMPOSE = (REPO_ROOT / 'docker-compose.yml').read_text()

DOMAINS = {
    'assets': 'ASSETS_UPSTREAM',
    'maintenance': 'MAINTENANCE_UPSTREAM',
    'workorders': 'WORKORDERS_UPSTREAM',
    'inspections': 'INSPECTIONS_UPSTREAM',
    'spareparts': 'SPAREPARTS_UPSTREAM',
    'reports': 'REPORTS_UPSTREAM',
}


def _block(text, opening):
    matches = re.findall(
        rf'{re.escape(opening)}\s*\{{(?P<body>.*?)\n\}}',
        text,
        flags=re.DOTALL,
    )
    assert len(matches) == 1, f'expected one block for {opening}'
    return matches[0]


def test_domain_upstreams_use_one_env_placeholder_each():
    for domain, variable in DOMAINS.items():
        body = _block(TEMPLATE, f'upstream {domain}_backend')
        assert body.count(f'${{{variable}}}') == 1


def test_domain_locations_proxy_to_domain_upstreams():
    for domain in DOMAINS:
        body = _block(TEMPLATE, f'location /api/{domain}/')
        assert f'proxy_pass http://{domain}_backend;' in body


def test_api_catchall_still_proxies_to_web():
    body = _block(TEMPLATE, 'location /api/')
    assert 'proxy_pass http://web_backend;' in body


def test_static_nginx_config_includes_rendered_conf_directory():
    config = (REPO_ROOT / 'gateway/nginx.conf').read_text()
    assert 'include /etc/nginx/conf.d/*.conf;' in config


def test_compose_domain_upstreams_default_to_monolith():
    for domain, variable in DOMAINS.items():
        assert re.search(
            rf'^\s+{variable}: \$\{{{variable}:-web:8000\}}$',
            COMPOSE,
            flags=re.MULTILINE,
        )
