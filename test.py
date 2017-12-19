import unittest

import Runner

P = Runner.Player('IMG/Hero/ch1.png', (16, 16))


class TestClassPlayer(unittest.TestCase):
    def test_init(self):
        self.assertEqual(P.standing.__len__(), 4)
        self.assertEqual(P.anim_objs.__len__(), 4)

    def test_func(self):
        self.assertEqual(P.get_pos(), (0, 0))
        self.assertEqual(P.get_pos_cam(), (16, 16))
        # Check (0, 0)
        list_in = [(dx, dy) for dx in range(-1, 2) for dy in range(-1, 2)]
        list_out = [(dx, dy) for dx in [0, 0, 1] for dy in [0, 0, 1]]
        for a, b in zip(list_in, list_out):
            self.assertEqual(P.check_pos(100, 100, a[0], a[1]), b)

        P.move(0, 68)
        self.assertEqual(P.get_pos(), (0, 68))
        self.assertEqual(P.get_pos_cam(), (16, 84))
        # Check (0, 100)
        list_out = [(dx, dy) for dx in [0, 0, 1] for dy in [-1, 0, 0]]
        for a, b in zip(list_in, list_out):
            self.assertEqual(P.check_pos(100, 100, a[0], a[1]), b)

        P.move(68, -68)  # (68, 0)
        self.assertEqual(P.get_pos(), (68, 0))
        self.assertEqual(P.get_pos_cam(), (84, 16))
        # Check (100, 0)
        list_out = [(dx, dy) for dx in [-1, 0, 0] for dy in [0, 0, 1]]
        for a, b in zip(list_in, list_out):
            self.assertEqual(P.check_pos(100, 100, a[0], a[1]), b)

        P.move(0, 68)  # (68, 68)
        self.assertEqual(P.get_pos(), (68, 68))
        self.assertEqual(P.get_pos_cam(), (84, 84))
        # Check (100, 100)
        list_out = [(dx, dy) for dx in [-1, 0, 0] for dy in [-1, 0, 0]]
        for a, b in zip(list_in, list_out):
            self.assertEqual(P.check_pos(100, 100, a[0], a[1]), b)


if __name__ == '__main__':
    unittest.main()
