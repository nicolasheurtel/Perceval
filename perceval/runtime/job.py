# MIT License
#
# Copyright (c) 2022 Quandela
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from abc import ABC, abstractmethod
from typing import Any, Callable

from .job_status import JobStatus, RunningStatus


class Job(ABC):
    def __init__(self, fn: Callable, result_mapping_function: Callable = None, delta_parameters = None):
        # create an id or check existence of current id
        self._fn = fn
        # id will be assigned by remote job - not implemented for local class
        self._id = None
        self._results = None
        self._result_mapping_function = result_mapping_function
        self._delta_parameters = delta_parameters or {}
        pass

    def _adapt_parameters(self, args, kwargs):
        r"""adapt the parameters according to delta_parameters map passed to the LocalJob
            change delta parameters to reintegrate the missing parameters"""
        new_delta_parameters = {}
        args = list(args)
        for k, v in self._delta_parameters.items():
            if v is None:
                if k in kwargs:
                    new_delta_parameters[k] = kwargs[k]
                    del kwargs[k]
                else:
                    new_delta_parameters[k] = args.pop(0)
            else:
                kwargs[k] = v
        self._delta_parameters = new_delta_parameters
        return tuple(args), kwargs

    def __call__(self, *args, **kwargs) -> Any:
        return self.execute_sync(*args, **kwargs)

    @property
    def id(self):
        return self._id

    def get_results(self) -> Any:
        if not self.is_completed():
            raise RuntimeError('The job is still running, results are not available yet.')
        job_status = self.status
        if job_status.status != RunningStatus.SUCCESS:
            raise RuntimeError('The job failed with exception: ' + job_status.stop_message)
        if self._result_mapping_function:
            self._results['results'] = self._result_mapping_function(self._results['results'],
                                                                     **self._delta_parameters)
        return self._results

    @property
    @abstractmethod
    def status(self) -> JobStatus:
        pass

    def is_completed(self) -> bool:
        return self.status.completed

    @abstractmethod
    def execute_sync(self, *args, **kwargs) -> Any:
        pass

    @abstractmethod
    def execute_async(self, *args, **kwargs):
        pass
