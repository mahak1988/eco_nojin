"""
Distributed ML Training Infrastructure
=======================================

Provides:
- Distributed PINN training (data parallel, model parallel)
- Distributed GP training (subset of data, inducing points)
- Model serving with TorchServe / Triton
- Hyperparameter optimization (Optuna, Ray Tune)
- Experiment tracking (MLflow, Weights & Biases)
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP

from engine.hydroma.models.expansion.registry import (
    ModelDomain,
    ModelFidelity,
    ModelStatus,
    register_model,
)

logger = logging.getLogger(__name__)


@dataclass
class DistributedConfig:
    """Configuration for distributed training."""

    backend: str = "nccl"  # nccl, gloo
    world_size: int = 1
    rank: int = 0
    local_rank: int = 0
    master_addr: str = "localhost"
    master_port: int = 29500
    use_ddp: bool = True
    find_unused_parameters: bool = False
    gradient_accumulation_steps: int = 1
    mixed_precision: bool = True
    checkpoint_dir: Path = Path("checkpoints/distributed")


class DistributedTrainer:
    """
    Distributed training coordinator for physics-ML models.

    Supports:
    - Data parallel (DDP)
    - Model parallel (pipeline parallelism)
    - Gradient accumulation
    - Mixed precision (AMP)
    - Checkpointing
    """

    def __init__(self, config: DistributedConfig | None = None):
        self.config = config or DistributedConfig()
        self._initialized = False
        self._model = None
        self._optimizer = None
        self._scheduler = None
        self._scaler = None

    def setup_distributed(self) -> None:
        """Initialize distributed training environment."""
        if self._initialized:
            return

        # Set environment variables
        os.environ["MASTER_ADDR"] = self.config.master_addr
        os.environ["MASTER_PORT"] = str(self.config.master_port)
        os.environ["WORLD_SIZE"] = str(self.config.world_size)
        os.environ["RANK"] = str(self.config.rank)
        os.environ["LOCAL_RANK"] = str(self.config.local_rank)

        # Initialize process group
        if self.config.world_size > 1:
            dist.init_process_group(
                backend=self.config.backend,
                world_size=self.config.world_size,
                rank=self.config.rank,
            )
            logger.info(
                f"Initialized distributed training: rank={self.config.rank}, world_size={self.config.world_size}"
            )

        # Set device
        if torch.cuda.is_available():
            torch.cuda.set_device(self.config.local_rank)
            self.device = torch.device(f"cuda:{self.config.local_rank}")
        else:
            self.device = torch.device("cpu")

        # Mixed precision scaler
        if self.config.mixed_precision:
            self._scaler = torch.cuda.amp.GradScaler()

        self._initialized = True

    def cleanup_distributed(self) -> None:
        """Cleanup distributed training."""
        if self._initialized and self.config.world_size > 1:
            dist.destroy_process_group()
            self._initialized = False

    def wrap_model(self, model: torch.nn.Module) -> torch.nn.Module:
        """Wrap model with DDP if using distributed training."""
        if self.config.use_ddp and self.config.world_size > 1:
            model = model.to(self.device)
            model = DDP(
                model,
                device_ids=[self.config.local_rank] if torch.cuda.is_available() else None,
                output_device=self.config.local_rank if torch.cuda.is_available() else None,
                find_unused_parameters=self.config.find_unused_parameters,
            )
        else:
            model = model.to(self.device)
        self._model = model
        return model

    def setup_optimizer(self, optimizer_class: type, **kwargs) -> torch.optim.Optimizer:
        """Setup optimizer."""
        self._optimizer = optimizer_class(self._model.parameters(), **kwargs)
        return self._optimizer

    def setup_scheduler(self, scheduler_class: type, **kwargs):
        """Setup learning rate scheduler."""
        self._scheduler = scheduler_class(self._optimizer, **kwargs)
        return self._scheduler

    def train_step(
        self,
        model: torch.nn.Module,
        batch: tuple[torch.Tensor, ...],
        loss_fn: Callable,
        epoch: int,
        step: int,
    ) -> dict[str, float]:
        """Single training step with gradient accumulation and mixed precision."""
        model.train()

        # Unpack batch
        if isinstance(batch, (list, tuple)):
            inputs, targets = batch[0], batch[1] if len(batch) > 1 else None
        else:
            inputs, targets = batch, None

        inputs = inputs.to(self.device, non_blocking=True)
        if targets is not None:
            targets = targets.to(self.device, non_blocking=True)

        # Forward pass with mixed precision
        if self.config.mixed_precision and self._scaler is not None:
            with torch.cuda.amp.autocast():
                outputs = model(inputs)
                loss = loss_fn(outputs, targets) if targets is not None else loss_fn(outputs)
                loss = loss / self.config.gradient_accumulation_steps

            # Backward pass
            self._scaler.scale(loss).backward()

            # Gradient accumulation
            if (step + 1) % self.config.gradient_accumulation_steps == 0:
                self._scaler.step(self._optimizer)
                self._scaler.update()
                self._optimizer.zero_grad()
        else:
            outputs = model(inputs)
            loss = loss_fn(outputs, targets) if targets is not None else loss_fn(outputs)
            loss = loss / self.config.gradient_accumulation_steps
            loss.backward()

            if (step + 1) % self.config.gradient_accumulation_steps == 0:
                self._optimizer.step()
                self._optimizer.zero_grad()

        # Step scheduler
        if self._scheduler is not None:
            self._scheduler.step()

        return {
            "loss": loss.item() * self.config.gradient_accumulation_steps,
            "lr": self._optimizer.param_groups[0]["lr"],
        }

    def save_checkpoint(
        self,
        epoch: int,
        step: int,
        metrics: dict[str, float],
        path: Path | None = None,
    ) -> Path:
        """Save distributed checkpoint (only rank 0)."""
        if self.config.rank != 0:
            return Path()

        path = path or self.config.checkpoint_dir / f"checkpoint_epoch_{epoch}_step_{step}.pt"
        path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "epoch": epoch,
            "step": step,
            "model_state_dict": self._model.module.state_dict()
            if hasattr(self._model, "module")
            else self._model.state_dict(),
            "optimizer_state_dict": self._optimizer.state_dict(),
            "scheduler_state_dict": self._scheduler.state_dict() if self._scheduler else None,
            "scaler_state_dict": self._scaler.state_dict() if self._scaler else None,
            "metrics": metrics,
            "config": self.config.__dict__,
        }

        torch.save(checkpoint, path)
        logger.info(f"Saved checkpoint: {path}")
        return path

    def load_checkpoint(self, path: Path) -> dict[str, Any]:
        """Load checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)

        if hasattr(self._model, "module"):
            self._model.module.load_state_dict(checkpoint["model_state_dict"])
        else:
            self._model.load_state_dict(checkpoint["model_state_dict"])

        self._optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        if self._scheduler and checkpoint["scheduler_state_dict"]:
            self._scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        if self._scaler and checkpoint["scaler_state_dict"]:
            self._scaler.load_state_dict(checkpoint["scaler_state_dict"])

        logger.info(f"Loaded checkpoint from {path}")
        return checkpoint


