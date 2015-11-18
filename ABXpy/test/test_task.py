"""This script contains test classes of task.py"""

import h5py
import os
import numpy as np
import pytest

import ABXpy.task
import ABXpy.misc.items as items


def tables_equivalent(t1, t2):
    """Returns True if each element of t2 is found in t1."""
    if not t1.shape == t2.shape:
        return False

    # not optimized, but unimportant
    for a1 in t1:
        res = False
        for a2 in t2:
            if np.array_equal(a1, a2):
                res = True
        if not res:
            return False

    return True


def get_triplets(hdf5file, by):
    triplet_db = hdf5file['triplets']
    triplets = triplet_db['data']
    by_index = list(hdf5file['bys']).index(by)
    triplets_index = triplet_db['by_index'][by_index]
    return triplets[slice(*triplets_index)]


def get_pairs(hdf5file, by):
    pairs_db = hdf5file['unique_pairs']
    pairs = pairs_db['data']
    pairs_index = pairs_db.attrs[by][1:3]
    return pairs[slice(*pairs_index)]


# test1, triplets and pairs verification
def test_basic():
    items.generate_testitems(2, 3, name='data.item')
    try:
        os.remove('data.item')
        os.remove('data.abx')
    except(OSError):
        pass


class TestTaskParser:
    """test of task.task_parser()"""

    def setup(self):
        self.parser = ABXpy.task.task_parser

    def test_by(self):
        by1 = self.parser('db -o c0 -b c0 -b c1').by
        by2 = self.parser('db -o c0 -b c0 c1').by
        assert by1 == by2 == ['c0', 'c1']

    def test_across(self):
        ac1 = self.parser('db -o c0 -a c0 -a c1 -a c2').across
        ac2 = self.parser('db -o c0 -a c0 c1 c2').across
        ac3 = self.parser('db -o c0 -a c0 c1 -a c2').across
        assert ac1 == ac2 == ac3 == ['c0', 'c1', 'c2']

    def test_on(self):
        assert self.parser('db -o 1').on == '1'
        assert self.parser('db -o abcd').on == 'abcd'
        assert self.parser('db -o "abcd"').on == '"abcd"'

    # @pytest.mark.xfail
    # def test_on_bad(self):
    #     """These tests lead argeparse to exit."""
    #     self.parser('db -o 1 2').on
    #     self.parser('db -o "1 2"').on


class TestTaskTripletsPairs:
    """basic stats, triplets and pairs verification."""

    def setup(self):
        items.generate_testitems(2, 3, name='data.item')
        self.task = ABXpy.task.Task('data.item', 'c0', 'c1', 'c2')

    def teardown(self):
        rm_data_files()

    def test_stats(self):
        assert self.task.stats['nb_blocks'] == 8
        assert self.task.stats['nb_triplets'] == 8
        assert self.task.stats['nb_by_levels'] == 2

    def test_triplets(self):
        self.task.generate_triplets()
        f = h5py.File('data.abx', 'r')
        triplets = f['triplets']['data'][...]
        by_indexes = f['triplets']['by_index'][...]
        triplets_block0 = triplets[slice(*by_indexes[0])]
        triplets_block1 = triplets[slice(*by_indexes[1])]
        triplets_block0 = get_triplets(f, '0')
        triplets_block1 = get_triplets(f, '1')
        triplets = np.array([[0, 1, 2], [1, 0, 3], [2, 3, 0], [3, 2, 1]])

        assert tables_equivalent(triplets, triplets_block0)
        assert tables_equivalent(triplets, triplets_block1)

    def test_pairs(self):
        self.task.generate_triplets()
        f = h5py.File('data.abx', 'r')

        pairs = [2, 6, 7, 3, 8, 12, 13, 9]
        pairs_block0 = f.get('unique_pairs/0')
        pairs_block1 = f.get('unique_pairs/1')

        assert set(pairs) == set(pairs_block0[:, 0])
        assert set(pairs) == set(pairs_block1[:, 0])


class TestTaskMultipleAcross:
    """testing with a list of across attributes, triplets verification"""

    def setup(self):
        items.generate_testitems(2, 3, name='data.item')
        self.task = ABXpy.task.Task('data.item', 'c0', ['c1', 'c2'])

    def teardown(self):
        rm_data_files()

    def test_stats(self):
        assert self.task.stats['nb_blocks'] == 8
        assert self.task.stats['nb_triplets'] == 8
        assert self.task.stats['nb_by_levels'] == 1

    def test_triplets(self):
        self.task.generate_triplets()
        f = h5py.File('data.abx', 'r')

        triplets_block = np.array(f.get('triplets/0'))
        triplets = np.array([[0, 1, 6], [1, 0, 7], [2, 3, 4], [3, 2, 5],
                             [4, 5, 2], [5, 4, 3], [6, 7, 0], [7, 6, 1]])

        assert tables_equivalent(triplets, triplets_block)


