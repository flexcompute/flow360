import asyncio
import json
import os
from typing import List, Literal, Union, Optional

import aiohttp
import backoff
import matplotlib.pyplot as plt
from pydantic import Field, model_validator, NonNegativeInt
from pylatex import (
    Command,
    Document,
    Figure,
    NewPage,
    NoEscape,
    Section,
    SubFigure,
    Subsection,
)
from pylatex.utils import bold, escape_latex

from flow360 import Case
from flow360.component.simulation.framework.base_model import Flow360BaseModel
from .utils import Delta, Tabulary, data_from_path, get_root_path, get_requirements_from_data_path, _requirements_mapping
from .uvf_shutter import UVFshutter

here = os.path.dirname(os.path.abspath(__file__))


class ReportItem(Flow360BaseModel):

    boundaries: Union[Literal["ALL"], List[str]] = "ALL"
    _requirements: List[str] = None


    def get_doc_item(
        self,
        cases: List[Case],
        doc: Document,
        section_func: Union[Section, Subsection] = Section,
        case_by_case=False,
        data_storage: str = '.'
    ) -> None:
        with doc.create(section_func(self.__class__.__name__)):
            doc.append(f"this is {self.__class__.__name__}")

    def get_requirements(self):
        if self._requirements is not None:
            return self._requirements
        raise NotImplementedError(f'Internal error: get_requirements() not implemented for {self.__class__.__name__}')


class Summary(ReportItem):
    text: str
    type: Literal['Summary'] = Field("Summary", frozen=True)
    _requirements: List[str] = []

    def get_doc_item(
        self,
        cases: List[Case],
        doc: Document,
        section_func: Union[Section, Subsection] = Section,
        case_by_case=False,
        data_storage: str = '.'
    ) -> None:
        section = section_func("Summary")
        doc.append(section)
        doc.append(f"{self.text}\n")
        Table(data_path=["name"], section_title=None, custom_headings=["Case Name"]).get_doc_item(
            cases, doc, section_func, case_by_case
        )


class Inputs(ReportItem):
    """
    Inputs is a wrapper for a specific Table setup that details key inputs from the simulation
    """
    type: Literal['Inputs'] = Field("Inputs", frozen=True)
    _requirements: List[str] = [_requirements_mapping["params"]]

    def get_doc_item(
        self,
        cases: List[Case],
        doc: Document,
        section_func: Union[Section, Subsection] = Section,
        case_by_case=False,
        data_storage: str = '.'
    ) -> None:
        Table(
            data_path=[
                "params/version",
                "params/time_stepping/type_name",
                "params/outputs/0/output_format",
                "params/operating_condition/velocity_magnitude",
                "params/operating_condition/alpha",
            ],
            section_title="Inputs",
            custom_headings=[
                "Version",
                "Time stepping",
                "Output Format",
                "Velocity",
                "Alpha",
            ],
        ).get_doc_item(cases, doc, section_func, case_by_case, data_storage)


class Table(ReportItem):
    data_path: list[Union[str, Delta]]
    section_title: Union[str, None]
    custom_headings: Union[list[str], None] = None
    type: Literal['Table'] = Field("Table", frozen=True)


    @model_validator(mode="after")
    def check_custom_heading_count(self) -> None:
        if self.custom_headings is not None:
            if len(self.data_path) != len(self.custom_headings):
                raise ValueError(
                    f"Suppled `custom_headings` must be the same length as `data_path`: "
                    f"{len(self.custom_headings)} instead of {len(self.data_path)}"
                )
        return self
            
    def get_requirements(self):
        return get_requirements_from_data_path(self.data_path)


    def get_doc_item(
        self,
        cases: List[Case],
        doc: Document,
        section_func: Union[Section, Subsection] = Section,
        case_by_case=False,
        data_storage: str = '.'
    ) -> None:
        # Only create a title if specified
        if self.section_title is not None:
            section = section_func(self.section_title)
            doc.append(section)

        # Getting tables to wrap is a pain - Tabulary seems the best approach
        with doc.create(
            Tabulary("|C" * (len(self.data_path) + 1) + "|", width=len(self.data_path) + 1)
        ) as table:
            table.add_hline()

            # Manage column headings
            field_titles = [bold("Case No.")]
            if self.custom_headings is None:
                for path in self.data_path:
                    if isinstance(path, Delta):
                        field = path.__str__()
                    else:
                        field = path.split("/")[-1]

                    field_titles.append(bold(str(field)))
            else:
                field_titles.extend([bold(heading) for heading in self.custom_headings])

            table.append(Command("rowcolor", "gray!20"))
            table.add_row(field_titles)
            table.add_hline()

            # Build data rows
            for idx, case in enumerate(cases):
                row_list = [data_from_path(case, path, cases, case_by_case=case_by_case) for path in self.data_path]
                row_list.insert(0, str(idx + 1))  # Case numbers
                table.add_row(row_list)
                table.add_hline()


