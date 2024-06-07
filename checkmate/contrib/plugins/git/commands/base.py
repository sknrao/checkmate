from checkmate.management.commands.base import BaseCommand
from sqlalchemy.orm.exc import NoResultFound


class Command(BaseCommand):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        if not hasattr(self, 'project'):
            raise AttributeError("No project defined!")
        if not hasattr(self.project, 'git'):
            raise AttributeError("Not a git project!")
        try:
            self.project.git.eager
        except self.project.git.DoesNotExist:
            raise AttributeError("Repository not found!")
