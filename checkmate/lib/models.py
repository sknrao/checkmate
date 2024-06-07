# -*- coding: utf-8 -*-


from blitzdb import Document, SqlBackend
from blitzdb.fields import (BooleanField,
                            CharField,
                            DateTimeField,
                            ForeignKeyField,
                            ManyToManyField,
                            TextField,
                            EnumField,
                            IntegerField)


import os
import uuid
import time
import datetime
import logging
import traceback

from checkmate.helpers.hashing import Hasher
from checkmate.lib.stats.helpers import directory_splitter
from checkmate.lib.analysis import AnalyzerSettingsError
from checkmate.helpers.issue import IssuesMapReducer

try:
    from sqlalchemy.sql import (select,
                                insert,
                                func,
                                and_,
                                expression,
                                exists)
except ImportError:
    pass

logger = logging.getLogger(__name__)


class BaseDocument(Document):

    __abstract__ = True

    created_at = DateTimeField(auto_now_add=True, indexed=True)
    updated_at = DateTimeField(auto_now=True, indexed=True)

    def before_save(self):
        if not 'created_at' in self:
            self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()

    def before_update(self, set_fields, unset_fields):
        self.updated_at = datetime.datetime.now()
        set_fields['updated_at'] = self.updated_at


class IssueCategory(BaseDocument):

    name = CharField(indexed=True, unique=True, length=50)


class IssueClass(BaseDocument):

    class Severity:
        critical = 1
        potential_bug = 2
        minor = 3
        recommendation = 4

    hash = CharField(indexed=True, length=64)
    title = CharField(indexed=True, length=100)
    analyzer = CharField(indexed=True, length=50)
    language = CharField(indexed=True, length=50)
    code = CharField(indexed=True, length=50)
    description = TextField(indexed=False)
    file = CharField(indexed=True, length=50)
    line = CharField(indexed=True, length=50)




    # obsolete
    occurrence_description = CharField(indexed=True, length=2000)

    severity = IntegerField(indexed=True)
    categories = ManyToManyField('IssueCategory')

    class Meta(BaseDocument.Meta):
        unique_together = (('code', 'analyzer'),)


class IssueOccurrence(BaseDocument):

    # can be uniquely identified by its filerevision.pk, issue.pk and from_row,to_row,from_column,to_column,sequence

    # calculated as hash(file_revision.hash,issue.hash,from_row,to_row,from_column,to_column,sequence)
    hash = CharField(indexed=True, length=64)
    file_revision = ForeignKeyField(
        'FileRevision', backref='issue_occurrences')
    issue = ForeignKeyField('Issue', backref='issue_occurrences')
    from_row = IntegerField()
    to_row = IntegerField()
    from_column = IntegerField()
    to_column = IntegerField()
    sequence = IntegerField(default=0)


class Issue(BaseDocument):

    """
    An `Issue` object represents an issue or problem with the code.
    It can be associated with one or multiple file revisions, code objects etc.

    An issue fingerprint should be a unique identifier for a given issue, hence if
    two issues have the same fingerprint they should be judged "identical".
    """

    class IgnoreReason:
        not_specified = 0
        not_relevant = 1
        false_positive = 2

    # calculated as hash(analyzer,code,fingerprint)
    hash = CharField(indexed=True, length=64)
    configuration = CharField(indexed=True, length=64)
    project = ForeignKeyField('Project', backref='issues', nullable=False)
    analyzer = CharField(indexed=True, length=100, nullable=False)
    code = CharField(indexed=True, length=100, nullable=False)
    fingerprint = CharField(indexed=True, length=255, nullable=False)
    file = CharField(indexed=True, length=100, nullable=False)
    line = CharField(indexed=True, length=100, nullable=False)


    # determines if this issue should be ignored
    ignore = BooleanField(indexed=True, default=False,
                          nullable=False, server_default=False)
    # gives a reason for the issue to be ignored (e.g. false_positive, )
    ignore_reason = IntegerField(indexed=True, nullable=True)
    # an optional comment for the ignore reason
    ignore_comment = CharField(indexed=False, length=255, nullable=True)

    class Meta(Document.Meta):
        unique_together = [('project', 'fingerprint', 'analyzer', 'code')]
        dbref_includes = ['code', 'analyzer']


class MockFileRevision(BaseDocument):

    __abstract__ = True

    def get_file_content(self):
        return self.code


