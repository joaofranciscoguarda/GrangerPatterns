import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
import pandas as pd
import numpy as np

def generate_report(analysis, output_path, figures_dir, base_name):
    """
    Generate a PDF report for a single analysis
    
    Args:
        analysis (dict): Analysis results
        output_path (str): Path to save the PDF report
        figures_dir (str): Directory containing figures
        base_name (str): Base name for figure files
    """
    # Initialize the document
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Add custom styles
    styles.add(ParagraphStyle(name='ReportTitle',
                             parent=styles['Heading1'],
                             fontSize=16,
                             spaceAfter=12))
    
    styles.add(ParagraphStyle(name='ReportHeading2',
                             parent=styles['Heading2'],
                             fontSize=14,
                             spaceAfter=10))
    
    styles.add(ParagraphStyle(name='ReportBodyText',
                             parent=styles['Normal'],
                             fontSize=11,
                             spaceAfter=6))
    
    # Build elements for the document
    elements = []
    
    # Report title
    participant_id = analysis['metadata']['participant_id']
    timepoint = analysis['metadata']['timepoint']
    condition = analysis['metadata']['condition']
    
    title = f"Granger Causality Analysis Report: Participant {participant_id}, {timepoint}, {condition}"
    elements.append(Paragraph(title, styles['ReportTitle']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Introduction
    intro_text = """
    This report presents the results of Granger Causality (GC) analysis in the time domain,
    examining directional influences between brain regions. Granger Causality measures the 
    extent to which past values of one signal help predict future values of another signal
    beyond what can be predicted by past values of the second signal alone.
    """
    elements.append(Paragraph("Introduction", styles['ReportHeading2']))
    elements.append(Paragraph(intro_text, styles['ReportBodyText']))
    elements.append(Spacer(1, 0.2*inch))
    
    # 1. Connectivity Matrix
    elements.append(Paragraph("1. Connectivity Matrix", styles['ReportHeading2']))
    
    matrix_text = """
    The connectivity matrix shows the strength of directional influence from row (source) to column (target).
    Each cell represents the Granger Causality value GC(source → target). Higher values indicate stronger
    causal influence from the source electrode to the target electrode.
    """
    elements.append(Paragraph(matrix_text, styles['ReportBodyText']))
    
    # Add matrix figure
    matrix_img_path = os.path.join(figures_dir, f"{base_name}_matrix.png")
    if os.path.exists(matrix_img_path):
        img = Image(matrix_img_path, width=6*inch, height=5*inch)
        elements.append(img)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # 2. Network Graph
    elements.append(Paragraph("2. Network Visualization", styles['ReportHeading2']))
    
    network_text = """
    The network graph visualizes the directional connectivity between electrodes. Arrows show the direction
    of influence, with thicker arrows indicating stronger Granger causal connections. Only connections
    above a threshold (0.0005) are shown to highlight the most significant pathways.
    """
    elements.append(Paragraph(network_text, styles['ReportBodyText']))
    
    # Add network figure
    network_img_path = os.path.join(figures_dir, f"{base_name}_network.png")
    if os.path.exists(network_img_path):
        img = Image(network_img_path, width=6*inch, height=5*inch)
        elements.append(img)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # 3. Nodal Metrics
    elements.append(Paragraph("3. Electrode-Level Metrics", styles['ReportHeading2']))
    
    nodal_text = """
    These metrics characterize each electrode's role in the network:
    
    • In-Strength: Sum of all incoming GC values to each electrode, indicating how much the electrode
      is influenced by others.
    
    • Out-Strength: Sum of all outgoing GC values from each electrode, showing how much the electrode
      influences others.
    
    • Causal Flow: The difference between out-strength and in-strength. Positive values indicate
      "sender" nodes that have more outgoing than incoming influence, while negative values indicate
      "receiver" nodes.
    """
    elements.append(Paragraph(nodal_text, styles['ReportBodyText']))
    
    # Add table with nodal metrics
    nodal_data = []
    nodal_data.append(['Electrode', 'In-Strength', 'Out-Strength', 'Causal Flow', 'Category'])
    
    # Sort electrodes by causal flow
    sorted_electrodes = sorted(analysis['nodal'].keys(), 
                              key=lambda e: analysis['nodal'][e]['causal_flow'],
                              reverse=True)
    
    for electrode in sorted_electrodes:
        metrics = analysis['nodal'][electrode]
        nodal_data.append([
            electrode,
            f"{metrics['in_strength']:.6f}",
            f"{metrics['out_strength']:.6f}",
            f"{metrics['causal_flow']:.6f}",
            metrics['category']
        ])
    
    table = Table(nodal_data, colWidths=[0.8*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Add nodal figure
    nodal_img_path = os.path.join(figures_dir, f"{base_name}_nodal.png")
    if os.path.exists(nodal_img_path):
        img = Image(nodal_img_path, width=6*inch, height=6*inch)
        elements.append(img)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # 4. Pairwise Connections
    elements.append(Paragraph("4. Directional Connectivity Strengths", styles['ReportHeading2']))
    
    pairwise_text = """
    This section shows the strength of Granger causal influence for each pair of electrodes.
    The bars represent the GC value for each source→target connection, sorted from strongest
    to weakest. This allows for comparison of directional influences (e.g., C3→F4 vs F4→C3).
    """
    elements.append(Paragraph(pairwise_text, styles['ReportBodyText']))
    
    # Add pairwise figure
    pairwise_img_path = os.path.join(figures_dir, f"{base_name}_pairwise.png")
    if os.path.exists(pairwise_img_path):
        img = Image(pairwise_img_path, width=6*inch, height=4*inch)
        elements.append(img)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # 5. Global Metrics
    elements.append(Paragraph("5. Global Network Measures", styles['ReportHeading2']))
    
    global_text = """
    Global metrics provide an overview of the entire Granger causality network:
    
    • Global GC Strength: Sum of all GC values in the matrix, indicating overall connectivity.
    
    • Mean GC Strength: Average of all GC values, providing a normalized measure of connectivity.
    
    • Network Density: Proportion of connections that exceed specific thresholds (0.0001, 0.0005, 0.001),
      showing how densely connected the network is.
    """
    elements.append(Paragraph(global_text, styles['ReportBodyText']))
    
    # Add table with global metrics
    global_metrics = analysis['global']
    global_data = []
    global_data.append(['Metric', 'Value'])
    
    metrics_to_display = [
        ('Global GC Strength', global_metrics['global_gc_strength']),
        ('Mean GC Strength', global_metrics['mean_gc_strength']),
        ('Median GC Strength', global_metrics['median_gc_strength']),
        ('Network Density (th=0.0001)', global_metrics['network_density_th0.0001']),
        ('Network Density (th=0.0005)', global_metrics['network_density_th0.0005']),
        ('Network Density (th=0.001)', global_metrics['network_density_th0.001']),
    ]
    
    for metric, value in metrics_to_display:
        global_data.append([metric, f"{value:.6f}"])
    
    table = Table(global_data, colWidths=[3*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Add global metrics figure
    global_img_path = os.path.join(figures_dir, f"{base_name}_global.png")
    if os.path.exists(global_img_path):
        img = Image(global_img_path, width=6*inch, height=3*inch)
        elements.append(img)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Conclusion
    elements.append(Paragraph("Conclusion", styles['ReportHeading2']))
    
    conclusion_text = f"""
    This report presents a comprehensive analysis of Granger Causality for participant {participant_id}
    during {timepoint} in the {condition} condition. The results provide insights into directed connectivity
    patterns among electrodes, highlighting key sender and receiver nodes, and quantifying the strength of
    directional influences between brain regions.
    """
    elements.append(Paragraph(conclusion_text, styles['ReportBodyText']))
    
    # Build the document
    doc.build(elements)
    
    return output_path

def generate_group_report(group_stats, output_path, figures_dir, group_name):
    """
    Generate a PDF report for group-level statistics
    
    Args:
        group_stats (dict): Group statistics results
        output_path (str): Path to save the PDF report
        figures_dir (str): Directory containing figures
        group_name (str): Name for the group report
    """
    # Initialize the document
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Add custom styles
    styles.add(ParagraphStyle(name='GroupTitle',
                             parent=styles['Heading1'],
                             fontSize=16,
                             spaceAfter=12))
    
    styles.add(ParagraphStyle(name='GroupHeading2',
                             parent=styles['Heading2'],
                             fontSize=14,
                             spaceAfter=10))
    
    styles.add(ParagraphStyle(name='GroupBodyText',
                             parent=styles['Normal'],
                             fontSize=11,
                             spaceAfter=6))
    
    # Build elements for the document
    elements = []
    
    # Report title
    title = f"Group-Level Granger Causality Analysis Report: {group_name}"
    elements.append(Paragraph(title, styles['GroupTitle']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Introduction
    intro_text = """
    This report presents group-level statistics from Granger Causality analysis.
    The results show average metrics across participants, providing insight into
    consistent patterns of directed connectivity in the group.
    """
    elements.append(Paragraph("Introduction", styles['GroupHeading2']))
    elements.append(Paragraph(intro_text, styles['GroupBodyText']))
    elements.append(Spacer(1, 0.2*inch))
    
    # 1. Nodal Metrics
    elements.append(Paragraph("1. Group Electrode-Level Metrics", styles['GroupHeading2']))
    
    nodal_text = """
    The table below shows the average nodal metrics across participants:
    
    • In-Strength: The group average of incoming influence for each electrode.
    • Out-Strength: The group average of outgoing influence for each electrode.
    • Causal Flow: The group average of net causal influence (out - in) for each electrode.
    • Dominant Category: The most common categorization (sender/receiver/neutral) across participants.
    """
    elements.append(Paragraph(nodal_text, styles['GroupBodyText']))
    
    # Add table with group nodal metrics
    nodal_data = []
    nodal_data.append(['Electrode', 'In-Strength (Mean±SD)', 'Out-Strength (Mean±SD)', 
                     'Causal Flow (Mean±SD)', 'Dominant Category'])
    
    # Sort electrodes by mean causal flow
    sorted_electrodes = sorted(group_stats['nodal'].keys(), 
                              key=lambda e: group_stats['nodal'][e]['causal_flow_mean'],
                              reverse=True)
    
    for electrode in sorted_electrodes:
        metrics = group_stats['nodal'][electrode]
        nodal_data.append([
            electrode,
            f"{metrics['in_strength_mean']:.6f}±{metrics['in_strength_std']:.6f}",
            f"{metrics['out_strength_mean']:.6f}±{metrics['out_strength_std']:.6f}",
            f"{metrics['causal_flow_mean']:.6f}±{metrics['causal_flow_std']:.6f}",
            metrics['dominant_category']
        ])
    
    table = Table(nodal_data, colWidths=[0.7*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    
    # 2. Pairwise Connections
    elements.append(Paragraph("2. Group Directional Connectivity Strengths", styles['GroupHeading2']))
    
    pairwise_text = """
    This section summarizes the average Granger causal influence for each pair of electrodes across the group.
    The table shows the mean and standard deviation for the strongest connections, sorted from highest to lowest.
    """
    elements.append(Paragraph(pairwise_text, styles['GroupBodyText']))
    
    # Add table with top pairwise connections
    pairwise_data = []
    pairwise_data.append(['Connection', 'Mean GC Value', 'Standard Deviation'])
    
    # Sort pairs by mean value and take top 10
    sorted_pairs = sorted(group_stats['pairwise'].keys(), 
                         key=lambda p: group_stats['pairwise'][p]['mean'],
                         reverse=True)
    top_pairs = sorted_pairs[:10]  # Show only top 10 pairs
    
    for pair in top_pairs:
        metrics = group_stats['pairwise'][pair]
        pairwise_data.append([
            pair,
            f"{metrics['mean']:.6f}",
            f"{metrics['std']:.6f}"
        ])
    
    table = Table(pairwise_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    
    # 3. Global Metrics
    elements.append(Paragraph("3. Group Global Network Measures", styles['GroupHeading2']))
    
    global_text = """
    The table below shows the average global metrics across participants:
    """
    elements.append(Paragraph(global_text, styles['GroupBodyText']))
    
    # Add table with global metrics
    global_data = []
    global_data.append(['Metric', 'Mean', 'Standard Deviation', 'Min', 'Max'])
    
    metrics_to_display = [
        'global_gc_strength',
        'mean_gc_strength',
        'network_density_th0.0001',
        'network_density_th0.0005',
        'network_density_th0.001',
    ]
    
    metric_names = {
        'global_gc_strength': 'Global GC Strength',
        'mean_gc_strength': 'Mean GC Strength',
        'network_density_th0.0001': 'Network Density (th=0.0001)',
        'network_density_th0.0005': 'Network Density (th=0.0005)',
        'network_density_th0.001': 'Network Density (th=0.001)',
    }
    
    for metric_key in metrics_to_display:
        if metric_key in group_stats['global']:
            metric = group_stats['global'][metric_key]
            global_data.append([
                metric_names.get(metric_key, metric_key),
                f"{metric['mean']:.6f}",
                f"{metric['std']:.6f}",
                f"{metric['min']:.6f}",
                f"{metric['max']:.6f}"
            ])
    
    table = Table(global_data, colWidths=[2*inch, 1*inch, 1*inch, 0.8*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Conclusion
    elements.append(Paragraph("Conclusion", styles['GroupHeading2']))
    
    conclusion_text = f"""
    This report presents group-level statistics from Granger Causality analysis for {group_name}.
    The results highlight consistent patterns of directed connectivity across participants,
    identifying common sender and receiver nodes and quantifying the group average strength
    of directional influences between brain regions.
    """
    elements.append(Paragraph(conclusion_text, styles['GroupBodyText']))
    
    # Build the document
    doc.build(elements)
    
    return output_path 