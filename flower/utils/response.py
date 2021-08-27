
class HTTPCode(object):
    ok = 200
    paramserror = 400
    unauth = 401
    methoderror = 405
    servererror = 500


def result(code=HTTPCode.ok, message="", data=None, kwargs=None):
    json_dict = {"code": code, "message": message, "data": data}

    if kwargs and isinstance(kwargs, dict) and kwargs.keys():
        json_dict.update(kwargs)

    return json_dict


def ok(data=None):
    return result(data=data)


def unauth(message="", data=None):
    return result(code=HTTPCode.unauth, message=message, data=data)


def method_error(message="", data=None):
    return result(code=HTTPCode.methoderror, message=message, data=data)


def server_error(message="", data=None):
    return result(code=HTTPCode.servererror, message=message, data=data)



