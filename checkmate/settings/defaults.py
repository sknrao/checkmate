from checkmate.lib.stats.helpers import directory_splitter
from checkmate.lib.models import (Project,
                                  Snapshot,
                                  DiskSnapshot,
                                  FileRevision,
                                  Issue)

from collections import defaultdict
import requests
import os
import time
from pathlib import Path

"""
Default settings values
"""

hooks = defaultdict(list)

valid=1

try:
  gpt = os.getenv('OPENAI_GPT_API')
except:
  gpt = ""
  pass

if gpt:
    path = '/root/.config/ptpt'
    os.system("mkdir -p /root/.config/ptpt")
    filename = "config.yaml"
    fullname = os.path.join(path, filename)
    myfile = open(fullname, "w")
    myfile.write("api_key: "+gpt)
    myfile.close()


if not valid:
  plugins = {
    'git': 'checkmate.contrib.plugins.git',
    'trufflehog3':  'checkmate.contrib.plugins.all.trufflehog3',
    'trojansource': 'checkmate.contrib.plugins.all.trojansource',
    'metrics': 'checkmate.contrib.plugins.all.metrics',
    'bandit': 'checkmate.contrib.plugins.all.bandit',
    'brakeman': 'checkmate.contrib.plugins.all.brakeman',
    'phpanalyzer':  'checkmate.contrib.plugins.all.progpilot',
    'gosec':  'checkmate.contrib.plugins.all.gosec',
    'confused': 'checkmate.contrib.plugins.all.confused',
    'pmd': 'checkmate.contrib.plugins.all.pmd',
    'semgrep': 'checkmate.contrib.plugins.all.semgrep',
    'checkov': 'checkmate.contrib.plugins.all.checkov',
    'tfsec': 'checkmate.contrib.plugins.all.tfsec',
    'kubescape': 'checkmate.contrib.plugins.all.kubescape',
    'insidersecswift': 'checkmate.contrib.plugins.all.insidersecswift',
    'insiderseckotlin': 'checkmate.contrib.plugins.all.insiderseckotlin',
    'insiderseccsharp': 'checkmate.contrib.plugins.all.insiderseccsharp',
    'pmdapex': 'checkmate.contrib.plugins.all.pmdapex',
    'semgrepccpp': 'checkmate.contrib.plugins.all.semgrepccpp',
    'semgrepjava': 'checkmate.contrib.plugins.all.semgrepjava',
    'semgrepeslint': 'checkmate.contrib.plugins.all.semgrepeslint',
    'graudit': 'checkmate.contrib.plugins.all.graudit',
    'text4shell': 'checkmate.contrib.plugins.all.text4shell',
    'yara': 'checkmate.contrib.plugins.all.yara',
    'osvscanner': 'checkmate.contrib.plugins.all.osvscanner',
    'fluidattackscsharp': 'checkmate.contrib.plugins.csharp.fluidattacksscanner',
    'fluidattacksgolang': 'checkmate.contrib.plugins.golang.fluidattacksscanner',
    'fluidattacksjava': 'checkmate.contrib.plugins.java.fluidattacksscanner',
    'fluidattacksjavascript': 'checkmate.contrib.plugins.javascript.fluidattacksscanner',
    'fluidattacksswift': 'checkmate.contrib.plugins.swift.fluidattacksscanner',
    'fluidattackskotlin': 'checkmate.contrib.plugins.kotlin.fluidattacksscanner',
    'fluidattackspython': 'checkmate.contrib.plugins.python.fluidattacksscanner',
    'gostaticcheck': 'checkmate.contrib.plugins.all.gostaticcheck',
    'gptanalyzer': 'checkmate.contrib.plugins.all.gptanalyzer',

  }


  language_patterns = {
    'all': {
        'name': 'All',
        'patterns': [u'\.none$'],
    },
  }

