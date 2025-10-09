#!/usr/bin/env python3
"""
Run the Aesthetic Evaluator
"""

import os
import asyncio
from src.aesthetic_evaluator import AestheticEvaluator

async def main():
    # Check for API key
    openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
    if not openrouter_api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set your OpenRouter API key:")
        print("export OPENROUTER_API_KEY='your-api-key-here'")
        return
    
    # Create and run evaluator
    evaluator = AestheticEvaluator(openrouter_api_key)
    
    try:
        print("🚀 Starting comprehensive page evaluation with link checking...")
        report = await evaluator.evaluate_all_pages()
        
        # Save report
        report_file = await evaluator.save_report(report)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 EVALUATION SUMMARY")
        print("="*60)
        
        summary = report['evaluation_summary']
        print(f"📄 Pages Evaluated: {summary['total_pages_evaluated']}")
        print(f"✅ Successful: {summary['successful_evaluations']}")
        print(f"❌ Failed: {summary['failed_evaluations']}")
        
        if summary['average_scores']:
            print(f"\n📈 Average Scores:")
            for category, score in summary['average_scores'].items():
                print(f"  {category.replace('_', ' ').title()}: {score:.1f}/10")
        
        if report['recommendations']:
            print(f"\n🎯 Top Recommendations:")
            for rec in report['recommendations'][:3]:
                print(f"  {rec['priority'].upper()}: {rec['recommendation']}")
        
        # Link analysis summary
        if 'link_analysis' in report:
            link_analysis = report['link_analysis']
            print(f"\n🔗 Link Health Analysis:")
            print(f"  Total Links Checked: {link_analysis['total_links_checked']}")
            print(f"  Working Links: {link_analysis['working_links']}")
            print(f"  Broken Links: {link_analysis['broken_links']}")
            print(f"  Health Score: {link_analysis['health_score']:.1f}%")
            
            if link_analysis['critical_issues']:
                print(f"\n❌ Critical Issues (Missing Data Files):")
                for issue in link_analysis['critical_issues'][:5]:
                    print(f"  - {issue['url']}: {issue.get('error', 'Not found')}")
        
        print(f"\n📁 Full report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Error during evaluation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())