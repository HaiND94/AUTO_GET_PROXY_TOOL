from cgitb import text
from concurrent.futures import thread
from tkinter import E
from typing import Protocol
from weakref import proxy
import redis
import ast
import requests
import threading
import os

import time

import pandas as pd

import logging

import schedule

import queue

from schedule import repeat, every

from proxy_checker import ProxyChecker
from threading import Thread


MAX_THREAD = 40

checker = ProxyChecker()


# Define proxy queue
global queues_proxy

queues_proxy = queue.Queue()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log_file.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Init redis
r = redis.Redis(host='localhost', port=6379, db=10)

# Set data path proxy
csv_file = './proxy_data.csv'


# Check proxy is live
def is_live(ip):
    try:
        response = os.popen(f"ping {ip} -c 1").read()

    except Exception as e:
        logger.error(f"Can not ping to {ip} because {e}")
        return False
    
    if "0% packet loss" in response:
        return True
    
    return False



# @repeat(every(1).minutes,csv_file,r)
def get_proxy(csv_file):

    data = pd.read_csv(csv_file)

    for i in range(1, len(data)):

        # Get api data
        proxy_api = data['url']
        url = proxy_api[i]
        logger.info(url)

        # Get protocol
        protocol = data['protocol'][i]

        # Get type
        type = str(data['type'][i]).lower()

        # Check connection to api 
        try:
            result = requests.get(url, timeout=10)
            if result.status_code != 200:
                continue

        except Exception as e:
            logger.error(e)
            continue
        
        if type == 'text':
            
            contents = result.content.decode('utf-8').splitlines()
            if len(contents) == 1:

                for i in range(20):
                    time.sleep(0.5)
                    try:
                        result = requests.get(url, timeout=10)
                        if result.status_code != 200:
                            continue

                    except Exception as e:
                        logger.error(e)
                        continue
                    
                    # Check connection to api 
                    try:
                        result = requests.get(url, timeout=10)
                        if result.status_code != 200:
                            continue

                        _contents = result.content.decode('utf-8').splitlines()
                        contents += _contents

                    except Exception as e:
                        logger.error(e)
                        continue

            # Get content
            for content in contents:

                logger.info(content)
                _data = content.split(':')
                if len(_data) != 2:
                    logger.warn("Data format not True!")
                    continue
                data_proxy = str(content) + ':' + str(protocol)
                queues_proxy.put(data_proxy)
        elif type == 'json':
            continue

        continue

                
def check_proxy(r):
    # TEST proxy is live
    while not queues_proxy.empty():
    
        proxy = queues_proxy.get()

        logger.info(f"Start check proxy {proxy}")

        data = proxy.split(':')
        if len(data) != 3:
            continue

        ip = data[0]
        port = data[1]
        protocol = data[2]
        _proxy = ip + ':' + port

        try:
            data = checker.check_proxy(_proxy)
            # check_live = is_live(ip)
            # if not check_live:
            #     continue

        except Exception as e:
            logger.error(e)
            continue

        if not data:
            logger.info(f"Proxy fail {proxy}")
            continue

        # Get protocol
        try:
            protocol = data['protocols'][0]
            # logger.info(protocol)
        except Exception as e:
            logger.error(e)
            continue

        json_data = {
            "ip": ip,
            "port": port,
            "protocol": protocol
        }

        logger.info(json_data)

        try:
            # Check key already
            if r.exists(str(proxy)):
                continue
        
            r.set(str(proxy), str(json_data))

        except Exception as e:
            logger.error(e)
            continue

        continue
    logger.info("NO proxy found to check!")
    return True
                
            
                    
if __name__ == "__main__":

    # Define Queue
    data_queue = queue.Queue()
    thread = dict()


    while True:
        queue_thread = Thread(target=get_proxy, args=(csv_file,))
        queue_thread.daemon = True
        queue_thread.start()
        time.sleep(20)

        for idx in range(int(MAX_THREAD)):
            try:
                thread[f'thread_{idx}'] = Thread(target=check_proxy, args=(r,))
                thread[f'thread_{idx}'].daemon = True
                thread[f'thread_{idx}'].start()
            except Exception as e:
                logger.error(e)
                continue

        for idx in range(len(thread)):
            try:
                thread[f'thread_{idx}'].join(timeout=30)
            except Exception as e:
                logger.error(e)
        queue_thread.join()
        logger.info("Finish!")
