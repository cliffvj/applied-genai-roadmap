"""Property-based tests for validated application settings."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from tests.factories import create_test_settings


@st.composite
def valid_retry_wait_ranges(
    draw: st.DrawFn,
) -> tuple[float, float]:
    """Generate retry ranges satisfying maximum >= minimum."""
    minimum_milliseconds = draw(
        st.integers(
            min_value=0,
            max_value=10_000,
        ),
    )
    maximum_milliseconds = draw(
        st.integers(
            min_value=minimum_milliseconds,
            max_value=30_000,
        ),
    )

    return (
        minimum_milliseconds / 1000,
        maximum_milliseconds / 1000,
    )


@st.composite
def inverted_retry_wait_ranges(
    draw: st.DrawFn,
) -> tuple[float, float]:
    """Generate retry ranges satisfying maximum < minimum."""
    minimum_milliseconds = draw(
        st.integers(
            min_value=1,
            max_value=10_000,
        ),
    )
    maximum_milliseconds = draw(
        st.integers(
            min_value=0,
            max_value=minimum_milliseconds - 1,
        ),
    )

    return (
        minimum_milliseconds / 1000,
        maximum_milliseconds / 1000,
    )


@given(retry_range=valid_retry_wait_ranges())
def test_settings_accept_valid_retry_wait_ranges(
    retry_range: tuple[float, float],
) -> None:
    """Every retry range with maximum >= minimum should validate."""
    minimum_wait, maximum_wait = retry_range

    settings = create_test_settings(
        model_service_retry_min_wait_seconds=minimum_wait,
        model_service_retry_max_wait_seconds=maximum_wait,
    )

    assert settings.model_service_retry_min_wait_seconds == minimum_wait
    assert settings.model_service_retry_max_wait_seconds == maximum_wait


@given(retry_range=inverted_retry_wait_ranges())
def test_settings_reject_inverted_retry_wait_ranges(
    retry_range: tuple[float, float],
) -> None:
    """Every retry range with maximum < minimum should fail."""
    minimum_wait, maximum_wait = retry_range

    with pytest.raises(
        ValidationError,
        match=("model_service_retry_max_wait_seconds must be greater than or equal"),
    ):
        create_test_settings(
            model_service_retry_min_wait_seconds=minimum_wait,
            model_service_retry_max_wait_seconds=maximum_wait,
        )


@given(
    trailing_slashes=st.integers(
        min_value=1,
        max_value=20,
    ),
)
def test_settings_normalize_base_url_trailing_slashes(
    trailing_slashes: int,
) -> None:
    """Any number of trailing URL slashes should be removed."""
    settings = create_test_settings(
        model_service_base_url=("https://models.example.com" + ("/" * trailing_slashes)),
    )

    assert settings.model_service_base_url == "https://models.example.com"


@given(
    port=st.integers(
        min_value=1,
        max_value=65535,
    ),
)
def test_settings_accept_valid_tcp_ports(
    port: int,
) -> None:
    """All valid TCP port numbers should pass validation."""
    settings = create_test_settings(port=port)

    assert settings.port == port
