from typing import Any, SupportsFloat
import gymnasium as gym
import numpy as np
import matplotlib.pyplot as plt

from cec2017.functions import *
from algorithm import evolutionary_algorithm, CrossingType, calculate_avg_distance
from q_learning import q_learning_greedy


def generate_start_population(population_size: int, dimension: int, min_range: float, max_range: float) -> np.array:
    return np.array([np.random.uniform(min_range, max_range, dimension) for _ in range(population_size)])


def _to1DSpace(space: tuple[int, int], coord: tuple[int, int]) -> int:
    return coord[0] * space[1] + coord[1]


def _to2DSpace(space: tuple[int, int], coord: int) -> tuple[int, int]:
    return (coord // space[1], coord % space[1])


class EvolutionaryEnv(gym.Env):
    def __init__(self, max_steps: int) -> None:
        self._action_dim = (len(CrossingType), 5)
        self._observation_dim = (10, 100)
        
        self._success_bins = np.linspace(0, 1, num=self._observation_dim[0] - 1)
        self._distance_bins = np.linspace(0, 10e10, num=self._observation_dim[1] - 1)
        self._mutation_probabilities = np.linspace(0, 1, num=self._action_dim[1])

        self.action_space = gym.spaces.Discrete(self._action_dim[0] * self._action_dim[1])
        self.observation_space = gym.spaces.Discrete(self._observation_dim[0] * self._observation_dim[1])

        self._max_steps = max_steps
        self._current_step = 0
        self._population = generate_start_population(200, 10, -50, 50) # aktualny stan algorytmu ewolucyjnego

        self.best_quality = 0
        self._current_success = 0
        self._current_distance = np.digitize(calculate_avg_distance(self._population), self._distance_bins)

    def step(self, action: Any) -> tuple[Any, SupportsFloat, bool, bool, dict[str, Any]]:
        
        
        selected_crossover, selected_mutation = _to2DSpace(self._action_dim, action)

        _, self.best_quality, success_percent, avg_distance = evolutionary_algorithm(f=f7,
                                    population=self._population,
                                    mutation_value=50.,
                                    mutation_probability=self._mutation_probabilities[selected_mutation],
                                    elite_size=20,
                                    t_max=10,
                                    crossing_type=CrossingType(selected_crossover),
                                    crossing_probability=0
                                    )
        
        success = np.digitize(success_percent, self._success_bins)
        distance = np.digitize(avg_distance, self._distance_bins)
        
        reward = self._calculate_reward(success, distance)
        terminated = self._current_step >= self._max_steps

        self._current_success = success
        self._current_distance = distance
        self._current_step += 1

        return _to1DSpace(self._observation_dim, (self._current_success, self._current_distance)), reward, terminated, False, {}
    
    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None) -> tuple[Any, dict[str, Any]]:
        self._current_step = 0
        self._population = generate_start_population(200, 10, -50, 50) # aktualny stan algorytmu ewolucyjnego

        self.best_quality = 0
        self._current_success = 0
        self._current_distance = np.digitize(calculate_avg_distance(self._population), self._distance_bins)
        return _to1DSpace(self._observation_dim, (self._current_success, self._current_distance)), {}

    def _calculate_reward(self, success, distance):
        reward = -1
        if success > self._current_success:
            reward += 10
        if distance < self._current_distance:
            reward += 10
        return reward


if __name__ == "__main__":
    env = EvolutionaryEnv(20)
    q_learning_greedy(env, 0.8, 0.9, 50, 0.1, 5)
    plt.show()