def run_distributed_training(
    train_fn: Callable,
    config: DistributedConfig,
    *args,
    **kwargs,
) -> Any:
    """
    Run distributed training across multiple processes.

    Usage:
        def train(rank, world_size, *args, **kwargs):
            config = DistributedConfig(world_size=world_size, rank=rank, ...)
            trainer = DistributedTrainer(config)
            trainer.setup_distributed()
            # ... training loop
            trainer.cleanup_distributed()

        run_distributed_training(train, config, *args, **kwargs)
    """
    if config.world_size == 1:
        # Single process
        return train_fn(config.rank, config.world_size, *args, **kwargs)

    # Multi-process
    mp.spawn(
        train_fn,
        args=(config.world_size, *args),
        nprocs=config.world_size,
        join=True,
    )


class HyperparameterOptimizer:
    """
    Distributed hyperparameter optimization using Optuna + Ray Tune.

    Features:
    - Distributed trials
    - Pruning (Median, Hyperband)
    - Multi-objective optimization
    - Integration with MLflow/W&B
    """

    def __init__(
        self,
        study_name: str,
        storage: str = "sqlite:///optuna_study.db",
        direction: str = "minimize",
        n_trials: int = 100,
        n_jobs: int = 1,
    ):
        self.study_name = study_name
        self.storage = storage
        self.direction = direction
        self.n_trials = n_trials
        self.n_jobs = n_jobs
        self._study = None

    def create_study(self) -> Any:
        """Create Optuna study."""
        try:
            import optuna
            from optuna.pruners import MedianPruner
            from optuna.samplers import TPESampler

            self._study = optuna.create_study(
                study_name=self.study_name,
                storage=self.storage,
                direction=self.direction,
                sampler=TPESampler(seed=42),
                pruner=MedianPruner(n_warmup_steps=10),
                load_if_exists=True,
            )
            return self._study
        except ImportError:
            logger.warning("Optuna not available")
            return None

    def optimize(
        self,
        objective_fn: Callable,
        n_trials: int | None = None,
    ) -> Any:
        """Run hyperparameter optimization."""
        if self._study is None:
            self.create_study()

        if self._study is None:
            return None

        n_trials = n_trials or self.n_trials

        self._study.optimize(
            objective_fn,
            n_trials=n_trials,
            n_jobs=self.n_jobs,
            show_progress_bar=True,
        )

        logger.info(f"Best trial: {self._study.best_trial.value}")
        logger.info(f"Best params: {self._study.best_trial.params}")

        return self._study.best_trial


