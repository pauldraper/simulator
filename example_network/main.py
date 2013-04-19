import random
import string
import logging

from host import Host
from link import Link, Packet
from sim import sim

class RandomSender:
	"""A client for sending randomly generated messages."""

	def __init__(self, host):
		"""Create a RandomSender."""
		self.host = host
		
	def send(self, dest, message_len, rate, duration):
		"""Sends random messages for the specified duration."""
		stop_time = sim.time() + duration
		sim.sleep(random.expovariate(rate))
		while stop_time > sim.time():
			message = ''.join(random.choice(string.letters) for _ in xrange(message_len))
			self.host.sched_send(Packet(self.host.ip, dest, message))
			sim.sleep(random.expovariate(rate))

def run_random(latency, bandwidth, usage, packet_len, duration):
	# set up network
	host1 = Host('123.0.0.0')
	host2 = Host('101.0.0.0')
	Link(host1, host2, prop_delay=latency, bandwidth=bandwidth)

	# set up network use events
	client = RandomSender(host=host1)
	rate = usage * bandwidth / packet_len
	sim.new_thread(
		lambda: client.send(dest=host2.ip, rate=rate, duration=duration, message_len=packet_len)
	)
	
	#run
	sim.run()

def configure_logging(level):
	import sys
	logging.basicConfig(stream=sys.stdout, level=level)
	class Formatter(logging.Formatter):
		def format(self, record):
			if record.levelno == logging.DEBUG:
				self._fmt = '%(name)s - %(message)s'
			else:
				record.time = sim.time()
				self._fmt = '%(time)7.4f %(message)s'
			return super(Formatter, self).format(record)
	logging.getLogger().handlers[0].setFormatter(Formatter())
	#logging.getLogger(network.link.__name__).propagate = False
	#logging.getLogger(network.host.__name__).propogate = False

if __name__ == '__main__':
	"""Main method."""
	def parse_args():
		import argparse
		parser = argparse.ArgumentParser()
		parser.add_argument('--bandwidth', default=0.5e6, type=float)
		parser.add_argument('--duration', default=2.0, type=float)
		parser.add_argument('--latency', default=0.150, type=float)
		parser.add_argument('--packet-len', default=1500, type=int)
		parser.add_argument('--usage', default=.75, type=float)
		parser.add_argument(
				'--level',
				default=logging.getLevelName(logging.INFO),
				choices=logging._levelNames.values()
		)
		return parser.parse_args()
	args = parse_args()
	
	configure_logging(args.level)
	
	run_random(
		latency=args.latency,
		bandwidth=args.bandwidth,
		usage=args.usage,
		packet_len=args.packet_len,
		duration=args.duration
	)