class Chart(ReportItem):
    section_title: Union[str, None]
    fig_name: str
    fig_size: float = 0.7  # Relates to fraction of the textwidth
    items_in_row: Union[int, None] = None
    select_indices: Optional[List[NonNegativeInt]] = None
    single_plot: bool = False
    force_new_page: bool = False

    @model_validator(mode="after")
    def check_chart_args(self) -> None:
        if self.items_in_row is not None and self.items_in_row != -1:
            if self.items_in_row < 1:
                raise ValueError(
                    f"`Items_in_row` should be greater than 1. Use -1 to include all cases on a single row. Use `None` to disable the argument."
                )
        if self.items_in_row is not None and self.single_plot:
            raise ValueError(f"`Items_in_row` and `single_plot` cannot be used together.")
        return self

    def _assemble_fig_rows(self, img_list: list[str], doc: Document, fig_caption: str):
        """
        Build a figure from SubFigures which displays images in rows

        Using Doc manually here may be uncessary - but it does allow for more control
        """

        # Smaller than 1 to avoid overflowing - single subfigure sizing seems to be weird
        minipage_size = 0.95 / self.items_in_row if self.items_in_row != 1 else 0.7
        doc.append(NoEscape(r"\begin{figure}[h!]"))
        doc.append(NoEscape(r"\centering"))

        # Build list of indices to combine into rows
        indices = list(range(len(img_list)))
        idx_list = [
            indices[i : i + self.items_in_row] for i in range(0, len(indices), self.items_in_row)
        ]
        for row_idx in idx_list:
            for idx in row_idx:
                sub_fig = SubFigure(position="t", width=NoEscape(rf"{minipage_size}\textwidth"))
                sub_fig.add_image(filename=img_list[idx], width=NoEscape(r"\textwidth"))

                # Stop caption for single subfigures - happens when include_case_by_case
                if self.items_in_row != 1:
                    sub_fig.add_caption(idx)

                doc.append(sub_fig)

                doc.append(NoEscape(r"\hfill"))

            doc.append(NoEscape(r"\\"))

        doc.append(NoEscape(r"\caption{" + escape_latex(fig_caption) + "}"))
        doc.append(NoEscape(r"\end{figure}"))


