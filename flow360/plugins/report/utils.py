"""
report utils, utils.py
"""

from __future__ import annotations

import ast
import os
import posixpath
import re
import shutil
import uuid
from PIL import Image
from abc import ABCMeta, abstractmethod
from numbers import Number
from typing import Annotated, Any, List, Literal, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numexpr as ne
import numpy as np
import pydantic as pd
from matplotlib.ticker import LogFormatterSciNotation
from PIL import Image

# this plugin is optional, thus pylatex is not required: TODO add handling of installation of pylatex
# pylint: disable=import-error
from pylatex import NoEscape, Package, Tabular

from flow360 import Case
from flow360.component.results import case_results
from flow360.component.simulation.framework.base_model import (
    Conflicts,
    Flow360BaseModel,
)
from flow360.component.volume_mesh import VolumeMeshV2
from flow360.log import log

here = os.path.dirname(os.path.abspath(__file__))


class RequirementItem(pd.BaseModel):
    resource_type: Literal["case", "volume_mesh", "surface_mesh", "geometry"] = "case"
    filename: str

    model_config = {"frozen": True}


# pylint: disable=protected-access
_requirements_mapping = {
    "params": RequirementItem(filename="simulation.json"),
    "total_forces": RequirementItem(
        filename=case_results.TotalForcesResultCSVModel()._remote_path()
    ),
    "surface_forces": RequirementItem(
        filename=case_results.SurfaceForcesResultCSVModel()._remote_path()
    ),
    "nonlinear_residuals": RequirementItem(
        filename=case_results.NonlinearResidualsResultCSVModel()._remote_path()
    ),
    "x_slicing_force_distribution": RequirementItem(
        filename=case_results.XSlicingForceDistributionResultCSVModel()._remote_path()
    ),
    "y_slicing_force_distribution": RequirementItem(
        filename=case_results.YSlicingForceDistributionResultCSVModel()._remote_path()
    ),
    "volume_mesh": RequirementItem(resource_type="volume_mesh", filename="simulation.json"),
    "volume_mesh/stats": RequirementItem(
        resource_type="volume_mesh", filename=VolumeMeshV2._mesh_stats_file
    ),
}


def get_requirements_from_data_path(data_path) -> List[RequirementItem]:
    """
    Retrieves requirements based on data path entries by mapping root paths
    to their corresponding requirements.

    Parameters
    ----------
    data_path : iterable
        An iterable containing data path entries to be checked.

    Returns
    -------
    list
        A list of unique requirements derived from the data path.

    Raises
    ------
    ValueError
        If a root path in the data path does not have a corresponding requirement.
    """

    requirements = set()
    for item in data_path:
        root_path = get_root_path(item)
        matched_requirement = None
        for key in _requirements_mapping:
            if root_path.startswith(key):
                matched_requirement = _requirements_mapping[key]
                requirements.add(matched_requirement)
        if matched_requirement is None:
            raise ValueError(f"Unknown result type: {item}")
    return list(requirements)


def detect_latex_compiler():
    """
    Detects available LaTeX compilers on the system.
    Returns:
        compiler (str), compiler_args (list[str]): Name of the LaTeX compiler ('xelatex', 'latexmk', 'pdflatex').
    Raises:
        RuntimeError: If no LaTeX compiler is found.
    """
    preferred_compilers = [("xelatex", []), ("latexmk", ["--pdf"]), ("pdflatex", [])]
    for compiler, compiler_args in preferred_compilers:
        if shutil.which(compiler):
            return compiler, compiler_args
    # If no compiler is found, raise an error
    raise RuntimeError(
        "No LaTeX compiler found. Please install a LaTeX distribution (e.g., TeX Live, MiKTeX)."
    )


def check_landscape(doc):
    """
    Checks if a document is in landscape orientation based on geometry package options.

    Parameters
    ----------
    doc : Document
        The LaTeX document to check for landscape orientation.

    Returns
    -------
    bool
        True if the document is in landscape orientation, False otherwise.
    """

    for package in doc.packages:
        if "geometry" in str(package.arguments):
            return "landscape" in str(package.options)
    return False


