import hashlib
import webapp2
import jinja2
import os
from google.appengine.ext import ndb
import markdown
from random import shuffle
from random import random

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

md = markdown.Markdown(extensions=['meta'])
JINJA_ENVIRONMENT.filters['markdown'] = lambda text: jinja2.Markup(md.convert(text))

pwhash='9f7b201f28a1ae7f08e576344dc73ee190ccf4894913335daae89f17'

class ITT(ndb.Model):
    title = ndb.StringProperty(indexed=True)
    prompt = ndb.TextProperty(indexed=False)
    scores = ndb.IntegerProperty(repeated=True)

class Answer(ndb.Model):
    title = ndb.StringProperty(indexed=True)
    answer = ndb.TextProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)
    sincere = ndb.StringProperty(indexed=False)    
    votes = ndb.IntegerProperty(repeated=True);

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        template = JINJA_ENVIRONMENT.get_template('index.html')
        tests=ITT.query().fetch()
        self.response.write(template.render({'tests':[test.title for test in tests]}))

class CreatePage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        template = JINJA_ENVIRONMENT.get_template('create.html')
        self.response.write(template.render({}))

class DoCreate(webapp2.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        title = self.request.get('title')
        prompt = self.request.get('prompt')
        if title == '':
            self.response.write('Title is required')
            return
        itt = ITT(title=title, prompt=prompt)
        itt.put()
        self.response.write('Success')        

class SubmitPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        template = JINJA_ENVIRONMENT.get_template('submit.html')
        title = self.request.get('test')
        prompt = ITT.query().filter(ITT.title==title).fetch()[0].prompt
        self.response.write(template.render({'title':title, 'prompt':prompt}))

class DoSubmit(webapp2.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        ans = Answer(
            title = self.request.get('title'),
            answer = self.request.get('answer'),
            email = self.request.get('email'),
            sincere = self.request.get('sincere'),
            votes = [0, 0, 0, 0, 0, 0, 0, 0, 0])
        ans.put()
        self.response.write('Success')

class JudgePage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        template = JINJA_ENVIRONMENT.get_template('judge.html')
        title = self.request.get('test')
        itt = ITT.query().filter(ITT.title==title).fetch()[0]
        answers = Answer.query().filter(ITT.title==title).fetch()
        shuffle(answers)
        scores = [str(x) for x in itt.scores]
        self.response.write(template.render({'title':title, 'prompt':itt.prompt, 'answers':answers, 'scores':', '.join(scores)}))

class DoJudge(webapp2.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        out=''
        for i in self.request.POST:
            if i[:2]=='rb' and self.request.POST[i]!='none':
                key = ndb.Key(urlsafe=i[2:])
                ans = key.get()
                if len(ans.votes)!=9:
                    ans.votes=[0,0,0,0,0,0,0,0,0]
                v = int(self.request.POST[i])-1
                ans.votes[v]+=1
                ans.put()
            if (i[:6]=='remove' and self.request.POST[i]=='on' and
                hashlib.sha224(self.request.get('password')).hexdigest()==pwhash): 
                key = ndb.Key(urlsafe=i[6:])
                key.delete()
        score=self.request.get('score')
        if score!='NaN':
            itt = ITT.query().filter(ITT.title==self.request.get('title')).fetch()[0]
            itt.scores.append(int(score))
            itt.scores.sort()
            itt.put()
        self.response.write('Success '+out)

class DoRemove(webapp2.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        if hashlib.sha224(self.request.get('password')).hexdigest()==pwhash: 
            title = self.request.get('title')
            itt = ITT.query().filter(ITT.title==title).fetch()[0]            
            key = itt.key
            key.delete()
            self.response.write('Success')            
        else:
            self.response.write('Bad pw')            


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/create', CreatePage),
    ('/do_create', DoCreate),
    ('/submit', SubmitPage),
    ('/do_submit', DoSubmit),
    ('/judge', JudgePage),
    ('/do_judge', DoJudge),
    ('/do_remove', DoRemove)
], debug=True)
