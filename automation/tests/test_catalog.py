import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import content_catalog as c

class CatalogTests(unittest.TestCase):
    def test_unique_topics_and_scripts(self):
        ideas = [c.script(t) for t in c.TOPICS]
        self.assertEqual(len(ideas),len({i[0] for i in ideas}))
        self.assertEqual(len(ideas),len({c.fingerprint(i[2]) for i in ideas}))
        self.assertTrue(all(len(line)<=38 for i in ideas for line in i[2]))

    def test_history_prevents_topic_reuse_even_after_queue_archived(self):
        ideas=[c.script(t) for t in c.TOPICS]
        state={'posts':{'old':{'concept':ideas[0][0]}}}
        remaining=c.rotate(ideas,{'posts':[]},state)
        self.assertNotIn(ideas[0],remaining)

    def test_identical_script_with_renamed_id_is_not_new(self):
        idea=c.script(c.TOPICS[0])
        queue={'posts':[{'concept':'renamed','script_sha256':c.fingerprint(idea[2])}]}
        self.assertEqual(c.rotate([idea],queue,{'posts':{}}),[])

    def test_rotation_avoids_consecutive_categories_when_available(self):
        ordered=c.rotate([c.script(t) for t in c.TOPICS],{'posts':[]},{'posts':{}})
        self.assertTrue(all(c.category(a[0]) != c.category(b[0]) for a,b in zip(ordered,ordered[1:])))

    def test_exhaustion_does_not_recycle(self):
        ideas=[c.script(t) for t in c.TOPICS]
        self.assertEqual(c.rotate(ideas,{'posts':[{'concept':i[0]} for i in ideas]},{'posts':{}}),[])
