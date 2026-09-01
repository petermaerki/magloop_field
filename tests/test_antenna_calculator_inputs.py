import pytest

from magloop_field.calculations import AntennaCalculator, InvalidAntennaInput


def _valid_kwargs() -> dict[str, float | int]:
    return {
        "D_m": 1.014,
        "d_m": 0.1,
        "n": 1,
        "swr_min": 1.2,
        "f_Hz": 14.1e6,
        "bw262_Hz": 86.6e3,
        "powerPfwd_W": 94.0,
        "p_m": 0.0,
    }


def test_valid_inputs_are_accepted() -> None:
    calc = AntennaCalculator(**_valid_kwargs())
    assert calc.eta_SWR_ant > 0
    assert calc.powerPload_W >= 0


@pytest.mark.parametrize(
    ("field", "value", "msg"),
    [
        ("n", 0, "n must be a positive integer"),
        ("n", -1, "n must be a positive integer"),
        ("n", 1.5, "n must be an integer"),
        ("n", True, "n must be an integer"),
        ("D_m", 0.0, "D_m must be positive"),
        ("D_m", -1.0, "D_m must be positive"),
        ("d_m", 0.0, "d_m must be positive"),
        ("d_m", -1.0, "d_m must be positive"),
        ("p_m", -0.001, "p_m must be non-negative"),
        ("swr_min", 0.9, "swr_min must be >= 1.0"),
        ("f_Hz", 0.0, "f_Hz must be > 0"),
        ("f_Hz", -10.0, "f_Hz must be > 0"),
        ("bw262_Hz", 0.0, "bw262_Hz must be > 0"),
        ("bw262_Hz", -10.0, "bw262_Hz must be > 0"),
        ("powerPfwd_W", -0.1, "powerPfwd_W must be >= 0"),
    ],
)
def test_invalid_single_inputs_raise(
    field: str, value: float | int | bool, msg: str
) -> None:
    kwargs = _valid_kwargs()
    kwargs[field] = value
    with pytest.raises(InvalidAntennaInput, match=msg):
        AntennaCalculator(**kwargs)


def test_multi_turn_requires_positive_pitch() -> None:
    kwargs = _valid_kwargs()
    kwargs["n"] = 2
    kwargs["p_m"] = 0.0
    with pytest.raises(InvalidAntennaInput, match="p_m must be positive for n > 1"):
        AntennaCalculator(**kwargs)


def test_loop_diameter_must_be_greater_than_conductor_diameter() -> None:
    kwargs = _valid_kwargs()
    kwargs["D_m"] = 0.05
    kwargs["d_m"] = 0.1
    with pytest.raises(InvalidAntennaInput, match="D_m must be greater than d_m"):
        AntennaCalculator(**kwargs)
