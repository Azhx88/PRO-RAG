import os
import uuid
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from config import settings
from services.llm_service import call_groq

CHART_TYPES = ["bar", "line", "pie", "scatter", "heatmap", "histogram"]

def detect_chart_type(query: str) -> str:
    q = query.lower()
    if "pie" in q: return "pie"
    if "line" in q or "trend" in q or "over time" in q: return "line"
    if "scatter" in q or "correlation" in q: return "scatter"
    if "heat" in q: return "heatmap"
    if "histogram" in q or "distribution" in q: return "histogram"
    return "bar"  # default

def generate_chart(query: str, data: list[dict], schema_json: dict) -> str:
    """
    Generate chart image from SQL result data.
    Returns path to saved PNG file.
    """
    if not data:
        raise ValueError("No data to chart")

    df = pd.DataFrame(data)
    chart_type = detect_chart_type(query)

    # Ask LLM which columns to use
    col_names = list(df.columns)
    prompt = f"""Given these column names: {col_names}
User asked: "{query}"
Which column is the X-axis (categories) and which is the Y-axis (values)?
Return JSON only: {{"x": "col_name", "y": "col_name"}}"""

    try:
        col_response = call_groq(prompt, system="Return only valid JSON.")
        col_json = json.loads(col_response)
        x_col = col_json.get("x", col_names[0])
        y_col = col_json.get("y", col_names[1] if len(col_names) > 1 else col_names[0])
    except:
        x_col = col_names[0]
        y_col = col_names[1] if len(col_names) > 1 else col_names[0]

    # Set dark theme
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#1C1A17")
    ax.set_facecolor("#252219")

    accent = "#D97757"
    text_color = "#F5F0E8"

    # Ensure y_col is numeric for chart types that need it
    if chart_type in ("bar", "line", "scatter", "histogram"):
        df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
        df = df.dropna(subset=[y_col])

    try:
        if chart_type == "bar":
            colors = sns.color_palette("husl", len(df))
            ax.bar(df[x_col].astype(str), df[y_col], color=colors, alpha=0.85)
        elif chart_type == "line":
            ax.plot(df[x_col].astype(str), df[y_col], color="#00e5ff", linewidth=3, marker="o", markersize=8, markerfacecolor="#ff007f")
            ax.fill_between(df[x_col].astype(str), df[y_col], color="#00e5ff", alpha=0.1)
        elif chart_type == "pie":
            y_numeric = pd.to_numeric(df[y_col], errors="coerce").dropna()
            labels = df[x_col].astype(str).iloc[:len(y_numeric)]
            colors = sns.color_palette("Set3", len(y_numeric))
            ax.pie(y_numeric, labels=labels, autopct="%1.1f%%", explode=[0.05]*len(y_numeric), colors=colors, shadow=True, textprops={'color': "white", 'weight': 'bold'})
        elif chart_type == "scatter":
            colors = sns.color_palette("plasma", len(df))
            ax.scatter(df[x_col], df[y_col], c=range(len(df)), cmap="plasma", alpha=0.8, s=100, edgecolors="white")
        elif chart_type == "histogram":
            ax.hist(df[y_col], bins=15, color="#ff9100", alpha=0.7, edgecolor="white")
        elif chart_type == "heatmap":
            numeric_df = df.select_dtypes(include="number")
            sns.heatmap(numeric_df.corr(), ax=ax, cmap="coolwarm", annot=True, fmt=".2f", linewidths=.5)
    except Exception as e:
        ax.text(0.5, 0.5, f"Chart error: {str(e)}", transform=ax.transAxes,
                ha="center", color=text_color)

    ax.tick_params(colors=text_color)
    ax.set_xlabel(x_col, color=text_color)
    ax.set_ylabel(y_col, color=text_color)
    ax.set_title(query[:60], color=text_color, pad=16)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    chart_filename = f"chart_{uuid.uuid4().hex[:8]}.png"
    chart_path = os.path.join(settings.upload_dir, "charts", chart_filename)
    os.makedirs(os.path.dirname(chart_path), exist_ok=True)
    plt.savefig(chart_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()

    return chart_path