class TestTaskNoAcross:
    """testing without any across attribute"""

    def setup(self):
        items.generate_testitems(2, 3, name='data.item')
        self.task = ABXpy.task.Task('data.item', 'c0', [], 'c2')

    def teardown(self):
        rm_data_files()

    def test_stats(self):
        assert self.task.stats['nb_blocks'] == 8
        assert self.task.stats['nb_triplets'] == 16
        assert self.task.stats['nb_by_levels'] == 2

    def test_triplets(self):
        # TODO
        pass


class TestTaskMultipleBy:
    """testing for multiple by attributes"""

    def setup(self):
        items.generate_testitems(3, 4, name='data.item')
        self.task = ABXpy.task.Task('data.item', 'c0', [], ['c1', 'c2', 'c3'])

    def teardown(self):
        rm_data_files()

    def test_stats(self):
        assert self.task.stats['nb_blocks'] == 81
        assert self.task.stats['nb_triplets'] == 0
        assert self.task.stats['nb_by_levels'] == 27


class TestTaskFilter:
    """testing for a general filter (discarding last column)"""

    def setup(self):
        items.generate_testitems(2, 4, name='data.item')
        self.task = ABXpy.task.Task('data.item', 'c0', 'c1', 'c2',
                                    filters=["[attr == 0 for attr in c3]"])

    def teardown(self):
        rm_data_files()

    def test_stats(self):
        assert self.task.stats['nb_blocks'] == 8
        assert self.task.stats['nb_triplets'] == 8
        assert self.task.stats['nb_by_levels'] == 2

    def test_triplets(self):
        self.task.generate_triplets()
        f = h5py.File('data.abx', 'r')

        triplets_block0 = np.array(f.get('triplets/0'))
        triplets_block1 = np.array(f.get('triplets/1'))
        triplets = np.array([[0, 1, 2], [1, 0, 3], [2, 3, 0], [3, 2, 1]])

        assert tables_equivalent(triplets, triplets_block0)
        assert tables_equivalent(triplets, triplets_block1)

    def test_pairs(self):
        self.task.generate_triplets()
        f = h5py.File('data.abx', 'r')

        pairs = [2, 6, 7, 3, 8, 12, 13, 9]
        pairs_block0 = f.get('unique_pairs/0')
        pairs_block1 = f.get('unique_pairs/1')

        assert (set(pairs) == set(pairs_block0[:, 0]))
        assert (set(pairs) == set(pairs_block1[:, 0]))


class TestTaskFilterOnABX:
    """testing with simple filter on A, B and X, verifying triplet generation"""

    def setup(self):
        items.generate_testitems(2, 2, name='data.item')

    def teardown(self):
        rm_data_files()

    def task_filtered(self, filters):
        return ABXpy.task.Task('data.item', 'c0',filters=filters)

    def test_filter_on_A(self):
        """testing with simple filter on A"""
        filter_A = ["[attr == 0 for attr in c0_A]"]

        task = self.task_filtered(filter_A)
        stats = task.stats
        assert stats['nb_blocks'] == 4
        assert stats['nb_triplets'] == 4
        assert stats['nb_by_levels'] == 1

        task.generate_triplets()
        f = h5py.File('data.abx', 'r')

        triplets_block0 = f.get('triplets/0')
        triplets = np.array([[0, 1, 2], [0, 3, 2], [2, 1, 0], [2, 3, 0]])
        assert tables_equivalent(triplets, triplets_block0)

    def test_filter_on_B(self):
        """testing with simple filter on B"""
        filter_B = ["[attr == 0 for attr in c1_B]"]

        task = self.task_filtered(filter_B)
        stats = task.stats

        assert stats['nb_blocks'] == 4
        assert stats['nb_triplets'] == 4
        assert stats['nb_by_levels'] == 1

        task.generate_triplets()
        f = h5py.File('data.abx', 'r')
        triplets_block0 = get_triplets(f, '0')
        triplets = np.array([[0, 1, 2], [1, 0, 3], [2, 1, 0], [3, 0, 1]])
        assert tables_equivalent(triplets, triplets_block0)

    def test_filter_on_X(self):
        """testing with simple filter on X"""
        filter_X=["[attr == 0 for attr in c1_X]"]

        task = self.task_filtered(filter_X)
        stats = task.stats

        assert stats['nb_blocks'] == 4
        assert stats['nb_triplets'] == 4
        assert stats['nb_by_levels'] == 1

        task.generate_triplets()
        f = h5py.File('data.abx', 'r')
        triplets_block0 = get_triplets(f, '0')
        triplets = np.array([[2, 1, 0], [2, 3, 0], [3, 0, 1], [3, 2, 1]])
        assert tables_equivalent(triplets, triplets_block0)
