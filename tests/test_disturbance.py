"""No Webots needed: verify force limits, scheduling, and evidence gates."""
import csv
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'simulation/webots/controllers/rl_h25_controller'))
sys.path.insert(0, str(ROOT / 'tools'))
from disturbance import DisturbanceSpec, DisturbanceInjector
from disturbance_report import inspect_run, compare_pairs


class FakeSolid:
    def __init__(self): self.calls = []
    def addForceWithOffset(self, f, o, relative): self.calls.append((f,o,relative))


class FakeForceAPI:
    mode = "offline_mock_only"

    def __init__(self, solid): self.solid = solid

    def add(self, force, offset, relative):
        self.solid.addForceWithOffset(force, offset, relative)


class DisturbanceTests(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertIsNone(DisturbanceSpec.from_env({}))

    def test_axis_and_pulse(self):
        spec = DisturbanceSpec.from_env({'RL_H25_DISTURBANCE':'1',
              'RL_H25_DIST_AXIS':'pitch','RL_H25_DIST_DIRECTION':'-1'})
        self.assertEqual([0,0,-.10], spec.force_vector())
        solid = FakeSolid()
        inj = DisturbanceInjector(spec, solid, force_api=FakeForceAPI(solid))
        for t in (0, 3.9, 4.0, 4.016, 4.032, 4.048, 4.064, 4.080, 4.096, 4.112, 4.5):
            inj.step(t, can_apply=True)
        self.assertEqual(7, inj.applied_steps)
        self.assertEqual(7, len(solid.calls))
        self.assertEqual([0., .04, 0.], solid.calls[0][1])
        self.assertFalse(solid.calls[0][2])

    def test_fault_gate(self):
        spec = DisturbanceSpec.from_env({'RL_H25_DISTURBANCE':'1'})
        solid = FakeSolid()
        inj = DisturbanceInjector(spec, solid, force_api=FakeForceAPI(solid))
        inj.step(4.0, can_apply=False)
        self.assertEqual(0, inj.applied_steps)

    def test_roll(self):
        spec = DisturbanceSpec.from_env({'RL_H25_DISTURBANCE':'1','RL_H25_DIST_AXIS':'roll'})
        self.assertEqual([.1,0.,0.], spec.force_vector())

    def test_reject_unsafe(self):
        for k,v in [('RL_H25_DIST_FORCE_N','3'),('RL_H25_DIST_PULSE_S','.8'),
                    ('RL_H25_DIST_ONSET_S','0'),('RL_H25_DIST_FORCE_N','nan'),
                    ('RL_H25_DIST_AXIS','yaw'),('RL_H25_DIST_DIRECTION','0'),
                    ('RL_H25_DIST_OFFSET_M','.7')]:
            with self.subTest(k=k,v=v), self.assertRaises(ValueError):
                DisturbanceSpec.from_env({'RL_H25_DISTURBANCE':'1',k:v})
        with self.assertRaises(ValueError):
            DisturbanceSpec.from_env({'RL_H25_DISTURBANCE':'yes'})


def fixture(directory:Path, name:str, mode:str, peak:float, fault:bool=False,
            inject:bool=True, onset=4.0, initial=.0)->Path:
    p=directory / f'{name}.csv'
    cols=['run_id','t_s','mode','state','roll_rad','pitch_rad','root_height_m','root_x_m','root_z_m']
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for i in range(950):
            t=round(.016*(i+1),4)
            dt=t-onset
            # Sharp 0.12s excitation, exponential relaxation; near 0 after 5s.
            tilt=peak*math.exp(-max(0,dt-.16)*2.0) if dt>=.05 else 0
            bad=fault and t>=5.0
            w.writerow(dict(run_id=name,t_s=t,mode=mode,
                    state='FAULT' if bad else 'STAND', roll_rad=0,
                    pitch_rad=initial+tilt,
                    root_height_m=.183 if not bad else .09,
                    root_x_m=0.,root_z_m=0.))
    meta={'run_id':name,'mode':mode,'result':'controller_exited',
          'fault_injection':None,
          'disturbance':{'axis':'pitch','direction':1,'force_n':.10,'pulse_s':.112,
                         'offset_m':.04,'onset_s':onset,'applied_steps':7 if inject else 0,
                         'first_application_s':onset if inject else None}}
    p.with_suffix('.json').write_text(json.dumps(meta))
    return p


class ReportTests(unittest.TestCase):
    def test_recovered_and_improved(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            pairs=[]
            for i in range(3):
                pairs.append((fixture(directory, f'b{i}','baseline',.07),
                              fixture(directory, f'c{i}','balance',.04)))
            r=compare_pairs(pairs)
            self.assertEqual('IMPROVED',r['verdict'])
            self.assertEqual(3,r['comparable_pairs'])

    def test_no_excitation_is_inconclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=fixture(Path(tmp),'zero','balance',.001)
            self.assertEqual('INCONCLUSIVE',inspect_run(p)['verdict'])

    def test_fault_is_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=fixture(Path(tmp),'fall','balance',.05,fault=True)
            self.assertEqual('FAIL',inspect_run(p)['verdict'])

    def test_missing_event_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=fixture(Path(tmp),'missing','balance',.04,inject=False)
            self.assertEqual('INVALID',inspect_run(p)['verdict'])

    def test_initial_angle_too_large(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=fixture(Path(tmp),'start_lean','balance',.04,initial=.24)
            self.assertEqual('INVALID',inspect_run(p)['verdict'])

    def test_different_force_is_not_comparable(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            b=fixture(d,'b','baseline',.07)
            c=fixture(d,'c','balance',.04)
            meta=json.loads(c.with_suffix('.json').read_text())
            meta['disturbance']['force_n']=.20
            c.with_suffix('.json').write_text(json.dumps(meta))
            result=compare_pairs([(b,c)]*3)
            self.assertEqual('INCONCLUSIVE',result['verdict'])

    def test_corrupt_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=fixture(Path(tmp),'bad','balance',.04)
            with p.open('a') as f:f.write('different-row\n')
            self.assertEqual('INVALID',inspect_run(p)['verdict'])

if __name__=='__main__':unittest.main()

class SupervisorFakeTests(unittest.TestCase):
    def test_native_controller_experiment_uses_supervisor_and_metadata(self):
        """End-to-end fake Webots controller applies force; real physics still NOT tested."""
        import importlib.util
        import os
        import types
        from unittest.mock import patch
        # Reuse the existing API stand-ins; run until just beyond onset.
        from test_controller_fake import FakeRobot
        controlpath = ROOT/'simulation/webots/controllers/rl_h25_controller/rl_h25_controller.py'
        class ExperimentRobot(FakeRobot):
            applied = []
            def getSelf(self):return self
            def addForceWithOffset(self,f,o,relative): self.applied.append((f,o,relative))
            def step(self,ms):
                if self.t >= 4.5:return -1
                self.t+=ms/1000
                return 0
        ExperimentRobot.applied=[]
        api=types.ModuleType('controller')
        api.Robot=FakeRobot
        api.Supervisor=ExperimentRobot
        spec=importlib.util.spec_from_file_location('rl_h25_controller_experiment',controlpath)
        module=importlib.util.module_from_spec(spec)
        with tempfile.TemporaryDirectory() as tmp:
            newenv={'RL_H25_LOG_DIR':tmp, 'RL_H25_RUN_ID':'fake-dist',
                    'RL_H25_MODE':'balance', 'RL_H25_DURATION_S':'0',
                    'RL_H25_DISTURBANCE':'1', 'RL_H25_DIST_FORCE_N':'0.1',
                    'RL_H25_DIST_AXIS':'pitch','RL_H25_FORCE_FAULT':'',
                    'RL_H25_LOG_PERIOD_S':'0.016'}
            with patch.dict(sys.modules,{'controller':api}),patch.dict(os.environ,newenv):
                spec.loader.exec_module(module)
                with patch('disturbance.ForceWithOffsetAPI', FakeForceAPI):
                    module.main()
            meta=json.loads((Path(tmp)/'fake-dist.json').read_text())
            self.assertEqual('STAND',meta['final_state'])
            self.assertGreater(meta['disturbance']['applied_steps'],0)
            self.assertEqual(meta['disturbance']['applied_steps'],len(ExperimentRobot.applied))
            with (Path(tmp)/'fake-dist.csv').open() as f:
                rows=list(csv.DictReader(f))
            self.assertGreater(len(rows),100)
