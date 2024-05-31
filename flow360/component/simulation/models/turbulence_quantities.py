"""
Turbulence quantities parameters
"""

# pylint: disable=unused-import
from abc import ABCMeta
from typing import Literal, Optional, Union

import pydantic as pd

from flow360.component.simulation.framework.base_model import Flow360BaseModel


class TurbulentKineticEnergy(Flow360BaseModel):
    """
    turbulentKineticEnergy : non-dimensional [`C_inf^2`]
        Turbulent kinetic energy. Applicable only when using SST model.
    """

    model_type: Literal["TurbulentKineticEnergy"] = pd.Field("TurbulentKineticEnergy", frozen=True)
    turbulent_kinetic_energy: VelocitySquaredType.NonNegativeFloat = pd.Field()


class TurbulentIntensity(Flow360BaseModel):
    """
    turbulentIntensity : non-dimensional [`-`]
        Turbulent intensity. Applicable only when using SST model.
        This is related to turbulent kinetic energy as:
        `turbulentKineticEnergy = 1.5*pow(U_ref * turbulentIntensity, 2)`.
        Note the use of the freestream velocity U_ref instead of C_inf.
    """

    model_type: Literal["TurbulentIntensity"] = pd.Field("TurbulentIntensity", frozen=True)
    turbulent_intensity: pd.NonNegativeFloat = pd.Field()


class _SpecificDissipationRate(Flow360BaseModel, metaclass=ABCMeta):
    """
    specificDissipationRate : non-dimensional [`C_inf/L_gridUnit`]
        Turbulent specific dissipation rate. Applicable only when using SST model.
    """

    model_type: Literal["SpecificDissipationRate"] = pd.Field(
        "SpecificDissipationRate", frozen=True
    )
    specific_dissipation_rate: InverseTimeType.NonNegativeFloat = pd.Field()


class TurbulentViscosityRatio(Flow360BaseModel):
    """
    turbulentViscosityRatio : non-dimensional [`-`]
        The ratio of turbulent eddy viscosity over the freestream viscosity. Applicable for both SA and SST model.
    """

    model_type: Literal["TurbulentViscosityRatio"] = pd.Field(
        "TurbulentViscosityRatio", frozen=True
    )
    turbulent_viscosity_ratio: pd.NonNegativeFloat = pd.Field()


class TurbulentLengthScale(Flow360BaseModel, metaclass=ABCMeta):
    """
    turbulentLengthScale : non-dimensional [`L_gridUnit`]
        The turbulent length scale is an estimation of the size of the eddies that are modeled/not resolved.
        Applicable only when using SST model. This is related to the turbulent kinetic energy and turbulent
        specific dissipation rate as: `L_T = sqrt(k)/(pow(beta_0^*, 0.25)*w)` where `L_T` is turbulent length scale,
        `k` is turbulent kinetic energy, `beta_0^*` is 0.09 and `w` is turbulent specific dissipation rate.
        Applicable only when using SST model.
    """

    model_type: Literal["TurbulentLengthScale"] = pd.Field("TurbulentLengthScale", frozen=True)
    turbulent_length_scale: LengthType.PositiveFloat = pd.Field()


class ModifiedTurbulentViscosityRatio(Flow360BaseModel):
    """
    modifiedTurbulentViscosityRatio : non-dimensional [`-`]
        The ratio of modified turbulent eddy viscosity (SA) over the freestream viscosity.
        Applicable only when using SA model.
    """

    model_type: Literal["ModifiedTurbulentViscosityRatio"] = pd.Field(
        "ModifiedTurbulentViscosityRatio", frozen=True
    )
    modified_turbulent_viscosity_ratio: pd.PositiveFloat = pd.Field()


class ModifiedTurbulentViscosity(Flow360BaseModel):
    """
    modifiedTurbulentViscosity : non-dimensional [`C_inf*L_gridUnit`]
        The modified turbulent eddy viscosity (SA). Applicable only when using SA model.
    """

    model_type: Literal["ModifiedTurbulentViscosity"] = pd.Field(
        "ModifiedTurbulentViscosity", frozen=True
    )
    modified_turbulent_viscosity: Optional[ViscosityType.PositiveFloat] = pd.Field()


