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
        for k,v in [('RL_H25_DIST_FORCE_N','5'),('RL_H25_DIST_PULSE_S','.8'),
                    ('RL_H25_DIST_ONSET_S','0'),('RL_H25_DIST_FORCE_N','nan'),
                    ('RL_H25_DIST_AXIS','yaw'),('RL_H25_DIST_DIRECTION','0'),
                    ('RL_H25_DIST_OFFSET_M','.7')]:
            with self.subTest(k=k,v=v), self.assertRaises(ValueError):
                DisturbanceSpec.from_env({'RL_H25_DISTURBANCE':'1',k:v})
        with self.assertRaises(ValueError):
            DisturbanceSpec.from_env({'RL_H25_DISTURBANCE':'yes'})

    def test_high_force_requires_explicit_calibration_mode(self):
        with self.assertRaises(ValueError):
            DisturbanceSpec.from_env({'RL_H25_DISTURBANCE':'1',
                                      'RL_H25_DIST_FORCE_N':'1.0'})
        spec = DisturbanceSpec.from_env({'RL_H25_DISTURBANCE':'1',
                                         'RL_H25_DIST_FORCE_N':'1.0',
                                         'RL_H25_DIST_CALIBRATION':'1'})
        self.assertTrue(spec.calibration_mode)


