#!/usr/bin/env python3
"""
AI Log Analyzer - Vibe Logger inspired analysis tool
Analyzes structured JSON logs for AI-assisted debugging
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


class AILogAnalyzer:
    def __init__(self, log_file_path):
        self.log_file = Path(log_file_path)
        self.logs = []
        self.errors = []
        self.operations = defaultdict(list)

    def load_logs(self):
        """Load and parse JSONL log file"""
        if not self.log_file.exists():
            print(f"Log file not found: {self.log_file}")
            return False

        with open(self.log_file) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    log_entry = json.loads(line.strip())
                    self.logs.append(log_entry)

                    # Categorize by operation type
                    op_type = log_entry.get("operation", {}).get("type", "UNKNOWN")
                    self.operations[op_type].append(log_entry)

                    # Collect errors
                    if log_entry.get("operation", {}).get("exit_code", 0) != 0:
                        self.errors.append(log_entry)

                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON on line {line_num}: {e}")

        return True

    def generate_ai_report(self):
        """Generate AI-friendly analysis report"""
        report = {
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
            "summary": {
                "total_operations": len(self.logs),
                "error_count": len(self.errors),
                "operation_breakdown": {op_type: len(entries) for op_type, entries in self.operations.items()},
                "time_range": self._get_time_range(),
            },
            "errors": self._analyze_errors(),
            "patterns": self._detect_patterns(),
            "ai_insights": self._generate_insights(),
            "debugging_hints": self._create_debugging_hints(),
        }

        return report

    def _get_time_range(self):
        """Get the time range of logs"""
        if not self.logs:
            return {"start": None, "end": None}

        timestamps = [log.get("timestamp") for log in self.logs if log.get("timestamp")]
        if timestamps:
            return {"start": min(timestamps), "end": max(timestamps)}
        return {"start": None, "end": None}

    def _analyze_errors(self):
        """Analyze error patterns"""
        error_analysis = []

        for error in self.errors:
            analysis = {
                "timestamp": error.get("timestamp"),
                "correlation_id": error.get("correlation_id"),
                "operation": error.get("operation", {}).get("tool"),
                "command": error.get("operation", {}).get("command"),
                "ai_hint": error.get("ai_metadata", {}).get("hint"),
                "suggested_action": error.get("ai_metadata", {}).get("suggested_action"),
                "context": {
                    "project": error.get("context", {}).get("project", {}).get("name"),
                    "branch": error.get("context", {}).get("project", {}).get("git_branch"),
                },
            }
            error_analysis.append(analysis)

        return error_analysis

    def _detect_patterns(self):
        """Detect patterns in operations"""
        patterns = {
            "frequent_operations": self._get_frequent_operations(),
            "error_prone_operations": self._get_error_prone_operations(),
            "file_activity": self._analyze_file_activity(),
        }
        return patterns

    def _get_frequent_operations(self):
        """Get most frequent operations"""
        op_counts = [(op, len(entries)) for op, entries in self.operations.items()]
        op_counts.sort(key=lambda x: x[1], reverse=True)
        return op_counts[:5]

    def _get_error_prone_operations(self):
        """Identify operations that frequently result in errors"""
        error_by_op = defaultdict(int)
        total_by_op = defaultdict(int)

        for log in self.logs:
            op_type = log.get("operation", {}).get("type", "UNKNOWN")
            total_by_op[op_type] += 1

            if log.get("operation", {}).get("exit_code", 0) != 0:
                error_by_op[op_type] += 1

        error_rates = []
        for op_type, total in total_by_op.items():
            if total > 0:
                error_rate = error_by_op[op_type] / total
                if error_rate > 0:
                    error_rates.append(
                        {
                            "operation": op_type,
                            "error_rate": round(error_rate * 100, 2),
                            "errors": error_by_op[op_type],
                            "total": total,
                        }
                    )

        error_rates.sort(key=lambda x: x["error_rate"], reverse=True)
        return error_rates

    def _analyze_file_activity(self):
        """Analyze file modification patterns"""
        file_stats = defaultdict(lambda: {"modifications": 0, "reads": 0})

        for log in self.logs:
            files = log.get("operation", {}).get("files", [])
            op_type = log.get("operation", {}).get("type", "")

            for file_info in files:
                file_path = file_info.get("path", "")
                if file_path:
                    if op_type in ["CODE_MODIFICATION"]:
                        file_stats[file_path]["modifications"] += 1
                    elif op_type in ["FILE_INSPECTION"]:
                        file_stats[file_path]["reads"] += 1

        # Get top 10 most active files
        active_files = []
        for path, stats in file_stats.items():
            total_activity = stats["modifications"] + stats["reads"]
            if total_activity > 0:
                active_files.append(
                    {
                        "path": path,
                        "total_activity": total_activity,
                        "modifications": stats["modifications"],
                        "reads": stats["reads"],
                    }
                )

        active_files.sort(key=lambda x: x["total_activity"], reverse=True)
        return active_files[:10]

    def _generate_insights(self):
        """Generate AI-friendly insights"""
        insights = []

        # High error rate insight
        if self.errors and len(self.errors) / len(self.logs) > 0.1:
            insights.append(
                {
                    "type": "high_error_rate",
                    "severity": "high",
                    "message": f"Error rate is {len(self.errors)/len(self.logs)*100:.1f}%. Consider reviewing error patterns.",
                    "ai_todo": "Analyze error patterns and suggest preventive measures",
                }
            )

        # Repetitive operations
        for op_type, entries in self.operations.items():
            if len(entries) > 10:
                insights.append(
                    {
                        "type": "repetitive_operation",
                        "severity": "medium",
                        "message": f"Operation '{op_type}' was performed {len(entries)} times",
                        "ai_todo": f"Check if '{op_type}' operations can be optimized or batched",
                    }
                )

        return insights

    def _create_debugging_hints(self):
        """Create debugging hints for AI"""
        hints = []

        for error in self.errors[:5]:  # Top 5 recent errors
            hint = {
                "error_context": {
                    "tool": error.get("operation", {}).get("tool"),
                    "command": error.get("operation", {}).get("command"),
                    "timestamp": error.get("timestamp"),
                },
                "ai_instructions": [
                    "Review the command syntax and parameters",
                    "Check file permissions and paths",
                    "Verify environment variables and dependencies",
                    "Consider the git branch and project state",
                ],
                "human_note": error.get("ai_metadata", {}).get("human_note", ""),
            }
            hints.append(hint)

        return hints

    def print_report(self, report, format="json"):
        """Print the analysis report"""
        if format == "json":
            print(json.dumps(report, indent=2))
        elif format == "summary":
            print("\n=== AI Log Analysis Summary ===")
            print(f"Total Operations: {report['summary']['total_operations']}")
            print(f"Errors Found: {report['summary']['error_count']}")
            print(f"Time Range: {report['summary']['time_range']['start']} to {report['summary']['time_range']['end']}")

            print("\n--- Operation Breakdown ---")
            for op, count in report["summary"]["operation_breakdown"].items():
                print(f"  {op}: {count}")

            if report["errors"]:
                print("\n--- Recent Errors ---")
                for error in report["errors"][:3]:
                    print(f"  • {error['timestamp']}: {error['operation']} - {error['command']}")
                    print(f"    AI Hint: {error['ai_hint']}")

            if report["ai_insights"]:
                print("\n--- AI Insights ---")
                for insight in report["ai_insights"]:
                    print(f"  • [{insight['severity'].upper()}] {insight['message']}")
                    print(f"    TODO: {insight['ai_todo']}")


def main():
    parser = argparse.ArgumentParser(description="Analyze AI-friendly activity logs")
    parser.add_argument(
        "--log-file",
        default=str(Path.home() / ".claude" / "ai-activity.jsonl"),
        help="Path to the AI activity log file",
    )
    parser.add_argument("--format", choices=["json", "summary"], default="summary", help="Output format")
    parser.add_argument("--errors-only", action="store_true", help="Show only error analysis")

    args = parser.parse_args()

    analyzer = AILogAnalyzer(args.log_file)

    if not analyzer.load_logs():
        sys.exit(1)

    report = analyzer.generate_ai_report()

    if args.errors_only:
        error_report = {
            "errors": report["errors"],
            "debugging_hints": report["debugging_hints"],
        }
        print(json.dumps(error_report, indent=2))
    else:
        analyzer.print_report(report, format=args.format)


if __name__ == "__main__":
    main()
