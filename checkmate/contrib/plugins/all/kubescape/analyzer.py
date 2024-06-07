# -*- coding: utf-8 -*-


from checkmate.lib.analysis.base import BaseAnalyzer

import logging
import os
import tempfile
import json
import subprocess

logger = logging.getLogger(__name__)


class KubescapeAnalyzer(BaseAnalyzer):

    def __init__(self, *args, **kwargs):
        super(KubescapeAnalyzer, self).__init__(*args, **kwargs)
        try:
            result = subprocess.check_output(
                ["kubescape", "version"])
        except subprocess.CalledProcessError:
            logger.error(
                "Cannot initialize kubescape analyzer: Executable is missing, please install it.")
            raise

    def summarize(self, items):
        pass

    def analyze(self, file_revision):
        issues = []
        tmpdir = "/tmp/"+file_revision.project.pk

        if not os.path.exists(os.path.dirname(tmpdir+"/"+file_revision.path)):
            try:
                os.makedirs(os.path.dirname(tmpdir+"/"+file_revision.path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        f = open(tmpdir+"/"+file_revision.path, "w")

        fout = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        result = {}
        try:
            with f:
                f.write(file_revision.get_file_content().decode("utf-8"))
            try:
                result = subprocess.check_output(["kubescape",
                                                  "scan",
                                                  f.name,
                                                  "--format",
                                                  "json",
                                                  "--format-version",
                                                  "v2",
                                                  "--output",
                                                  fout.name])
            except subprocess.CalledProcessError as e:
                if e.returncode == 1:
                    result = e.output
                    pass
                elif e.returncode == 3:
                    result = []
                    pass
                else:
                    result = e.output
                    pass

            with open(fout.name, "r") as f:
                try:
                    result = json.load(f)
                except ValueError as e:
                    result['warnings'] = []
                    pass
            json_result = result

            try:

                for issue in json_result['results']:
                  for control in issue['controls']: 
                    line = 1
                    location = (((line, None),
                                 (line, None)),)

                    issues.append({
                            'code': control['controlID'],
                            'location': location,
                            'data': control['name'],
                            'file': file_revision.path,
                            'line': line,
                            'fingerprint': self.get_fingerprint_from_code(file_revision, location, extra_data=control['name'])
                    })
            except:
                pass

        finally:
            return {'issues': issues}
