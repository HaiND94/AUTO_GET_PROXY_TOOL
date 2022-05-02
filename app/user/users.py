import flask
from flask import flash
from app import users_table, login
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from flask_login import UserMixin, login_user, logout_user

import logging
import json

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class User(UserMixin):

    def __init__(self, name=None, email=None, password=None):
        self.name = name
        self.email = email
        self.password = password

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.name

    @login.user_loader
    def load_user(name):
        u = users_table.find_one({"name": name})
        if not u:
            return None
        return User(name=u['name'])

    @staticmethod
    def signup(**kwargs):
        DEFAULT_KEY = ['name', 'email', 'password']
        _list_key = kwargs.keys()
        _check = all(item in _list_key for item in DEFAULT_KEY)
        if not _check:
            return False

        user = dict()

        user['name'] = kwargs.get('name').lower()
        user['email'] = kwargs.get('email').lower()
        _query = {
            "or": [
                {'name': user['name'].lower()},
                {'email': user['email'].lower()}
            ]
        }
        _query = {'name': user['name'].lower()}
        try:
            status = users_table.find_one(_query)
        except:
            status = False
        if not status:
            _query = {'email': user['email'].lower()}
            status = users_table.find_one(_query)

        if status:
            logging.error("User have already")
            return False

        value = kwargs.get('password')
        _hash = generate_password_hash(value)
        user['pass'] = _hash

        if 'type' in kwargs:
            value = str(kwargs.get('type')).lower()
            if value in ['admin', 'user']:
                user['type'] = value
            else:
                return False
        else:
            user['type'] = 'user'
        try:
            users_table.insert_one(user)
        except Exception as e:
            logging.error(e)
            return False

        return True

    @staticmethod
    def update(name_old=None, id_old=None, **kwargs):
        if not name_old and not id_old:
            logging.error("must be have id or name field")
            return False

        elif name_old:
            query = {'name': name_old.lower()}
            u = users_table.find_one(query)
        else:
            query = {'_id': ObjectId(id_old)}
            u = users_table.find_one(query)

        if not u:
            logging.error("No user name")
            return False

        user = dict()

        # update user name
        if 'name' in kwargs:
            user['name'] = kwargs.get('name').lower()
            check_user = users_table.find_one({'name': user['name'].lower()})
            if check_user:
                logging.error("Can not update user with new user name, have already.")
                return False

        # Update email
        if 'email' in kwargs:
            user['email'] = kwargs.get('email').lower()

        # Update password
        if 'password' in kwargs:
            value = kwargs.get('password')
            _hash = generate_password_hash(value)
            user['pass'] = _hash

        if 'type' in kwargs:
            value = str(kwargs.get('type')).lower()
            if value in ['admin', 'user']:
                user['type'] = value
            else:
                logging.error("type must be admin or user")
                return False

        set_user_new = {"$set": user}

        try:
            users_table.update_one(filter=query, update=set_user_new)
        except Exception as e:
            logging.error(e)
            return False

        return True

    @staticmethod
    def remove(**kwargs):
        DEFAULT_KEY = ['name']
        _list_key = kwargs.keys()
        _check = all(item in _list_key for item in DEFAULT_KEY)
        if not _check:
            logging.error("must be have id or name field")
            return False

        if 'id' in kwargs:
            _id = kwargs.get('id')
            try:
                users_table.delete_one({"_id": ObjectId(_id)})
            except Exception as e:
                logging.error(e)
                return False

            return True
        if 'name' in kwargs:
            value = kwargs.get('name')
            try:
                result = users_table.delete_many({'name': value})
            except Exception as e:
                logging.error(e)
                return False
            if result.deleted_count == 0:
                logging.warn("No user need to delete")
                return False

            return True

        return False

    # Query data
    def query(self, query=None, limit=None, **kwargs):

        # Define variable
        _filter = dict()

        # Find follow query
        if not query:
            if not limit:
                try:
                    result = users_table.find(query)
                    return result
                except Exception as e:
                    logging.error(f"Can not find data in tss table\n {e}")
            else:
                try:
                    number_of = int(limit)
                    if number_of >= 0:
                        result = users_table.find(query).limit(number_of)
                    else:
                        result = users_table.find(query)
                    return result

                except Exception as e:
                    logging.error(f"Can not find data user follow query\n {e}")

        if 'name' in kwargs:
            _filter['name'] = kwargs.get('name')
        if 'email' in kwargs:
            _filter['email'] = kwargs.get('email')
        if 'id' in kwargs:
            value = kwargs.get('id')
            _filter['_id'] = ObjectId(value)
        if 'type' in kwargs:
            _filter['type'] = kwargs.get('type')

        result = None
        # if have kwargs
        if _filter:
            try:
                result = users_table.find(filter=_filter)
            except Exception as e:
                logging.error(f"Can not find data {e}")

        return result

    def check_password(self):
        _user = None
        if self.name:
            _user = users_table.find_one({"name": self.name})
        else:
            _user = users_table.find_one({"email": self.email})

        if not _user:
            flash('Invalid username or password')
            return False

        hash_pass = _user['pass']
        check = check_password_hash(hash_pass, self.password)

        return check
