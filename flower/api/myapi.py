from __future__ import absolute_import

import json
import logging
from functools import total_ordering
from tornado import web
from tornado import gen
from ..utils import response, tasks
from ..utils.broker import Redis
from .control import ControlHandler

logger = logging.getLogger(__name__)
default_device_info = {
    "gpu": [
        {
            "name": "N/A",
            "total": 0,
            "used": 0,
            "free": 0,
            "usage": 0
        }
    ],
    "cpu": {
        "cores": 0,
        "logical_counts": 0,
        "usage": 0
    },
    "mem": {
        "total": 0,
        "free": 0,
        "used": 0,
        "process_used": 0
    },
}

class DashBoard(ControlHandler):
    @web.authenticated
    @gen.coroutine
    def get(self):
        app = self.application
        events = app.events.state
        broker = app.capp.connection().as_uri()
        workers = {}

        for name, values in events.counter.items():
            if name not in events.workers:
                continue
            worker = events.workers[name]
            info = dict(values)
            info.update(self._as_dict(worker))
            info.update(status=worker.alive)
            workers[name] = info
            redis_client = Redis(broker).redis
            device_info = redis_client.get(name)
            if device_info is not None:
                info.update(device_info=json.loads(device_info.decode()))
            else:
                info.update(device_info=default_device_info)
        self.write(response.ok(list(workers.values())))

    @classmethod
    def _as_dict(cls, worker):
        if hasattr(worker, '_fields'):
            return dict((k, worker.__getattribute__(k)) for k in worker._fields)
        else:
            return cls._info(worker)

    @classmethod
    def _info(cls, worker):
        _fields = ('hostname', 'pid', 'freq', 'heartbeats', 'clock',
                   'active', 'processed', 'loadavg', 'sw_ident',
                   'sw_ver', 'sw_sys', 'device_info')

        def _keys():
            for key in _fields:
                value = getattr(worker, key, None)
                if value is not None:
                    yield key, value

        return dict(_keys())


@total_ordering
class Comparable(object):
    """
    Compare two objects, one or more of which may be None.  If one of the
    values is None, the other will be deemed greater.
    """

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        try:
            return self.value < other.value
        except TypeError:
            return self.value is None


class TaskTableData(ControlHandler):
    @web.authenticated
    @gen.coroutine
    def get(self):
        start = self.get_argument('start', 0, type=int)
        length = self.get_argument('length', 10, type=int)
        sort_by = 'started'
        sort_order = 'asc' == 'desc'
        search = ''
        app = self.application

        def key(item):
            return Comparable(getattr(item[1], sort_by))

        self.maybe_normalize_for_sort(app.events.state.tasks_by_timestamp(), sort_by)

        sorted_tasks = sorted(
            tasks.iter_tasks(app.events, search=search),
            key=key,
            reverse=sort_order
        )

        filtered_tasks = []

        for task in sorted_tasks[start:start + length]:
            task_dict = tasks.as_dict(self.format_task(task)[1])
            if task_dict.get('worker'):
                task_dict['worker'] = task_dict['worker'].hostname

            filtered_tasks.append(task_dict)
        self.write(response.ok(dict(tasks=filtered_tasks, total=len(sorted_tasks), filtered=len(sorted_tasks))))

    @classmethod
    def maybe_normalize_for_sort(cls, tasks, sort_by):
        sort_keys = {'name': str, 'state': str, 'received': float, 'started': float, 'runtime': float}
        if sort_by in sort_keys:
            for _, task in tasks:
                attr_value = getattr(task, sort_by, None)
                if attr_value:
                    try:
                        setattr(task, sort_by, sort_keys[sort_by](attr_value))
                    except TypeError:
                        pass
