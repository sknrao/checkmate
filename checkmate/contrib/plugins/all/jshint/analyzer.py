# -*- coding: utf-8 -*-


from checkmate.lib.analysis.base import BaseAnalyzer

import logging
import os
import tempfile
import json
import subprocess

logger = logging.getLogger(__name__)


class JSHintAnalyzer(BaseAnalyzer):

    def __init__(self, *args, **kwargs):
        super(JSHintAnalyzer, self).__init__(*args, **kwargs)
        try:
            result = subprocess.check_output(["jshint", "--version"])
        except subprocess.CalledProcessError:
            logger.error(
                "Cannot initialize JSHint analyzer: Executable is missing, please install it.")
            raise

    def summarize(self, items):
        pass

    def analyze(self, file_revision):
        if ".js$" not in file_revision.path:
            return
        issues = []
        f = tempfile.NamedTemporaryFile(delete=False)
        try:
            with f:
                f.write(file_revision.get_file_content())
            try:
                result = subprocess.check_output(["jshint",
                                                  "--filename",
                                                  file_revision.path,
                                                  "--reporter",
                                                  os.path.join(os.path.abspath(__file__+"/.."),
                                                               'js/json_reporter'),
                                                  f.name])
            except subprocess.CalledProcessError as e:
                if e.returncode == 2:
                    result = e.output
                else:
                    raise
            json_result = json.loads(result)
            if ".js$" in file_revision.path:
                for issue in json_result:
                    location = (((issue['error']['line'], issue['error']['character']),
                                 (issue['error']['line'], None)),)
                    issues.append({
                        'code': issue['error']['code'],
                        'location': location,
                        'data': issue['error'],
                        'file': file_revision.path,
                        'line': issue['error']['line'],
                        'fingerprint': self.get_fingerprint_from_code(file_revision, location, extra_data=issue['error'])
                    })

        finally:
            #os.unlink(f.name)
            pass
        return {'issues': issues}
