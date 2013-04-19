import logging

from link import Link

class Host:
	"""Represents an endpoint on the Internet.
	Currently, a Host may have exactly one IP address.
	"""

	def __init__(self, ip):
		"""Construct a host with the given ip address."""
		self.ip = ip
		self.routing = {}        #ip address to link
		Link(self, self, 1e-6, 1e9) #loopback

	def __log(self, fmt, *args, **kwargs):
		level = kwargs.get('level', logging.INFO)
		logging.getLogger(__name__).log(level, 'host %s '+fmt, self.ip, *args)

	def sched_send(self, packet):
		"""Send packet."""
		try:
			link = self.routing[packet.dest]
		except KeyError:
			self.__log('no entry for %s', packet.dest, level=logging.WARNING)
		else:
			self.__log('send-packet %s', packet.dest)
			link.enqueue(packet)

	def received(self, packet):
		"""Called (by Link) to deliver a packet to this Host."""
		if packet.dest != self.ip:
			self.__log('received packet for %s', packet.dest, level=logging.WARNING)
		self.__log('recv-packet %s', packet.origin)
