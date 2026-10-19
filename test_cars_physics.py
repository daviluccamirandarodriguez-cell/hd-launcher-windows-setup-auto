"""Regressões: física da edição nativa compatível com o The Cars HD web v0.1."""
import unittest
from cars_physics import (
    CAR_OPTIONS, RaceState, TRACK_METERS, TOTAL_LAPS, DRAW_DIST,
    SEG, NUM_SEG, center, slope, mod,
)


class CarsParityTests(unittest.TestCase):
    def test_website_track_and_garage(self):
        self.assertEqual(SEG,210)
        self.assertEqual(NUM_SEG,650)
        self.assertEqual(TRACK_METERS,136500)
        self.assertEqual(DRAW_DIST,165)
        self.assertEqual(TOTAL_LAPS,3)
        self.assertEqual([c['top'] for c in CAR_OPTIONS],[3650,3950,3470])
        self.assertEqual([c['color'] for c in CAR_OPTIONS],['#09dd72','#2699ff','#ffcc32'])

    def test_three_laps_and_track_closed(self):
        for z in (0,987,53000,130000):
            self.assertAlmostEqual(center(z),center(z+TRACK_METERS),places=6)
            self.assertAlmostEqual(slope(z),slope(z+TRACK_METERS),places=6)
        r=RaceState()
        r.distance=TRACK_METERS+500
        self.assertEqual(r.lap,2)
        r.distance=TRACK_METERS*TOTAL_LAPS-1
        r.speed=2000
        r.update(.04,accelerate=True)
        self.assertTrue(r.finished)
        self.assertIn(r.place,range(1,7))

    def test_five_rivals_and_33_collectibles(self):
        r=RaceState()
        self.assertEqual(len(r.rivals),5)
        self.assertEqual(len(r.pickups),33)
        self.assertEqual(r.place,5)  # four rivals start ahead, one behind
        self.assertTrue(all(p.progress<TRACK_METERS for p in r.pickups))

    def test_acceleration_and_brake(self):
        r=RaceState()
        r.update(.04,accelerate=True)
        self.assertAlmostEqual(r.speed,2050*.04)
        old=r.speed
        r.update(.04,brake=True)
        self.assertLess(r.speed,old)

    def test_nitro_consumption_matches_web(self):
        r=RaceState()
        self.assertAlmostEqual(r.nitro,.68)
        for _ in range(18):r.update(.04,accelerate=True)
        before=r.nitro
        r.update(.04,accelerate=True,nitro=True)
        self.assertLess(r.nitro,before)
        self.assertTrue(r.nitro_active)
        self.assertGreater(r.speed,0)

    def test_steering_and_offroad(self):
        r=RaceState()
        for _ in range(170):r.update(.04,accelerate=True,steer=1)
        self.assertLessEqual(r.lane,1.8)
        self.assertGreater(r.lane,1.04)
        self.assertLessEqual(r.speed,r.car['top']*.63)

    def test_collect_item_and_use(self):
        r=RaceState()
        pickup=r.pickups[0]
        r.distance=pickup.progress-1120
        r.lane=pickup.lane
        r.update(.016,accelerate=True)
        self.assertEqual(pickup.collected_lap,0)
        self.assertIn(r.item,('NITRO','ESCUDO','ONDA'))
        self.assertTrue(r.use_item())
        self.assertIsNone(r.item)
        self.assertFalse(r.use_item())

    def test_pause_scenario_no_update_after_finishing(self):
        r=RaceState()
        r.distance=TRACK_METERS*TOTAL_LAPS
        r.update(.016,accelerate=True)
        before=r.seconds
        r.update(.016,accelerate=True)
        self.assertEqual(r.seconds,before)

    def test_website_item_effects(self):
        r=RaceState()
        r.item='ESCUDO'
        self.assertTrue(r.use_item())
        self.assertEqual(r.shield,7)
        r.item='NITRO';r.nitro=.25;r.use_item()
        self.assertAlmostEqual(r.nitro,.80)
        r.item='ONDA';r.use_item()
        self.assertEqual(r.emp,2.5)

    def test_wraparound_progress(self):
        self.assertEqual(mod(TRACK_METERS+200,TRACK_METERS),200)
        self.assertEqual(mod(-100,TRACK_METERS),TRACK_METERS-100)


if __name__=='__main__':unittest.main()
