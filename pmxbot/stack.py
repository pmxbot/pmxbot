"""!stack, a crunchbot command for managing short lists.

Extended Example
----------------

!stack
    (empty)
!stack add drop partitions
!stack
    1: drop partitions
!stack add fix up join diagrams
!stack
    1: fix up join diagrams
    2: drop partitions
!stack add review frank's ticket
!stack
    1: review frank's ticket
    2: fix up join diagrams
    3: drop partitions
!stack add [-1] crunchbot stack command
!stack
    1: review frank's ticket
    2: fix up join diagrams
    3: drop partitions
    4: crunchbot stack command
!stack add [2] review kim's ticket
!stack
    1: review frank's ticket
    2: review kim's ticket
    3: fix up join diagrams
    4: drop partitions
    5: crunchbot stack command
!stack pop
    -: review frank's ticket
!stack
    1: review kim's ticket
    2: fix up join diagrams
    3: drop partitions
    4: crunchbot stack command
!stack pop [-1]
    -: crunchbot stack command
!stack
    1: review kim's ticket
    2: fix up join diagrams
    3: drop partitions
!stack pop [:]
    -: drop partitions
    -: fix up join diagrams
    -: review kim's ticket
!stack
    (empty)

Topic and Index Parameters
--------------------------

Topic and index parameters are specified immediately after the !stack subcommand,
and take the form: `topic[index]`; for example, "meetup[3]". The square brackets
must always be included, even if no index is given. For example, "meetup[]"
identifies the "meetup" topic but gives no index parameter--what that means
depends on the subcommand. Similarly, you can specify "[3]" to give an index
with no topic.

If no topic is given, the user's nick is used as the topic.
This allows the most common use as a personal stack of work items.

The items in each topic are organized as a stack. Each item in the stack has
an index number; the top-most item is 1 and the bottom-most item is always
the length of the stack. With some restrictions depending on the command,
an "index" argument may be any of the following:

    * A single item index, like `[3]`. Negative indices count backward from
      the bottom; that is, the bottom-most item in a 3-item stack can be
      identified by `[3]` or `[-1]`.
    * A slice, shorthand for the entire inclusive range between two numbers,
      like `[3:5]`. Either number may be negative, or omitted to mean 1 or -1,
      respectively. If both are omitted as `[:]` then all items match.
    * Any "text" surrounded by single or double-quotes, which matches any
      item containing the text.
    * Any /text/ surrounded by forward-slashes, a regular expression
      to match item content.
    * Any combination of the above, separated by commas; for example,
      given a stack of items
      "1: red | 2: orange | 3: yellow | 4: green | 5: blue | 6: indigo | 7: violet",
      the index `[6, :2, "i"]` identifies "6: indigo | 1: red | 2: orange | 7: violet".
      Note that "indigo" matches both `[6]` and `["i"]`, but is only included
      once. However, if the stack had another "8: indigo" entry, it would have
      been included.

Subcommands
-----------

!stack add         topic[index] <item>
    Adds the given item to the given topic at the given index(es).

!stack pop         topic[index] <item>
    Removes items from the given topic at the given index(es).

    If index is omitted, it defaults to `[1]`.

!stack shuffle topic[index]
    Reorders the given topic.

    If the `index` argument is omitted, the topic is shuffled in random order.
    Otherwise, it must be a valid index and the topic is reordered to match.
    For example, with stack "1: a | 2: b | 3: c", the command `!stack shuffle [3, 1]`
    reorders the stack to "1: c | 2: a", and the "b" item is dropped.

"""

from . import storage
from .core import command


class Stack(storage.SelectableStorage):
    @classmethod
    def init(cls):
        cls.store = cls.from_URI()
        cls._finalizers.append(cls.finalize)

    @classmethod
    def finalize(cls):
        del cls.store


class SQLiteStack(Stack, storage.SQLiteStorage):
    def init_tables(self):
        CREATE_STACK_TABLE = '''
            CREATE TABLE
            IF NOT EXISTS stack
            (
                topic VARCHAR NOT NULL,
                items VARCHAR NOT NULL,
                primary key(topic)
            )
        '''
        self.db.execute(CREATE_STACK_TABLE)
        self.db.commit()

    def get_items(self, topic):
        rows = self.db.execute("SELECT items FROM stack WHERE topic = ?", [topic])
        if not rows:
            return None
        else:
            return rows[0][0]

    def save_items(self, topic, items):
        if self.get_items(topic) is None:
            return self.db.execute(
                "INSERT INTO stack (topic, items) VALUES (?, ?)", [topic, items])
        else:
            return self.db.execute(
                "UPDATE stack SET items = ? WHERE topic = ?", [items, topic])