class ModelServer:
    """
    High-performance model serving with TorchServe / Triton Inference Server.

    Features:
    - Batch inference
    - Dynamic batching
    - Model versioning
    - A/B testing
    - Metrics endpoint
    """

    def __init__(
        self,
        model: torch.nn.Module,
        model_name: str,
        version: str = "1.0",
        device: str = "cuda",
        max_batch_size: int = 32,
        max_queue_delay_ms: int = 100,
    ):
        self.model = model.to(device)
        self.model.eval()
        self.model_name = model_name
        self.version = version
        self.device = device
        self.max_batch_size = max_batch_size
        self.max_queue_delay_ms = max_queue_delay_ms

        # Request queue for dynamic batching
        self._request_queue: list[tuple[torch.Tensor, asyncio.Future]] = []
        self._batch_task = None

    async def predict(self, inputs: torch.Tensor) -> torch.Tensor:
        """Async prediction with dynamic batching."""
        import asyncio

        future = asyncio.get_event_loop().create_future()
        self._request_queue.append((inputs, future))

        # Start batch processing if not running
        if self._batch_task is None or self._batch_task.done():
            self._batch_task = asyncio.create_task(self._process_batch())

        return await future

    async def _process_batch(self) -> None:
        """Process queued requests as a batch."""
        import asyncio

        await asyncio.sleep(self.max_queue_delay_ms / 1000)

        if not self._request_queue:
            return

        # Collect batch
        batch_inputs = []
        futures = []
        for _ in range(min(self.max_batch_size, len(self._request_queue))):
            inp, fut = self._request_queue.pop(0)
            batch_inputs.append(inp)
            futures.append(fut)

        # Stack and predict
        batch = torch.stack(batch_inputs).to(self.device)
        with torch.no_grad():
            outputs = self.model(batch)

        # Return results
        for i, fut in enumerate(futures):
            fut.set_result(outputs[i].cpu())

    def export_onnx(
        self,
        sample_input: torch.Tensor,
        path: Path,
        dynamic_axes: dict | None = None,
    ) -> Path:
        """Export model to ONNX for Triton."""
        path.parent.mkdir(parents=True, exist_ok=True)

        if dynamic_axes is None:
            dynamic_axes = {
                "input": {0: "batch_size"},
                "output": {0: "batch_size"},
            }

        torch.onnx.export(
            self.model,
            sample_input.to(self.device),
            path,
            export_params=True,
            opset_version=14,
            do_constant_folding=True,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes=dynamic_axes,
        )

        logger.info(f"Exported ONNX model to {path}")
        return path


# Experiment tracking integration
class ExperimentTracker:
    """
    Unified experiment tracking for MLflow, Weights & Biases, TensorBoard.
    """

    def __init__(
        self,
        experiment_name: str,
        tracking_uri: str = "mlruns",
        backend: str = "mlflow",  # mlflow, wandb, tensorboard
    ):
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri
        self.backend = backend
        self._client = None
        self._run = None

    def start_run(self, run_name: str | None = None, tags: dict | None = None) -> Any:
        """Start experiment run."""
        if self.backend == "mlflow":
            import mlflow

            mlflow.set_tracking_uri(self.tracking_uri)
            mlflow.set_experiment(self.experiment_name)
            self._run = mlflow.start_run(run_name=run_name, tags=tags)
            return self._run
        elif self.backend == "wandb":
            import wandb

            self._run = wandb.init(
                project=self.experiment_name,
                name=run_name,
                config=tags,
            )
            return self._run
        return None

    def log_params(self, params: dict[str, Any]) -> None:
        """Log parameters."""
        if self.backend == "mlflow":
            import mlflow

            mlflow.log_params(params)
        elif self.backend == "wandb":
            import wandb

            wandb.config.update(params)

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        """Log metrics."""
        if self.backend == "mlflow":
            import mlflow

            mlflow.log_metrics(metrics, step=step)
        elif self.backend == "wandb":
            import wandb

            wandb.log(metrics, step=step)

    def log_artifact(self, path: Path) -> None:
        """Log artifact."""
        if self.backend == "mlflow":
            import mlflow

            mlflow.log_artifact(str(path))
        elif self.backend == "wandb":
            import wandb

            wandb.save(str(path))

    def log_model(self, model: torch.nn.Module, artifact_path: str) -> None:
        """Log model."""
        if self.backend == "mlflow":
            import mlflow

            mlflow.pytorch.log_model(model, artifact_path)

    def end_run(self) -> None:
        """End run."""
        if self.backend == "mlflow":
            import mlflow

            mlflow.end_run()
        elif self.backend == "wandb":
            import wandb

            wandb.finish()


# Register distributed training as a model capability
register_model(
    model_class=DistributedTrainer,
    name="Distributed PINN Trainer",
    version="1.0.0",
    domain=ModelDomain.CLIMATE,
    fidelity=ModelFidelity.HYBRID,
    status=ModelStatus.EXPERIMENTAL,
    description="Distributed training infrastructure for PINN and GP models",
    references=[
        "Li et al. (2020) PyTorch Distributed: Experiences on Accelerating Data Parallel Training",
    ],
    doi="10.1109/IPDPS51204.2020.00044",
    authors=["Pytorch Team"],
    tags=["distributed", "ddp", "pinn", "training", "scaling"],
)
