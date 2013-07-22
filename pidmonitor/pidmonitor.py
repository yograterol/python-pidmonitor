"""
Copyright (c) 2013 Yohan Graterol <yograterol@fedoraproject.org>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. Neither the name of copyright holders nor the names of its
   contributors may be used to endorse or promote products derived
   from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
''AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL COPYRIGHT HOLDERS OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
from ctrldaemon import ControlDaemon
from threading import Thread
from ConfigParser import RawConfigParser
from os import path
from logging import (getLogger, FileHandler, Formatter, WARNING)
from time import sleep
global options
options = ['memory_max', 'virt_max']


class PidMonitor(object):

    __slots__ = ['config_dict', 'thread_pid']

    def __init__(self):
        self.get_config()
        self.thread_pid = None

    def get_config(self):
        config = PidMonitorConfig()
        if config.exist_file_config():
            self.config_dict = config.read_config()

    def activate_thread(self):
        if not self.thread_pid:
            self.thread_pid = PidMonitorThread(self.config_dict)
            self.thread_pid.setDaemon(True)
            self.thread_pid.run()


class PidMonitorThread(Thread):

    __slots__ = ['ctrl_daemon', 'services', 'logger']
    ctrl_daemon = list()

    def __init__(self, services):
        super(PidMonitorThread, self).__init__()
        self.services = services
        self.logger = PidMonitorLog()
        self.init_control_daemon()

    def init_control_daemon(self):
        for service in self.services.keys():
            self.ctrl_daemon.append(ControlDaemon(service))

    def run(self):
        while True:
            for daemon in self.ctrl_daemon:
                self.check_service(daemon)
            sleep(60)

    def check_service(self, daemon):
        if daemon.get_status():
            memory_usage = daemon.get_memory_usage()
            print memory_usage
            memory_max = self.services[str(daemon)][options[0]]
            print memory_max
            #memory_virt = self.services[str(daemon)][options[1]]
            if memory_usage > memory_max:
                daemon.restart()
                if daemon.get_status():
                    self.logger.set_msg('INFO', daemon, 'Restarted')
                else:
                    self.logger.set_msg('ERROR', daemon, 'Don\'t restarted')


class PidMonitorConfig(object):

    __slots__ = ['config', 'path_config', 'options']

    def __init__(self, path_config=None):
        if not path_config:
            self.path_config = '/etc/pidmonitor.cfg'
        self.config = RawConfigParser()

    def exist_file_config(self):
        return path.isfile(self.path_config)

    def read_config(self):
        self.config.read(self.path_config)
        tmp_config = dict()
        for section in self.config.sections():
            tmp_options = dict()
            for option in options:
                print section, option
                tmp_options[option] = self.config.getint(str(section),
                                                         str(option))
            tmp_config[section] = tmp_options
        return tmp_config


class PidMonitorLog(object):

    __slots__ = ['logger', 'handler']

    def __init__(self):
        self.logger = getLogger('PidMonitor')
        self.handler = FileHandler('/var/log/pidmonitor.log')
        formatter = Formatter('%(asctime)s %(levelname)s %(message)s')
        self.handler.setFormatter(formatter)
        self.logger.addHandler(self.handler)
        self.logger.setLevel(WARNING)
        self.logger.info('Init Program')

    def set_msg(self, type_msg, daemon_name, msg):
        text = '{} - {}'.format(daemon_name, msg)
        if type_msg == 'ERROR':
            self.logger.error(text)
        elif type_msg == 'INFO':
            self.logger.info(text)
        else:
            pass