class FileRevision(BaseDocument):

    # calculated as hash(path,sha)
    hash = CharField(indexed=True, length=64)
    configuration = CharField(indexed=True, length=64)
    project = ForeignKeyField('Project')
    path = CharField(indexed=True, length=2000)
    language = CharField(indexed=True, length=50)
    sha = CharField(indexed=True, length=64)
    dependencies = ManyToManyField(
        'FileRevision', backref='dependent_file_revisions')

    class Meta(Document.Meta):
        collection = "filerevision"

    def get_file_content(self):
        if hasattr(self, '_file_content'):
            if callable(self._file_content):
                return self._file_content()
            return self._file_content
        raise NotImplementedError


class Diff(BaseDocument):

    """
    """

    # calculated as hash(snapshot_a.hash,snapshot_b.hash)
    hash = CharField(indexed=True, length=64)
    configuration = CharField(indexed=True, length=64)
    project = ForeignKeyField('Project', backref='diffs')
    snapshot_a = ForeignKeyField('Snapshot', backref='diffs_a')
    snapshot_b = ForeignKeyField('Snapshot', backref='diffs_b')

    def get_issues_count(self, by_severity=False):
        if isinstance(self.backend, SqlBackend):
            return self._get_issues_count_sql(by_severity=by_severity)
        raise NotImplementedError

    def _get_issues_count_sql(self, by_severity=False):

        diff_issue_occurrence_table = self.backend.get_table(
            DiffIssueOccurrence)
        issue_class_table = self.backend.get_table(self.project.IssueClass)
        project_issue_class_table = self.backend.get_table(ProjectIssueClass)
        issue_occurrence_table = self.backend.get_table(IssueOccurrence)
        issue_table = self.backend.get_table(Issue)

        s = select([diff_issue_occurrence_table.c.key, issue_class_table.c.severity, func.count().label('count')])\
            .select_from(diff_issue_occurrence_table
                         .join(issue_occurrence_table, diff_issue_occurrence_table.c.issue_occurrence == issue_occurrence_table.c.pk)
                         .join(issue_table)
                         .join(issue_class_table, and_(issue_table.c.analyzer == issue_class_table.c.analyzer,
                                                       issue_table.c.code == issue_class_table.c.code))
                         .join(project_issue_class_table, and_(
                             project_issue_class_table.c.issue_class == issue_class_table.c.pk,
                             project_issue_class_table.c.enabled == True,
                             project_issue_class_table.c.project == self.project.pk
                         )))\
            .where(diff_issue_occurrence_table.c.diff == self.pk)\
            .group_by(diff_issue_occurrence_table.c.key, issue_class_table.c.severity)

        with self.backend.transaction():
            result = self.backend.connection.execute(s).fetchall()

        if by_severity:
            counts = {'added': {}, 'fixed': {}}
            for row in result:
                if not row['severity'] in counts[row['key']]:
                    counts[row['key']][row['severity']] = 0
                counts[row['key']][row['severity']] += row['count']
        else:
            counts = {'added': 0, 'fixed': 0}
            for row in result:
                counts[row['key']] += row['count']
        return counts

    def _summarize_issues_sql(self, include_filename=False, ignore=False):

        diff_issue_occurrence_table = self.backend.get_table(
            DiffIssueOccurrence)
        issue_occurrence_table = self.backend.get_table(IssueOccurrence)
        issue_table = self.backend.get_table(Issue)
        file_revision_table = self.backend.get_table(FileRevision)
        project_issue_class_table = self.backend.get_table(ProjectIssueClass)
        issue_class_table = self.backend.get_table(self.project.IssueClass)

        # we group by file revision path, issue code and analyzer
        group_columns = [file_revision_table.c.language,
                         file_revision_table.c.path,
                         diff_issue_occurrence_table.c['key'],
                         # we should not group by pk
                         #                         diff_issue_occurrence_table.c['pk'],
                         issue_table.c.code,
                         issue_table.c.analyzer]

        project_pk_type = self.backend.get_field_type(
            self.project.fields['pk'])

        # here we make sure that the given issue class is enabled for the project
        subselect = select([issue_class_table.c.pk])\
            .select_from(issue_class_table.join(project_issue_class_table))\
            .where(and_(
                issue_table.c.analyzer == issue_class_table.c.analyzer,
                issue_table.c.code == issue_class_table.c.code,
                issue_table.c.ignore == ignore,
                project_issue_class_table.c.project == expression.cast(
                    self.project.pk, project_pk_type),
                project_issue_class_table.c.enabled == True))\

        # we perform a JOIN of the file revision table to the issue tables
        table = diff_issue_occurrence_table\
            .join(issue_occurrence_table,
                  issue_occurrence_table.c.pk == diff_issue_occurrence_table.c.issue_occurrence)\
            .join(issue_table, and_(issue_occurrence_table.c.issue == issue_table.c.pk, issue_table.c.ignore == ignore))\
            .join(file_revision_table)

        # we select the aggregated issues for all file revisions in this snapshot
        s = select(group_columns+[func.count().label('count')])\
            .select_from(table)\
            .where(and_(exists(subselect), diff_issue_occurrence_table.c.diff == self.pk))\
            .group_by(*group_columns)\
            .order_by(file_revision_table.c.path)

        # we fetch the result
        with self.backend.transaction():
            result = self.backend.connection.execute(s).fetchall()

        # we aggregate the issues by path fragments
        def aggregator(f): return directory_splitter(
            f['path'], include_filename=include_filename)

        added_issues = []
        fixed_issues = []

        for row in result:
            if row['key'] == 'added':
                added_issues.append(row)
            else:
                fixed_issues.append(row)

        # we perform a map/reduce on the result
        map_reducer = IssuesMapReducer(aggregators=[aggregator],
                                       group_by=['language', 'analyzer', 'code'])

        return {'added': map_reducer.mapreduce(added_issues),
                'fixed': map_reducer.mapreduce(fixed_issues)}

    def summarize_issues(self, include_filename=False, ignore=False):
        if isinstance(self.backend, SqlBackend):
            return self._summarize_issues_sql(include_filename=include_filename, ignore=ignore)
        raise NotImplementedError


