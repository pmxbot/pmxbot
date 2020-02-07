import pytest
import unittest

from pmxbot.stack import stack, Stack, helpdoc


class DummyStorage:
    def __init__(self, table=None):
        self.table = table or {}

    def get_topics(self):
        return list(self.table.keys())

    def get_items(self, topic):
        return self.table.get(topic, [])

    def save_items(self, topic, items):
        self.table[topic] = items


class StackTestCase(unittest.TestCase):
    def make_colors(self):
        """Set Store.stack to a dummy with ROYGBIV color names as items."""
        Stack.store = DummyStorage(
            {
                "fumanchu": [
                    "red",
                    "orange",
                    "yellow",
                    "green",
                    "blue",
                    "indigo",
                    "violet",
                ]
            }
        )
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: red | 2: orange | 3: yellow | 4: green | "
            "5: blue | 6: indigo | 7: violet",
        )


class TestStackAdd(StackTestCase):
    def test_stack_add(self):
        Stack.store = DummyStorage()
        self.assertEqual(stack("fumanchu", ""), "(empty)")
        stack("fumanchu", "add foo")
        self.assertEqual(stack("fumanchu", ""), "1: foo")
        stack("fumanchu", "add an interruption")
        self.assertEqual(stack("fumanchu", ""), "1: an interruption | 2: foo")
        stack("fumanchu", "add [-1] cleanup")
        self.assertEqual(
            stack("fumanchu", ""), "1: an interruption | 2: foo | 3: cleanup"
        )
        stack("fumanchu", "add [1] a Distraction")
        self.assertEqual(
            stack("fumanchu", ""),
            "1: an interruption | 2: a Distraction | 3: foo | 4: cleanup",
        )
        stack("fumanchu", "add ['distract'] lunch")
        self.assertEqual(
            stack("fumanchu", ""),
            "1: an interruption | 2: a Distraction | 3: lunch | " "4: foo | 5: cleanup",
        )
        stack("fumanchu", "add [0] bar")
        self.assertEqual(
            stack("fumanchu", ""),
            "1: bar | 2: an interruption | 3: a Distraction | 4: lunch | "
            "5: foo | 6: cleanup",
        )

    def test_stack_add_multiple(self):
        Stack.store = DummyStorage()
        self.assertEqual(stack("fumanchu", ""), "(empty)")
        stack("fumanchu", "add foo")
        self.assertEqual(stack("fumanchu", ""), "1: foo")
        stack("fumanchu", "add foo")
        self.assertEqual(stack("fumanchu", ""), "1: foo | 2: foo")
        stack("fumanchu", "add foo")
        self.assertEqual(stack("fumanchu", ""), "1: foo | 2: foo | 3: foo")
        stack("fumanchu", "add ['foo'] bar")
        self.assertEqual(
            stack("fumanchu", ""), "1: foo | 2: bar | 3: foo | 4: bar | 5: foo | 6: bar"
        )


