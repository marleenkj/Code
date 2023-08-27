from .layout import layout
from .callbacks import *

from app import route_preffix

id_ = __name__.split('.')[1]
name = id_.replace('_', ' ').capitalize()
path = route_preffix + id_