def get_case_from_id(case_id: str, cases: list[Case]) -> Case:
    """
    Retrieves a case by its unique identifier from a list of cases.

    Parameters
    ----------
    case_id : str
        The unique identifier of the case to retrieve.
    cases : list[Case]
        A list of `Case` objects to search.

    Returns
    -------
    Case
        The `Case` object matching the specified `case_id`.

    Raises
    ------
    ValueError
        If no cases are provided or the specified `case_id` is not found.
    """
    if len(cases) == 0:
        raise ValueError("No cases provided for `get_case_from_id`.")
    for case in cases:
        if case.id == case_id:
            return case
    raise ValueError(f"{case_id=} not found in {cases=}")


def get_root_path(data_path):
    """
    Extracts the root path from a given data path.

    If the provided `data_path` is of type `Delta`, the function retrieves
    the path from `data_path.data`.

    Parameters
    ----------
    data_path : str or Delta or None
        The data path to parse or a `Delta` object containing a data path.

    Returns
    -------
    str or None
        The root path as a string if `data_path` is valid, otherwise `None`.
    """

    if data_path is not None:
        if isinstance(data_path, (Delta, DataItem)):
            data_path = data_path.data
        if isinstance(data_path, DataItem):
            data_path = data_path.data
        return data_path
    return None


def split_path(path):
    # Split the path using both '/' and '.' as separators
    path_components = [comp for comp in re.split(r"[/.]", path) if comp]
    return path_components


# pylint: disable=too-many-return-statements
def data_from_path(
    case: Case, path: str, cases: list[Case] = None, case_by_case: bool = False
) -> Any:
    """
    Retrieves data from a specified path within a `Case` object, with optional delta calculations.

    Parameters
    ----------
    case : Case
        The primary `Case` object to search.
    path : str
        The path string indicating the nested attributes or dictionary keys.
    cases : list[Case], optional
        List of additional cases for delta calculations, default is an empty list.
    case_by_case : bool, default=False
        Flag for enabling case-by-case delta calculation when `path` is a `Delta` object.

    Returns
    -------
    Any
        The data extracted from the specified path within the `Case` object or calculated delta.

    Raises
    ------
    ValueError
        If a specified path component is not found or cannot be accessed.

    Notes
    -----
    This function splits the path into components and recursively searches through attributes,
    dictionary keys, or list indices as indicated in each component. Supports delta calculation
    using `Delta` objects and error handling for invalid paths.
    """
    if cases is None:
        cases = []

    if isinstance(path, Delta):
        if case_by_case:
            return path.model_copy(update={"ref_index": None}).calculate(case, cases)
        return path.calculate(case, cases)

    if isinstance(path, DataItem):
        return path.calculate(case, cases)

    # Split path into components
    path_components = split_path(path)

    def _search_path(case: Case, component: str) -> Any:
        """
        Case starts as a `Case` object but changes as it recurses through the path components
        """
        # Check if component is an attribute
        try:
            return getattr(case, component)
        except AttributeError:
            pass

        # Check if component is an attribute of case.results
        # Convenience feature so the user doesn't have to include "results" in path
        try:
            return getattr(case.results, component)
        except AttributeError:
            pass

        # Check if component is a key for a dictionary
        try:
            case = case[component]
            # Have to test for int or str here otherwise...
            if isinstance(case, (int, str)):
                return case
            # .. this raises a KeyError.
            # This is a convenience that may be removed for if people want something other than the value
            if "value" in case:
                return case["value"]
            return case
        except TypeError:
            pass

        # Check if case is a list and interpret component as an int index
        # E.g. in user defined functions
        if isinstance(case, list):
            try:
                return case[int(component)]
            except (ValueError, IndexError):
                pass

        # Check if case is a number
        if isinstance(case, Number):
            return case

        if isinstance(case, case_results.PerEntityResultCSVModel):
            return case

        # Check if component is a key of a value
        try:
            return case.values[component]
        except KeyError as err:
            raise ValueError(
                f"Could not find path component: '{component}', available: {case.values.keys()}"
            ) from err
        except AttributeError:
            log.warning(f"unknown value for path: {case=}, {component=}")

        return None

    # Case variable is slightly misleading as this is only a case on the first iteration
    for component in path_components:
        case = _search_path(case, component)

    return case


