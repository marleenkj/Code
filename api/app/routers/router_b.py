from fastapi import APIRouter
from dependencies import logger #,engine, #bucket

router = APIRouter(prefix='/b', tags=['router_b'])

@router.get('/example_b')
def example_b():
    logger.info('Request on endpoint example_b')
    return 'example_b'
