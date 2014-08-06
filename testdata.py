#!/usr/bin/env python
# These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

from ukhra import APP
from ukhra.default_config import DB_URL
from ukhra.lib import model
import ukhra.lib as mmlib
from redis import Redis
import json
import hashlib
from datetime import datetime

r = Redis()
SESSION = mmlib.create_session(DB_URL)

#Now add a user too.
password = 'asdf%s' % APP.config.get('PASSWORD_SEED', None)
password = hashlib.sha512(password).hexdigest()
user = model.User(user_name='kdas',email_address='kushaldas@gmail.com',display_name='Kushal Das', password=password)
SESSION.add(user)
SESSION.commit()

group = model.Group(group_name='admin',display_name='Admin')
SESSION.add(group)
SESSION.commit()

ugbase = model.UserGroup(user_id=user.id, group_id=group.id)
SESSION.add(ugbase)
SESSION.commit()

password = 'asdf%s' % APP.config.get('PASSWORD_SEED', None)
password = hashlib.sha512(password).hexdigest()
user = model.User(user_name='bdas',email_address='kushal@fedoraproject.org',display_name='Kushal Das', password=password)
SESSION.add(user)
SESSION.commit()

helptext = u'''Welcome to the new wiki system of dgplug.

### How to create a new page?


Just type in the URL, if the pages does not exist then it will ask you to start a new one.
Remember to add some summary to each change.

Example URL: '/page/MyNewPage'



### Tags are not showing!!!

Yes, we are yet to add that feature.

###  What format do you support?

We support two of the best developer friendly formats, [markdown](http://daringfireball.net/projects/markdown/syntax) is default choice or else you can use [reStructuredText](http://getnikola.com/quickstart.html).

reST support was added with help from [Nikola](http://getnikola.com/) project.  Yes, we support the [extensions](http://getnikola.com/handbook.html#restructuredtext-extensions) provided by Nikola.'''

page = model.Page(title='Help page', data=helptext, created=datetime.now(), updated=datetime.now(), path='help', writer=1, version=0, format=0)

SESSION.add(page)
SESSION.commit()



r.flushall()
mmlib.load_all(SESSION)
