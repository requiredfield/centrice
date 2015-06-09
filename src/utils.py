# -*- coding: UTF-8 -*-
import cherrypy,settings

# Simple RBAC decorator
def role(roleNameList): # roleNameList: "*" | ["roleName"]
  def _decor(f):
    def _roleChecker(*args,**kwargs):
      username = cherrypy.request.login
      role = settings.USERS[username]['role']
      if role not in roleNameList:
        status = "403 Forbidden Role:" + role
        cherrypy.response.status = status
        return "<h1>" + status + "</h1>"
      return f(*args,**kwargs)

    if roleNameList == '*':
      return f
    else:
      return _roleChecker
  return _decor

# Content-Type decorator
def mimetype(type):
    def decorate(func):
        def wrapper(*args, **kwargs):
            cherrypy.response.headers['Content-Type'] = type
            return func(*args, **kwargs)
        return wrapper
    return decorate
