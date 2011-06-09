from pmxbot import logging
mlog = logging.Logger.from_URI('mongodb://localhost')
slog = logging.Logger.from_URI('sqlite:pmxbot.sqlite')
for msg_pair in zip(mlog.all_messages(), slog.export_all()):
	mmsg, smsg = msg_pair
	if mmsg['message'] != smsg['message']: break

