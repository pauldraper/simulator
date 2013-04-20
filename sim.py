import collections
import itertools
import logging
import sched

import greenlet

class Simulator:
	"""Simulates a multi-threaded environment."""
	
	def __init__(self):
		"""Creates a new Simulator, starting at time 0."""
		self.__time = 0
		self.__thread_id_counter = itertools.count()
		self.__thread_ids = {}
		def delay(units):
			self.__time += units
		self._scheduler = sched.scheduler(self.time, delay)
		self._edt = greenlet.greenlet(self._scheduler.run)
	
	def _log(self, t, fmt, *args, **kwargs):
		level = kwargs.get('level', logging.DEBUG)
		logging.getLogger(__name__).log(level, 'thread %d '+fmt, self.__thread_ids[t], *args, **kwargs)
	
	def time(self):
		"""Return the current simulated time."""
		return self.__time
		
	def new_thread(self, f):
		"""Add a new thread."""
		t = greenlet.greenlet(f)
		self.__thread_ids[t] = next(self.__thread_id_counter) 
		self._log(t, 'created from %s', f)
		t.switch()
	
	def sleep(self, timeout):
		"""Put the current thread to sleep for an amount of time."""
		t = greenlet.getcurrent()
		self._log(t, 'sleeping for %f', timeout)
		def resume():
			t.parent = self._edt
			self._log(t, 'waking up')
			t.switch()
		self._scheduler.enter(timeout, 1, resume, ())
		t.parent.switch()
	
	def run(self):
		"""Run the simulation to completion."""
		self._edt.switch()

sim = Simulator() # singleton

class TimeoutException(Exception):
	"""Thrown when a call to wait() times out."""
	pass

class Event:
	"""The equivalent of a condition variable."""
	
	def __init__(self, sim=sim):
		"""Create an Event."""
		self.__sim = sim
		self.__waiting = set()
		self.__timeouts = set()
		
	def __str__(self):
		return 'event_{:x}'.format(id(self))
	
	def wait(self, timeout=None):
		"""Cause the current thread to wait on this Event.
		If timeout is specified and notify() is not called within the timeout, an
		TimeoutException is raised."""
		t = greenlet.getcurrent()
		self.__sim._log(t, 'waiting on %s', self)
		self.__waiting.add(t)
		if timeout is not None:
			def watchdog():
				if watchdog in self.__timeouts:
					self.__timeouts.remove(watchdog)
					self.__waiting.remove(t)
					self.__sim._log(t, 'waking up due to timeout on %s', self)
					t.parent = self.__sim._edt
					t.throw(TimeoutException(self))
			self.__timeouts.add(watchdog)
			self.__sim._scheduler.enter(timeout, 1, watchdog, ())
		return t.parent.switch()
	
	def notify(self, *args, **kwargs):
		"""Wake up any threads waiting on this Event."""
		t = greenlet.getcurrent()
		self.__sim._log(t, 'notifying %s', self)
		waiting, self.__waiting = self.__waiting, set()
		self.__timeouts.clear()
		for other_t in waiting:
			self.__sim._log(other_t, 'released by %s', self)
			other_t.parent = t
			other_t.switch(*args, **kwargs)

class Semaphore:
	
	def __init__(self, count=0, sim=sim):
		self._count = count
		self.__sim = sim
		self.__events = collections.deque()

	def post(self):
		self._count += 1
		if self._count > 0 and self.__events:
			self.__events.pop().notify()

	def wait(self, timeout=None):
		self._count -= 1
		if self._count > 0:
			event = Event(self.__sim)
			self.__events.appendleft(event)
			event.wait(timeout)

class Mutex:
	
	def __init__(self, sim=sim):
		self.__semaphore = Semaphore(count=1, sim=sim)
		
	def lock(self, timeout=None):
		self.__semaphore.wait(timeout)
		
	def unlock(self):
		if not self.__semaphore._count:
			self.__semaphore.post()
