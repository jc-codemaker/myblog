# coding=utf-8
import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
import os.path
import re
from pymongo import MongoClient


from tornado.options import define,options
define('port',default=8000,help='run on the given port',type=int)

client = MongoClient('localhost',27017)
db = client.blog
collection = db.test_collection
users = db.users


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/register',registerHandler),
            (r'/login', loginHandler),
            (r'/', indexHandler),
            (r'/addart', addarticleHandler),
            (r'/article/(.*?)',articleHandler),
            (r'/reviseart/(.*?)', revarticleHandler),
            (r'/delart/(.*?)', delarticleHandler),
            (r'/search',findHandler),
            (r'/addfriend/(.*?)', addfriendHandler),
            (r'/delfriend/(.*?)', delfriendHandler),
            (r'/friend/(.*?)', viwfriendHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret='hF+ae4mKQBWZgv/ZET+pcqBiXIdtXUWRgXlo/d1zlzE=',
            # xsrf_cookies=True,
            login_url = '/login',
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class registerHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(
            "register.html",
            error = '',
        )
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        email = self.get_argument('email')
        confirm = self.get_argument('confirm')
        if users.find_one({'username':username}) == None:
            if password == confirm:
                import datetime
                user = {
                    'username': username,
                    'password': password,
                    'email':email,
                    'date': datetime.datetime.utcnow(),
                    'friends':[]
                }
                users.insert_one(user)
                self.redirect(
                    '/login'
                )
            else:
                self.render(
                    'register.html',
                    error = u'两次输入密码不一致'
                )
        else:
            self.render(
                'register.html',
                error = u'该用户名已被注册'
            )

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('username')

class loginHandler(BaseHandler):
    def get(self):
        self.render(
            'login.html',
            error = '',
        )

    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        if users.find_one({'username':username}):
            if users.find_one({'username':username})['password'] == password:
                self.set_secure_cookie('username', self.get_argument('username'))
                self.redirect(
                    '/'
                )
            else:
                self.render(
                    'login.html',
                    error=u'账号或密码错误'
                )
        else:
            self.render(
                'login.html',
                error=u'账号或密码错误'
            )

class indexHandler(BaseHandler):
    articles = db.articles
    @tornado.web.authenticated
    def get(self):
        username=self.current_user
        articlelist = db.articles.find({'author':username})
        user = db.users.find({'username':username})
        friends = db.users.find_one({'username':username})['friends']
        self.render(
            'homepage.html',
            articlelist = articlelist,
            userlist = db.users.find(),
            friends = friends
        )

    @tornado.web.authenticated
    def post(self):
        articles = db.articles
        search = self.get_argument('search', None)
        articlelist = articles.find({'title':re.compile(search)})
        username = self.current_user
        friends = db.users.find_one({'username': username})['friends']
        self.render(
            'find.html',
            articlelist=articlelist,
            userlist=db.users.find(),
            friends=friends
        )

class addarticleHandler(BaseHandler):
    articles = db.articles
    @tornado.web.authenticated
    def get(self):
        username = self.current_user
        friends = db.users.find_one({'username': username})['friends']
        self.render(
            'addarticle.html',
            userlist=db.users.find(),
            friends=friends
        )
    @tornado.web.authenticated
    def post(self):
        import datetime
        articles = db.articles
        username = self.current_user
        title = self.get_argument('title')
        content = self.get_argument('content')
        article = {
            'title': title,
            'content': content,
            'author': username,
            'date': str(datetime.datetime.utcnow()),
        }
        articles.insert_one(article)
        self.redirect(
            '/'
        )

class articleHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self,date):
        article = db.articles.find_one({'date':date})
        username = self.current_user
        friends = db.users.find_one({'username': username})['friends']
        self.render(
            'article.html',
            article = article,
            userlist=db.users.find(),
            friends=friends
        )

class delarticleHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self,date):
        articles = db.articles
        articles.remove({'date':date})
        self.redirect('/')

class revarticleHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self,date):
        articles = db.articles
        article = articles.find_one({'date':date})
        username = self.current_user
        friends = db.users.find_one({'username': username})['friends']
        self.render(
            'revarticle.html',
            article = article,
            userlist=db.users.find(),
            friends=friends
        )

    @tornado.web.authenticated
    def post(self,date):
        import datetime
        articles = db.articles
        article1 = articles.find_one({'date': date})
        username = self.current_user
        friends = db.users.find_one({'username': username})['friends']
        title = self.get_argument('title')
        content = self.get_argument('content')
        article = {
            'title': title,
            'content': content,
            'author': username,
            'date': str(datetime.datetime.utcnow()),
        }
        db.articles.update(article1, {'$set': article}, multi=True)
        self.render(
            'article.html',
            article=article,
            userlist=db.users.find(),
            friends=friends
        )

class findHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        articles = db.articles
        articlelist = ''
        username = self.current_user
        friends = db.users.find_one({'username': username})['friends']
        self.render(
            'find.html',
            articlelist = articlelist,
            userlist=db.users.find(),
            friends=friends
        )

    @tornado.web.authenticated
    def post(self):
        articles = db.articles
        search = self.get_argument('search', None)
        articlelist = articles.find({'title':re.compile(search)})
        username = self.current_user
        friends = db.users.find_one({'username': username})['friends']
        self.render(
            'find.html',
            articlelist=articlelist,
            userlist=db.users.find(),
            friends=friends
        )

class addfriendHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self,username):
        user = self.current_user
        user1 = users.find_one({'username': user})
        friends = db.users.find_one({'username': user})['friends']
        if username in friends:
            self.redirect('/')
        else:
            friends.append(username)
            password = db.users.find_one({'username': user})['password']
            email = db.users.find_one({'username': user})['email']
            date = db.users.find_one({'username': user})['date']
            user = {
                'username': user,
                'password': password,
                'email': email,
                'date': date,
                'friends': friends
            }
            db.users.update(user1, {'$set': user}, multi=True)
            self.redirect('/')

class delfriendHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, username):
        user = self.current_user
        user1 = users.find_one({'username': user})
        friends = db.users.find_one({'username': user})['friends']
        friends.remove(username)
        password = db.users.find_one({'username': user})['password']
        email = db.users.find_one({'username': user})['email']
        date = db.users.find_one({'username': user})['date']
        user = {
            'username': user,
            'password': password,
            'email': email,
            'date': date,
            'friends': friends
        }
        db.users.update(user1, {'$set': user}, multi=True)
        self.redirect('/')

class viwfriendHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, username):
        articlelist = db.articles.find({'author': username})
        friends = db.users.find_one({'username': username})['friends']
        self.render(
            'friend.html',
            articlelist=articlelist,
            userlist=db.users.find(),
            friends=friends
        )

    @tornado.web.authenticated
    def post(self,username):
        articles = db.articles
        search = self.get_argument('search', None)
        articlelist = articles.find({'author': username},{'title': re.compile(search)})
        user = self.current_user
        friends = db.users.find_one({'username': user})['friends']
        self.render(
            'find.html',
            articlelist=articlelist,
            userlist=db.users.find(),
            friends=friends
        )


if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


