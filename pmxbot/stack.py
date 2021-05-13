"""!stack, a pmxbot command for managing short lists.

Example
-------

!stack
    (empty)
!stack add drop partitions
!stack
    1: drop partitions
!stack add fix up join diagrams
!stack
    1: fix up join diagrams | 2: drop partitions
!stack add [-1] review frank's ticket
!stack
    1: fix up join diagrams | 2: drop partitions | 3: review frank's ticket
!stack pop
    -: fix up join diagrams
!stack
    1: drop partitions | 2: review frank's ticket
!stack pop [-1]
    -: review frank's ticket
!stack
    1: drop partitions
!stack pop [:]
    -: drop partitions
!stack
    (empty)

Topic and Index Parameters
--------------------------

Topic and index parameters are specified immediately after the !stack
subcommand, and take the form: `topic[index]`; for example, "meetup[3]".
The square brackets must always be included, even if no index is given.
For example, "meetup[]" identifies the "meetup" topic but gives no index
parameter--what that means depends on the subcommand. Similarly, you can
specify "[3]" to give an index with no topic.

If no topic is given, the user's nick is used as the topic.
This allows the most common use as a personal stack of work items.

The items in each topic are organized as a stack. Each item in the stack
has an index number; the top-most item is 1 and the bottom-most item is
always the length of the stack. With some restrictions depending on the
command, an "index" argument may be any of the following:

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
    * The sentinel values first and last.
    * Any combination of the above, separated by commas; for example,
      given a stack of items "1: red | 2: orange | 3: yellow | 4: green |
      5: blue | 6: indigo | 7: violet", the index `[6, :2, "i"]` identifies
      "6: indigo | 1: red | 2: orange | 7: violet".
      Note that "indigo" matches both `[6]` and `["i"]`, but is only included
      once. However, if the stack had another "8: indigo" entry, it would have
      been included.

Subcommands
-----------

!stack show        topic[index]
    Returns the list of items for the given topic.

!stack add         topic[index] <item>
    Adds the given item to the given topic before the given index(es).
    If no index is given, the default is [1] which adds to the front.
    Any index higher than the number of items adds to the end of the stack.

!stack pop         topic[index] <item>
    Removes items from the given topic at the given index(es).

    If index is omitted, it defaults to `[1]`.

!stack shuffle topic[index]
    Reorders the given topic.

    If the `index` argument is omitted, the topic is shuffled in random order.
    Otherwise, it must be a valid index and the topic is reordered to match.
    For example, with stack "1: a | 2: b | 3: c", the command
    `!stack shuffle [3, 1]` reorders the stack to "1: c | 2: a",
    and the "b" item is dropped.

!stack topics [index]
    Return a list of topics, numbered in alphabetical order.
"""

import random
import re
import itertools
import os

from . import storage
from .core import command


flatten = itertools.chain.from_iterable


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

    def get_topics(self):
        rows = self.db.execute("SELECT topic FROM stack")
        return [row[0] for row in rows]

    def get_items(self, topic):
        rows = self.db.execute(
            "SELECT items FROM stack WHERE topic = ?", [topic]
        ).fetchone()
        if not rows:
            return []
        else:
            return rows[0].split("\n")

    def save_items(self, topic, items):
        items = "\n".join(items)
        has_entry = self.db.execute(
            "SELECT items FROM stack WHERE topic = ?", [topic]
        ).fetchone()
        if has_entry:
            if items:
                return self.db.execute(
                    "UPDATE stack SET items = ? WHERE topic = ?", [items, topic]
                )
            else:
                return self.db.execute("DELETE FROM stack WHERE topic = ?", [topic])
        else:
            return self.db.execute(
                "INSERT INTO stack (topic, items) VALUES (?, ?)", [topic, items]
            )


