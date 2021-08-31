from __future__ import absolute_import


import logging
from functools import total_ordering
from tornado import web
from tornado import gen
from ..utils import response, tasks
from ..utils.broker import Redis
from .control import ControlHandler

class TestView(ControlHandler):
    @web.authenticated
    @gen.coroutine
    def get(self):
        app = self.application

        res = tasks.iter_tasks(app.events, search='')

        self.write(response.ok())