class GenericOperation(Flow360BaseModel, metaclass=ABCMeta):
    @abstractmethod
    def calculate(self, data, case, cases, variables, new_variable_name):
        pass


class Average(GenericOperation):
    start_step: Optional[pd.NonNegativeInt] = None
    end_step: Optional[pd.NonNegativeInt] = None
    start_time: Optional[pd.NonNegativeFloat] = None
    end_time: Optional[pd.NonNegativeFloat] = None
    fraction: Optional[pd.PositiveFloat] = pd.Field(None, le=1)
    type_name: Literal["Average"] = pd.Field("Average", frozen=True)

    model_config = pd.ConfigDict(
        conflicting_fields=[
            Conflicts(field1="start_step", field2="start_time"),
            Conflicts(field1="start_step", field2="fraction"),
            Conflicts(field1="start_time", field2="fraction"),
            Conflicts(field1="end_step", field2="end_time"),
            Conflicts(field1="end_step", field2="fraction"),
            Conflicts(field1="end_time", field2="fraction"),
        ],
        require_one_of=["start_step", "start_time", "fraction"],
    )

    def calculate(self, data, case, cases, variables, new_variable_name):
        if isinstance(data, case_results.ResultCSVModel):
            if self.fraction is None:
                raise NotImplementedError(f'Only "fraction" average method implemented.')
            averages = data.get_averages(avarage_fraction=self.fraction)
            return data, cases, averages

        raise NotImplementedError(
            f"{self.__class__.__name__} not implemented for data type: {type(data)=}"
        )


class Variable(Flow360BaseModel):
    name: str
    data: str


class Expression(GenericOperation):
    expr: str
    type_name: Literal["Expression"] = pd.Field("Expression", frozen=True)

    @classmethod
    def get_variables(cls, expr):
        """
        Parse the expression and return a set of variable names.
        """
        tree = ast.parse(expr, mode="eval")
        return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}

    @classmethod
    def evaluate_expression(cls, df, expr, variables: List[Variable], new_variable_name, case):
        """
        Evaluate the expression on the dataframe and add the result as a new column.
        """
        expr_variables = cls.get_variables(expr)
        missing_vars = expr_variables - set(df.columns)
        found_variables = set()
        for missing_var in missing_vars:
            try:
                if variables is not None:
                    for v in variables:
                        if missing_var == v.name:
                            df[missing_var] = data_from_path(case, v.data)
                            found_variables.add(missing_var)
            except Exception as e:
                log.warning(e)
        missing_vars -= found_variables
        if missing_vars:
            raise ValueError(
                f"The following variables are missing in the dataframe: {', '.join(missing_vars)}"
            )

        local_dict = {var: df[var].values for var in expr_variables}

        try:
            result = ne.evaluate(expr, local_dict)
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {e}")

        df[new_variable_name] = result
        return df

    def calculate(self, data, case, cases, variables, new_variable_name):
        log.debug(f"evaluating expression {self.expr}, {case.id=}")

        if isinstance(data, case_results.SurfaceForcesResultCSVModel):
            df = self.evaluate_expression(
                data.as_dataframe(), self.expr, variables, new_variable_name, case
            )
            data.update(df)
            return data, cases, data.values

        raise NotImplementedError(
            f"{self.__class__.__name__} not implemented for data type: {type(data)=}"
        )


OperationTypes = Annotated[Union[Average, Expression], pd.Field(discriminator="type_name")]


