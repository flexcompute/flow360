"""
Validator API
"""
from enum import Enum
from typing import Union
import json

from .flow360_params import Flow360Params
from ..cloud.rest_api import RestApi
from ..exceptions import ValueError, ValidationError
from ..log import log

class Validator(Enum):

    VOLUME_MESH = "VolumeMesh"
    SURFACE_MESH = "SurfaceMesh"
    CASE = "Case"

    def _get_url(self):
        if self is Validator.VOLUME_MESH:
            return f"validator/volume_mesh/validate"
        if self is Validator.SURFACE_MESH:
            return f"validator/surface_mesh/validate"
        if self is Validator.CASE:
            return f"validator/case/validate"

        return None

    def validate(self, params: Union[Flow360Params, dict], solver_version=None, mesh_id=None):
        if not isinstance(params, Flow360Params):
            raise ValueError('params must be instance of Flow360Params')

        api = RestApi(self._get_url())
        body = {
            "jsonConfig": params.to_flow360_json(),
            "version": solver_version
        }

        if mesh_id is not None:
            body['meshId'] = mesh_id

        try:    
            res = api.post(body)
        except Exception as e:
            return
        
        if 'validationWarning' in res and res['validationWarning'] is not None:
            res_str = str(res['validationWarning']).replace('[', '\[')
            log.warning(f'warning when validating: {res_str}')

        if 'success' in res and res['success'] == True:
            return res
        elif 'success' in res and res['success'] == False:
            if 'validationError' in res and res['validationError'] is not None:
                res_str = str(res).replace('[', '\[')
                raise ValidationError(f'Error when validating: {res_str}')

