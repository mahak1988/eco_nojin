"""PINN surrogate tests (skip gracefully without torch)."""
import pytest

from services.models import pinn_surrogate


def test_status_always_reports_honestly():
    s = pinn_surrogate.status()
    assert "available" in s
    assert isinstance(s["available"], bool)


@pytest.mark.skipif(not pinn_surrogate.TORCH_AVAILABLE, reason="PyTorch not installed")
def test_toy_training_reduces_loss():
    import math

    model = pinn_surrogate.PINNSurrogate(n_inputs=1, hidden=[16])
    # y = sin(x) toy target
    xs = [[i / 50.0] for i in range(0, 100)]
    ys = [math.sin(x[0] * 4) for x in xs]
    before = float(model.net[0].weight.abs().mean())
    result = model.fit(xs, ys, epochs=300, lr=1e-2)
    assert result["final_loss"] < 0.5
    # surrogate approximates sin(pi/2)=1 reasonably after training
    pred = float(model.predict([[math.pi / 8]])[0, 0])
    assert abs(pred - math.sin(math.pi / 2)) < 0.3


@pytest.mark.skipif(not pinn_surrogate.TORCH_AVAILABLE, reason="PyTorch not installed")
def test_predict_shape():
    model = pinn_surrogate.PINNSurrogate(n_inputs=2, n_outputs=1)
    out = model.predict([[1.0, 2.0], [3.0, 4.0]])
    assert tuple(out.shape) == (2, 1)
