# -*- coding: UTF-8 -*-
import os

USERS = { # Override this in `settings_local.py`
  # UserName as key
  'guest':{
    'password': 'guest',
    # type role = Enum(guest|mandator|admin)
    #   guest: only have the permission to `fetch` public rank domains
    #   mandator: can `fetch` and `update` all domains
    #   admin: reserved
    'role': 'guest'
  }
}

# Enum(''|'production')
environment = ''

host = '0.0.0.0'
port = 1988

# Set the CA file path to enable https
ssl_certificate = ''
ssl_private_key = ''

DB_FILE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),'db.sqlite3')


from settings_local import *
