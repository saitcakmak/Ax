#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from copy import deepcopy

import numpy as np
from ax.core.observation import ObservationData
from ax.exceptions.core import UserInputError
from ax.modelbridge.transforms.winsorize import Winsorize, WinsorizationConfig
from ax.utils.common.testutils import TestCase
from ax.utils.testing.core_stubs import (
    get_optimization_config,
    get_multi_objective_optimization_config,
)


class WinsorizeTransformTest(TestCase):
    def setUp(self):
        self.obsd1 = ObservationData(
            metric_names=["m1", "m2", "m2"],
            means=np.array([0.0, 0.0, 1.0]),
            covariance=np.array([[1.0, 0.2, 0.4], [0.2, 2.0, 0.8], [0.4, 0.8, 3.0]]),
        )
        self.obsd2 = ObservationData(
            metric_names=["m1", "m1", "m2", "m2"],
            means=np.array([1.0, 2.0, 2.0, 1.0]),
            covariance=np.array(
                [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.2, 0.4],
                    [0.0, 0.2, 2.0, 0.8],
                    [0.0, 0.4, 0.8, 3.0],
                ]
            ),
        )
        self.t = Winsorize(
            search_space=None,
            observation_features=None,
            observation_data=[deepcopy(self.obsd1), deepcopy(self.obsd2)],
            config={
                "winsorization_config": WinsorizationConfig(upper_quantile_margin=0.2)
            },
        )
        self.t1 = Winsorize(
            search_space=None,
            observation_features=None,
            observation_data=[deepcopy(self.obsd1), deepcopy(self.obsd2)],
            config={
                "winsorization_config": WinsorizationConfig(upper_quantile_margin=0.8)
            },
        )
        self.t2 = Winsorize(
            search_space=None,
            observation_features=None,
            observation_data=[deepcopy(self.obsd1), deepcopy(self.obsd2)],
            config={
                "winsorization_config": WinsorizationConfig(lower_quantile_margin=0.2)
            },
        )
        self.t3 = Winsorize(
            search_space=None,
            observation_features=None,
            observation_data=[deepcopy(self.obsd1), deepcopy(self.obsd2)],
            config={
                "winsorization_config": {
                    "m1": WinsorizationConfig(upper_quantile_margin=0.6),
                    "m2": WinsorizationConfig(
                        upper_quantile_margin=0.6, upper_boundary=1.9
                    ),
                }
            },
        )
        self.t4 = Winsorize(
            search_space=None,
            observation_features=None,
            observation_data=[deepcopy(self.obsd1), deepcopy(self.obsd2)],
            config={
                "winsorization_config": {
                    "m1": WinsorizationConfig(lower_quantile_margin=0.8),
                    "m2": WinsorizationConfig(
                        lower_quantile_margin=0.8, lower_boundary=0.3
                    ),
                }
            },
        )

        self.obsd3 = ObservationData(
            metric_names=["m3", "m3", "m3", "m3"],
            means=np.array([0.0, 1.0, 5.0, 3.0]),
            covariance=np.eye(4),
        )
        self.t5 = Winsorize(
            search_space=None,
            observation_features=None,
            observation_data=[
                deepcopy(self.obsd1),
                deepcopy(self.obsd2),
                deepcopy(self.obsd3),
            ],
            config={
                "winsorization_config": {
                    "m1": WinsorizationConfig(upper_quantile_margin=0.6),
                    "m2": WinsorizationConfig(lower_quantile_margin=0.4),
                }
            },
        )
        self.t6 = Winsorize(
            search_space=None,
            observation_features=None,
            observation_data=[deepcopy(self.obsd1), deepcopy(self.obsd2)],
            config={
                "winsorization_config": {
                    "m1": WinsorizationConfig(upper_quantile_margin=0.6),
                    "m2": WinsorizationConfig(
                        lower_quantile_margin=0.4, lower_boundary=0.0
                    ),
                }
            },
        )

    def testInit(self):
        self.assertEqual(self.t.percentiles["m1"], (0.0, 2.0))
        self.assertEqual(self.t.percentiles["m2"], (0.0, 2.0))
        self.assertEqual(self.t1.percentiles["m1"], (0.0, 1.0))
        self.assertEqual(self.t1.percentiles["m2"], (0.0, 1.0))
        self.assertEqual(self.t2.percentiles["m1"], (0.0, 2.0))
        self.assertEqual(self.t2.percentiles["m2"], (0.0, 2.0))
        with self.assertRaises(ValueError):
            Winsorize(search_space=None, observation_features=[], observation_data=[])

    def testTransformObservations(self):
        observation_data = self.t1.transform_observation_data(
            [deepcopy(self.obsd1)], []
        )[0]
        self.assertListEqual(list(observation_data.means), [0.0, 0.0, 1.0])
        observation_data = self.t1.transform_observation_data(
            [deepcopy(self.obsd2)], []
        )[0]
        self.assertListEqual(list(observation_data.means), [1.0, 1.0, 1.0, 1.0])
        observation_data = self.t2.transform_observation_data(
            [deepcopy(self.obsd1)], []
        )[0]
        self.assertListEqual(list(observation_data.means), [0.0, 0.0, 1.0])
        observation_data = self.t2.transform_observation_data(
            [deepcopy(self.obsd2)], []
        )[0]
        self.assertListEqual(list(observation_data.means), [1.0, 2.0, 2.0, 1.0])

    def testInitPercentileBounds(self):
        self.assertEqual(self.t3.percentiles["m1"], (0.0, 1.0))
        self.assertEqual(self.t3.percentiles["m2"], (0.0, 1.9))
        self.assertEqual(self.t4.percentiles["m1"], (1.0, 2.0))
        self.assertEqual(self.t4.percentiles["m2"], (0.3, 2.0))

    def testTransformObservationsPercentileBounds(self):
        observation_data = self.t3.transform_observation_data(
            [deepcopy(self.obsd1)], []
        )[0]
        self.assertListEqual(list(observation_data.means), [0.0, 0.0, 1.0])
        observation_data = self.t3.transform_observation_data(
            [deepcopy(self.obsd2)], []
        )[0]
        self.assertListEqual(list(observation_data.means), [1.0, 1.0, 1.9, 1.0])
        observation_data = self.t4.transform_observation_data(
            [deepcopy(self.obsd1)], []
        )[0]
        self.assertListEqual(list(observation_data.means), [1.0, 0.3, 1.0])
        observation_data = self.t4.transform_observation_data(
            [deepcopy(self.obsd2)], []
        )[0]
        self.assertListEqual(list(observation_data.means), [1.0, 2.0, 2.0, 1.0])

    def testTransformObservationsDifferentLowerUpper(self):
        observation_data = self.t5.transform_observation_data(
            [deepcopy(self.obsd2)], []
        )[0]
        self.assertEqual(self.t5.percentiles["m1"], (0.0, 1.0))
        self.assertEqual(self.t5.percentiles["m2"], (1.0, 2.0))
        self.assertEqual(self.t5.percentiles["m3"], (-float("inf"), float("inf")))
        self.assertListEqual(list(observation_data.means), [1.0, 1.0, 2.0, 1.0])
        # Nothing should happen to m3
        observation_data = self.t5.transform_observation_data(
            [deepcopy(self.obsd3)], []
        )[0]
        self.assertListEqual(list(observation_data.means), [0.0, 1.0, 5.0, 3.0])
        # With winsorization boundaries
        observation_data = self.t6.transform_observation_data(
            [deepcopy(self.obsd2)], []
        )[0]
        self.assertEqual(self.t6.percentiles["m1"], (0.0, 1.0))
        self.assertEqual(self.t6.percentiles["m2"], (0.0, 2.0))
        self.assertListEqual(list(observation_data.means), [1.0, 1.0, 2.0, 1.0])

    def test_optimization_config_default(self):
        # 20% winsorization by default
        optimization_config = get_optimization_config()
        percentiles = get_default_transform_percentiles(
            optimization_config=optimization_config
        )
        self.assertDictEqual(percentiles, {"m1": (1, 5)})

        # Don't winsorize by default for MOO problems
        optimization_config = get_multi_objective_optimization_config()
        percentiles = get_default_transform_percentiles(
            optimization_config=optimization_config
        )
        self.assertDictEqual(percentiles, {"m1": (-float("inf"), float("inf"))})

        # Don't winsorize if optimization_config is mistyped
        optimization_config = "not an optimization config"
        with self.assertRaisesRegex(
            UserInputError,
            "Expected `optimization_config` of type `OptimizationConfig`",
        ):
            get_default_transform_percentiles(optimization_config=optimization_config)


def get_default_transform_percentiles(optimization_config, obs_data_len=6):
    obsd = ObservationData(
        metric_names=["m1"] * obs_data_len,
        means=np.array(range(obs_data_len)),
        covariance=np.eye(obs_data_len),
    )
    transform = Winsorize(
        search_space=None,
        observation_features=None,
        observation_data=[deepcopy(obsd)],
        config={"optimization_config": optimization_config},
    )
    return transform.percentiles
