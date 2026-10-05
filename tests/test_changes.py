import copy, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from changes import build,digest
class Plans(unittest.TestCase):
 def setUp(self):
  self.data={'exportedAt':'test','tasks':[dict(id='a',name='Example',notes='Keep me',status='open',modificationDate='today')],'projects':[], 'lists':[{'id':'s','name':'Someday'}], 'databaseSupplement':{'tables':{'TMTask':[{'uuid':'a'}]}}}
 def test_preview_preserves_before(self):
  plan=build(self.data,[{'id':'a','action':'rename','value':'New'}]);self.assertEqual(plan['operations'][0]['before']['notes'],'Keep me')
 def test_recurring_refused(self):
  self.data['databaseSupplement']['tables']['TMTask'][0]['repeater']='rule'
  with self.assertRaises(ValueError): build(self.data,[{'id':'a','action':'trash'}])
 def test_unknown_destination(self):
  with self.assertRaises(ValueError): build(self.data,[{'id':'a','action':'move','destinationId':'missing'}])
 def test_duplicate_refused(self):
  with self.assertRaises(ValueError): build(self.data,[{'id':'a','action':'trash'}]*2)
 def test_project_refused(self):
  self.data['projects']=[{'id':'a'}]
  with self.assertRaises(ValueError): build(self.data,[{'id':'a','action':'trash'}])
 def test_token_binds_content(self):
  plan=build(self.data,[{'id':'a','action':'rename','value':'New'}]);other=copy.deepcopy(plan);other['operations'][0]['value']='Different';self.assertNotEqual(digest(plan),digest(other))
if __name__=='__main__':unittest.main()
