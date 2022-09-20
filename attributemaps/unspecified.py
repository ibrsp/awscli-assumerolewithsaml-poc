AWS = 'https://aws.amazon.com/SAML/Attributes/'
MAP = {
    'identifier': 'urn:oasis:names:tc:SAML:2.0:attrname-format:unspecified',
    'fro': {
        AWS + 'Role': 'RoleEntitlement',
        AWS + 'RoleSessionName': 'RoleSessionName',
        AWS + 'SessionDuration': 'SessionDuration',
    },
    'to': {
        'RoleEntitlement': AWS + 'Role',
        'RoleSessionName': AWS + 'RoleSessionName',
        'SessionDuration': AWS + 'SessionDuration',
    },
}
