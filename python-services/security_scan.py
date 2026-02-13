#!/usr/bin/env python3
"""
Security Dependency Scanner for Legal LLM Supreme Court System

This script:
1. Scans dependencies for known vulnerabilities
2. Generates a requirements.lock file with pinned versions
3. Creates an SBOM (Software Bill of Materials)
4. Provides recommendations for updates

Usage:
    python security_scan.py --scan
    python security_scan.py --lock
    python security_scan.py --sbom
    python security_scan.py --all
"""

import argparse
import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path


def run_command(cmd, capture_output=True):
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_tools_installed():
    """Check if required security tools are installed"""
    tools = {
        "pip-audit": "pip install pip-audit",
        "safety": "pip install safety",
        "pip-tools": "pip install pip-tools"
    }
    
    missing = []
    for tool, install_cmd in tools.items():
        code, _, _ = run_command(f"{tool} --version")
        if code != 0:
            missing.append((tool, install_cmd))
    
    if missing:
        print("❌ Missing required tools:")
        for tool, install_cmd in missing:
            print(f"   - {tool}: Install with '{install_cmd}'")
        return False
    
    print("✅ All required tools are installed")
    return True


def scan_vulnerabilities():
    """Scan dependencies for known vulnerabilities"""
    print("\n" + "=" * 80)
    print("VULNERABILITY SCAN")
    print("=" * 80)
    
    # Run pip-audit
    print("\n📊 Running pip-audit...")
    code, stdout, stderr = run_command("pip-audit -r requirements.txt --format json")
    
    if code == 0:
        print("✅ No vulnerabilities found by pip-audit")
    else:
        print("⚠️  Vulnerabilities found:")
        try:
            vulns = json.loads(stdout)
            for vuln in vulns.get('dependencies', []):
                print(f"\n   Package: {vuln.get('name')} {vuln.get('version')}")
                for issue in vuln.get('vulns', []):
                    print(f"   - {issue.get('id')}: {issue.get('description')}")
                    print(f"     Fix: Upgrade to {issue.get('fix_versions', ['latest'])[0]}")
        except:
            print(stdout)
            print(stderr)
    
    # Run safety check
    print("\n📊 Running safety check...")
    code, stdout, stderr = run_command("safety check -r requirements.txt --json")
    
    if code == 0:
        print("✅ No vulnerabilities found by safety")
    else:
        print("⚠️  Vulnerabilities found:")
        try:
            vulns = json.loads(stdout)
            for vuln in vulns:
                print(f"\n   Package: {vuln[0]} {vuln[2]}")
                print(f"   - {vuln[1]}")
                print(f"     Fix: {vuln[3]}")
        except:
            print(stdout)
            print(stderr)
    
    print("\n" + "=" * 80)


def generate_lock_file():
    """Generate requirements.lock with pinned versions"""
    print("\n" + "=" * 80)
    print("GENERATING REQUIREMENTS.LOCK")
    print("=" * 80)
    
    print("\n📦 Compiling dependencies...")
    code, stdout, stderr = run_command(
        "pip-compile requirements.txt --output-file requirements.lock --resolver=backtracking"
    )
    
    if code == 0:
        print("✅ requirements.lock generated successfully")
        print(f"   Location: {Path('requirements.lock').absolute()}")
        
        # Count dependencies
        with open('requirements.lock', 'r') as f:
            lines = [l for l in f.readlines() if l.strip() and not l.startswith('#')]
            print(f"   Total dependencies (including transitive): {len(lines)}")
    else:
        print("❌ Failed to generate requirements.lock")
        print(stderr)
    
    print("\n" + "=" * 80)


