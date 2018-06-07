#!/usr/bin/env python

import unittest
import os
import shutil
import sys
import subprocess
import RMF

TOPDIR = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..'))

class Tests(unittest.TestCase):
    def test_simple(self):
        """Test simple complete run"""
        output = 'test-output'
        os.chdir(TOPDIR)
        if os.path.exists(output):
            shutil.rmtree(output)
        os.mkdir(output)
        # Make initial model
        subprocess.check_call(
                ["Scripts/load_whole_new_coarse_grained_v5.py",
                 os.path.join(output, "config.pb"),
                 "InputData/47-35_1spoke.rmf3"],
                stdout=open(os.path.join(output, 'config.txt'), 'w'))
        # Check outputs
        for out in ('config.txt', 'config.pb'):
            self.assertTrue(os.path.exists(os.path.join(output, out)))

        # Run simulation
        os.chdir(output)
        subprocess.check_call(
                ["fg_simulation", "--configuration", "config.pb", "--output",
                 "output.pb", "--short_init_factor", "0.025",
                 "--short_sim_factor", "0.01", "--conformations", "movie.rmf",
                 "--random_seed", "1234"],
                stdout=open('LOG.fg_simulation', 'w'))

        # Check outputs
        r = RMF.open_rmf_file_read_only('final_conformations.rmf')
        self.assertEqual(r.get_number_of_frames(), 1)

        r = RMF.open_rmf_file_read_only('movie.rmf')
        self.assertEqual(r.get_number_of_frames(), 5)
        self.assertTrue(os.path.exists('output.pb'))
        self.assertTrue(os.path.exists('output.pb.hdf5'))

if __name__ == '__main__':
    unittest.main()
