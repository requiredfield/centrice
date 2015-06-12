#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import cherrypy,settings,json,os,re,sqlite3
from cherrypy.lib import auth_basic
from cherrypy import expose,HTTPError
from utils import *


class App():
  def __init__(self):
    self._init_database()
    self._debug = True
    if settings.environment == 'production':
      self._debug = False

  def _init_database(self):
    db = sqlite3.connect(settings.DB_FILE_PATH)
    cursor = db.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS MirrorDomain (
      domain TEXT PRIMARY KEY NOT NULL,
      site TEXT NOT NULL,
      rank INTEGER NOT NULL,
      status TEXT NOT NULL
    )''')
    cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS domain_index ON MirrorDomain(domain)')
    cursor.execute('CREATE INDEX IF NOT EXISTS query_index ON MirrorDomain(site,status,rank)')
    db.commit()
    db.close()

  """
  Fetch accessible domains in the default public rank
  GET /domains/fetch_public?site=getlantern
    Params:
      site: The site id, required

  Output:
    Domain list seperated by line feed char
  """
  @expose
  @role('*')
  @mimetype('text/plain')
  def fetch_public(self,site):
    return self._fetch(site=site,rank=0,status='up')

  """
  Fetch domains by rank and status
  GET /domains/fetch?site=getlantern&rank=0&status=up
    Params:
      site: The site id, required
      rank: The domain rank, default is 0, i.e. public.
      status: The accessible status, default is up,i.e. not blocked.
              Enum(up|down)
  Output:
    Domain list seperated by line feed char
  """
  @expose
  @role(['admin','mandator'])
  @mimetype('text/plain')
  def fetch(self,site,rank=0,status='up'):
    return self._fetch(site=site,rank=rank,status=status)

  def _fetch(self,site,rank=0,status='up'):
    db = sqlite3.connect(settings.DB_FILE_PATH)
    cursor = db.cursor()
    cursor.execute('SELECT domain FROM MirrorDomain WHERE site=? AND rank=? AND status=?',(site,rank,status))
    domains = map(lambda t:t[0],cursor.fetchall())
    db.close()
    return "\n".join(domains)


  """
  POST /domains/update/
    Body:site=xxx&status=up&domains=a.example.com,b.example.com
    Params:
      site, status: Same as `fetch` API
      domains: domain split by comma
  """
  @expose
  @role(['admin','mandator'])
  @mimetype('text/plain')
  def update(self,site,domains,status='up'):
    if status != 'up':
      status =  'down'

    db = sqlite3.connect(settings.DB_FILE_PATH)
    cursor = db.cursor()
    """
    if cherrypy.request.method != 'POST':
      raise HTTPError(400,'Bad Request, Not POST')
    """
    domains = re.split('[,\s]+',domains)
    domains = filter(lambda x:x,domains)
    rank = 0
    updates = map(lambda domain:(domain,site,status,rank),domains)
    cursor.executemany('INSERT OR REPLACE INTO MirrorDomain(domain,site,status,rank) values(?,?,?,?)',updates)
    db.commit()
    db.close()
    return "OK"


  @expose
  @role(['admin','mandator'])
  def submitForm(self):
    return '''
    <form action="/domains/update/" method="POST" style="width:50em;margin:4em auto;">
      <p><label>Site ID: <input type="text" name="site"/></label></p>
      <p><label>Domains split by comma or newline: </br><textarea name="domains" style="width:40em;height:10em;"></textarea></label></p>
      <p><label>Status:
        <select name="status">
          <option value="up" selected="selected">Up</option>
          <option value="down">Down</option>
        </select>
      </label></p>
      <p><input type="submit"  value="Submit"/></p>
    </form>
    '''



def validate_password(realm,username, password):
  if username in settings.USERS and settings.USERS[username]['password'] == password:
     return True
  return False

conf = {
  '/': {
    'tools.auth_basic.on': True,
    'tools.auth_basic.realm': 'localhost',
    'tools.auth_basic.checkpassword': validate_password
  }
}
cherrypy.config.update({
  'server.ssl_module':'builtin',
  'server.ssl_certificate':settings.ssl_certificate,
  'server.ssl_private_key':settings.ssl_private_key,
  'server.socket_host': settings.host,
  'server.socket_port': settings.port,
  'environment': settings.environment
})


if __name__ == '__main__':
   cherrypy.quickstart(App(),'/domains/',conf)
