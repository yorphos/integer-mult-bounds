"""Adversarial tests for current selected-word admission and strict-data rebinding."""
import argparse,copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from support import HERE,ROOT,read,sha,load_source,source_context,validate_sources
from native import verify_substitution,SELECTED_CANONICAL
from rebind_plan import refreshed
from prepare_hosted import provider
BASELINE=CANDIDATE=None

class IntegrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=read(BASELINE/'CANONICAL-WORD.json.gz');cls.candidate=read(CANDIDATE/'CANONICAL-WORD.json.gz');cls.plan=read(ROOT/'research/gauge44-slots-t16/data/T8/PLAN.json')
 def test_exact_typed_boundary(self):
  r=verify_substitution(self.original,self.candidate);self.assertEqual((r['columns_each_orientation'],r['orientations'],r['changed_fields']),(704,2,['compensation']))
 def test_other_fields_rejected(self):
  for field in ['start','final','frames','precondition','tail','A','B','centers']:
   bad=copy.deepcopy(self.candidate);bad[field].pop()
   with self.subTest(field=field),self.assertRaisesRegex(ValueError,'Only compensation'):verify_substitution(self.original,bad)
 def test_schema_rejected(self):
  bad=copy.deepcopy(self.candidate);bad['trusted']=True
  with self.assertRaisesRegex(ValueError,'inventory'):verify_substitution(self.original,bad)
 def test_endpoint_invisible_wrapped_access_rejected(self):
  r=next(r for r in range(224,704) if self.original['start'][r]==0 and self.original['final'][r]!=1);bad=copy.deepcopy(self.candidate);bad['compensation'][:0]=[['add',r,112,1,1,0],['add',r,112,-1,1,0]]
  with self.assertRaisesRegex(ValueError,'pre-wrapper'):verify_substitution(self.original,bad)
 def test_missing_restore_rejected(self):
  bad=copy.deepcopy(self.candidate);bad['compensation'].pop()
  with self.assertRaisesRegex(ValueError,'identity'):verify_substitution(self.original,bad)
 def test_bad_gate_fields_rejected(self):
  for field,value in [(1,True),(2,704),(4,3),(4,0),(5,1)]:
   bad=copy.deepcopy(self.candidate);bad['compensation'][0][field]=value
   with self.subTest(field=field,value=value),self.assertRaises((ValueError,IndexError)):verify_substitution(self.original,bad)
 def test_complete_source_pins(self):self.assertGreaterEqual(len(validate_sources()['source_sha256']),1570)
 def test_provider_only_plan_rebind(self):
  old=copy.deepcopy(self.plan);new=refreshed(old,BASELINE,CANDIDATE);self.assertEqual(old,self.plan)
  for key in old:
   if key not in ('provider_registry','provider_calls'):self.assertEqual(old[key],new[key],key)
  self.assertNotEqual(old['provider_registry'],new['provider_registry'])
 def test_stale_provider_binding_rejected(self):
  bad=copy.deepcopy(self.plan);bad['provider_registry']['gauge44']['artifact_semantic_sha256']['CANONICAL-WORD.json.gz']='0'*64
  with self.assertRaisesRegex(ValueError,'original native'):refreshed(bad,BASELINE,CANDIDATE)
 def test_changed_provider_geometry_rejected(self):
  for field in ['ports','centers','widths']:
   bad=copy.deepcopy(self.plan);bad['provider_registry']['gauge44'][field][0]+=1
   with self.subTest(field=field),self.assertRaisesRegex(ValueError,'ports/centers'):refreshed(bad,BASELINE,CANDIDATE)
 def test_stale_per_call_binding_rejected(self):
  bad=copy.deepcopy(self.plan);bad['provider_calls'][0]['local_program_sha256']='f'*64
  with self.assertRaisesRegex(ValueError,'call bindings'):refreshed(bad,BASELINE,CANDIDATE)
 def test_no_existing_output_replaced(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);out=p/'already';out.mkdir();s=out/'keep';s.write_text('unchanged')
   r=subprocess.run([sys.executable,'-B',str(HERE/'native.py'),'--baseline-local',str(BASELINE),'--out',str(out)],capture_output=True)
   self.assertNotEqual(r.returncode,0);self.assertEqual(s.read_text(),'unchanged');self.assertEqual(list(out.iterdir()),[s])
 def test_loader_keeps_original_import_context(self):
  before=list(sys.path);module=load_source(ROOT/'research/gauge44-slots-t16/code/generated_identity.py','pr1042_test_ids');self.assertEqual(sys.path,before);self.assertEqual(module.artifact_identities(BASELINE)['CANONICAL-WORD.json.gz'],SELECTED_CANONICAL)
 def test_delayed_import_context(self):
  before=list(sys.path);prior=sys.modules.get('common')
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'common.py').write_text('VALUE=731\n');(p/'delayed.py').write_text('def check():\n from common import VALUE\n return VALUE\n');m=load_source(p/'delayed.py','pr1042_test_delayed')
   with source_context(p):self.assertEqual(m.check(),731)
  self.assertEqual(sys.path,before);self.assertIs(sys.modules.get('common'),prior)
 def test_provider_geometry_cannot_hide_in_recount(self):
  spec=read(ROOT/'research/gauge44-slots-t16/data/SPEC.json')['providers']['gauge44'];before=copy.deepcopy(spec['complete_contract']);after=copy.deepcopy(before);after['artifacts']={}
  for field in ['helpers','children','n','widths','paid_profile']:
   bad=copy.deepcopy(after);bad[field]=None
   with self.subTest(field=field),self.assertRaisesRegex(ValueError,'unchanged fields'):provider(spec,before,bad)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline-local',type=Path,required=True);p.add_argument('--candidate-local',type=Path,required=True);a,rest=p.parse_known_args();BASELINE=a.baseline_local.resolve();CANDIDATE=a.candidate_local.resolve();unittest.main(argv=[sys.argv[0],*rest],verbosity=2)