def fixture(directory:Path, name:str, mode:str, peak:float, fault:bool=False,
            inject:bool=True, onset=4.0, initial=.0, direction=1,
            calibration:bool=False, force=.10)->Path:
    p=directory / f'{name}.csv'
    cols=['run_id','t_s','mode','state','reason','roll_rad','pitch_rad',
          'root_height_m','root_x_m','root_z_m']
    cols += ['root_angular_velocity_x_rad_s', 'root_angular_velocity_y_rad_s',
             'root_angular_velocity_z_rad_s', 'root_com_x_m', 'root_com_y_m',
             'root_com_z_m', 'static_balance', 'gyro_x_rad_s', 'gyro_y_rad_s',
             'gyro_z_rad_s', 'root_velocity_x_m_s', 'root_velocity_y_m_s',
             'root_velocity_z_m_s', 'pitch_correction_rad', 'roll_correction_rad']
    joint_names = ['left_hip_roll', 'left_hip_pitch', 'left_knee_pitch',
                   'left_ankle_pitch', 'left_ankle_roll', 'right_hip_roll',
                   'right_hip_pitch', 'right_knee_pitch', 'right_ankle_pitch',
                   'right_ankle_roll']
    for joint in joint_names:
        cols += [f'{joint}_target_rad', f'{joint}_measured_rad',
                 f'{joint}_torque_feedback_nm']
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for i in range(950):
            t=round(.016*(i+1),4)
            dt=t-onset
            # Sharp 0.12s excitation, exponential relaxation; near 0 after 5s.
            tilt=peak*math.exp(-max(0,dt-.16)*2.0) if dt>=.05 else 0
            bad=fault and t>=5.0
            correction = (0.01 * direction if mode == 'balance' and dt >= 0
                          and type(direction) is int else 0.0)
            actuator_target = correction if mode == 'balance' and dt >= 0 else 0.0
            actuator_measured = actuator_target * 0.8
            w.writerow(dict(run_id=name,t_s=t,mode=mode,
                    state='FAULT' if bad else 'STAND',
                    reason='excessive_tilt' if bad else '', roll_rad=0,
                    pitch_rad=initial+tilt,
                    root_height_m=.183 if not bad else .09,
                    root_x_m=0.,root_z_m=0.,
                    root_angular_velocity_x_rad_s=0.,
                    root_angular_velocity_y_rad_s=0.,
                    root_angular_velocity_z_rad_s=0.,
                    root_com_x_m=0., root_com_y_m=.12, root_com_z_m=0.,
                    static_balance=True, gyro_x_rad_s=0., gyro_y_rad_s=0.,
                    gyro_z_rad_s=0., root_velocity_x_m_s=0.,
                    root_velocity_y_m_s=0., root_velocity_z_m_s=0.,
                    pitch_correction_rad=correction if mode == 'balance' else 0.,
                    roll_correction_rad=0.,
                    **{f'{joint}_{kind}':
                       (actuator_target if mode == 'balance' and joint in
                        ('left_hip_pitch', 'left_ankle_pitch', 'right_hip_pitch', 'right_ankle_pitch')
                        and kind == 'target_rad' else
                        (actuator_measured if mode == 'balance' and joint in
                         ('left_hip_pitch', 'left_ankle_pitch', 'right_hip_pitch', 'right_ankle_pitch')
                         and kind == 'measured_rad' else 0.))
                       for joint in joint_names
                       for kind in ('target_rad', 'measured_rad',
                                    'torque_feedback_nm')}))
    world_force=[0.,0.,force * direction] if type(direction) is int else [0.,0.,force]
    meta={'run_id':name,'mode':mode,'result':'controller_exited',
          'build_commit':'d'*40,
          'source_commit_sha':'a'*40,
          'test_merge_sha':'e'*40,
          'config_sha256':'b'*64,
          'world_sha256':'c'*64,
          'software_version':'rlh25-v0.2',
          'telemetry_schema_version':2,
          'log_period_s':.016,
          'simulation_timestep_s':0.016,
          'webots_version':'Webots R2025a mock-only',
          'fault_injection':None,
          'contact_evidence':{
              'sample_count':950, 'samples_with_contacts':950,
              'min_contact_count':8, 'max_contact_count':8,
              'contact_solid_node_ids':[78, 138],
              'samples_by_solid_node_id':{'78':950, '138':950},
              'foot_mapping':'world_x_sign',
              'samples_by_foot':{'left':950, 'right':950},
          },
          'disturbance':{'axis':'pitch','direction':direction,'force_n':force,'pulse_s':.112,
                         'offset_m':.04,'onset_s':onset,
                         'world_force_n':world_force,
                         'force_api_mode':'r2025a_ctypes_force_with_offset',
                         'calibration_mode':calibration,
                         'applied_steps':7 if inject else 0,
                         'first_application_s':onset if inject else None,
                         'last_application_s':onset + .096 if inject else None}}
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

    def test_wrong_signed_response_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            for direction, peak in ((1, -.04), (-1, .04)):
                with self.subTest(direction=direction):
                    p=fixture(Path(tmp),f'wrong-sign-{direction}','balance',peak,
                              direction=direction)
                    result=inspect_run(p)
                    self.assertEqual('FAIL',result['verdict'])
                    self.assertIn('wrong_signed_response',result['reasons'])

    def test_initial_wrong_sign_cannot_be_hidden_by_later_larger_peak(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=fixture(Path(tmp),'sign-reversal','balance',.04,direction=1)
            with p.open(newline='', encoding='utf-8') as f:
                rows=list(csv.DictReader(f))
                fieldnames=list(rows[0])
            for row in rows:
                if 4.05 <= float(row['t_s']) < 4.13:
                    row['pitch_rad']='-0.009'
            with p.open('w',newline='',encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            result=inspect_run(p)
            self.assertEqual('FAIL',result['verdict'])
            self.assertIn('wrong_signed_response',result['reasons'])

    def test_invalid_direction_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for index, direction in enumerate((0, 1.9, True, '1')):
                with self.subTest(direction=direction):
                    p=fixture(Path(tmp),f'bad-direction-{index}','balance',.04,
                              direction=direction)
                    self.assertEqual('INVALID',inspect_run(p)['verdict'])

    def test_force_vector_metadata_must_match_direction(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=fixture(Path(tmp),'wrong-force-vector','balance',-.04,direction=-1)
            meta=json.loads(p.with_suffix('.json').read_text())
            meta['disturbance']['world_force_n']=[0.,0.,.10]
            p.with_suffix('.json').write_text(json.dumps(meta))
            result=inspect_run(p)
            self.assertEqual('INVALID',result['verdict'])
            self.assertIn('invalid_or_unapplied_force',result['reasons'])

    def test_fault_is_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=fixture(Path(tmp),'fall','balance',.05,fault=True)
            result = inspect_run(p)
            self.assertEqual('FAIL', result['verdict'])
            self.assertEqual('excessive_tilt', result['first_fault_reason'])

    def test_truncated_pulse_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = fixture(Path(tmp), 'truncated', 'balance', .04)
            meta = json.loads(p.with_suffix('.json').read_text())
            meta['disturbance']['applied_steps'] = 1
            meta['disturbance']['last_application_s'] = meta['disturbance']['onset_s']
            p.with_suffix('.json').write_text(json.dumps(meta))
            result = inspect_run(p)
            self.assertEqual('INVALID', result['verdict'])
            self.assertIn('incomplete_force_pulse', result['reasons'])

    def test_pulse_application_count_must_match_timestamps(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = fixture(Path(tmp), 'bad-count', 'balance', .04)
            meta = json.loads(p.with_suffix('.json').read_text())
            meta['disturbance']['applied_steps'] = 1
            p.with_suffix('.json').write_text(json.dumps(meta))
            result = inspect_run(p)
            self.assertEqual('INVALID', result['verdict'])
            self.assertIn('incomplete_force_pulse', result['reasons'])

    def test_reviewed_half_newton_is_gate_eligible_but_higher_force_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            accepted = fixture(directory, 'half-newton', 'balance', .04, force=.50)
            rejected = fixture(directory, 'over-half-newton', 'balance', .04, force=.5001)
            self.assertEqual('RECOVERED', inspect_run(accepted)['verdict'])
            self.assertEqual('INVALID', inspect_run(rejected)['verdict'])

    def test_calibration_pairs_cannot_satisfy_scientific_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            pairs = [
                (fixture(directory, f'cal-b{i}', 'baseline', .07, calibration=True),
                 fixture(directory, f'cal-c{i}', 'balance', .04, calibration=True))
                for i in range(3)
            ]
            result = compare_pairs(pairs)
            self.assertEqual('CALIBRATION_ONLY', result['verdict'])

    def test_cross_axis_dominant_response_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = fixture(Path(tmp), 'cross-axis', 'balance', .04)
            with p.open(newline='', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
                fieldnames = list(rows[0])
            for row in rows:
                if float(row['t_s']) >= 4.05:
                    row['roll_rad'] = str(float(row['pitch_rad']) * 1.25)
            with p.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            result = inspect_run(p)
            self.assertEqual('FAIL', result['verdict'])
            self.assertIn('cross_axis_dominant_response', result['reasons'])

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

    def test_different_applied_step_count_is_not_comparable(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            pairs = []
            for index in range(3):
                baseline = fixture(directory, f'steps-b-{index}', 'baseline', .07)
                balance = fixture(directory, f'steps-c-{index}', 'balance', .04)
                meta = json.loads(balance.with_suffix('.json').read_text())
                meta['disturbance']['applied_steps'] = 6
                meta['disturbance']['last_application_s'] = 4.08
                balance.with_suffix('.json').write_text(json.dumps(meta))
                pairs.append((baseline, balance))
            result = compare_pairs(pairs)
            self.assertEqual('INCONCLUSIVE', result['verdict'])
            self.assertEqual(0, result['comparable_pairs'])

    def test_missing_provenance_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = fixture(Path(tmp), 'unknown-build', 'balance', .04)
            meta = json.loads(p.with_suffix('.json').read_text())
            meta['webots_version'] = 'unverified'
            p.with_suffix('.json').write_text(json.dumps(meta))
            self.assertEqual('INVALID', inspect_run(p)['verdict'])

    def test_build_and_test_merge_provenance_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            for field in ('build_commit', 'test_merge_sha'):
                with self.subTest(field=field):
                    p = fixture(Path(tmp), 'missing-' + field, 'balance', .04)
                    meta = json.loads(p.with_suffix('.json').read_text())
                    meta[field] = 'unverified'
                    p.with_suffix('.json').write_text(json.dumps(meta))
                    self.assertEqual('INVALID', inspect_run(p)['verdict'])

    def test_pair_rejects_mismatched_test_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            pairs = []
            for i in range(3):
                base = fixture(directory, f'base-{i}', 'baseline', .07)
                balance = fixture(directory, f'balance-{i}', 'balance', .04)
                meta = json.loads(balance.with_suffix('.json').read_text())
                meta['test_merge_sha'] = 'f' * 40
                balance.with_suffix('.json').write_text(json.dumps(meta))
                pairs.append((base, balance))
            result = compare_pairs(pairs)
            self.assertEqual('INCONCLUSIVE', result['verdict'])
            self.assertEqual(0, result['comparable_pairs'])

    def test_contact_evidence_is_required_for_every_sample_and_both_feet(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            mutations = (
                ('INVALID', lambda meta: meta.update(contact_evidence=None)),
                ('FAIL', lambda meta: meta['contact_evidence'].update(samples_with_contacts=949)),
                ('FAIL', lambda meta: meta['contact_evidence'].update(contact_solid_node_ids=[78])),
                ('FAIL', lambda meta: meta['contact_evidence']['samples_by_solid_node_id'].update({'138':949})),
            )
            for index, (expected, mutate) in enumerate(mutations):
                with self.subTest(index=index):
                    p = fixture(directory, f'bad-contact-{index}', 'balance', .04)
                    meta = json.loads(p.with_suffix('.json').read_text())
                    mutate(meta)
                    p.with_suffix('.json').write_text(json.dumps(meta))
                    result = inspect_run(p)
                    self.assertEqual(expected, result['verdict'])
                    self.assertTrue(any('contact' in reason for reason in result['reasons']))

    def test_peak_inside_absolute_settle_band_must_still_decay(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = fixture(Path(tmp), 'no-relative-recovery', 'balance', .01)
            with p.open(newline='', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
                fieldnames = list(rows[0])
            for row in rows:
                if float(row['t_s']) >= 4.05:
                    row['pitch_rad'] = '.01'
            with p.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            result = inspect_run(p)
            self.assertEqual('FAIL', result['verdict'])
            self.assertIn('did_not_recover_from_peak', result['reasons'])

    def test_joint_target_measurement_and_torque_observability_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = fixture(Path(tmp), 'missing-torque', 'balance', .04)
            with p.open(newline='', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
                fieldnames = [name for name in rows[0]
                              if name != 'right_ankle_roll_torque_feedback_nm']
            with p.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(rows)
            result = inspect_run(p)
            self.assertEqual('INVALID', result['verdict'])
            self.assertTrue(any('actuator' in reason for reason in result['reasons']))

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
            def getFromProtoDef(self, name):
                return type('FakeNode', (), {'getId': lambda self: 11 if name == 'LEFT_FOOT' else 12})()
            def getVelocity(self):return [0., 0., 0., 0., 0., 0.]
            def getCenterOfMass(self):return [0., .12, 0.]
            def getStaticBalance(self):return True
            def enableContactPointsTracking(self, timestep, include_descendants):pass
            def getContactPoints(self, include_descendants):
                from test_controller_fake import FakeContactPoint
                return [FakeContactPoint((-.03, 0., 0.), 11),
                        FakeContactPoint((.03, 0., 0.), 12)]
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
            self.assertEqual('True', rows[-1]['static_balance'])
            self.assertEqual(0.0, float(rows[-1]['root_angular_velocity_x_rad_s']))
            self.assertEqual(0.12, float(rows[-1]['root_com_y_m']))
            self.assertEqual(
                10,
                len([name for name in rows[-1] if name.endswith('_torque_feedback_nm')]),
            )
