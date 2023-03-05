from sqlalchemy.orm import DeclarativeBase

#
# class MediaType(Enum):
#     IMAGE = 0
#     VIDEO = 1
#     TEXT = 2
#
#     def __str__(self):
#         return self.name
#
#
# class TriggerStatus(Enum):
#     WAIT = 0
#     RUN = 1
#     ERROR = 2
#
#     def __str__(self):
#         return self.name
#
#
# class ModelStatus(Enum):
#     OKAY = 0
#     FAIL = 1
#
#     def __str__(self):
#         return self.name


class Base(DeclarativeBase):
    pass
