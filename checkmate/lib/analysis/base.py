# -*- coding: utf-8 -*-


import abc
from checkmate.helpers.hashing import Hasher


class AnalyzerSettingsError(BaseException):

    def __init__(self, errors):
        "Errors should be a dictionary"
        self.errors = errors


class BaseAnalyzer(object):

    """
    This abstract base class defines an analyzer, which takes file content and produces
    statistics as well as a list of issues. It is also responsible for diffing statistical
    data and issues obtained for different file revisions or snapshots.
    """

    def __init__(self,
                 code_environment,
                 settings=None,
                 ignore=None):
        self.code_environment = code_environment
        if settings:
            self.validate_settings(settings)
        self.settings = settings
        if ignore is not None:
            self.ignore = {}
            for code in ignore:
                self.ignore[code] = True

    def get_fingerprint_from_code(self, file_revision, location, extra_data=None):
        """
        This function generates a fingerprint from a series of code snippets.

        Can be used by derived analyzers to generate fingerprints based on code
        if nothing better is available.
        """
        code = file_revision.get_file_content()
        if not isinstance(code, str):
            code = str(code, errors='ignore')
        lines = code.split("\n")
        s = ""
        for l in location:
            ((from_row, from_column), (to_row, to_column)) = l
            if from_column is None:
                continue
            if from_row == to_row:
                s += lines[from_row-1][from_column:to_column]
            else:
                if to_row < from_row:
                    raise ValueError("from_row must be smaller than to_row")
                s += lines[from_row-1][from_column:]
                current_row = from_row+1
                while current_row < to_row:
                    s += lines[current_row-1]
                    current_row += 1
                s += lines[current_row-1][:to_column]

        hasher = Hasher()
        hasher.add(s)

        if extra_data is not None:
            hasher.add(extra_data)

        return hasher.digest.hexdigest()

    @classmethod
    def validate_settings(cls, settings):
        # should raise AnalyzerSettingsError if the settings are not valid
        raise NotImplementedError

    @abc.abstractmethod
    def analyze(self, file_revision):
        """
        Analyze a file and return a tuple (stats,issues) containing statistics and issues.

        This method should return a dictionary with one of the following entries:

        * issues: A list of issues found in the file revision
        * stats: Statistics about the file revision
        * depends_on: A list of dependencies for the file revision
        * provides: A list of things the file revision provides (e.g. a module),
                    to be used with the `depends_on` field.
        """
        pass

    def diff(self, results_a, results_b):
        pass

    def diff_summary(self, summary_a, summary_b):
        pass

    @abc.abstractmethod
    def summarize(self, items):
        """
        Aggregate a list of items containing statistical information generated by 'analyze'.
        """
        pass
