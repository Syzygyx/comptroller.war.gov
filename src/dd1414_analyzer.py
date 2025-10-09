#!/usr/bin/env python3
"""
DD1414 Data Analyzer

This script analyzes the extracted DD1414 data and creates comprehensive insights,
visualizations, and reports for GitHub Pages publication.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from collections import defaultdict, Counter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DD1414Analyzer:
    """Analyzer for DD1414 data"""
    
    def __init__(self, data_file: str = "data/dd1414_csv/dd1414_enhanced_data.csv", output_dir: str = "docs"):
        self.data_file = Path(data_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Load data
        self.df = pd.read_csv(self.data_file)
        logger.info(f"Loaded {len(self.df)} DD1414 records")
        
        # Clean and prepare data
        self.prepare_data()
    
    def prepare_data(self):
        """Clean and prepare data for analysis"""
        # Convert fiscal year to int
        self.df['fiscal_year'] = pd.to_numeric(self.df['fiscal_year'], errors='coerce')
        
        # Clean amounts
        self.df['total_amount'] = pd.to_numeric(self.df['total_amount'], errors='coerce')
        self.df['amount_reprogrammed'] = pd.to_numeric(self.df['amount_reprogrammed'], errors='coerce')
        
        # Clean confidence scores
        self.df['confidence_score'] = pd.to_numeric(self.df['confidence_score'], errors='coerce')
        
        # Create decade column
        self.df['decade'] = (self.df['fiscal_year'] // 10) * 10
        
        # Create amount categories
        self.df['amount_category'] = pd.cut(
            self.df['total_amount'], 
            bins=[0, 1e6, 1e9, 1e12, float('inf')], 
            labels=['< $1M', '$1M - $1B', '$1B - $1T', '> $1T']
        )
        
        logger.info("Data preparation completed")
    
    def generate_summary_stats(self):
        """Generate comprehensive summary statistics"""
        stats = {
            'total_documents': len(self.df),
            'fiscal_years_covered': sorted(self.df['fiscal_year'].dropna().unique().tolist()),
            'years_span': f"{self.df['fiscal_year'].min()}-{self.df['fiscal_year'].max()}",
            'total_value': self.df['total_amount'].sum(),
            'average_amount': self.df['total_amount'].mean(),
            'median_amount': self.df['total_amount'].median(),
            'max_amount': self.df['total_amount'].max(),
            'min_amount': self.df['total_amount'].min(),
            'extraction_methods': self.df['extraction_method'].value_counts().to_dict(),
            'document_types': self.df['document_type'].value_counts().to_dict(),
            'organizations': self.df['requesting_organization'].value_counts().to_dict(),
            'average_confidence': self.df['confidence_score'].mean(),
            'high_confidence_docs': len(self.df[self.df['confidence_score'] >= 90]),
            'ocr_documents': len(self.df[self.df['extraction_method'] == 'ocr']),
            'text_documents': len(self.df[self.df['extraction_method'] == 'text'])
        }
        
        return stats
    
    def create_sankey_diagram(self):
        """Create Sankey diagram showing reprogramming flows per year"""
        logger.info("Creating Sankey diagram...")
        
        # Prepare data for Sankey
        sankey_data = []
        
        for year in sorted(self.df['fiscal_year'].dropna().unique()):
            year_data = self.df[self.df['fiscal_year'] == year]
            
            # Source: Organization
            org = year_data['requesting_organization'].iloc[0] if len(year_data) > 0 else 'Unknown'
            if pd.isna(org):
                org = 'Unknown'
            
            # Target: Document Type
            doc_type = year_data['document_type'].iloc[0] if len(year_data) > 0 else 'Unknown'
            if pd.isna(doc_type):
                doc_type = 'Unknown'
            
            # Value: Total amount
            total_amount = year_data['total_amount'].sum()
            if pd.isna(total_amount) or total_amount == 0:
                total_amount = 1  # Minimum value for visualization
            
            sankey_data.append({
                'source': f"{org} ({year})",
                'target': f"{doc_type} ({year})",
                'value': total_amount,
                'year': year
            })
        
        # Create Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=list(set([item['source'] for item in sankey_data] + [item['target'] for item in sankey_data])),
                color="lightblue"
            ),
            link=dict(
                source=[list(set([item['source'] for item in sankey_data] + [item['target'] for item in sankey_data])).index(item['source']) for item in sankey_data],
                target=[list(set([item['source'] for item in sankey_data] + [item['target'] for item in sankey_data])).index(item['target']) for item in sankey_data],
                value=[item['value'] for item in sankey_data],
                color="rgba(0,100,80,0.4)"
            )
        )])
        
        fig.update_layout(
            title_text="DD1414 Reprogramming Flows by Year and Organization",
            font_size=10,
            height=600
        )
        
        return fig
    
    def create_timeline_chart(self):
        """Create timeline chart showing amounts over time"""
        logger.info("Creating timeline chart...")
        
        # Group by year and sum amounts
        yearly_data = self.df.groupby('fiscal_year').agg({
            'total_amount': 'sum',
            'filename': 'count'
        }).reset_index()
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Total Reprogramming Amounts by Year', 'Number of Documents by Year'),
            vertical_spacing=0.1
        )
        
        # Amount chart
        fig.add_trace(
            go.Scatter(
                x=yearly_data['fiscal_year'],
                y=yearly_data['total_amount'],
                mode='lines+markers',
                name='Total Amount',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # Document count chart
        fig.add_trace(
            go.Bar(
                x=yearly_data['fiscal_year'],
                y=yearly_data['filename'],
                name='Document Count',
                marker_color='lightblue'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title_text="DD1414 Reprogramming Analysis Over Time",
            height=800,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Fiscal Year", row=2, col=1)
        fig.update_yaxes(title_text="Amount ($)", row=1, col=1)
        fig.update_yaxes(title_text="Number of Documents", row=2, col=1)
        
        return fig
    
    def create_organization_chart(self):
        """Create organization distribution chart"""
        logger.info("Creating organization chart...")
        
        org_data = self.df['requesting_organization'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=org_data.index,
            values=org_data.values,
            hole=0.3
        )])
        
        fig.update_layout(
            title_text="DD1414 Documents by Organization",
            height=500
        )
        
        return fig
    
    def create_confidence_analysis(self):
        """Create confidence score analysis"""
        logger.info("Creating confidence analysis...")
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Confidence Score Distribution', 'Confidence by Extraction Method'),
            specs=[[{"type": "histogram"}, {"type": "box"}]]
        )
        
        # Histogram
        fig.add_trace(
            go.Histogram(
                x=self.df['confidence_score'],
                nbinsx=20,
                name='Confidence Distribution'
            ),
            row=1, col=1
        )
        
        # Box plot by method
        for method in self.df['extraction_method'].unique():
            if pd.notna(method):
                method_data = self.df[self.df['extraction_method'] == method]['confidence_score']
                fig.add_trace(
                    go.Box(
                        y=method_data,
                        name=method.title(),
                        boxpoints='outliers'
                    ),
                    row=1, col=2
                )
        
        fig.update_layout(
            title_text="DD1414 Data Quality Analysis",
            height=500
        )
        
        return fig
    
    def create_dashboard_html(self):
        """Create comprehensive dashboard HTML"""
        logger.info("Creating dashboard HTML...")
        
        # Generate all charts
        sankey_fig = self.create_sankey_diagram()
        timeline_fig = self.create_timeline_chart()
        org_fig = self.create_organization_chart()
        confidence_fig = self.create_confidence_analysis()
        
        # Generate summary stats
        stats = self.generate_summary_stats()
        
        # Create HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DD1414 Reprogramming Analysis Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .chart-title {{
            font-size: 1.5em;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .data-table {{
            margin-top: 30px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #667eea;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .download-section {{
            margin-top: 30px;
            padding: 20px;
            background: #e8f4f8;
            border-radius: 8px;
            text-align: center;
        }}
        .btn {{
            display: inline-block;
            padding: 10px 20px;
            margin: 5px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }}
        .btn:hover {{
            background: #5a6fd8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 DD1414 Reprogramming Analysis Dashboard</h1>
            <p>Comprehensive Analysis of Department of Defense Reprogramming Actions</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_documents']}</div>
                <div class="stat-label">Total Documents</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['years_span']}</div>
                <div class="stat-label">Years Covered</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats['total_value']:,.0f}</div>
                <div class="stat-label">Total Value</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats['average_amount']:,.0f}</div>
                <div class="stat-label">Average Amount</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['average_confidence']:.1f}%</div>
                <div class="stat-label">Avg Confidence</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['high_confidence_docs']}</div>
                <div class="stat-label">High Confidence Docs</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">📊 Reprogramming Flows by Year and Organization</div>
            <div id="sankey-chart"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">📈 Timeline Analysis</div>
            <div id="timeline-chart"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">🏛️ Organization Distribution</div>
            <div id="org-chart"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">⭐ Data Quality Analysis</div>
            <div id="confidence-chart"></div>
        </div>
        
        <div class="data-table">
            <h3>📋 Detailed Data Table</h3>
            <div id="data-table"></div>
        </div>
        
        <div class="download-section">
            <h3>📥 Download Data</h3>
            <a href="data/dd1414_csv/dd1414_enhanced_data.csv" class="btn">Download CSV</a>
            <a href="data/dd1414_csv/dd1414_enhanced_data.json" class="btn">Download JSON</a>
            <a href="dd1414_analysis_report.html" class="btn">View Full Report</a>
        </div>
    </div>
    
    <script>
        // Sankey Chart
        {sankey_fig.to_html(include_plotlyjs=False, div_id="sankey-chart")}
        
        // Timeline Chart
        {timeline_fig.to_html(include_plotlyjs=False, div_id="timeline-chart")}
        
        // Organization Chart
        {org_fig.to_html(include_plotlyjs=False, div_id="org-chart")}
        
        // Confidence Chart
        {confidence_fig.to_html(include_plotlyjs=False, div_id="confidence-chart")}
        
        // Data Table
        const data = {self.df.to_json(orient='records')};
        const table = document.getElementById('data-table');
        table.innerHTML = '<table><thead><tr><th>Filename</th><th>Fiscal Year</th><th>Type</th><th>Amount</th><th>Organization</th><th>Confidence</th></tr></thead><tbody>' +
            data.map(row => `<tr><td>${{row.filename}}</td><td>${{row.fiscal_year}}</td><td>${{row.document_type}}</td><td>$${{row.total_amount?.toLocaleString() || 'N/A'}}</td><td>${{row.requesting_organization || 'N/A'}}</td><td>${{row.confidence_score?.toFixed(1) || 'N/A'}}%</td></tr>`).join('') +
            '</tbody></table>';
    </script>
</body>
</html>
        """
        
        return html_content
    
    def save_analysis(self):
        """Save all analysis results"""
        logger.info("Saving analysis results...")
        
        # Save dashboard HTML
        dashboard_html = self.create_dashboard_html()
        with open(self.output_dir / "dd1414_dashboard.html", 'w') as f:
            f.write(dashboard_html)
        
        # Save individual charts
        sankey_fig = self.create_sankey_diagram()
        sankey_fig.write_html(self.output_dir / "dd1414_sankey.html")
        
        timeline_fig = self.create_timeline_chart()
        timeline_fig.write_html(self.output_dir / "dd1414_timeline.html")
        
        org_fig = self.create_organization_chart()
        org_fig.write_html(self.output_dir / "dd1414_organizations.html")
        
        confidence_fig = self.create_confidence_analysis()
        confidence_fig.write_html(self.output_dir / "dd1414_confidence.html")
        
        # Save summary statistics
        stats = self.generate_summary_stats()
        with open(self.output_dir / "dd1414_summary.json", 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        # Save processed data
        self.df.to_csv(self.output_dir / "dd1414_processed_data.csv", index=False)
        
        logger.info(f"Analysis saved to {self.output_dir}")
    
    def run_analysis(self):
        """Run complete analysis"""
        logger.info("Starting DD1414 analysis...")
        
        try:
            self.save_analysis()
            logger.info("Analysis completed successfully!")
            
            # Print summary
            stats = self.generate_summary_stats()
            print(f"\n🎉 DD1414 Analysis Complete!")
            print(f"📊 Documents: {stats['total_documents']}")
            print(f"📅 Years: {stats['years_span']}")
            print(f"💰 Total Value: ${stats['total_value']:,.0f}")
            print(f"⭐ Confidence: {stats['average_confidence']:.1f}%")
            print(f"📁 Output: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DD1414 Data Analyzer")
    parser.add_argument("--data-file", default="data/dd1414_csv/dd1414_enhanced_data.csv", help="Input CSV file")
    parser.add_argument("--output-dir", default="docs", help="Output directory")
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = DD1414Analyzer(args.data_file, args.output_dir)
    
    # Run analysis
    analyzer.run_analysis()

if __name__ == "__main__":
    main()