class Delta(pd.BaseModel):
    """
    Represents a delta calculation between a reference case and a target case based on specified data.

    Parameters
    ----------
    data : str
        Path to the data item used for delta calculation.
    ref_index : Optional[NonNegativeInt], default=0
        Index of the reference case in the list of cases for comparison.
    """

    data: Union[str, DataItem]
    ref_index: Optional[pd.NonNegativeInt] = 0
    type_name: Literal["Delta"] = pd.Field("Delta", frozen=True)

    def calculate(self, case: Case, cases: List[Case]) -> float:
        """
        Calculates the delta between the specified case and the reference case.

        Parameters
        ----------
        case : Case
            The target case for which the delta is calculated.
        cases : List[Case]
            A list of available cases, including the reference case.

        Returns
        -------
        float
            The computed delta value between the case and reference case data.

        Raises
        ------
        ValueError
            If `ref_index` is out of bounds or `None`, indicating a missing reference.
        """

        if self.ref_index is None or self.ref_index >= len(cases):
            return "Ref not found."
        ref = cases[self.ref_index]
        case_result = data_from_path(case, self.data)
        ref_result = data_from_path(ref, self.data)
        return case_result - ref_result

    def __str__(self):
        if isinstance(self.data, str):
            data_str = split_path(self.data)[-1]
        else:
            data_str = str(self.data)
        return f"Delta {data_str}"


class DataItem(pd.BaseModel):
    """
    Represents a delta calculation between a reference case and a target case based on specified data.

    Parameters
    ----------
    data : str
        Path to the data item used for delta calculation.
    ref_index : Optional[NonNegativeInt], default=0
        Index of the reference case in the list of cases for comparison.
    exclude : Optional[List[str]]
        List of boundaries to exclude from data. Applicable to:
        x_slicing_force_distribution, y_slicing_force_distribution, surface_forces
    """

    data: str
    title: Optional[str] = None
    exclude: Optional[List[str]] = None
    operations: Optional[List[OperationTypes]] = None
    variables: Optional[List[Variable]] = None
    type_name: Literal["DataItem"] = pd.Field("DataItem", frozen=True)

    @pd.model_validator(mode="before")
    def validate_operations(cls, values):
        operations = values.get("operations")
        if operations is None:
            values["operations"] = []
        elif not isinstance(operations, list):
            values["operations"] = [operations]
        return values

    def _preprocess_data(self, case):
        source = data_from_path(case, self.data)

        if isinstance(source, case_results.SurfaceForcesResultCSVModel):
            full_path = split_path(self.data)
            new_variable_name = "opr_" + uuid.uuid4().hex[:8]
            variable_name = None
            if len(full_path) == 1:
                pass
            elif len(full_path) == 2:
                variable_name = full_path[-1]
                self.operations.insert(0, Expression(expr=variable_name))
            else:
                raise ValueError(
                    f"{self.__class__.__name__}, unknown input: data={self.data}, allowed single <source> or <source>/<variable>"
                )

            return source, new_variable_name

        raise NotImplementedError(
            f"{self.__class__.__name__} not implemented for data type: data={self.data}, {type(source)=}"
        )

    def calculate(self, case: Case, cases: List[Case]) -> float:
        """
        Calculates the delta between the specified case and the reference case.

        Parameters
        ----------
        case : Case
            The target case for which the delta is calculated.
        cases : List[Case]
            A list of available cases, including the reference case.

        Returns
        -------
        float
            The computed delta value between the case and reference case data.

        Raises
        ------
        ValueError
            If `ref_index` is out of bounds or `None`, indicating a missing reference.

        """

        source = data_from_path(case, self.data)
        if isinstance(source, case_results.SurfaceForcesResultCSVModel):
            if self.exclude is not None:
                source.filter(exclude=self.exclude)

            source, new_variable_name = self._preprocess_data(case)
            if len(self.operations) > 0:
                for opr in self.operations:
                    source, cases, result = opr.calculate(
                        source, case, cases, self.variables, new_variable_name
                    )
                return result[new_variable_name]

            return source

    def __str__(self):
        if self.title is not None:
            return self.title
        return split_path(self.data)[-1]


# pylint: disable=too-few-public-methods
class Tabulary(Tabular):
    """The `tabulary` package works better than the existing pylatex implementations so this includes it in pylatex"""

    packages = [Package("tabulary")]

    def __init__(self, *args, width_argument=NoEscape(r"\linewidth"), **kwargs):
        """
        Args
        ----
        width_argument:
            The width of the table. By default the table is as wide as the
            text.
        """
        super().__init__(*args, start_arguments=width_argument, **kwargs)


