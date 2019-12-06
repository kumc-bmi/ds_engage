"""ref_code_gen -- generate referral codes in REDCap

We can make a batch of 2 records from each of 3 sites::

    >>> b = ReferralCode.batch(2, 3)
    >>> print(pformat(b))
    [{'record_id': 'SA-0000', 'redcap_data_access_group': 'sa'},
     {'record_id': 'SA-0001', 'redcap_data_access_group': 'sa'},
     {'record_id': 'SB-0000', 'redcap_data_access_group': 'sb'},
     {'record_id': 'SB-0001', 'redcap_data_access_group': 'sb'},
     {'record_id': 'SC-0000', 'redcap_data_access_group': 'sc'},
     {'record_id': 'SC-0001', 'redcap_data_access_group': 'sc'}]
"""

from pprint import pformat
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import OpenerDirector as OpenerDirector_T
import json
import logging
import typing as py

log = logging.getLogger(__name__)

Record = py.Dict[str, object]


def main(argv: py.List[str], environ: py.Dict[str, str],
         basicConfig: py.Callable[..., None],
         web_ua: OpenerDirector_T) -> None:
    basicConfig(
        format='%(asctime)s (%(levelname)s) %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG if '--debug' in argv
        else logging.INFO)
    if '--debug' in argv:
        argv.remove('--debug')

    batch_size = int(argv[1]) if len(argv) >= 2 else ReferralCode.batch_size
    site_qty = int(argv[2]) if len(argv) >= 3 else ReferralCode.site_qty

    batch = ReferralCode.batch(batch_size, site_qty)
    log.debug('batch: %s', batch)

    p1 = Project(web_ua, Project.kumc_redcap_api, environ[Project.key])
    p1.import_records(batch)


class ReferralCode:
    batch_size = 100
    site_qty = 5

    @classmethod
    def batch(cls, batch_size: int, site_qty: int) -> py.List[Record]:
        sites = [f'S{chr(c)}' for c in range(ord('A'), ord('A') + site_qty)]
        return [{'record_id': f'{site}-{n:04d}',
                 'redcap_data_access_group': site.lower()}
                for site in sites
                for n in range(batch_size)]


class Project:
    '''Access to a REDCap Project to import_records()
    '''

    kumc_redcap_api = 'https://redcap.kumc.edu/api/'
    key = 'REDCAP_API_TOKEN'

    def __init__(self, ua: OpenerDirector_T, url: str, api_token: str) -> None:
        self.__ua = ua
        self.url = url
        self.__api_token = api_token

    def import_records(self, data: py.List[Record]) -> object:
        ua, url, api_token = self.__ua, self.url, self.__api_token

        form = [('token', api_token),
                ('content', 'record'),
                ('data', json.dumps(data)),
                ('format', 'json')]
        log.info('sending: %s', [(k, v[:15] if k != 'token' else '...')
                                 for (k, v) in form])
        log.debug('sending: %s', data)
        try:
            reply = ua.open(url, urlencode(form).encode('utf8'))
        except HTTPError as err:
            body = err.read()
            try:
                body = json.loads(body)
            except ValueError:
                pass
            log.error('code: %d\n%s', err.code, pformat(body))
            raise
        if reply.getcode() != 200:
            raise IOError(reply.getcode())

        result = json.load(reply)  # type: py.Dict[str, object]
        log.info('result: %s', result)
        if ('error' in result or 'count' not in result):
            raise IOError(result)
        return result


if __name__ == '__main__':
    def _script_io() -> None:
        from sys import argv
        from os import environ
        from urllib.request import build_opener

        main(argv[:], environ.copy(), logging.basicConfig, build_opener())

    _script_io()
