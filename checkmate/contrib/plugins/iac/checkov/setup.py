from .analyzer import CheckovAnalyzer
from .issues_data import issues_data

analyzers = {
    'checkov':
        {
            'name': 'checkov',
            'title': 'checkov',
            'class': CheckovAnalyzer,
            'language': 'iac',
            'issues_data': issues_data,
        },
}