class MongoDBStack(Stack, storage.MongoDBStorage):
    collection_name = 'stack'

    def get_topics(self):
        docs = self.db.find({}, {'topic': True})
        return [doc['topic'] for doc in docs]

    def get_items(self, topic):
        doc = self.db.find_one({'topic': topic})
        if doc is None:
            return []
        else:
            return doc["items"]

    def save_items(self, topic, items):
        if items:
            return self.db.update_one(
                {"topic": topic}, {"$set": {"items": items}}, upsert=True
            )
        else:
            return self.db.delete_one({"topic": topic})


helpdoc = dict(
    stack='!stack <subcommand> <topic[index]> <item> '
    '| subcommand: add, pop, show, shuffle, topics, list, help '
    '| index: [2, 4:-3 (inclusive), "foo", /ba.*r/]',
    help="!stack help <show, add, pop, shuffle, help, stack, index>"
    ": Show help for the given subcommand or feature (default: help)",
    add="!stack add <topic[index]> item: Add the given item to the "
    "given topic before the given (1-based) index (default: 1)",
    pop="!stack pop <topic[index]>: Pop any items from the given topic "
    "at the given (1-based) index(es) (default: 1)",
    show="!stack show <topic[index]>: Show items from the "
    "given topic at the given (1-based) indexes (default: all)",
    shuffle="!stack shuffle <topic[index]>: Shuffle items from the given "
    "topic into the the given (1-based) index order "
    "(default: random)",
    topics="!stack topics <[index]>: Show topic names, numbered in "
    "alphabetical order.",
    index='!stack indexes must be integers `[2]`, start:end slices '
    '(inclusive) `[4:-3]`, `"text"` or a `/regex/` to match, '
    '`first` or `last`, or any combination of those '
    'separated by commas.',
)

helpdoc['list'] = helpdoc['topics']


def parse_index(index, items):
    """Return a list of 0-based index numbers from a (1-based) `index` str.

    * A single item index, like `[3]`. Negative indices count backward from
      the bottom; that is, the bottom-most item in a 3-item stack can be
      identified by `[3]` or `[-1]`.
    * A slice, shorthand for the entire inclusive range between two numbers,
      like `[3:5]`. Either number may be negative, or omitted to mean 1 or -1,
      respectively. If both are omitted as `[:]` then all items match.
    * Any "text" surrounded by single or double-quotes, which matches any
      item containing the text (case-insensitive).
    * Any /text/ surrounded by forward-slashes, a regular expression
      to match item content.
    * The values "first" or "last" (without quotes).
    * Any combination of the above, separated by commas; for example,
      given a stack of items "1: red | 2: orange | 3: yellow | 4: green |
      5: blue | 6: indigo | 7: violet", the index `[6, :2, "i"]` identifies
      "6: indigo | 1: red | 2: orange | 7: violet". Note that "indigo"
      matches both `[6]` and `["i"]`, but is only included once. However,
      if the stack had another "8: indigo" entry, it would have been included.

    """
    if index is None:
        index = ""

    atoms = filter(None, (atom.strip() for atom in index.split(",")))
    return list(flatten(_parse_atom(atom, items) for atom in atoms))


def _parse_atom(atom, items):
    if (atom.startswith("'") and atom.endswith("'")) or (
        atom.startswith('"') and atom.endswith('"')
    ):
        yield from _parse_atom_substring(atom[1:-1].lower(), items)
    elif atom.startswith('/') and atom.endswith('/'):
        yield from _parse_atom_pattern(atom[1:-1], items)
    elif ":" in atom:
        yield from _parse_atom_range(atom, items)
    elif atom == "first":
        yield 0
    elif atom == "last":
        yield len(items) - 1
    else:
        index = int(atom)
        if index < 0:
            index += len(items) + 1
        # Shift to Python 0-based indices
        yield index - 1


def _parse_atom_substring(substring, items):
    return (index for index, item in enumerate(items) if substring in item.lower())


def _parse_atom_pattern(pattern, items):
    return (index for index, item in enumerate(items) if re.search(pattern, item))


def _parse_atom_range(range_str, items):
    start, end = (x.strip() for x in range_str.split(":", 1))
    start = int(start) if start else 1
    if start < 0:
        start += len(items) + 1
    end = int(end) if end else len(items)
    if end < 0:
        end += len(items) + 1
    start -= 1  # Shift to Python 0-based indices
    end -= 1  # Shift to Python 0-based indices
    return range(start, end + 1)


