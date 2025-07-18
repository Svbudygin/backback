import asyncio
import os
import sys

here = os.path.dirname(__file__)
sys.path.append(os.path.join(here, '..'))

from app.functions.user import (
    create_root_if_not_exist,
    create_b_worker_if_not_exist,
    create_c_worker_if_not_exist, create_tv_worker_if_not_exist)

from app.schemas.UserScheme import (
    UserSchemeRequestCreateRoot,
    UserSchemeRequestCreateBWorker,
    UserSchemeRequestCreateCWorker, UserSchemeRequestCreateTVWorker)

if sys.argv[1] == 'root':
    print(asyncio.run(create_root_if_not_exist(UserSchemeRequestCreateRoot(name='MAIN ROOT'))))

if sys.argv[1] == 'c-worker':
    print(asyncio.run(create_c_worker_if_not_exist(UserSchemeRequestCreateCWorker(name='MAIN C_WORKER'))))

if sys.argv[1] == 'b-worker':
    print(asyncio.run(create_b_worker_if_not_exist(UserSchemeRequestCreateBWorker(name='MAIN B_WORKER'))))

if sys.argv[1] == 'tv-worker':
    print(asyncio.run(create_tv_worker_if_not_exist(UserSchemeRequestCreateTVWorker(name='MAIN TV_WORKER'))))
    