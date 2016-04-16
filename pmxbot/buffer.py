import logging

from jaraco.stream import buffer
import irc.client

log = logging.getLogger(__name__)


class ErrorReportingBuffer(buffer.LineBuffer):
	encoding = 'utf-8'

	def lines(self):
		lines = super().lines()
		for line in lines:
			try:
				yield line.decode(self.encoding)
			except UnicodeDecodeError:
				log.error("Unable to decode line: {line!r}".format(line=line))

	@classmethod
	def install(cls):
		irc.client.ServerConnection.buffer_class = cls