class Chart2D(Chart):
    data_path: list[Union[str, Delta]]
    background: Union[Literal["geometry"], None] = None
    _requirements: List[str] = [_requirements_mapping["total_forces"]]
    type: Literal['Chart2D'] = Field("Chart2D", frozen=True)



    def get_requirements(self):
        return get_requirements_from_data_path(self.data_path)
    
    def is_log_plot(self):
        root_path = get_root_path(self.data_path[1])
        return root_path == 'nonlinear_residuals'
    

    def _create_fig(
        self, x_data: list, y_data: list, x_lab: str, y_lab: str, save_name: str
    ) -> None:
        """Create a simple matplotlib figure"""
        if self.is_log_plot():
            plt.semilogy(x_data, y_data)
        else:
            plt.plot(x_data, y_data)
        plt.xlabel(x_lab)
        plt.ylabel(y_lab)
        if self.single_plot:
            plt.legend([val + 1 for val in range(len(x_data))])

        plt.savefig(save_name)
        if not self.single_plot:
            plt.close()

    def get_doc_item(
        self,
        cases: List[Case],
        doc: Document,
        section_func: Union[Section, Subsection] = Section,
        case_by_case=False,
        data_storage: str = '.'
    ) -> None:
        # Create new page is user requests one
        if self.force_new_page:
            doc.append(NewPage())

        # Change items in row to be the number of cases if higher number is supplied
        if self.items_in_row is not None:
            if self.items_in_row > len(cases) or self.items_in_row == -1:
                self.items_in_row = len(cases)

        # Only create a title if specified
        if self.section_title is not None:
            section = section_func(self.section_title)
            doc.append(section)

        x_lab = self.data_path[0].split("/")[-1]
        y_lab = self.data_path[1].split("/")[-1]

        figure_list = []
        if case_by_case is False:
            cases = [cases[i] for i in self.select_indices] if self.select_indices is not None else cases
        for case in cases:

            # Extract data from the Case
            x_data = data_from_path(case, self.data_path[0], cases)
            y_data = data_from_path(case, self.data_path[1], cases)

            # Create the figure using basic matplotlib
            cbc_str = "_cbc_" if case_by_case else ""
            save_name = os.path.join(data_storage, self.fig_name + cbc_str + case.name + ".png")
            self._create_fig(x_data, y_data, x_lab, y_lab, save_name)

            # Allow for handling the figures later inside a subfig
            if self.items_in_row is not None:
                figure_list.append(save_name)

            elif self.single_plot:
                continue

            else:
                # Fig is added to doc later to facilitate method of creating single_plot
                fig = Figure(position="h!")
                fig.add_image(save_name, width=NoEscape(rf"{self.fig_size}\textwidth"))
                fig.add_caption(
                    NoEscape(f"{bold(y_lab)} against {bold(x_lab)} for {bold(case.name)}.")
                )
                figure_list.append(fig)

        if self.items_in_row is not None:
            fig_caption = NoEscape(f'{bold(y_lab)} against {bold(x_lab)} for {bold("all cases")}.')
            self._assemble_fig_rows(figure_list, doc, fig_caption)

        elif self.single_plot:
            # Takes advantage of plot cached by matplotlib and that the last save_name is the full plot
            fig = Figure(position="h!")
            fig.add_image(save_name, width=NoEscape(rf"{self.fig_size}\textwidth"))
            fig.add_caption(
                NoEscape(f'{bold(y_lab)} against {bold(x_lab)} for {bold("all cases")}.')
            )
            doc.append(fig)
        else:
            for fig in figure_list:
                doc.append(fig)

        # Stops figures floating away from their sections
        doc.append(NoEscape(r"\FloatBarrier"))
        doc.append(NoEscape(r"\clearpage"))

        # Clear the matplotlib cache to be certain figure won't appear
        plt.close()


class Chart3D(Chart):
    # field: str
    # camera: List[float]
    # limits: List[float]

    _requirements: List[str] = [Case._manifest_path]
    type: Literal['Chart3D'] = Field("Chart3D", frozen=True)

    def get_doc_item(
        self,
        cases: List[Case],
        doc: Document,
        section_func: Union[Section, Subsection] = Section,
        case_by_case: bool = False,
        data_storage: str = '.',
        use_mock_manifest: bool = False
    ):
        # Create new page is user requests one
        if self.force_new_page:
            doc.append(NewPage())

        # Change items in row to be the number of cases if higher number is supplied
        if self.items_in_row is not None:
            if self.items_in_row > len(cases) or self.items_in_row == -1:
                self.items_in_row = len(cases)

        # Only create a title if specified
        if self.section_title is not None:
            section = section_func(self.section_title)
            doc.append(section)

        # Reduce the case list by the selected IDs
        cases = [cases[i] for i in self.select_indices] if self.select_indices is not None else cases

        img_list = UVFshutter(cases=cases, data_storage=data_storage).get_images(self.fig_name, use_mock_manifest=use_mock_manifest)

        if self.items_in_row is not None:
            fig_caption = f"Chart3D Row"
            self._assemble_fig_rows(img_list, doc, fig_caption)

        else:
            for filename in img_list:
                fig = Figure(position="h!")
                fig.add_image(filename, width=NoEscape(rf"{self.fig_size}\textwidth"))
                fig.add_caption(f"A Chart3D test picture.")
                doc.append(fig)

        # Stops figures floating away from their sections
        doc.append(NoEscape(r"\FloatBarrier"))
        doc.append(NoEscape(r"\clearpage"))