class DiffIssueOccurrence(BaseDocument):

    # calculated as hash(diff.hash,issue_occurrence.hash,key)
    hash = CharField(indexed=True, length=64)
    configuration = CharField(indexed=True, length=64)
    diff = ForeignKeyField('Diff', backref='issue_occurrences')
    issue_occurrence = ForeignKeyField(
        'IssueOccurrence', backref='diff_issue_occurrences')
    key = EnumField(enums=('added', 'fixed'))


class DiffFileRevision(BaseDocument):

    # calculated as hash(diff.hash,file_revision.hash,key)
    hash = CharField(indexed=True, length=64)
    configuration = CharField(indexed=True, length=64)
    diff = ForeignKeyField('Diff', backref='file_revisions')
    file_revision = ForeignKeyField('FileRevision', backref='diffs')
    key = EnumField(enums=('added', 'deleted', 'modified'))


class Snapshot(BaseDocument):

    # calculated as by the creating object
    hash = CharField(indexed=True, length=64)
    configuration = CharField(indexed=True, length=64)
    project = ForeignKeyField('Project')
    file_revisions = ManyToManyField('FileRevision', backref='snapshots')
    analyzed = BooleanField(indexed=True)

    class Meta(Document.Meta):
        pass

    def load(self, data):
        """
        Imports a snapshot from a data structure
        """
        pass

    def export(self):
        """
        Exports a snapshot to a data structure
        """

    def summarize_issues(self, include_filename=False, ignore=False):
        if isinstance(self.backend, SqlBackend):
            return self._summarize_issues_sql(include_filename=include_filename, ignore=ignore)
        raise NotImplementedError

    def _summarize_issues_sql(self, include_filename=False, ignore=False):

        snapshot_file_revisions_table = self.backend.get_table(
            self.fields['file_revisions'].relationship_class)
        fr_table = self.backend.get_table(FileRevision)
        issue_table = self.backend.get_table(Issue)
        issue_occurrence_table = self.backend.get_table(IssueOccurrence)
        project_issue_class_table = self.backend.get_table(ProjectIssueClass)
        issue_class_table = self.backend.get_table(self.project.IssueClass)

        project_pk_type = self.backend.get_field_type(
            self.project.fields['pk'])
        snapshot_pk_type = self.backend.get_field_type(self.fields['pk'])

        # we group by file revision path, issue code and analyzer
        group_columns = [fr_table.c.language, fr_table.c.path,
                         issue_table.c.code, issue_table.c.analyzer]

        # we perform a JOIN of the file revision table to the issue tables
        table = fr_table\
            .join(issue_occurrence_table, fr_table.c.pk == issue_occurrence_table.c.file_revision)\
            .join(issue_table, and_(issue_table.c.pk == issue_occurrence_table.c.issue, issue_table.c.ignore == ignore))

        # here we make sure that the given issue class is enabled for the project
        subselect = select([issue_class_table.c.pk])\
            .select_from(issue_class_table.join(project_issue_class_table))\
            .where(and_(
                issue_table.c.analyzer == issue_class_table.c.analyzer,
                issue_table.c.code == issue_class_table.c.code,
                issue_table.c.ignore == ignore,
                project_issue_class_table.c.project == expression.cast(
                    self.project.pk, project_pk_type),
                project_issue_class_table.c.enabled == True))\

        file_revisions_select = select([snapshot_file_revisions_table.c.filerevision])\
            .where(snapshot_file_revisions_table.c.snapshot == expression.cast(self.pk, snapshot_pk_type))

        # we select the aggregated issues for all file revisions in this snapshot
        s = select(group_columns+[func.count().label('count')])\
            .select_from(table)\
            .where(and_(exists(subselect), fr_table.c.pk.in_(file_revisions_select)))\
            .group_by(*group_columns)\
            .order_by(fr_table.c.path)

        # we fetch the result
        with self.backend.transaction():
            result = self.backend.connection.execute(s).fetchall()

        # we aggregate the issues by path fragments
        def aggregator(f): return directory_splitter(
            f['path'], include_filename=include_filename)

        # we perform a map/reduce on the result
        # the resulting items will contain the number of files and the number of issues in the file
        map_reducer = IssuesMapReducer(aggregators=[aggregator])
        return map_reducer.mapreduce(result)