# pylint: disable=missing-class-docstring
class SpecificDissipationRateAndTurbulentKineticEnergy(
    _SpecificDissipationRate, TurbulentKineticEnergy
):
    model_type: Literal["SpecificDissipationRateAndTurbulentKineticEnergy"] = pd.Field(
        "SpecificDissipationRateAndTurbulentKineticEnergy", frozen=True
    )


class TurbulentViscosityRatioAndTurbulentKineticEnergy(
    TurbulentViscosityRatio, TurbulentKineticEnergy
):
    model_type: Literal["TurbulentViscosityRatioAndTurbulentKineticEnergy"] = pd.Field(
        "TurbulentViscosityRatioAndTurbulentKineticEnergy", frozen=True
    )


class TurbulentLengthScaleAndTurbulentKineticEnergy(TurbulentLengthScale, TurbulentKineticEnergy):
    model_type: Literal["TurbulentLengthScaleAndTurbulentKineticEnergy"] = pd.Field(
        "TurbulentLengthScaleAndTurbulentKineticEnergy", frozen=True
    )


class TurbulentIntensityAndSpecificDissipationRate(TurbulentIntensity, _SpecificDissipationRate):
    model_type: Literal["TurbulentIntensityAndSpecificDissipationRate"] = pd.Field(
        "TurbulentIntensityAndSpecificDissipationRate", frozen=True
    )


class TurbulentIntensityAndTurbulentViscosityRatio(TurbulentIntensity, TurbulentViscosityRatio):
    model_type: Literal["TurbulentIntensityAndTurbulentViscosityRatio"] = pd.Field(
        "TurbulentIntensityAndTurbulentViscosityRatio", frozen=True
    )


class TurbulentIntensityAndTurbulentLengthScale(TurbulentIntensity, TurbulentLengthScale):
    model_type: Literal["TurbulentIntensityAndTurbulentLengthScale"] = pd.Field(
        "TurbulentIntensityAndTurbulentLengthScale", frozen=True
    )


class SpecificDissipationRateAndTurbulentViscosityRatio(
    _SpecificDissipationRate, TurbulentViscosityRatio
):
    model_type: Literal["SpecificDissipationRateAndTurbulentViscosityRatio"] = pd.Field(
        "SpecificDissipationRateAndTurbulentViscosityRatio", frozen=True
    )


class SpecificDissipationRateAndTurbulentLengthScale(
    _SpecificDissipationRate, TurbulentLengthScale
):
    model_type: Literal["SpecificDissipationRateAndTurbulentLengthScale"] = pd.Field(
        "SpecificDissipationRateAndTurbulentLengthScale", frozen=True
    )


class TurbulentViscosityRatioAndTurbulentLengthScale(TurbulentViscosityRatio, TurbulentLengthScale):
    model_type: Literal["TurbulentViscosityRatioAndTurbulentLengthScale"] = pd.Field(
        "TurbulentViscosityRatioAndTurbulentLengthScale", frozen=True
    )


# pylint: enable=missing-class-docstring

TurbulenceQuantitiesType = Union[
    TurbulentViscosityRatio,
    TurbulentKineticEnergy,
    TurbulentIntensity,
    TurbulentLengthScale,
    ModifiedTurbulentViscosityRatio,
    ModifiedTurbulentViscosity,
    SpecificDissipationRateAndTurbulentKineticEnergy,
    TurbulentViscosityRatioAndTurbulentKineticEnergy,
    TurbulentLengthScaleAndTurbulentKineticEnergy,
    TurbulentIntensityAndSpecificDissipationRate,
    TurbulentIntensityAndTurbulentViscosityRatio,
    TurbulentIntensityAndTurbulentLengthScale,
    SpecificDissipationRateAndTurbulentViscosityRatio,
    SpecificDissipationRateAndTurbulentLengthScale,
    TurbulentViscosityRatioAndTurbulentLengthScale,
]


