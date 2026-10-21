import argparse
from pathlib import Path

from .ast_analyzer import ASTAnalyzer
from .code_quality_checker import CodeQualityChecker
from .sarif_reporter import SarifReporter
from .security_rule_engine import SecurityRuleEngine
from .vuln_pattern_matcher import VulnPatternMatcher


def analyze_file(
    file_path: str | Path, report_path: str | Path = "report.sarif"
) -> list[dict]:
    file_path = Path(file_path)
    code = file_path.read_text(encoding="utf-8")
    ast_issues = ASTAnalyzer().analyze(code)
    pattern_issues = VulnPatternMatcher().match(code)
    quality_checker = CodeQualityChecker()
    quality_issues = quality_checker.check(file_path)
    quality_metrics = quality_checker.metrics(file_path)
    issues = SecurityRuleEngine().evaluate(ast_issues, pattern_issues)
    issues.extend(SecurityRuleEngine().evaluate(quality_issues, []))
    SarifReporter().generate_report(
        issues, report_path, file_path, quality_metrics
    )
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze Python source and emit a SARIF report."
    )
    parser.add_argument("file", help="Python source file to analyze")
    parser.add_argument(
        "--report", default="report.sarif", help="Output SARIF file"
    )
    args = parser.parse_args()
    issues = analyze_file(args.file, args.report)
    print(
        f"Analysis complete. Report saved to {args.report} "
        f"with {len(issues)} issues."
    )


if __name__ == "__main__":
    main()
