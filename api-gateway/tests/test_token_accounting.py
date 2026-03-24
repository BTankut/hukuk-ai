from __future__ import annotations

from token_accounting import _token_sequence_length


class _TensorLike:
    shape = (1, 42)


class _ToListLike:
    def tolist(self):
        return [[1, 2, 3, 4]]


def test_token_sequence_length_accepts_tensor_shape() -> None:
    assert _token_sequence_length(_TensorLike(), error_message="x") == 42


def test_token_sequence_length_accepts_tolist_result() -> None:
    assert _token_sequence_length(_ToListLike(), error_message="x") == 4
