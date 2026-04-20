"""GAIL (Generative Adversarial Imitation Learning) algorithm."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

from src.learning.imitation._base import ImitationLearner, TrainingConfig
from src.learning.imitation.dataset import DemonstrationDataset


class GAIL(ImitationLearner):
    """Generative Adversarial Imitation Learning.

    GAIL uses a discriminator to distinguish between expert and
    policy trajectories, training the policy to fool the discriminator.

    This is a simplified implementation - full GAIL requires
    integration with RL algorithms like PPO.
    """

    def __init__(
        self,
        observation_dim: int,
        action_dim: int,
        config: TrainingConfig | None = None,
        device: str = "cpu",
    ) -> None:
        """Initialize GAIL learner."""
        if not (observation_dim is not None):
            raise ValueError("observation_dim must be provided")
        if not (observation_dim is not None):
            raise ValueError("observation_dim must be provided")
        super().__init__(observation_dim, action_dim, config, device)
        self._policy: list[dict[str, NDArray[np.floating]]] = []
        self._discriminator: list[dict[str, NDArray[np.floating]]] = []
        self._build_networks()

    def _build_networks(self) -> None:
        """Build policy and discriminator networks."""
        # Build simple MLP policy
        policy_layers = []
        input_dim = self.observation_dim

        for hidden_dim in self.config.hidden_sizes:
            policy_layers.append(
                {
                    "W": np.random.randn(input_dim, hidden_dim) * 0.01,
                    "b": np.zeros(hidden_dim),
                }
            )
            input_dim = hidden_dim

        policy_layers.append(
            {
                "W": np.random.randn(input_dim, self.action_dim) * 0.01,
                "b": np.zeros(self.action_dim),
            }
        )
        self._policy = policy_layers  # type: ignore[assignment]

        # Build discriminator (state-action -> [0, 1])
        disc_layers = []
        input_dim = self.observation_dim + self.action_dim

        for hidden_dim in self.config.hidden_sizes:
            disc_layers.append(
                {
                    "W": np.random.randn(input_dim, hidden_dim) * 0.01,
                    "b": np.zeros(hidden_dim),
                }
            )
            input_dim = hidden_dim

        disc_layers.append(
            {
                "W": np.random.randn(input_dim, 1) * 0.01,
                "b": np.zeros(1),
            }
        )
        self._discriminator = disc_layers  # type: ignore[assignment]

    def _forward_policy(self, x: NDArray[np.floating]) -> NDArray[np.floating]:
        """Forward pass through policy network."""
        if not (x is not None):
            raise ValueError("x must be provided")
        if not (x is not None):
            raise ValueError("x must be provided")
        for i, layer in enumerate(self._policy):
            x = x @ layer["W"] + layer["b"]
            if i < len(self._policy) - 1:
                x = np.maximum(0, x)  # ReLU
        return x

    @staticmethod
    def _sigmoid(x: NDArray[np.floating]) -> NDArray[np.floating]:
        """Numerically stable sigmoid: clips x to avoid overflow."""
        x = np.clip(x, -50.0, 50.0)
        return 1.0 / (1.0 + np.exp(-x))

    def _forward_discriminator(
        self, state: NDArray[np.floating], action: NDArray[np.floating]
    ) -> NDArray[np.floating]:
        """Forward pass through discriminator."""
        if not (state is not None):
            raise ValueError("state must be provided")
        if not (state is not None):
            raise ValueError("state must be provided")
        x = np.concatenate([state, action], axis=-1)
        for i, layer in enumerate(self._discriminator):
            x = x @ layer["W"] + layer["b"]
            if i < len(self._discriminator) - 1:
                x = np.maximum(0, x)  # ReLU
            else:
                x = self._sigmoid(x)
        return x

    def _backward_discriminator(
        self,
        states: NDArray[np.floating],
        actions: NDArray[np.floating],
        targets: NDArray[np.floating],
    ) -> list[dict[str, NDArray[np.floating]]]:
        """Compute discriminator gradients via backpropagation for BCE loss."""
        batch_size = len(states)
        x = np.concatenate([states, actions], axis=-1)

        # Forward pass with activation cache
        activations: list[NDArray[np.floating]] = [x]
        for i, layer in enumerate(self._discriminator):
            z = x @ layer["W"] + layer["b"]
            if i < len(self._discriminator) - 1:
                x = np.maximum(0, z)
            else:
                x = self._sigmoid(z)
            activations.append(x)

        # Backward pass: d(BCE)/dz = D - target for sigmoid output layer
        delta: NDArray[np.floating] = (activations[-1] - targets) / batch_size
        gradients: list[dict[str, NDArray[np.floating]]] = []

        for i in range(len(self._discriminator) - 1, -1, -1):
            a = activations[i]
            grad_W: NDArray[np.floating] = a.T @ delta
            grad_b: NDArray[np.floating] = delta.sum(axis=0)
            gradients.insert(0, {"W": grad_W, "b": grad_b})
            if i > 0:
                delta = delta @ self._discriminator[i]["W"].T
                delta = delta * (activations[i] > 0)

        return gradients

    def train(
        self,
        dataset: DemonstrationDataset,
        validation_split: float = 0.1,
    ) -> dict[str, list[float]]:
        """Train GAIL.

        Note: This is a simplified version. Full GAIL training
        requires environment interaction and RL algorithm integration.

        Args:
            dataset: Expert demonstration dataset.
            validation_split: Fraction for validation.

        Returns:
            Training history.
        """
        # Get expert data
        if not (dataset is not None):
            raise ValueError("dataset must be provided")
        if not (dataset is not None):
            raise ValueError("dataset must be provided")
        expert_states, expert_actions = dataset.to_state_action_pairs()

        if len(expert_states) == 0:
            raise ValueError("Dataset has no state-action pairs")

        history: dict[str, list[float]] = {"discriminator_loss": [], "policy_loss": []}
        lr = self.config.learning_rate

        for _epoch in range(self.config.epochs):
            # Generate policy data (self-play would go here)
            # For simplicity, we just use noise-perturbed expert data
            noise = np.random.randn(*expert_states.shape) * 0.1
            policy_states = expert_states + noise
            policy_actions = self._forward_policy(policy_states)

            # Train discriminator
            expert_preds = self._forward_discriminator(expert_states, expert_actions)
            policy_preds = self._forward_discriminator(policy_states, policy_actions)

            # Binary cross entropy
            eps = 1e-8
            disc_loss = -np.mean(
                np.log(expert_preds + eps) + np.log(1 - policy_preds + eps)
            )

            # Expert targets=1, policy targets=0 — combine into one backward pass
            combined_states = np.concatenate([expert_states, policy_states], axis=0)
            combined_actions = np.concatenate([expert_actions, policy_actions], axis=0)
            n_expert = len(expert_states)
            n_policy = len(policy_states)
            combined_targets = np.concatenate(
                [
                    np.ones((n_expert, 1), dtype=np.float64),
                    np.zeros((n_policy, 1), dtype=np.float64),
                ],
                axis=0,
            )
            disc_grads = self._backward_discriminator(
                combined_states, combined_actions, combined_targets
            )
            for layer, grad in zip(self._discriminator, disc_grads, strict=True):
                layer["W"] -= lr * (grad["W"] + self.config.weight_decay * layer["W"])
                layer["b"] -= lr * grad["b"]

            # Policy reward is discriminator output
            policy_reward = -np.log(1 - policy_preds + eps)
            policy_loss = -np.mean(policy_reward)

            history["discriminator_loss"].append(float(disc_loss))
            history["policy_loss"].append(float(policy_loss))

        self._training_history = history
        return history

    def predict(
        self,
        observation: NDArray[np.floating],
        deterministic: bool = True,
    ) -> NDArray[np.floating]:
        """Predict action from observation.

        Args:
            observation: Current observation.
            deterministic: If True, return deterministic action.

        Returns:
            Predicted action.
        """
        if not (observation is not None):
            raise ValueError("observation must be provided")
        if not (observation is not None):
            raise ValueError("observation must be provided")
        if observation.ndim == 1:
            observation = observation.reshape(1, -1)

        action = self._forward_policy(observation)

        if not deterministic:
            action = action + np.random.randn(*action.shape) * 0.1

        if observation.shape[0] == 1:
            action = action.flatten()

        return action

    def get_reward(
        self,
        state: NDArray[np.floating],
        action: NDArray[np.floating],
    ) -> float:
        """Get GAIL reward for state-action pair.

        Args:
            state: Current state.
            action: Taken action.

        Returns:
            GAIL reward value.
        """
        if not (state is not None):
            raise ValueError("state must be provided")
        if not (state is not None):
            raise ValueError("state must be provided")
        if state.ndim == 1:
            state = state.reshape(1, -1)
        if action.ndim == 1:
            action = action.reshape(1, -1)

        disc_output = self._forward_discriminator(state, action)
        # Reward is -log(1 - D(s,a)); mean over batch if called with multiple rows
        return float(np.mean(-np.log(1 - disc_output + 1e-8)))

    def save(self, path: str | Path) -> None:
        """Save GAIL networks."""
        if not (path is not None):
            raise ValueError("path must be provided")
        if not (path is not None):
            raise ValueError("path must be provided")
        path = Path(path)
        data = {
            "observation_dim": self.observation_dim,
            "action_dim": self.action_dim,
            "policy": [
                {"W": layer["W"].tolist(), "b": layer["b"].tolist()}
                for layer in self._policy
            ],
            "discriminator": [
                {"W": layer["W"].tolist(), "b": layer["b"].tolist()}
                for layer in self._discriminator
            ],
        }
        np.savez(path, **{k: np.array(v, dtype=object) for k, v in data.items()})  # type: ignore[arg-type]

    def load(self, path: str | Path) -> None:
        """Load GAIL networks."""
        if not (path is not None):
            raise ValueError("path must be provided")
        if not (path is not None):
            raise ValueError("path must be provided")
        path = Path(path)
        data = np.load(path, allow_pickle=True)

        self.observation_dim = int(data["observation_dim"])
        self.action_dim = int(data["action_dim"])

        policy_data = data["policy"].tolist()
        self._policy = [
            {"W": np.array(layer["W"]), "b": np.array(layer["b"])}
            for layer in policy_data
        ]

        disc_data = data["discriminator"].tolist()
        self._discriminator = [
            {"W": np.array(layer["W"]), "b": np.array(layer["b"])}
            for layer in disc_data
        ]
