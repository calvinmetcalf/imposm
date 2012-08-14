# Copyright 2012 Omniscale (http://omniscale.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import platform
import itertools


import multiprocessing.process
import multiprocessing.queues
from multiprocessing.queues import Full

def patch_multiprocessing():
    if platform.python_version_tuple() < ('2', '6', '3'):
        print 'Patching multiprocessing.'
        multiprocessing.process.Process._bootstrap = process__bootstrap
        multiprocessing.queues.JoinableQueue.put = joinable_queue_put


# The following two methods are part of Python.
# Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009 Python
# Software Foundation; All Rights Reserved

# http://bugs.python.org/issue5313
# http://hg.python.org/cpython/rev/70adf0f68fbc/
def process__bootstrap(self):
    from multiprocessing import util
    global _current_process
    try:
        self._children = set()
        self._counter = itertools.count(1)
        try:
            sys.stdin.close()
            sys.stdin = open(os.devnull)
        except (OSError, ValueError):
            pass
        _current_process = self
        util._finalizer_registry.clear()
        util._run_after_forkers()
        util.info('child process calling self.run()')
        try:
            self.run()
            exitcode = 0
        finally:
            util._exit_function()
    except SystemExit, e:
        if not e.args:
            exitcode = 1
        elif type(e.args[0]) is int:
            exitcode = e.args[0]
        else:
            sys.stderr.write(e.args[0] + '\n')
            sys.stderr.flush()
            exitcode = 1
    except:
        exitcode = 1
        import traceback
        sys.stderr.write('Process %s:\n' % self.name)
        sys.stderr.flush()
        traceback.print_exc()
    util.info('process exiting with exitcode %d' % exitcode)
    return exitcode


# http://bugs.python.org/issue4660
# http://hg.python.org/cpython/rev/65d1682dcd5e/
def joinable_queue_put(self, obj, block=True, timeout=None):
    assert not self._closed
    if not self._sem.acquire(block, timeout):
        raise Full
    self._notempty.acquire()
    self._cond.acquire()
    try:
        if self._thread is None:
            self._start_thread()
        self._buffer.append(obj)
        self._unfinished_tasks.release()
        self._notempty.notify()
    finally:
        self._cond.release()
        self._notempty.release()