class MongoDBStack(Stack, storage.MongoDBStorage):
    collection_name = 'stack'

    def get_items(self, topic):
        rows = [doc["items"] for doc in self.db.find({'topic': topic})]
        if not rows:
            return None
        else:
            return rows[0]

    def save_items(self, topic, items):
        if self.get_items(topic) is None:
            return self.db.insert({"topic": topic, "items": items})
        else:
            return self.db.update({"topic": topic}, {"items": items})


helpstr = '!stack <subcommand> <topic[index]> <item> | subcommand: show, add, pop, shuffle | index: [2, 4:-3 (inclusive), "foo", /ba.*r/]'


def parse_index(index):
    """Parse the given string `index` param and return an ordered list of index numbers.

    * A single item index, like `[3]`. Negative indices count backward from
      the bottom; that is, the bottom-most item in a 3-item stack can be
      identified by `[3]` or `[-1]`.
    * A slice, shorthand for the entire inclusive range between two numbers,
      like `[3:5]`. Either number may be negative, or omitted to mean 1 or -1,
      respectively. If both are omitted as `[:]` then all items match.
    * Any "text" surrounded by single or double-quotes, which matches any
      item containing the text.
    * Any /text/ surrounded by forward-slashes, a regular expression
      to match item content.
    * Any combination of the above, separated by commas; for example,
      given a stack of items
      "1: red | 2: orange | 3: yellow | 4: green | 5: blue | 6: indigo | 7: violet",
      the index `[6, :2, "i"]` identifies "6: indigo | 1: red | 2: orange | 7: violet".
      Note that "indigo" matches both `[6]` and `["i"]`, but is only included
      once. However, if the stack had another "8: indigo" entry, it would have
      been included.

    """


@command()
def stack(nick, rest):
    if not rest:
        subcommand = "show"
    else:
        try:
            subcommand, rest = [atom.strip() for atom in rest.split(' ', 1)]
        except ValueError:
            subcommand = "show"

    start = rest.find("[")
    finish = rest.find("]")
    sp = rest.find(" ")
    if start != -1 and finish != -1 and start < sp and start < finish:
        topic, index = [atom.strip() for atom in rest[:finish].split("[", 1)]
        new_item = rest[finish:].strip()
    else:
        topic = nick
        index = None
        new_item = rest.strip()

    if subcommand == "add":
        if not new_item:
            return helpstr

        items = (Stack.store.get_items(topic) or "").split("\n")

        if index is None:
            items.insert(0, new_item)
        else:
            indices = parse_index(index, items)
            for i in reversed(indices):
                items.insert(i, new_item)

        Stack.store.save_items(topic, items)
    elif subcommand == "pop":
        items = (Stack.store.get_items(topic) or "").split("\n")

        popped_items = []
        if index is None:
            p = items.pop(0, None)
            if p is not None:
                popped_items.append(p)
        else:
            indices = parse_index(index, items)
            for i in reversed(indices):
                popped_items.append(items.pop(i))

        return " | ".join(["-: %s" % (item,) for item in popped_items]) or "(none popped)"
    elif subcommand == "show" and not rest:
        items = (Stack.store.get_items(topic) or "").split("\n")
        return " | ".join(["%d: %s" % (i, item) for i, item in enumerate(items)]) or "(empty)"
    elif subcommand == "shuffle":
        choke
    else:
        return helpstr


# -------------------- Unit Tests ----------------------- #

import unittest


class DummyStorage():

    def __init__(self):
        self.table = {}

    def get_items(self, topic):
        return self.table.get(topic, None)

    def save_items(self, topic, items):
        self.table.setdefault(topic, items)


class TestStackCommand(unittest.TestCase):

    def test_stack_add(self):
        self.assertEqual(stack("fumanchu", "add foo"), None)
        self.assertEqual(stack("fumanchu", ""), "1: foo")