# pylint: disable=too-many-arguments, too-many-return-statements, too-many-branches, invalid-name
# using class naming convetion here
def TurbulenceQuantities(
    viscosity_ratio=None,
    modified_viscosity_ratio=None,
    modified_viscosity=None,
    specific_dissipation_rate=None,
    turbulent_kinetic_energy=None,
    turbulent_length_scale=None,
    turbulent_intensity=None,
) -> TurbulenceQuantitiesType:
    """Return a matching tubulence specification object"""
    non_none_arg_count = sum(arg is not None for arg in locals().values())
    if non_none_arg_count == 0:
        return None

    if viscosity_ratio is not None:
        if non_none_arg_count == 1:
            return TurbulentViscosityRatio(turbulent_viscosity_ratio=viscosity_ratio)
        if turbulent_kinetic_energy is not None:
            return TurbulentViscosityRatioAndTurbulentKineticEnergy(
                turbulent_viscosity_ratio=viscosity_ratio,
                turbulent_kinetic_energy=turbulent_kinetic_energy,
            )
        if turbulent_intensity is not None:
            return TurbulentIntensityAndTurbulentViscosityRatio(
                turbulent_viscosity_ratio=viscosity_ratio,
                turbulent_intensity=turbulent_intensity,
            )
        if specific_dissipation_rate is not None:
            return SpecificDissipationRateAndTurbulentViscosityRatio(
                turbulent_viscosity_ratio=viscosity_ratio,
                specific_dissipation_rate=specific_dissipation_rate,
            )
        if turbulent_length_scale is not None:
            return TurbulentViscosityRatioAndTurbulentLengthScale(
                turbulent_viscosity_ratio=viscosity_ratio,
                turbulent_length_scale=turbulent_length_scale,
            )

    if modified_viscosity_ratio is not None and non_none_arg_count == 1:
        return ModifiedTurbulentViscosityRatio(
            modified_turbulent_viscosity_ratio=modified_viscosity_ratio
        )

    if modified_viscosity is not None and non_none_arg_count == 1:
        return ModifiedTurbulentViscosity(modified_turbulent_viscosity=modified_viscosity)

    if turbulent_intensity is not None:
        if non_none_arg_count == 1:
            return TurbulentIntensity(turbulent_intensity=turbulent_intensity)
        if specific_dissipation_rate is not None:
            return TurbulentIntensityAndSpecificDissipationRate(
                turbulent_intensity=turbulent_intensity,
                specific_dissipation_rate=specific_dissipation_rate,
            )
        if turbulent_length_scale is not None:
            return TurbulentIntensityAndTurbulentLengthScale(
                turbulent_intensity=turbulent_intensity,
                turbulent_length_scale=turbulent_length_scale,
            )

    if turbulent_kinetic_energy is not None:
        if non_none_arg_count == 1:
            return TurbulentKineticEnergy(turbulent_kinetic_energy=turbulent_kinetic_energy)
        if specific_dissipation_rate is not None:
            return SpecificDissipationRateAndTurbulentKineticEnergy(
                turbulent_kinetic_energy=turbulent_kinetic_energy,
                specific_dissipation_rate=specific_dissipation_rate,
            )
        if turbulent_length_scale is not None:
            return TurbulentLengthScaleAndTurbulentKineticEnergy(
                turbulent_kinetic_energy=turbulent_kinetic_energy,
                turbulent_length_scale=turbulent_length_scale,
            )

    if turbulent_length_scale is not None and non_none_arg_count == 1:
        return TurbulentLengthScale(turbulent_length_scale=turbulent_length_scale)

    if specific_dissipation_rate is not None:
        if turbulent_length_scale is not None:
            return SpecificDissipationRateAndTurbulentLengthScale(
                specific_dissipation_rate=specific_dissipation_rate,
                turbulent_length_scale=turbulent_length_scale,
            )

    raise ValueError(
        "Please recheck TurbulenceQuantities inputs and make sure they represents a valid specification."
    )