else:
  if gpt:
    plugins = {
      'git': 'checkmate.contrib.plugins.git',
      'trufflehog3':  'checkmate.contrib.plugins.all.trufflehog3',
      'trojansource': 'checkmate.contrib.plugins.all.trojansource',
      'yara': 'checkmate.contrib.plugins.all.yara',
      'metrics': 'checkmate.contrib.plugins.all.metrics',
      'bandit': 'checkmate.contrib.plugins.python.bandit',
      'brakeman': 'checkmate.contrib.plugins.ruby.brakeman',
      'phpanalyzer':  'checkmate.contrib.plugins.php.progpilot',
      'gosec':  'checkmate.contrib.plugins.golang.gosec',
      'confused': 'checkmate.contrib.plugins.supply.confused',
      'pmd': 'checkmate.contrib.plugins.java.pmd',
      'apex': 'checkmate.contrib.plugins.apex.pmdapex',
      'semgrep': 'checkmate.contrib.plugins.java.semgrep',
      'checkov': 'checkmate.contrib.plugins.iac.checkov',
      'tfsec': 'checkmate.contrib.plugins.iac.tfsec',
      'kubescape': 'checkmate.contrib.plugins.iac.kubescape',
      'insidersecswift': 'checkmate.contrib.plugins.swift.insidersecswift',
      'insiderseckotlin': 'checkmate.contrib.plugins.kotlin.insiderseckotlin',
      'insiderseccsharp': 'checkmate.contrib.plugins.csharp.insiderseccsharp',
      'pmdapex': 'checkmate.contrib.plugins.apex.pmdapex',
      'semgrepccpp': 'checkmate.contrib.plugins.ccpp.semgrepccpp',
      'semgrepjava': 'checkmate.contrib.plugins.java.semgrepjava',
      'semgrepeslint': 'checkmate.contrib.plugins.javascript.semgrepeslint',
      'graudit': 'checkmate.contrib.plugins.perl.graudit',
      'text4shell': 'checkmate.contrib.plugins.cve.text4shell',
      'osvscanner': 'checkmate.contrib.plugins.supply.osvscanner',
      'fluidattackscsharp': 'checkmate.contrib.plugins.csharp.fluidattacksscanner',
      'fluidattacksgolang': 'checkmate.contrib.plugins.golang.fluidattacksscanner',
      'fluidattacksjava': 'checkmate.contrib.plugins.java.fluidattacksscanner',
      'fluidattacksjavascript': 'checkmate.contrib.plugins.javascript.fluidattacksscanner',
      'fluidattacksswift': 'checkmate.contrib.plugins.swift.fluidattacksscanner',
      'fluidattackskotlin': 'checkmate.contrib.plugins.kotlin.fluidattacksscanner',
      'fluidattackspython': 'checkmate.contrib.plugins.python.fluidattacksscanner',
      'gostaticcheck': 'checkmate.contrib.plugins.golang.gostaticcheck',
      'gptanalyzer': 'checkmate.contrib.plugins.all.gptanalyzer',
    }
  else:
    plugins = {
      'git': 'checkmate.contrib.plugins.git',
      'trufflehog3':  'checkmate.contrib.plugins.all.trufflehog3',
      'trojansource': 'checkmate.contrib.plugins.all.trojansource',
      'yara': 'checkmate.contrib.plugins.all.yara',
      'metrics': 'checkmate.contrib.plugins.all.metrics',
      'bandit': 'checkmate.contrib.plugins.python.bandit',
      'brakeman': 'checkmate.contrib.plugins.ruby.brakeman',
      'phpanalyzer':  'checkmate.contrib.plugins.php.progpilot',
      'gosec':  'checkmate.contrib.plugins.golang.gosec',
      'confused': 'checkmate.contrib.plugins.supply.confused',
      'pmd': 'checkmate.contrib.plugins.java.pmd',
      'apex': 'checkmate.contrib.plugins.apex.pmdapex',
      'semgrep': 'checkmate.contrib.plugins.java.semgrep',
      'checkov': 'checkmate.contrib.plugins.iac.checkov',
      'tfsec': 'checkmate.contrib.plugins.iac.tfsec',
      'kubescape': 'checkmate.contrib.plugins.iac.kubescape',
      'insidersecswift': 'checkmate.contrib.plugins.swift.insidersecswift',
      'insiderseckotlin': 'checkmate.contrib.plugins.kotlin.insiderseckotlin',
      'insiderseccsharp': 'checkmate.contrib.plugins.csharp.insiderseccsharp',
      'pmdapex': 'checkmate.contrib.plugins.apex.pmdapex',
      'semgrepccpp': 'checkmate.contrib.plugins.ccpp.semgrepccpp',
      'semgrepjava': 'checkmate.contrib.plugins.java.semgrepjava',
      'semgrepeslint': 'checkmate.contrib.plugins.javascript.semgrepeslint',
      'graudit': 'checkmate.contrib.plugins.perl.graudit',
      'text4shell': 'checkmate.contrib.plugins.cve.text4shell',
      'osvscanner': 'checkmate.contrib.plugins.supply.osvscanner',
      'fluidattackscsharp': 'checkmate.contrib.plugins.csharp.fluidattacksscanner',
      'fluidattacksgolang': 'checkmate.contrib.plugins.golang.fluidattacksscanner',
      'fluidattacksjava': 'checkmate.contrib.plugins.java.fluidattacksscanner',
      'fluidattacksjavascript': 'checkmate.contrib.plugins.javascript.fluidattacksscanner',
      'fluidattacksswift': 'checkmate.contrib.plugins.swift.fluidattacksscanner',
      'fluidattackskotlin': 'checkmate.contrib.plugins.kotlin.fluidattacksscanner',
      'fluidattackspython': 'checkmate.contrib.plugins.python.fluidattacksscanner',
      'gostaticcheck': 'checkmate.contrib.plugins.golang.gostaticcheck',
    }
 

  language_patterns = {
     'apex':
     {
         'name' : 'Apex',
         'patterns' : [u'\.cls$'],
     },
     'ccpp':
     {
         'name' : 'CCPP',
         'patterns' : [u'\.c$',u'\.cpp$'],
     },
     'csharp':
     {
         'name' : 'CshareDotNet',
         'patterns' : [u'\.cs$'],
     },
     'kotlin':
     {
         'name' : 'Kotlin',
         'patterns' : [u'\.kt$'],
     },
     'perl':
     {
         'name' : 'Perl',
         'patterns' : [u'\.pl$'],
     },
     'swift':
     {
         'name' : 'Swift',
         'patterns' : [u'\.swift$'],
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
     'supply' : {
          'name' : 'Supply Chain',
          'patterns' : [u'package\.json$',u'Cargo\.lock$', u'packages\.lock\.json$',u'yarn\.lock$',u'pnpm-lock\.yaml$',u'composer\.lock$',u'Gemfile\.lock$',u'go\.mod$',u'mix\.lock$',u'poetry\.lock$',u'pubsepc\.lock$',u'pom\.xml$',u'requirements\.txt$',u'gradle\.lockfile$',u'buildscript-gradle\.lockfile$'],
     },
     'php' : {
          'name' : 'PHP',
          'patterns' : [u'\.php$'],
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
     'solidity' : {
          'name' : 'Solidity',
          'patterns' : [u'\.sol$'],
     },
     'all': {
        'name': 'All',
        'patterns': [u'\.none$'],
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
    'DiskSnapshot': DiskSnapshot,
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