class TestStackPop(StackTestCase):
    def test_stack_pop_no_index(self):
        self.make_colors()
        self.assertEqual(stack("fumanchu", "pop"), "-: red")
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: orange | 2: yellow | 3: green | 4: blue | " "5: indigo | 6: violet",
        )

    def test_stack_pop_integer_index(self):
        self.make_colors()

        self.assertEqual(stack("fumanchu", 'pop [2]'), "-: orange")
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: red | 2: yellow | 3: green | 4: blue | 5: indigo | 6: violet",
        )

        self.assertEqual(stack("fumanchu", 'pop [-1]'), "-: violet")
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: red | 2: yellow | 3: green | 4: blue | 5: indigo",
        )

        self.assertEqual(stack("fumanchu", 'pop [0]'), "(none popped)")
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: red | 2: yellow | 3: green | 4: blue | 5: indigo",
        )

        self.assertEqual(stack("fumanchu", 'pop [-1200]'), "(none popped)")
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: red | 2: yellow | 3: green | 4: blue | 5: indigo",
        )

        self.assertEqual(stack("fumanchu", 'pop [7346]'), "(none popped)")
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: red | 2: yellow | 3: green | 4: blue | 5: indigo",
        )

    def test_stack_pop_integer_range(self):
        self.make_colors()

        self.assertEqual(
            stack("fumanchu", 'pop [2:4]'), "-: orange | -: yellow | -: green"
        )
        self.assertEqual(
            stack("fumanchu", "show"), "1: red | 2: blue | 3: indigo | 4: violet"
        )

        self.assertEqual(stack("fumanchu", 'pop [-2:]'), "-: indigo | -: violet")
        self.assertEqual(stack("fumanchu", "show"), "1: red | 2: blue")

        self.assertEqual(stack("fumanchu", 'pop [-2123:]'), "-: red | -: blue")
        self.assertEqual(stack("fumanchu", "show"), "(empty)")

    def test_stack_pop_text_match(self):
        self.make_colors()

        self.assertEqual(stack("fumanchu", 'pop ["re"]'), "-: red | -: green")
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: orange | 2: yellow | 3: blue | 4: indigo | 5: violet",
        )

    def test_stack_pop_regex(self):
        self.make_colors()

        self.assertEqual(
            stack("fumanchu", 'pop [/r.*e/]'), "-: red | -: orange | -: green"
        )
        self.assertEqual(
            stack("fumanchu", "show"), "1: yellow | 2: blue | 3: indigo | 4: violet"
        )

    def test_stack_pop_first(self):
        self.make_colors()

        self.assertEqual(stack("fumanchu", "pop [first]"), "-: red")
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: orange | 2: yellow | 3: green | 4: blue | " "5: indigo | 6: violet",
        )

    def test_stack_pop_last(self):
        self.make_colors()

        self.assertEqual(stack("fumanchu", "pop [last]"), "-: violet")
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: red | 2: orange | 3: yellow | 4: green | 5: blue | 6: indigo",
        )

    def test_stack_pop_multiple_indices(self):
        self.make_colors()

        self.assertEqual(
            stack("fumanchu", "pop [3, -2, 2]"), "-: orange | -: yellow | -: indigo"
        )
        self.assertEqual(
            stack("fumanchu", "show"), "1: red | 2: green | 3: blue | 4: violet"
        )

    def test_stack_pop_duplicate_indices(self):
        self.make_colors()

        self.assertEqual(stack("fumanchu", "pop [6, 6, 6]"), "-: indigo")
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: red | 2: orange | 3: yellow | 4: green | 5: blue | 6: violet",
        )

    def test_stack_pop_combo(self):
        self.make_colors()

        self.assertEqual(
            stack("fumanchu", "pop [last, /r.*e/, 5]"),
            "-: red | -: orange | -: green | -: blue | -: violet",
        )
        self.assertEqual(stack("fumanchu", "show"), "1: yellow | 2: indigo")

    def test_stack_pop_illegal_combo(self):
        self.make_colors()

        self.assertEqual(
            stack("fumanchu", "pop [3, 'stray, comma', 7]"), helpdoc["index"]
        )


class TestStackShuffle(StackTestCase):
    def test_stack_shuffle_random(self):
        self.make_colors()

        olditems = set(Stack.store.table["fumanchu"])
        stack("fumanchu", "shuffle")
        self.assertEqual(set(Stack.store.table["fumanchu"]), olditems)

    def test_stack_shuffle_explicit(self):
        self.make_colors()

        self.assertEqual(
            stack("fumanchu", "shuffle [3:5, last, 1]"),
            "1: yellow | 2: green | 3: blue | 4: violet | 5: red",
        )

    def test_stack_shuffle_topic(self):
        self.make_colors()

        self.assertEqual(
            stack("fumanchu", "shuffle fumanchu[3:5, last, 1]"),
            "1: yellow | 2: green | 3: blue | 4: violet | 5: red",
        )

        olditems = set(Stack.store.table["fumanchu"])
        stack("fumanchu", "shuffle fumanchu[]")
        self.assertEqual(set(Stack.store.table["fumanchu"]), olditems)


class TestStackShow(StackTestCase):
    def test_stack_show_no_index(self):
        self.make_colors()
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: red | 2: orange | 3: yellow | 4: green | "
            "5: blue | 6: indigo | 7: violet",
        )

    def test_stack_show_integer_index(self):
        self.make_colors()

        self.assertEqual(stack("fumanchu", 'show [2]'), "2: orange")
        self.assertEqual(stack("fumanchu", 'show [-1]'), "7: violet")
        self.assertEqual(stack("fumanchu", 'show [0]'), "(empty)")
        self.assertEqual(stack("fumanchu", 'show [-1200]'), "(empty)")

    def test_stack_show_multiline(self):
        self.make_colors()
        stack("fumanchu", "add [//] a big thing to work on")
        self.assertEqual(
            stack("fumanchu", "show"),
            """1: red
2: a big thing to work on
3: orange
4: a big thing to work on
5: yellow
6: a big thing to work on
7: green
8: a big thing to work on
9: blue
10: a big thing to work on
11: indigo
12: a big thing to work on
13: violet
14: a big thing to work on""",
        )


