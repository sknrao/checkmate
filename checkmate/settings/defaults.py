from checkmate.lib.stats.helpers import directory_splitter
from checkmate.lib.models import (Project,
                                  Snapshot,
                                  FileRevision,
                                  Issue)
from checkmate.contrib.plugins.git.models import GitSnapshot
from collections import defaultdict
import requests
import os
import time
from pathlib import Path

"""
Default settings values
"""

hooks = defaultdict(list)





plugins = {
      'git': 'checkmate.contrib.plugins.git',
      'bandit': 'checkmate.contrib.plugins.python.bandit',
      'brakeman': 'checkmate.contrib.plugins.ruby.brakeman',
      'semgrep': 'checkmate.contrib.plugins.java.semgrep',
      'tfsec': 'checkmate.contrib.plugins.iac.tfsec',
      'kubescape': 'checkmate.contrib.plugins.iac.kubescape',
      'semgrepjava': 'checkmate.contrib.plugins.java.semgrepjava',
      'semgrepeslint': 'checkmate.contrib.plugins.javascript.semgrepeslint',
      'graudit': 'checkmate.contrib.plugins.perl.graudit',
      'text4shell': 'checkmate.contrib.plugins.cve.text4shell',
      'gostaticcheck': 'checkmate.contrib.plugins.golang.gostaticcheck',
      }
        
 

  language_patterns = {
     'perl':
     {
         'name' : 'Perl',
         'patterns' : [u'\.pl$'],
     },
     'python':
     {
         'name' : 'Python',
         'patterns' : [u'\.py$',u'\.pyw$'],
     },
     'javascript' : {
          'name' : 'Javascript',
          'patterns' : [u'\.js$',u'\.ts$'],
     },
     'java' : {
          'name' : 'Java',
          'patterns' : [u'\.java$'],
     },
     'ruby' : {
          'name' : 'Ruby',
          'patterns' : [u'\.rb$'],
     },
     'golang' : {
          'name' : 'Golang',
          'patterns' : [u'\.go$'],
     },
     'iac' : {
          'name' : 'IaC',
          'patterns' : [u'\.yml$',u'\.yaml$',u'Dockerfile$',u'\.tf$'],
     },
  
  }


analyzers = {}

commands = {
    'alembic': 'checkmate.management.commands.alembic.Command',
    'init': 'checkmate.management.commands.init.Command',
    'analyze': 'checkmate.management.commands.analyze.Command',
    'reset': 'checkmate.management.commands.reset.Command',
    'shell': 'checkmate.management.commands.shell.Command',
    'summary': 'checkmate.management.commands.summary.Command',
    'snapshots': 'checkmate.management.commands.snapshots.Command',
    'issues': 'checkmate.management.commands.issues.Command',
    'props': {
        'get': 'checkmate.management.commands.props.get.Command',
        'set': 'checkmate.management.commands.props.set.Command',
        'delete': 'checkmate.management.commands.props.delete.Command'
    }
}

models = {
    'Project': Project,
    'Snapshot': Snapshot,
    'GitSnapshot': GitSnapshot,
    'FileRevision': FileRevision,
    'Issue': Issue,
}

aggregators = {
    'directory':
        {
            'mapper': lambda file_revision: directory_splitter(file_revision['path'], include_filename=True)
        }
}

checkignore = """*/site-packages/*
*/dist-packages/*
*/build/*
*/eggs/*
*/migrations/*
*/alembic/versions/*
*/node_modules/*
*/.checkmate/*
"""
