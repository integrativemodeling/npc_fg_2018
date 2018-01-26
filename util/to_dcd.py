#!/usr/bin/env python

"""This is a simple script to convert an ensemble of output models
   (multiple single-frame RMF files) into DCD (CHARMM/NAMD) trajectories,
   with each bead represented as a single 'atom', in residue number order
   (the same order as in the NPC mmCIF file).

   We use the updated version of MDTools that's bundled with Chimera, so you
   may need to change sys.path accordingly, below.
"""

from __future__ import print_function
import glob
import os
import sys
sys.path.append('/opt/chimera-1.11-1.fc24/share/Trajectory/DCD/MDToolsMarch97/')
import md
import RMF

class DCDOutput(object):
    """Dump a series of FG repeat coordinates from RMFs to a DCD file."""

    def __init__(self, fname, comps, reference_coords):
        self.fname = fname
        self.comps = comps
        self.reference_coords = reference_coords
        self.n_ref_coords = self._count_coords(reference_coords)
        self._init_dcd(self.n_ref_coords)
    
    def _count_coords(self, coords):
        return sum(len(b) for b in coords.values())

    def dump(self, coords):
        """Dump a single RMF to the DCD file"""
        len_coords = self._count_coords(coords)
        assert(len_coords == len(self._ag.atoms))
        for atom, coord in zip(self._ag.atoms, self._get_coords(coords)):
            atom.x, atom.y, atom.z = coord
        self._d.append()

    def _init_dcd(self, n_coords):
        self._ag = md.AtomGroup()
        for i in range(n_coords):
            self._ag.atoms.append(md.Atom())
        self._d = md.DCDWrite(self.fname, self._ag)

    def _get_coords(self, coords):
        """Get all bead coordinates in the same order as in the mmCIF file"""
        for comp in self.comps:
            for coord in coords[comp]:
                yield coord


class FGRepeatRMFReader(object):
    """Read FG repeat coordinates from a set of RMF files"""
    beadsize = 20

    ranges = {'Nsp1': (600,1),
              'Nup1': (352,1049),
              'Nup49': (200,1),
              'Nup57': (200,1),
              'Nup60': (399,498),
              'Nup100': (550,11),
              'Nup116': (750,11),
              'Nup145': (200,1),
              'Nup159': (1081,482)}
    copies = {'Nsp1': ('.1', '.2', '.3', '.4', '.3@11', '.4@11'),
              'Nup1': ('',),
              'Nup49': ('.1', '.2', '.1@11', '.2@11'),
              'Nup57': ('.1', '.2', '.1@11', '.2@11'),
              'Nup60': ('.1', '.2'),
              'Nup100': ('.1', '.2'),
              'Nup116': ('.1', '.2'),
              'Nup145': ('.1', '.2'),
              'Nup159': ('.1', '.2')}

    def get_number_of_beads(self, name):
        rng = self.ranges[name]
        return (max(rng) - min(rng) + self.beadsize) // self.beadsize

    def read(self, rmf):
        rmf.set_current_frame(RMF.FrameID(0))
        node_for_nup = {}
        for node in rmf.get_root_node().get_children():
            if node.get_name() in self.copies:
                node_for_nup[node.get_name()] = node
        beads = {}
        for nup in self.copies:
            self._read_nup(nup, rmf, node_for_nup, beads)
        return beads

    def get_copy_names(self, name):
        """Yield all names of Nup copies, including symmetry units.
           These names should match the ordering of FG repeats in the RMF
           file."""
        for c in self.copies[name]:
            if c.endswith('@11'):
                # NPC symmetry copies alternate positive/negative rotations,
                # while FG Nup copies are always positive rotations
                for symm in ('@11', '@12', '@14', '@16', '@18', '@17',
                             '@15', '@13'):
                    yield(name + c[:-3] + symm)
            else:
                for symm in ('', '@2', '@4', '@6', '@8', '@7', '@5', '@3'):
                    yield(name + c + symm)

    def _read_nup(self, name, rh, nodemap, spheres):
        rff = RMF.ReferenceFrameConstFactory(rh)
        pf = RMF.ParticleConstFactory(rh)
        node = nodemap[name]
        node_copies = node.get_children()
        assert(len(node_copies) == len(self.copies[name]) * 8)
        for nc, copyname in zip(node_copies, self.get_copy_names(name)):
            node_beads = nc.get_children()
            # First bead is anchor
            assert(len(node_beads) == self.get_number_of_beads(name) + 1)
            spheres[copyname] = s = []
            for b in node_beads[1:]:
                assert(pf.get_is(b))
                assert(rff.get_is(b))
