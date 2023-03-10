import pytest

from pydantic import BaseModel, ValidationError
from typing import Optional

from flow360.component.types import (
    Axis, Vector, Coordinate
)


class TestModel(BaseModel):
    a: Optional[Axis]
    v: Optional[Vector]
    c: Optional[Coordinate]


def test_axis_correct():
    a = TestModel(a=Axis((0, 0, 1)))
    assert type(a.a) == Axis

def test_axis_correct2():
    a = TestModel(a=(0, 0, 1))
    assert type(a.a) == Axis

def test_axis_incorrect():
    with pytest.raises(ValidationError):
        a = TestModel(a=(0, 0, 0))

def test_axis_incorrect2():
    with pytest.raises(ValidationError):
        a = TestModel(a=(0, 0, 0, 1))

def test_axis_incorrect3():
    with pytest.raises(ValidationError):
        a = TestModel(a=Axis((0, 0, 0, 1)))

def test_vector_correct():
    a = TestModel(v=(0, 0, 1))
    assert type(a.v) == Vector

def test_vector_incorrect():
    with pytest.raises(ValidationError):
        a = TestModel(v=(0, 0, 0))

def test_vector_incorrect2():
    with pytest.raises(ValidationError):
        a = TestModel(v=(1, 0, 0, 0))

def test_coordinate_correct():
    a = TestModel(c=(0, 0, 0))
    assert type(a.c) == tuple

def test_coordinate_incorrect():
    with pytest.raises(ValidationError):
        a = TestModel(c=(1, 0, 0, 0))
