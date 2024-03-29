# -*- coding: utf-8 -*-

import os
import webapp2
import jinja2


from models import Animal
from google.appengine.ext import ndb
from mr import PredatorCountPipeline
from mapreduce import mapreduce_pipeline


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

PARENT = ndb.Key("FoodChain", 1)


class MainPage(webapp2.RequestHandler):
    def get(self):
        animals = [a.as_dict() for a in Animal.query(ancestor=PARENT)]
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render({"animals": animals}))


class NewAnimalHandler(webapp2.RequestHandler):        
    def post(self):
        name = self.request.get('animal')
        
        if name:
            animal = Animal(parent=PARENT, name=name)
            animal.put()
        
        self.redirect('/')
        

class NewPreyHandler(webapp2.RequestHandler):        
    def post(self):
        predator = self.request.get('predator')
        prey = self.request.get('prey')
        
        animal = Animal.get_by_id(int(predator), parent=PARENT)
        animal.prey.append(ndb.Key("FoodChain", 1, Animal, int(prey)))
        animal.put()
        
        self.redirect('/')
        

class MapRecuceHandler(webapp2.RequestHandler):
    def post(self):
        pipeline = PredatorCountPipeline()
        pipeline.start()
        plid = pipeline.pipeline_id
        self.redirect('/mr?pipeline=%s'%plid)

    def get(self):
        self.response.headers['content-type'] = 'text/plain; charset=utf-8'
        pipeline_id = self.request.get("pipeline")
        pipeline = mapreduce_pipeline.MapreducePipeline.from_id(pipeline_id)
        if pipeline.has_finalized:
            self.response.write("MapReduce-työ valmis.\n")
        else:
            self.response.write("MapReduce-työ käynnissä... Päivitä sivu...")


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/newanimal', NewAnimalHandler),
    ('/newprey', NewPreyHandler),
    ('/mr', MapRecuceHandler)], debug=True)