def generate_colorbar_from_image(
    image_filename=os.path.join(here, "img", "colorbar_rainbow_banded_30.png"),
    limits: Tuple[float, float] = (0, 1),
    field_name: str = "Field",
    output_filename="colorbar_with_ticks.png",
    height_px=25,
    is_log_scale=False,
):
    """
    Generate a color bar image from an existing PNG file with ticks and labels.

    This function reads a colormap from a provided PNG file (a horizontal strip of
    colors), and overlays ticks and labels according to the specified value limits
    and scale type (linear or logarithmic).

    For a linear scale, matplotlib automatically chooses the number and format of
    ticks. For a log scale, a twin axis is used for proper tick placement without
    distorting the color distribution.

    Parameters
    ----------
    image_filename : str
        Path to the colormap PNG file (horizontal strip).
    limits : tuple of float
        A tuple (min_value, max_value) specifying the data range.
        If `is_log_scale` is True, `max_value` must be greater than 0.
    field_name : str
        The field name for the label.
    output_filename : str
        The output filename for the resulting image with ticks.
    height_px : int
        The height in pixels for the color bar image.
    is_log_scale : bool
        If True, use a log scale axis for ticks and minor ticks.

    Returns
    -------
    None
        The resulting image is saved to `output_filename`.

    Notes
    -----
    - On a log scale, the main colorbar axis remains linear to avoid deforming
      the color distribution. A twin axis is used solely for log-scale labeling.
    """

    img = Image.open(image_filename)
    original_width, _ = img.size
    new_size = (original_width, height_px)
    img_resized = img.resize(new_size, Image.LANCZOS)
    img_array = np.array(img_resized)

    dpi = 200
    width_inch = new_size[0] / dpi * 4
    height_inch = height_px / dpi

    fig, ax = plt.subplots(figsize=(width_inch, height_inch), dpi=dpi)

    min_value = limits[0]
    max_value = limits[1]

    ax.imshow(img_array, aspect="auto", extent=[min_value, max_value, 0, 1])

    ax.get_yaxis().set_visible(False)

    if is_log_scale:
        if min_value <= 0:
            raise ValueError("min_value must be >0 for log scale.")

        ax2 = ax.twiny()
        ax2.set_xscale("log")
        ax2.set_xlim(min_value, max_value)

        ax2.xaxis.set_major_formatter(LogFormatterSciNotation())
        ax2.tick_params(
            axis="x", which="both", top=True, bottom=False, labeltop=True, labelbottom=False
        )
        ax.set_xticks([])

    ax.set_xlabel(field_name, fontsize=10)
    plt.savefig(output_filename, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


font_path = posixpath.join(here, "fonts/")
font_definition = (
    r"""
\setmainfont{TWKEverett}[
    Path = """
    + font_path
    + r""",
    Extension = .otf,
    UprightFont = *-Regular,
    ItalicFont = *-RegularItalic,
    BoldFont = *-Bold,
    BoldItalicFont = *-BoldItalic,
]
"""
)


def downsample_image_to_relative_width(input_path, output_path, relative_width=1.0, dpi=150):
    """
    Downsample the image so that when displayed at 'relative_width' fraction of A4 horizontal width,
    it corresponds approximately to the given DPI.

    Parameters
    ----------
    input_path : str
        Path to the original high-resolution image.
    output_path : str
        Path to save the downsampled image.
    relative_width : float
        Fraction of the A4 horizontal width (297 mm) the image should occupy.
        e.g., 1.0 means full width, 0.5 means half the width, etc.
    dpi : int
        Desired DPI (pixels per inch).
    """
    A4_WIDTH_MM = 297.0  # A4 width in mm in landscape orientation
    MM_PER_INCH = 25.4

    final_width_inches = (A4_WIDTH_MM * relative_width) / MM_PER_INCH
    desired_pixel_width = final_width_inches * dpi

    img = Image.open(input_path)
    original_width, original_height = img.size

    scale = desired_pixel_width / original_width

    if scale < 1:
        new_width = int(round(original_width * scale))
        new_height = int(round(original_height * scale))
        img = img.resize((new_width, new_height), Image.LANCZOS)

    img.save(output_path)