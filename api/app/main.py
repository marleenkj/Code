import os
from fastapi import FastAPI

from routers import router_list

extrapath = os.environ.get('EXTRAPATH', '')

app = FastAPI(title="Demo API",
    description="""Demo API that can be used as template""",
    root_path=extrapath
)

for router in router_list:
    app.include_router(router.router)
