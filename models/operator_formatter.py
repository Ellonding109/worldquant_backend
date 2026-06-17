from collections import defaultdict
from datetime import datetime

class OperatorFormatter:
    """Formats operators for different use cases"""
    
    FORMATS = {
        'detailed': 'detailed',
        'compact': 'compact',
        'structured': 'structured',
        'markdown': 'markdown',
        'json': 'json'
    }
    
    def __init__(self):
        self.formatters = {
            'detailed': self._format_detailed,
            'compact': self._format_compact,
            'structured': self._format_structured,
            'markdown': self._format_markdown,
            'json': self._format_json
        }
    
    def format(self, operators: list, format_type: str = 'compact', 
               categories: list = None) -> str:
        """Format operators list"""
        if categories:
            operators = [op for op in operators 
                        if op.get('category') in categories]
        
        formatter = self.formatters.get(format_type, self._format_compact)
        return formatter(operators)
    
    def _format_detailed(self, operators: list) -> str:
        """Detailed format with sections"""
        result = ["WORLDQUANT BRAIN OPERATORS REFERENCE"]
        result.append("=" * 60)
        result.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result.append(f"Total Operators: {len(operators)}\n")
        
        # Group by category
        by_category = defaultdict(list)
        for op in operators:
            by_category[op.get('category', 'Other')].append(op)
        
        for category in sorted(by_category.keys()):
            ops = by_category[category]
            result.append(f"\n{'='*60}")
            result.append(f"{category.upper()} ({len(ops)} operators)")
            result.append(f"{'='*60}\n")
            
            for op in sorted(ops, key=lambda x: x.get('name', '')):
                result.append(f"🔹 {op.get('name', 'N/A')}")
                result.append(f"   Category: {op.get('category', 'N/A')}")
                result.append(f"   Syntax: {op.get('definition', 'N/A')}")
                result.append(f"   Description: {op.get('description', 'N/A')}")
                doc = op.get('documentation')
                if doc:
                    result.append(f"   Documentation: {doc}")
                result.append("")
        
        return "\n".join(result)
    
    def _format_compact(self, operators: list) -> str:
        """Compact format for AI context"""
        result = []
        for op in operators:
            line = (
                f"OPERATOR: {op.get('name', 'N/A')} | "
                f"CATEGORY: {op.get('category', 'N/A')} | "
                f"USAGE: {op.get('definition', 'N/A')} | "
                f"PURPOSE: {op.get('description', 'N/A')}")
            result.append(line)
        return "\n".join(result)
    
    def _format_structured(self, operators: list) -> str:
        """Structured documentation format"""
        result = ["## WorldQuant Brain Operators\n"]
        
        by_category = defaultdict(list)
        for op in operators:
            by_category[op.get('category', 'Other')].append(op)
        
        for category in sorted(by_category.keys()):
            ops = by_category[category]
            result.append(f"### {category}\n")
            
            for op in sorted(ops, key=lambda x: x.get('name', '')):
                result.append(f"#### {op.get('name')}\n")
                result.append(f"**Definition:** `{op.get('definition', 'N/A')}`\n")
                result.append(f"**Description:** {op.get('description', 'N/A')}\n")
                if op.get('documentation'):
                    result.append(f"**Docs:** {op.get('documentation')}\n")
                result.append("")
        
        return "\n".join(result)
    
    def _format_markdown(self, operators: list) -> str:
        """Markdown table format"""
        result = ["| Operator | Category | Definition | Description |"]
        result.append("|----------|----------|------------|-------------|")
        
        for op in operators:
            name = op.get('name', 'N/A')
            category = op.get('category', 'N/A')
            definition = op.get('definition', 'N/A').replace('|', '\\|')
            description = op.get('description', 'N/A').replace('|', '\\|')
            result.append(f"| {name} | {category} | {definition} | {description} |")
        
        return "\n".join(result)
    
    def _format_json(self, operators: list) -> str:
        """JSON format"""
        import json
        return json.dumps(operators, indent=2)
    
    def get_statistics(self, operators: list) -> dict:
        """Get operator statistics"""
        by_category = defaultdict(int)
        for op in operators:
            by_category[op.get('category', 'Other')] += 1
        
        return {
            'total': len(operators),
            'by_category': dict(by_category),
            'categories': list(by_category.keys())
        }