import unittest
from ranking import relation, merge_sort_interactive, NeedComparison
class TestRanking(unittest.TestCase):
 def test_direct_and_inverse(self):
  h=[{'a':0,'b':1,'result':1}]
  self.assertEqual(relation(0,1,h,3),1);self.assertEqual(relation(1,0,h,3),2)
 def test_transitivity(self):
  h=[{'a':0,'b':1,'result':1},{'a':1,'b':2,'result':1}]
  self.assertEqual(relation(0,2,h,3),1)
 def test_tie_component(self):
  h=[{'a':0,'b':1,'result':0}]
  self.assertEqual(relation(0,1,h,2),0)
 def test_unknown_requests_comparison(self):
  with self.assertRaises(NeedComparison):merge_sort_interactive([0,1],[])
 def test_merge_sorted_by_judgments(self):
  h=[{'a':0,'b':1,'result':2},{'a':1,'b':2,'result':2},{'a':0,'b':2,'result':2}]
  self.assertEqual(merge_sort_interactive([0,1,2],h),[2,1,0])
if __name__=='__main__':unittest.main()
