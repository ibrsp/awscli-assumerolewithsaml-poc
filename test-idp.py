#!/usr/bin/env python3

from base64 import b64encode
from copy import deepcopy
from pprint import pprint
from saml2 import BINDING_HTTP_REDIRECT
from saml2.authn_context import UNSPECIFIED
from saml2.config import IdPConfig
from saml2.saml import NAME_FORMAT_UNSPECIFIED
from saml2.saml import NAMEID_FORMAT_TRANSIENT
from saml2.saml import NAMEID_FORMAT_PERSISTENT
from saml2.server import Server

import boto3
import datetime
import getpass
import json
import os
import xml.dom.minidom

# https://stackoverflow.com/questions/509742/change-directory-to-the-directory-of-a-python-script#509754
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

my_username = getpass.getuser()

CONFIG = {
    'entityid': f'https://login.example.com/{my_username}',
    'key_file': 'test-idp-key.pem',
    'cert_file': 'test-idp-cert.pem',
    'attribute_map_dir': './attributemaps',
    'metadata': {
        # 'local': [
        #     './aws-saml-metadata.xml',
        # ],
        'remote': [{
            'url': 'https://signin.aws.amazon.com/static/saml-metadata.xml',
        }],
    },
    'service': {
        'idp': {
            'endpoints': {
                'single_sign_on_service': [
                    ('https://login.rdctdev.us/meconomou/redirect', BINDING_HTTP_REDIRECT)
                ],
            },
            'name_id_format': [
                # NAMEID_FORMAT_TRANSIENT,
                NAMEID_FORMAT_PERSISTENT,
            ],
            'sign_assertion': True,
            'policy': {
                'default': {
                    'attribute_restrictions': None,
                    'fail_on_missing_requested': False,
                    'lifetime': {
                        'minutes': 15,
                    },
                    'name_form': NAME_FORMAT_UNSPECIFIED,
                    'sign_response': True,
                    'sign_assertion': False,
                },
                'urn:amazon:webservices': {
                    'attribute_restrictions': None,
                    'fail_on_missing_requested': False,
                    'lifetime': {
                        'minutes': 15,
                    },
                    'name_form': NAME_FORMAT_UNSPECIFIED,
                    'sign_response': True,
                    'sign_assertion': True,
                }
            },
        }
    }
}

config = IdPConfig().load(deepcopy(CONFIG))
idp = Server(config=config)

aws_account_id = os.environ['AWS_ACCOUNT_ID']
role_arn = f'arn:aws:iam::{aws_account_id}:role/my-test-role'
saml_provider_arn = f'arn:aws:iam::{aws_account_id}:saml-provider/my-test-idp'

saml_response = idp.create_authn_response(
    authn={
        'class_ref': UNSPECIFIED,
        'authn_auth': config.entityid,
    },
    identity={
        'RoleEntitlement': f'{role_arn},{saml_provider_arn}',
        'RoleSessionName': my_username,
        'SessionDuration': '1800',
        'MyCustomClaim': 'I am cool and groovy.',
    },
    sp_entity_id='urn:amazon:webservices',
    destination='https://signin.aws.amazon.com/saml',
    in_response_to=None,
)
base64_saml_response = b64encode(saml_response.encode('utf-8')).decode('ascii')

# https://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
# print(xml.dom.minidom.parseString(saml_response).toprettyxml())

sts = boto3.client('sts')
sts_response = sts.assume_role_with_saml(
    RoleArn=role_arn,
    PrincipalArn=saml_provider_arn,
    SAMLAssertion=base64_saml_response,
)
# pprint(sts_response)

# https://stackoverflow.com/questions/56554159/typeerror-object-of-type-datetime-is-not-json-serializable-with-serialize-fu#56562567,
class DateTimeEncoder(json.JSONEncoder):
    def default(self, z):
        if isinstance(z, datetime.datetime):
            # https://stackoverflow.com/questions/2150739/iso-time-iso-8601-in-python#28147286
            return z.isoformat()
        else:
            return super().default(z)

# https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.html
credentials = deepcopy(sts_response['Credentials'])
credentials['Version'] = 1
print(json.dumps(credentials, cls=DateTimeEncoder))
