import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'E"dL~n7.}_^;@26c'


