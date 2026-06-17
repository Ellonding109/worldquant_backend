from collections import defaultdict
import json

class DatasetFormatter:
    """Formats dataset details in a consistent summary style."""

    FORMATS = {
        'compact': 'compact',
        'markdown': 'markdown',
        'json': 'json'
    }

    def __init__(self):
        self.formatters = {
            'compact': self._format_compact,
            'markdown': self._format_markdown,
            'json': self._format_json
        }

    def format(self, dataset: dict, format_type: str = 'markdown') -> str:
        if format_type not in self.formatters:
            format_type = 'markdown'
        return self.formatters[format_type](dataset)

    def extract_relevant(self, dataset: dict) -> dict:
        core = {
            'id': dataset.get('id'),
            'name': dataset.get('name'),
            'description': dataset.get('description'),
            'category': dataset.get('category', {}).get('name'),
            'subcategory': dataset.get('subcategory', {}).get('name'),
            'total_universes': len(dataset.get('data', [])),
            'researchPapers': dataset.get('researchPapers', []),
            'data': []
        }

        for item in dataset.get('data', []):
            core['data'].append({
                'region': item.get('region'),
                'delay': item.get('delay'),
                'universe': item.get('universe'),
                'coverage': item.get('coverage'),
                'valueScore': item.get('valueScore'),
                'userCount': item.get('userCount'),
                'alphaCount': item.get('alphaCount'),
                'fieldCount': item.get('fieldCount'),
                'themes': item.get('themes', [])
            })

        return core

    def _format_compact(self, dataset: dict) -> str:
        lines = [
            f"DATASET: {dataset.get('name', 'N/A')} ({dataset.get('id', 'N/A')})",
            f"Category: {dataset.get('category', {}).get('name', 'N/A')} / {dataset.get('subcategory', {}).get('name', 'N/A')}",
            f"Description: {dataset.get('description', 'N/A')}"
        ]

        for item in dataset.get('data', []):
            lines.append(
                f"UNIVERSE: {item.get('universe', 'N/A')} | REGION: {item.get('region', 'N/A')} | "
                f"DELAY: {item.get('delay', 'N/A')} | COVERAGE: {item.get('coverage', 'N/A')} | "
                f"VALUE SCORE: {item.get('valueScore', 'N/A')} | FIELDS: {item.get('fieldCount', 'N/A')} | "
                f"ALPHAS: {item.get('alphaCount', 'N/A')}"
            )
        return '\n'.join(lines)

    def _format_markdown(self, dataset: dict) -> str:
        result = [
            f"## Dataset Summary: {dataset.get('name', 'N/A')} ({dataset.get('id', 'N/A')})\n",
            f"**Category:** {dataset.get('category', {}).get('name', 'N/A')}  ",
            f"**Subcategory:** {dataset.get('subcategory', {}).get('name', 'N/A')}  ",
            f"**Description:** {dataset.get('description', 'N/A')}\n",
            "### Data Coverage by Universe\n",
            "| Universe | Region | Delay | Coverage | Value Score | Fields | Alphas |",
            "|----------|--------|-------|----------|-------------|--------|--------|"
        ]

        for item in dataset.get('data', []):
            result.append(
                f"| {item.get('universe', 'N/A')} | {item.get('region', 'N/A')} | {item.get('delay', 'N/A')} | "
                f"{item.get('coverage', 'N/A')} | {item.get('valueScore', 'N/A')} | {item.get('fieldCount', 'N/A')} | {item.get('alphaCount', 'N/A')} |"
            )

        return '\n'.join(result)

    def _format_json(self, dataset: dict) -> str:
        return json.dumps(self.extract_relevant(dataset), indent=2)