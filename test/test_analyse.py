"""This test script contains tests for analyze.py"""
# -*- coding: utf-8 -*-

import os
import numpy as np

import ABXpy.task
import ABXpy.distances.distances as distances
import ABXpy.distances.metrics.cosine as cosine
import ABXpy.distances.metrics.dtw as dtw
import ABXpy.score as score
import ABXpy.analyze as analyze

import aux.generate as generate
import aux.compare as compare

FROZEN_FOLDER = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'frozen_files')


def frozen_file(ext):
    return os.path.join(FROZEN_FOLDER, 'data') + '.' + ext


def dtw_cosine_distance(x, y):
    return dtw.dtw(x, y, cosine.cosine_distance)


def test_analyze():
    try:
        if not os.path.exists('test_items'):
            os.makedirs('test_items')
        item_file = 'test_items/data.item'
        feature_file = 'test_items/data.features'
        distance_file = 'test_items/data.distance'
        scorefilename = 'test_items/data.score'
        taskfilename = 'test_items/data.abx'
        analyzefilename = 'test_items/data.csv'

        generate.items_and_features(3, 3, 1, item_file, 2, 3, feature_file)
        task = ABXpy.task.Task(item_file, 'c0', 'c1', 'c2')
        task.generate_triplets(taskfilename)
        distances.compute_distances(feature_file, '/features/', taskfilename,
                                    distance_file, dtw_cosine_distance, n_cpu=1)
        score.score(taskfilename, distance_file, scorefilename)
        analyze.analyze(taskfilename, scorefilename, analyzefilename)
    finally:
        try:
            os.remove(item_file)
            os.remove(feature_file)
            os.remove(taskfilename)
            os.remove(distance_file)
            os.remove(scorefilename)
            os.remove(analyzefilename)
        except:
            pass


def test_threshold_analyze():
    try:
        if not os.path.exists('test_items'):
            os.makedirs('test_items')
        item_file = 'test_items/data.item'
        feature_file = 'test_items/data.features'
        distance_file = 'test_items/data.distance'
        scorefilename = 'test_items/data.score'
        taskfilename = 'test_items/data.abx'
        analyzefilename = 'test_items/data.csv'
        threshold=2

        generate.items_and_features(3, 3, 1, item_file, 2, 3, feature_file)
        task = ABXpy.task.Task(item_file, 'c0', 'c1', 'c2')
        task.generate_triplets(taskfilename, threshold=threshold)
        distances.compute_distances(feature_file, '/features/', taskfilename,
                                    distance_file, dtw_cosine_distance, n_cpu=1)
        score.score(taskfilename, distance_file, scorefilename)
        analyze.analyze(taskfilename, scorefilename, analyzefilename)
        number_triplets = np.loadtxt(analyzefilename, dtype=int,
                                     delimiter='\t', skiprows=1, usecols=[-1])
        assert np.all(number_triplets == threshold)
    finally:
        try:
            os.remove(item_file)
            os.remove(feature_file)
            os.remove(taskfilename)
            os.remove(distance_file)
            os.remove(scorefilename)
            os.remove(analyzefilename)
        except:
            pass


def test_frozen_analyze():
    """Frozen analyze compare the results of a previously "frozen" run with
    a new one, asserting that the code did not change in behaviour.
    """
    try:
        if not os.path.exists('test_items'):
            os.makedirs('test_items')
        item_file = frozen_file('item')
        feature_file = frozen_file('features')
        distance_file = 'test_items/data.distance'
        scorefilename = 'test_items/data.score'
        taskfilename = 'test_items/data.abx'
        analyzefilename = 'test_items/data.csv'

        task = ABXpy.task.Task(item_file, 'c0', 'c1', 'c2')
        task.generate_triplets(taskfilename)
        distances.compute_distances(feature_file, '/features/', taskfilename,
                                    distance_file, dtw_cosine_distance, n_cpu=1)
        score.score(taskfilename, distance_file, scorefilename)
        analyze.analyze(taskfilename, scorefilename, analyzefilename)

        # assert items.h5cmp(taskfilename, frozen_file('abx'))
        # assert items.h5cmp(distance_file, frozen_file('distance'))
        # assert items.h5cmp(scorefilename, frozen_file('score'))
        assert compare.csvcmp(analyzefilename, frozen_file('csv'))

    finally:
        try:
            os.remove(taskfilename)
            os.remove(distance_file)
            os.remove(scorefilename)
            os.remove(analyzefilename)
        except:
            pass

test_threshold_analyze()