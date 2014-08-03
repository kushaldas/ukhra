#!/usr/bin/env python
# These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

from bugspad2 import APP
from bugspad2.default_config import DB_URL
from bugspad2.lib import model
import bugspad2.lib as mmlib
from redis import Redis
import json
import hashlib

r = Redis()
SESSION = mmlib.create_session(DB_URL)

pr = model.Product(name='Fedora', description='OS')
SESSION.add(pr)
SESSION.commit()
ver = model.Version(name='20', product_id=1, active=True)
SESSION.add(ver)
SESSION.commit()
data = [(1, '20'),]
r.set('product:1', json.dumps(data))

#Now add a user too.
password = 'asdf%s' % APP.config.get('PASSWORD_SEED', None)
password = hashlib.sha512(password).hexdigest()
user = model.User(user_name='kdas',email_address='kushaldas@gmail.com',display_name='Kushal Das', password=password)
SESSION.add(user)
SESSION.commit()
f = open('comps.json')
comps = json.load(f)
f.close()
print 'Adding components.'
for comp in comps:
    c = model.Component(name=comp['name'], description=comp['description'], product_id=1)
    SESSION.add(c)
    SESSION.commit()
mmlib.load_all(SESSION)