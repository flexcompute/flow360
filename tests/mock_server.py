import os
import pytest
import json


from flow360.cloud import http_util
from flow360.cloud.http_util import http


here = os.path.dirname(os.path.abspath(__file__))



TASK_NAME = "TASK_NAME"
TASK_ID = "TASK_ID"
PROJECT_ID = "PROJECT_ID"
PROJECT_NAME = "PROJECT_NAME"
FOLDER_NAME = "FOLDER_NAME"


class MockResponse:
    """generic response to a requests function."""

    status_code = 200

    @staticmethod
    def json():
        return {}

    def raise_for_status(self):
        pass



class MockResponseVolumeMeshesPage(MockResponse):
    """response if VolumeMeshList()"""

    @staticmethod
    def json():
        with open(os.path.join(here, 'data/mock_webapi/volumemesh_page_webapi_resp.json')) as fh:
            res = json.load(fh)
        res['data']['data'] = [item for item in res['data']['data'] if item['deleted'] == False]    
        return res
    

class MockResponseVolumeMeshesPageWithDeleted(MockResponse):
    """response if VolumeMeshList()"""

    @staticmethod
    def json():
        with open(os.path.join(here, 'data/mock_webapi/volumemesh_page_webapi_resp.json')) as fh:
            res = json.load(fh)
        return res


class MockResponseVolumeMeshes(MockResponse):
    """response if VolumeMeshList(limit=None)"""

    @staticmethod
    def json():
        with open(os.path.join(here, 'data/mock_webapi/volumemesh_webapi_resp.json')) as fh:
            res = json.load(fh)
        res['data'] = [item for item in res['data'] if item['deleted'] == False]    
        return res


class MockResponseVolumeMeshesWithDeleted(MockResponse):
    """response if VolumeMeshList(include=true)"""

    @staticmethod
    def json():
        with open(os.path.join(here, 'data/mock_webapi/volumemesh_webapi_resp.json')) as fh:
            res = json.load(fh)
        return res


class MockResponseInfoOk(MockResponse):
    """response if web.getinfo(task_id) and task_id found"""

    @staticmethod
    def json():
        return {"taskId": TASK_ID}


class MockResponseInfoNotFound(MockResponse):
    """response if web.getinfo(task_id) and task_id not found"""

    @staticmethod
    def json():
        return {"data": None}


class MockResponseUpload(MockResponse):
    """response if web.upload()"""

    @staticmethod
    def json():
        return {"taskId": TASK_ID}



class MockResponseStart(MockResponse):
    """response if web.start()"""

    @staticmethod
    def json():
        return {"data": None}




class MockResponseFolder(MockResponse):
    @staticmethod
    def json():
        return {"projectId": PROJECT_ID, "projectName": PROJECT_NAME}


# map method path to the proper mocj response
RESPONSE_MAP = {
    # get responses
    f"flow360/volumemeshes": MockResponseInfoOk(),
    f"tidy3d/tasks/None/detail": MockResponseInfoNotFound(),
    f"tidy3d/project?projectName={FOLDER_NAME}": MockResponseFolder(),
    # f'tidy3d/tasks/{TASK_ID}/file?filename=simulation.json': MockResponseUploadString()
    # post responses
    f"tidy3d/projects/{PROJECT_ID}/tasks": MockResponseUpload(),
    # f'tidy3d/projects/FAIL/tasks': MockResponseUploadFailure(),
    f"tidy3d/tasks/{TASK_ID}/submit": MockResponseStart(),
}


# RESPONSE_MAP = {
#     # get responses
#     f"flow360/volumemeshes": MockResponseVolumeMeshes(),
#     f"flow360/volumemeshes": MockResponseVolumeMeshes(),

#     f"tidy3d/tasks/None/detail": MockResponseInfoNotFound(),
#     f"tidy3d/project?projectName={FOLDER_NAME}": MockResponseFolder(),
#     # f'tidy3d/tasks/{TASK_ID}/file?filename=simulation.json': MockResponseUploadString()
#     # post responses
#     f"tidy3d/projects/{PROJECT_ID}/tasks": MockResponseUpload(),
#     # f'tidy3d/projects/FAIL/tasks': MockResponseUploadFailure(),
#     f"tidy3d/tasks/{TASK_ID}/submit": MockResponseStart(),
# }

def mock_webapi(url, params):
    method = url.split('flow360')[-1]

    print(method)

    if method.startswith("volumemeshes/page"):
        if params['includeDeleted']:
            return MockResponseVolumeMeshesPageWithDeleted()
        return MockResponseVolumeMeshesPage()

    if method.startswith("volumemeshes"):
        if params['includeDeleted']:
            return MockResponseVolumeMeshesWithDeleted()   
        return MockResponseVolumeMeshes()   
     
    else:
        MockResponseInfoNotFound(),




# monkeypatched requests.get moved to a fixture
@pytest.fixture
def mock_response(monkeypatch):
    """Requests.get() mocked to return {'mock_key':'mock_response'}."""

    def get_response(url: str, params, **kwargs) -> str:
        """Get the method path from a full url."""
        preamble = "https://flow360-api.simulation.cloud/"
        method = url.split(preamble)[-1]

        print(f'calling this mock, {url} {kwargs}')

        return mock_webapi(method, params)

    class MockRequests:
        def get(self, url, **kwargs):
            return get_response(url, **kwargs)

        def post(self, url, **kwargs):
            return get_response(url, **kwargs)

    monkeypatch.setattr(
        http_util, "api_key_auth", lambda: {"Authorization": None, "Application": "FLOW360"}
    )
    monkeypatch.setattr(http, "session", MockRequests())