#               radius = pf.get(b).get_radius()
                coord = rff.get(b).get_translation()
                s.append(tuple(coord))
            # mmCIF output is always N terminus to C terminus, so if this
            # FG repeat is stored C to N, reverse it
            rng = self.ranges[name]
            if rng[1] < rng[0]:
                s.reverse()


class CifParser(object):
    """Read an NPC mmCIF file.
       Read reference coordinates plus the order of components from the mmCIF
       file. This is a pretty simple parser, and will need to be updated
       if the formatting of the mmCIF file changes."""

    def _parse_struct_asym(self, fh):
        """Get a mapping from asym_ids to IMP component names"""
        asym_from_comp = {}
        for line in fh:
            if line.startswith('_'): continue
            if line.startswith('#'):
                return asym_from_comp
            asym_id, entity_id, imp_name = line.rstrip('\r\n').split()
            asym_from_comp[imp_name] = asym_id

    def _parse_obj_site(self, fh, asym_from_comp, model_num):
        """Get reference bead coordinates and the correct component ordering"""
        line_end = ' %s\n' % model_num
        coords = {}
        comps = []
        current_asym = None
        comp_from_asym = {}
        for comp, asym in asym_from_comp.items():
            comp_from_asym[asym] = comp
        for line in fh:
            if line.startswith('_'): continue
            if line.startswith('#'):
                return coords, comps
            if line.endswith(' 2\n'):
                sphere_obj = line.split()
                asym_id = sphere_obj[4]
                comp = comp_from_asym[asym_id]
                if asym_id != current_asym:
                    current_asym = asym_id
                    comps.append(comp)
                    coords[comp] = []
                coords[comp].append(tuple(float(x) for x in sphere_obj[5:8]))
        return coords, comps

    def parse(self, fh, model_num):
        asym_from_comp = {}
        for line in fh:
            if line == '_struct_asym.id\n':
                asym_from_comp = self._parse_struct_asym(fh)
            elif line == '_ihm_sphere_obj_site.ordinal_id\n':
                coords, comps = self._parse_obj_site(fh, asym_from_comp,
                                                     model_num)
                return coords, comps

def diff_coord2(a, b):
    """Return the squared distance between two xyz coordinates"""
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    dz = a[2] - b[2]
    return dx*dx + dy*dy + dz*dz

def check_coords(coords, comps, ref_coords):
    """Compare RMF coordinates with the mmCIF reference"""
    for comp in comps:
        for coord, ref_coord in zip(coords[comp], ref_coords[comp]):
            if diff_coord2(coord, ref_coord) > 0.1:
                raise ValueError("RMF coordinate %s does not match "
                                 "reference in mmCIF file %s\n"
                                 % (coord, ref_coord))

def parse_args():
    if len(sys.argv) != 5:
        print("Usage: %s path-to-8spoke.cif fg-model-num ref-rmf-name "
              "dcd-fname\n\n" % sys.argv[0], file=sys.stderr)
        # e.g. ./to_dcd.py npc-8spoke.cif 2 modelN11_101.rmf out.dcd
        sys.exit(1)
    return sys.argv[1:]

def main():
    cif_fname, fg_model_num, ref_rmf_name, dcd_fname = parse_args()

    c = CifParser()
    with open(cif_fname) as fh:
        coords, comps = c.parse(fh, fg_model_num)

    d = DCDOutput(dcd_fname, comps, coords)

    # Use first 100 models (sort so we get the same 100 each time)
    reader = FGRepeatRMFReader()
    checked = False
    for num, rmf in enumerate(sorted(glob.glob('/salilab/park4/barak/Runs/NPC_FullModel2016/FullNPC_Oct10_Cluster0model_Rg70_per_600aa_InflateObstacles_InflatedKaps/Ensemble/modelN11*.rmf'))[:100]):
        print("Handling RMF %d of 100" % (num + 1))
        r = RMF.open_rmf_file_read_only(rmf)
        beads = reader.read(r)
        d.dump(beads)
        if os.path.basename(rmf) == ref_rmf_name:
            check_coords(beads, comps, coords)
            checked = True
    if not checked:
        raise ValueError("Coordinates not checked against reference")

if __name__ == '__main__':
    main()
