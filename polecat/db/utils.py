def unparse_url(info):
    scheme = info['scheme']
    auth = info.get('username', '')
    if auth:
        password = info.get('password', None)
        if password:
            auth += f':{password}'
        auth += '@'
    host = info['host']
    dbname = info['dbname']
    return f'{scheme}://{auth}{host}/{dbname}'
