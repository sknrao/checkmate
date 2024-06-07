# -*- coding: utf-8 -*-


from checkmate.lib.analysis.base import BaseAnalyzer

import logging
import os
import tempfile
import json
import subprocess

logger = logging.getLogger(__name__)


class SemgrepeslintAnalyzer(BaseAnalyzer):

    def __init__(self, *args, **kwargs):
        super(SemgrepeslintAnalyzer, self).__init__(*args, **kwargs)
        try:
            result = subprocess.check_output(
                ["semgrep", "--version"])
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
        f = open(tmpdir+"/"+file_revision.path, "w")

        fout = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        result = {}
        try:
            with f:
                f.write(file_revision.get_file_content().decode("utf-8"))
            try:
                result = subprocess.check_output(["semgrep",
                                                  "--config",
                                                  "/root/eslint.yml",
                                                  "--no-git-ignore",
                                                  "--json",
                                                  f.name])
                
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

                    if ".js" in file_revision.path or ".ts" in file_revision.path:
                        val = issue['check_id']
                        val = val.replace("root.","")
                        val = val.replace(".","");
                        val = val.replace("-","");


                        issues.append({
                            'code': val,
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