def output(indexed_items, default="(empty)", pop=False):
    output = ["%s: %s" % (i, item) for i, item in indexed_items]
    joined_output = " | ".join(output)
    if len(joined_output) > 100:
        joined_output = "\n".join(output)
    return joined_output or default


def _items_for_command(cmd, topic):
    topics = cmd in 'topics list'.split()
    return sorted(Stack.store.get_topics()) if topics else Stack.store.get_items(topic)


@command()
def stack(nick, rest):
    'Manage short lists in pmxbot. See !stack help for more info'
    subcommand, params = _parse_stack_command(rest)

    index, new_item, topic = _parse_params(params, default_topic=nick)

    items = _items_for_command(subcommand, topic)

    try:
        indices = parse_index(index, items)
    except ValueError:
        return helpdoc["index"]

    _debug(subcommand, topic, indices, new_item)

    handler = globals().get(f'_handle_{subcommand}', _handle_other)
    return handler(new_item, indices, items, topic)


def _handle_add(new_item, indices, items, topic):
    if not new_item:
        return '!stack add <topic[index]> item: ' 'You must provide an item to add.'

    if not indices:
        items.insert(0, new_item)
    else:
        for i in reversed(sorted(set(indices))):
            if i >= len(items):
                items.append(new_item)
            else:
                items.insert(i + 1, new_item)

    Stack.store.save_items(topic, items)


def _handle_pop(new_item, indices, items, topic):
    if not indices:
        indices = [0]

    popped_items = [
        items.pop(i) for i in reversed(sorted(set(indices))) if len(items) > i >= 0
    ]

    Stack.store.save_items(topic, items)

    return output(
        [("-", item) for item in reversed(popped_items)], "(none popped)", pop=True
    )


def _handle_show(new_item, indices, items, topic):
    if new_item:
        return helpdoc["show"]

    if not indices:
        indices = range(len(items))

    return output([(i + 1, items[i]) for i in indices if len(items) > i >= 0])


def _handle_shuffle(new_item, indices, items, topic):
    if not indices:
        random.shuffle(items)
    else:
        items = [items[i] for i in indices if len(items) > i >= 0]

    Stack.store.save_items(topic, items)

    return output(enumerate(items, 1))


def _handle_topics(new_item, indices, items, topic):
    if new_item:
        return helpdoc["topics"]

    if not indices:
        indices = range(len(items))

    return output([(i + 1, items[i]) for i in indices if len(items) > i >= 0])


_handle_list = _handle_topics


def _handle_help(new_item, indices, items, topic):
    return helpdoc.get(new_item, helpdoc["help"])


def _handle_other(new_item, indices, items, topic):
    return helpdoc["stack"]


def _parse_params(params, default_topic):
    start = params.find("[")
    finish = params.rfind("]")
    sp = params.find(" ")
    if start != -1 and finish != -1 and start < finish and (sp == -1 or start < sp):
        topic, index = [atom.strip() for atom in params[:finish].split("[", 1)]
        if not topic:
            topic = default_topic
        new_item = params[finish + 1 :].strip()
    else:
        topic = default_topic
        index = None
        new_item = params.strip()
    return index, new_item, topic


def _parse_stack_command(text):
    atoms = [atom.strip() for atom in text.split(' ', 1) if atom.strip()]
    if len(atoms) == 0:
        subcommand = "show"
        rest = ""
    elif len(atoms) == 1:
        subcommand = atoms[0]
        rest = ""
    else:
        subcommand, rest = atoms
    return subcommand, rest


def _debug(subcommand, topic, indices, new_item):
    if not os.environ.get('PMXBOT_STACK_DEBUG'):
        return

    print(
        "SUBCOMMAND",
        subcommand.ljust(8),
        "TOPIC",
        topic.ljust(8),
        "INDICES",
        str(indices).ljust(12),
        "ITEM",
        new_item,
    )
