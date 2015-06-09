#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import cherrypy,settings,json,os,re
from collections import namedtuple
from cherrypy.lib import auth_basic
from cherrypy import expose,HTTPError
from utils import *

"""
DB_FILE Schema:
  type DB = SiteDomainMap
  type SiteDomainMap = { SiteID => Set(SiteDomain) }
  type SiteID = String
  type SiteDomain = NamedTuple('SiteDomain',
                      [
                        'origin', // URLOrigin
                        'rank',   // UnsignedInt , default is 0, means public
                        'status'  // Enum("up"|"down") , default is "up"
                      ])
  type URLOrigin = String // e.g. "https://sub.cloudfront.com"
"""
SiteDomain = namedtuple('SiteDomain',['origin','rank','status'])


class App():
  def __init__(self):
    if not os.path.exists(settings.DB_FILE_PATH):
      file(settings.DB_FILE_PATH,'wb').write('{}')
    data = json.load(file(settings.DB_FILE_PATH))
    for k in data:
      data[k] = set(map(lambda d: SiteDomain(**d),data[k]))

    self.db = data

    self._debug = True
    if settings.environment == 'production':
      self._debug = False


  def sync_db(self):
    data = dict()
    for k in self.db:
      data[k] = filter(lambda d:d.status =='up',self.db[k]) # current only save active domains
      data[k] = map(lambda d:d._asdict(),data[k])

    indent = None
    if self._debug:
      indent = 2
    data = json.dumps(data,sort_keys=True,indent=indent)
    file(settings.DB_FILE_PATH,'wb').write(data)

  """
  Fetch accessible domains in the default public rank
  GET /domains/fetch_public?site=getlantern
    Params:
      site: The site id, required

  Output:
    URL origin list seperated by line feed char
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
              Enum(up|down|all)
  Output:
    URL origin list seperated by line feed char
  """
  @expose
  @role(['admin','mandator'])
  @mimetype('text/plain')
  def fetch(self,site,rank=0,status='up'):
    return self._fetch(site=site,rank=rank,status=status)


  def _fetch(self,site,rank=0,status='up'):
    if site not in self.db:
      raise HTTPError(404,"Site '"+site+"' not found")

    domains = self.db[site]
    domains = filter(lambda d: (status == 'all' or d.status == status) and d.rank == rank,domains)
    return "\n".join(map(lambda d:d.origin,domains))


  """
  POST /domains/update
    Body:site=xxx&status=up&urls=http://a.example.com,http://b.example.com
    Params:
      site, status: Same as `fetch` API
      urls: URL origin split by comma
  """
  @expose
  @role(['admin','mandator'])
  @mimetype('text/plain')
  def update(self,site,urls,status='up'):
    """
    if cherrypy.request.method != 'POST':
      raise HTTPError(400,'Bad Request, Not POST')
    """
    urls = re.split('[,\s]+',urls)
    domains = []; origins = [];
    for url in urls:
      if url[-1]=='/':
        url = url[0:-1]
      origins.append(url)
      d = SiteDomain(origin=url,rank=0,status=status)
      domains.append(d)

    origins = set(origins)
    if site in self.db:
      existsDomains = self.db[site]
      for d in existsDomains:
        if d.origin in origins:
          pass
        else:
          domains.append(d)

    domains = set(domains)
    self.db[site] = domains
    self.sync_db()
    return "OK"


  @expose
  @role(['admin','mandator'])
  def submitForm(self):
    return '''
    <form action="../update/" method="POST" style="width:50em;margin:4em auto;">
      <p><label>Site ID: <input type="text" name="site"/></label></p>
      <p><label>Urls split by comma: </br><textarea name="urls" style="width:40em;height:10em;"></textarea></label></p>
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
