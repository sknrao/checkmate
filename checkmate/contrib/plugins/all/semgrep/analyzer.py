# -*- coding: utf-8 -*-


from checkmate.lib.analysis.base import BaseAnalyzer

import logging
import os
import tempfile
import json
import subprocess

logger = logging.getLogger(__name__)


class SemgrepAnalyzer(BaseAnalyzer):

    def __init__(self, *args, **kwargs):
        super(SemgrepAnalyzer, self).__init__(*args, **kwargs)
        try:
            result = subprocess.check_output(
                ["semgrep", "--version"],stderr=subprocess.DEVNULL).strip()
        except subprocess.CalledProcessError:
            logger.error(
                "Cannot initialize semgrep analyzer: Executable is missing, please install it.")
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

        f = open(tmpdir+"/"+file_revision.path, "wb")

        fout = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        result = {}
        try:
            with f:
                try:
                  f.write(file_revision.get_file_content())
                except UnicodeDecodeError:
                  pass
            try:
                result = subprocess.check_output(["semgrep",
                                                  "--config",
                                                  "/root/custom-semgrep/rules/custom/custom.yaml",
                                                  "--no-git-ignore",
                                                  "--json",
                                                  f.name],
                                                  stderr=subprocess.DEVNULL).strip()
                
            except subprocess.CalledProcessError as e:
                if e.returncode == 4:
                    result = e.output
                elif e.returncode == 3:
                    result = []
                    pass
                else:
                    
                    result = e.output
                    pass

            
            try:
                json_result = json.loads(result)

                for issue in json_result['results']:

                    location = (((issue['start']['line'], None),
                                 (issue['start']['line'], None)),)

                    if ".java" in file_revision.path or ".jsp" in file_revision.path or ".scala" in file_revision.path or ".xml" in file_revision.path:
                        if issue['check_id'] == "root.custom-semgrep.rules.custom.log4j-message-injection":
                            issue['check_id'] = "log4shell"
                        if issue['check_id'] == "root.custom-semgrep.rules.custom.detected-log4j-core":
                            issue['check_id'] = "log4shell"
                        if issue['check_id'] == "root.custom-semgrep.rules.custom.spring-controller-exists":
                            issue['check_id'] = "spring4shell"

                        issues.append({
                            'code': issue['check_id'],
                            'location': location,
                            'data': issue['extra']['message'],
                            'file': file_revision.path,
                            'line': issue['start']['line'],
                            'fingerprint': self.get_fingerprint_from_code(file_revision, location, extra_data=issue['extra']['message'])
                        })
            except:
                pass

        finally:
         return {'issues': issues}