def generate_sbom():
    """Generate Software Bill of Materials (SBOM)"""
    print("\n" + "=" * 80)
    print("GENERATING SBOM (Software Bill of Materials)")
    print("=" * 80)
    
    print("\n📋 Collecting dependency information...")
    
    # Get installed packages
    code, stdout, stderr = run_command("pip list --format json")
    
    if code != 0:
        print("❌ Failed to get package list")
        return
    
    try:
        packages = json.loads(stdout)
        
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": 1,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "component": {
                    "type": "application",
                    "name": "legal-llm-supreme-court-system",
                    "version": "1.0.0"
                }
            },
            "components": []
        }
        
        for pkg in packages:
            component = {
                "type": "library",
                "name": pkg["name"],
                "version": pkg["version"],
                "purl": f"pkg:pypi/{pkg['name']}@{pkg['version']}"
            }
            sbom["components"].append(component)
        
        # Write SBOM
        sbom_path = Path("sbom.json")
        with open(sbom_path, 'w') as f:
            json.dump(sbom, f, indent=2)
        
        print(f"✅ SBOM generated successfully")
        print(f"   Location: {sbom_path.absolute()}")
        print(f"   Total components: {len(sbom['components'])}")
        
    except Exception as e:
        print(f"❌ Failed to generate SBOM: {e}")
    
    print("\n" + "=" * 80)


def generate_security_report():
    """Generate comprehensive security report"""
    print("\n" + "=" * 80)
    print("SECURITY REPORT")
    print("=" * 80)
    
    report = []
    report.append(f"# Security Scan Report")
    report.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Project**: Legal LLM Supreme Court System")
    report.append("")
    
    # Vulnerability scan results
    report.append("## Vulnerability Scan")
    report.append("")
    
    code, stdout, _ = run_command("pip-audit -r requirements.txt --format json")
    if code == 0:
        report.append("✅ No vulnerabilities found")
    else:
        report.append("⚠️ Vulnerabilities detected - see details above")
    
    report.append("")
    
    # Dependency count
    report.append("## Dependencies")
    report.append("")
    
    with open('requirements.txt', 'r') as f:
        direct_deps = [l for l in f.readlines() if l.strip() and not l.startswith('#')]
        report.append(f"- Direct dependencies: {len(direct_deps)}")
    
    if Path('requirements.lock').exists():
        with open('requirements.lock', 'r') as f:
            all_deps = [l for l in f.readlines() if l.strip() and not l.startswith('#')]
            report.append(f"- Total dependencies (with transitive): {len(all_deps)}")
    
    report.append("")
    
    # SBOM status
    report.append("## SBOM")
    report.append("")
    if Path('sbom.json').exists():
        report.append("✅ SBOM generated: sbom.json")
    else:
        report.append("❌ SBOM not generated")
    
    report.append("")
    
    # Recommendations
    report.append("## Recommendations")
    report.append("")
    report.append("1. Review and fix any vulnerabilities found above")
    report.append("2. Use requirements.lock for reproducible builds")
    report.append("3. Run security scans regularly (weekly recommended)")
    report.append("4. Keep dependencies up to date")
    report.append("5. Monitor security advisories for used packages")
    
    # Write report
    report_path = Path("SECURITY_SCAN_REPORT.md")
    with open(report_path, 'w') as f:
        f.write('\n'.join(report))
    
    print(f"\n📄 Security report generated: {report_path.absolute()}")
    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Security dependency scanner for Legal LLM system"
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan dependencies for vulnerabilities"
    )
    parser.add_argument(
        "--lock",
        action="store_true",
        help="Generate requirements.lock file"
    )
    parser.add_argument(
        "--sbom",
        action="store_true",
        help="Generate SBOM (Software Bill of Materials)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all security checks"
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any([args.scan, args.lock, args.sbom, args.all]):
        parser.print_help()
        return
    
    print("=" * 80)
    print("LEGAL LLM SECURITY SCANNER")
    print("=" * 80)
    
    # Check tools
    if not check_tools_installed():
        print("\n❌ Please install missing tools and try again")
        sys.exit(1)
    
    # Run requested scans
    if args.all or args.scan:
        scan_vulnerabilities()
    
    if args.all or args.lock:
        generate_lock_file()
    
    if args.all or args.sbom:
        generate_sbom()
    
    if args.all:
        generate_security_report()
    
    print("\n✅ Security scan complete!")
    print("\nNext steps:")
    print("1. Review any vulnerabilities found")
    print("2. Update vulnerable packages")
    print("3. Use requirements.lock for deployment")
    print("4. Include sbom.json in your release artifacts")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
