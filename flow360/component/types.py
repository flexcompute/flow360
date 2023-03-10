""" Defines 'types' that various fields can be """

from typing import Tuple, Union, List, Optional

# Literal only available in python 3.8 + so try import otherwise use extensions
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from typing_extensions import Annotated

import pydantic
import numpy as np
from matplotlib.axes import Axes
from ..exceptions import ValidationError

""" Numpy Arrays """

# type tag default name
TYPE_TAG_STR = "type"


def annotate_type(UnionType):  # pylint:disable=invalid-name
    """Annotated union type using TYPE_TAG_STR as discriminator."""
    return Annotated[UnionType, pydantic.Field(discriminator=TYPE_TAG_STR)]


# generic numpy array
Numpy = np.ndarray


class TypedArrayLike(np.ndarray):
    """A numpy array with a type given by cls.inner_type"""

    @classmethod
    def make_tuple(cls, v):
        """Converts a nested list of lists into a list of tuples."""
        return (
            tuple(cls.make_tuple(x) for x in v)
            if isinstance(v, list)
            else cls.inner_type(v)  # pylint:disable=no-member
        )

    @classmethod
    def __get_validators__(cls):
        """boilerplate"""
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        """validator"""
        # need to fix, doesnt work for simulationdata_export and load?

        if isinstance(val, np.ndarray):
            val_ndims = len(val.shape)
            cls_ndims = cls.ndims  # pylint:disable=no-member

            if (cls_ndims is not None) and (cls_ndims != val_ndims):
                raise ValidationError(
                    "wrong number of dimensions given. " f"Given {val_ndims}, expected {cls_ndims}."
                )
            return cls.make_tuple(val.tolist())

        return tuple(val)

    @classmethod
    def __modify_schema__(cls, field_schema):
        """Sets the schema of ArrayLike."""

        field_schema.update(
            dict(
                title="Array Like",
                description="Accepts sequence (tuple, list, numpy array) and converts to tuple.",
                type="tuple",
                properties={},
                required=[],
            )
        )


class ArrayLikeMeta(type):
    """metclass for Array, enables Array[type] -> TypedArray"""

    def __getitem__(cls, type_ndims):
        """Array[type, ndims] -> TypedArrayLike"""
        desired_type, ndims = type_ndims
        return type("Array", (TypedArrayLike,), {"inner_type": desired_type, "ndims": ndims})


class ArrayLike(np.ndarray, metaclass=ArrayLikeMeta):
    """type of numpy array with annotated type (Array[float], Array[complex])"""



""" geometric """

Size1D = pydantic.NonNegativeFloat
Size = Tuple[Size1D, Size1D, Size1D]
# we use tuple for fixed length lists, beacause List is a mutable, variable length structure
Coordinate = Tuple[float, float, float]

class PydanticValidate(pydantic.BaseModel):
    c: Optional[Coordinate]


class Vector(Coordinate):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def validate(cls, v):
        a = PydanticValidate(c=v)
        if not isinstance(v, cls):
            v = cls(v)
        if v == (0, 0, 0):
            raise pydantic.ValidationError(ValidationError('Vector cannot be (0, 0, 0)'), cls)
        return v


class Axis(Vector):
    pass



""" plotting """

Ax = Axes
