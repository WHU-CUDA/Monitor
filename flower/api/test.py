from __future__ import absolute_import


import logging
from functools import total_ordering
from tornado import web
from tornado import gen
from ..utils import response, tasks
from ..utils.broker import Redis
from .control import ControlHandler
from celery.task.control import  inspect

class TestView(ControlHandler):
    @web.authenticated
    @gen.coroutine
    def get(self):
        app = self.capp
        print(app.Task)
        i = inspect()
        print(i.registered_tasks())
        self.write(response.ok())
