from typing import Any, Type

from fastapi import Request
from pydantic import BaseModel


class parse_form:
    def __init__(self, model: Type[BaseModel]):
        self.model = model

    async def _parse_form(self, request: Request):
        body = (await request.body()).decode("utf-8")
        # body is bytes form data, parse it to dict
        form_data = {}
        lines = body.split("\r\n")
        for i, line in enumerate(lines):
            if line.startswith("Content-Disposition"):
                key = line.split("name=")[1].strip('"')
                value = lines[i + 2]
                # key含有.说明是对象的属性，需要转换为dict
                if "." in key:
                    key, sub_key = key.split(".")
                    if key not in form_data:
                        form_data[key] = {}
                    form_data[key][sub_key] = value
                else:
                    form_data[key] = value
        return form_data

    async def __call__(self, request: Request) -> Any:
        data = await self._parse_form(request)
        return self.model.model_validate(data)