class TestStackTopics(StackTestCase):
    def test_stack_topic_as_nick(self):
        self.make_colors()
        self.assertEqual(stack("sarah", ""), "(empty)")
        self.assertEqual(stack("sarah", "add write tests"), None)
        self.assertEqual(stack("sarah", "show"), "1: write tests")
        # Working on sarah's topic shouldn't alter fumanchu's
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: red | 2: orange | 3: yellow | 4: green | "
            "5: blue | 6: indigo | 7: violet",
        )

    def test_stack_explicit_topics(self):
        self.make_colors()
        self.assertEqual(stack("fumanchu", "show project1[]"), "(empty)")
        self.assertEqual(stack("fumanchu", "add project1[] write tests"), None)
        self.assertEqual(stack("fumanchu", "show project1[]"), "1: write tests")
        # Working on project1's topic shouldn't alter fumanchu's
        self.assertEqual(
            stack("fumanchu", "show"),
            "1: red | 2: orange | 3: yellow | 4: green | "
            "5: blue | 6: indigo | 7: violet",
        )

    def test_stack_topics_command(self):
        self.make_colors()
        stack("sarah", "add bar")
        stack("fumanchu", "add project1[] foo")
        self.assertEqual(
            stack("fumanchu", "topics"), "1: fumanchu | 2: project1 | 3: sarah"
        )
        self.assertEqual(stack("fumanchu", 'topics [2]'), "2: project1")
        self.assertEqual(stack("fumanchu", 'topics [-1]'), "3: sarah")
        self.assertEqual(stack("fumanchu", 'topics [0]'), "(empty)")
        self.assertEqual(stack("fumanchu", 'topics [-1200]'), "(empty)")


class TestStackHelp(StackTestCase):
    def test_stack_help(self):
        Stack.store = DummyStorage()
        self.assertEqual(stack("fumanchu", "help"), helpdoc["help"])
        self.assertEqual(stack("fumanchu", "help add"), helpdoc["add"])
        self.assertEqual(stack("fumanchu", "help pop"), helpdoc["pop"])
        self.assertEqual(stack("fumanchu", "help show"), helpdoc["show"])
        self.assertEqual(stack("fumanchu", "help shuffle"), helpdoc["shuffle"])
        self.assertEqual(stack("fumanchu", "help index"), helpdoc["index"])
        self.assertEqual(stack("fumanchu", "help stack"), helpdoc["stack"])
        self.assertEqual(stack("fumanchu", "help topics"), helpdoc["topics"])
        self.assertEqual(stack("fumanchu", "help list"), helpdoc["topics"])

        self.assertEqual(stack("fumanchu", "not a command"), helpdoc["stack"])


class TestSQLiteStack:
    @pytest.fixture
    def sqlite_stack(self, request, tmpdir):
        filename = tmpdir / 'db.sqlite'
        return Stack.from_URI('sqlite://{filename}'.format(**locals()))

    def test_no_topics(self, sqlite_stack):
        assert sqlite_stack.get_topics() == []

        assert sqlite_stack.get_items(None) == []
        assert sqlite_stack.get_items('nonexistanttopic') == []

    def test_simple_workflow(self, sqlite_stack):
        s = sqlite_stack
        assert s.get_topics() == []
        assert s.get_items('foo') == []

        s.save_items('foo', ['a', 'b', 'c'])
        assert s.get_items('foo') == ['a', 'b', 'c']
        assert s.get_topics() == ['foo']

        s.save_items('foo', ['1', '2', '3'])
        assert s.get_items('foo') == ['1', '2', '3']

        s.save_items('foo', [])
        assert s.get_items('foo') == []

        assert s.get_topics() == []


class TestMongoDBStack:
    @pytest.fixture
    def mongodb_stack(self, request, mongodb_uri):
        k = Stack.from_URI(mongodb_uri)
        k.db = k.db.database.connection[k.db.database.name + '_test'][k.db.name]
        request.addfinalizer(k.db.drop)
        return k

    def test_no_topics(self, mongodb_stack):
        assert mongodb_stack.get_topics() == []
        assert mongodb_stack.get_items(None) == []
        assert mongodb_stack.get_items('nonexistanttopic') == []

    def test_simple_workflow(self, mongodb_stack):
        s = mongodb_stack
        assert s.get_topics() == []
        assert s.get_items('foo') == []

        s.save_items('foo', ['a', 'b', 'c'])
        assert s.get_items('foo') == ['a', 'b', 'c']
        assert s.get_topics() == ['foo']

        s.save_items('foo', ['1', '2', '3'])
        assert s.get_items('foo') == ['1', '2', '3']

        s.save_items('foo', [])
        assert s.get_items('foo') == []

        assert s.get_topics() == []