class DiskSnapshot(BaseDocument):

    snapshot = ForeignKeyField(
        'Snapshot', backref='disk_snapshot', unique=True)


class ProjectIssueClass(BaseDocument):

    project = ForeignKeyField('Project', backref='project_issue_classes')
    issue_class = ForeignKeyField(
        'IssueClass', backref='project_issue_classes')
    enabled = BooleanField(default=True)

    class Meta(BaseDocument.Meta):

        unique_together = (('project', 'issue_class'),)


class Project(BaseDocument):

    IssueClass = IssueClass

    # contains a hash of the project configuration that will be used to mark
    # snapshots, diffs, file revisions etc.
    configuration = CharField(indexed=True, length=64)

    class Meta(Document.Meta):
        collection = "project"

    @property
    def settings(self):
        return self.get('settings', {})

    def get_issue_classes(self, backend=None, enabled=True, sort=None, **kwargs):
        """
        Retrieves the issue classes for a given backend

        :param backend: A backend to use. If None, the default backend will be used
        :param enabled: Whether to retrieve enabled or disabled issue classes.
                        Passing `None` will retrieve all issue classes.
        """
        if backend is None:
            backend = self.backend

        query = {'project_issue_classes.project': self}
        if enabled is not None:
            query['project_issue_classes.enabled'] = enabled

        issue_classes = backend.filter(self.IssueClass, query,
                                       **kwargs)

        if sort is not None:
            issue_classes = issue_classes.sort(sort)

        return issue_classes

    def get_issues_data(self, backend=None, extra_fields=None):

        if backend is None:
            backend = self.backend

        if extra_fields is None:
            extra_fields = []

        issue_classes = self.get_issue_classes(include=(('categories', 'name'),),
                                               sort=[('categories.name', 1)],
                                               only=extra_fields +
                                               ['title',
                                                'analyzer',
                                                'language',
                                                'severity',
                                                'description',
                                                'code',
                                                'pk',
                                                'file',
                                                'line'],

                                               raw=True)
        grouped_issue_data = {}

        for issue_class in issue_classes:
            language_data = grouped_issue_data
            if not issue_class['language'] or not issue_class['analyzer'] or not issue_class['code']:
                continue
            if not issue_class['language'] in language_data:
                language_data[issue_class['language']] = {
                    'title': issue_class['language'], 'analyzers': {}}
            analyzer_data = language_data[issue_class['language']]['analyzers']
            if not issue_class['analyzer'] in analyzer_data:
                analyzer_data[issue_class['analyzer']] = {
                    'title': issue_class['analyzer'], 'codes': {}}
            code_data = analyzer_data[issue_class['analyzer']]['codes']
            code_data[issue_class['code']] = {
                'severity': issue_class['severity'],
                'title': issue_class['title'],
                'categories': [category['name'] for category in issue_class['categories']],
                'description': issue_class['description'],
                'code': issue_class['code'],
                'pk': issue_class['pk'],
                'file': issue_class['file'],
                'line': issue_class['line']
            }
            for field_name in extra_fields:
                code_data[issue_class['code']
                          ][field_name] = issue_class[field_name]

        return grouped_issue_data
