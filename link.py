from __future__ import division
from collections import deque
import itertools
import logging

from sim import sim

class Packet:
	"""Represents a network packet."""
	
	id_counter = itertools.count()

	def __init__(self, origin, dest, message):
		"""Create a Packet."""
		self.id = next(Packet.id_counter)
		self.origin = origin
		self.dest = dest
		self.message = message

	@property
	def size(self):
		"""Return the size, in bytes."""
		return len(self.message) if self.message else 0

class BlockingQueue:
	"""Blocking queue."""
	
	def __init__(self):
		self.__queue = deque()
		self.__enqueue_event = sim.new_event()
	
	def enqueue(self, item):
		self.__queue.appendleft(item)
		self.__enqueue_event.notify()
		
	def poll(self):
		if not self.__queue:
			self.__enqueue_event.wait()
		return self.__queue.pop()
			
class Link:
	"""Represents a unidirectional link."""

	def __init__(self, source, dest, prop_delay, bandwidth):
		"""Creates a Link between the specified Hosts.
		This also registers the Link with the source."""
		self.source = source
		self.dest = dest
		self.__queue = BlockingQueue()
		source.routing[dest.ip] = self
		
		def process_queue():
			while True:
				packet = self.__queue.poll()
				self.__log('queue-end %d', packet.id)
				
				self.__log('transmit-start %d', packet.id)
				sim.sleep(packet.size / bandwidth)
				self.__log('transmit-end %d', packet.id)
				
				def propogate(packet=packet):
					self.__log('propogate-start %d', packet.id)
					sim.sleep(prop_delay)
					self.__log('propogate-end %d', packet.id)
					self.dest.received(packet)
				sim.new_thread(propogate)

		sim.new_thread(process_queue)
	
	def __log(self, fmt, *args):
		logging.getLogger(__name__).info('link %s->%s '+fmt, self.source.ip, self.dest.ip, *args)

	def enqueue(self, packet):
		"""Called to place this packet in the queue."""
		self.__log('queue-start %d', packet.id)
		self.__queue.enqueue(packet)
