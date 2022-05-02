import ast
import logging
from weakref import proxy

from flask import render_template, \
    send_from_directory, \
    jsonify, \
    request

from flask import redirect, url_for, flash
from flask_login import current_user, login_user
from flask_login import login_required
# from app import login_manager

from app import app, r, logger
from app.user import User
from app import limiter

import random 


@app.route('/')
@limiter.exempt
def home():
    return render_template('home.html')
    # return "this is test program"


@app.route('/get-proxy')
# @login_required
def get_proxy():
    # Get all proxy
    keys = r.keys()
    if len(keys) == 0:
        logger.error("Proxy not found!")
        return jsonify({"content": "Proxy not found!"}), 400
    
    # Get proxy
    key_random = str(random.choice(keys).decode())
    check_format = True if len(key_random.split(':')) in [2, 3] else False
    times_out = 20

    while not check_format:
        times_out -= 1
        
        key_random = str(random.choice(keys).decode())
        check_format = True if len(key_random.split(':')) in [2, 3] else False
        if times_out <= 0:
            break
    
    if not check_format:
        logger.error("Proxy not found!")
        return jsonify({"content": "Proxy not found!"}), 400
    
    try:
        proxy_data = ast.literal_eval(r.get(key_random).decode('utf_8'))
    except Exception as e:
        logger.error(f"Can not convert to json from proxy data {e}")
    try:
        r.delete(key_random)
    except Exception as e:
        logger.warn(f"Can not delete proxy in redis {e}")
    
    return f"{proxy_data['ip']}:{proxy_data['port']}:{proxy_data['protocol']}"
            

    



    



    

