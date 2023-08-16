from fastapi import APIRouter
from dependencies import logger #,engine, #bucket

router = APIRouter(prefix='/a', tags=['router_a'])

@router.get('/example_a')
def example_a():
    logger.info('Request on endpoint example_a')
    return 'example_a'
