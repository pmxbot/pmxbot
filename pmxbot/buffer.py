from __future__ import absolute_import

import logging

import irc.buffer

log = logging.getLogger(__name__)

class ErrorReportingBuffer(irc.buffer.LineBuffer):
	encoding = 'utf-8'

	def lines(self):
		lines = super(ErrorReportingBuffer, self).lines()
		for line in lines:
			try:
				yield line.decode(self.encoding)
			except UnicodeDecodeError:
				log.error("Unable to decode line: {line!r}".format(line=line))

	@classmethod
	def install(cls):
		irc.client.ServerConnection.buffer_class = cls
