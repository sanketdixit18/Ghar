"""
MarketService
---------------
Direct port of utils/market_trends.py. Only cities that ship a
data/<city>/market_trends.csv (declared via features.market_trends in
config.json) will have this section active — other cities show a friendly
"not available" message, same as the original app.
"""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import plotly.express as px

from app.services.loader import city_manager
from app.utils.json_utils import to_jsonable

logger = logging.getLogger("real_estate.market")

SEQUENTIAL_SCALE = "Purples"
CATEGORICAL_PALETTE = ["#5B4FE9", "#00B8A9", "#F6A609", "#F65D5D",
                        "#3BB3E0", "#8E7DFF", "#2FB380", "#F08CD8"]


def _style(fig, title: str, height: int = 420, **layout_kwargs):
    fig.update_layout(
        template="plotly_dark",
        title=dict(text=title, font=dict(size=15, color="#F5F7FA")),
        height=height,
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(20,24,38,0.6)",
        coloraxis_showscale=False,
        **layout_kwargs,
    )
    return fig


def _clip_outliers(df: pd.DataFrame, col: str, lower=0.01, upper=0.99) -> pd.DataFrame:
    lo, hi = df[col].quantile([lower, upper])
    return df[df[col].between(lo, hi)]


def _top_n_bar(df: pd.DataFrame, group_col: str, value_col: str, agg: str, title: str,
               x_title: str, n: int = 10, text_fmt: str = ".2f", height: int = 420) -> dict:
    ranked = (df.groupby(group_col, as_index=False)[value_col].agg(agg)
              .rename(columns={value_col: "value"}).sort_values("value", ascending=False).head(n))
    fig = px.bar(ranked, x="value", y=group_col, orientation="h", color="value",
                 color_continuous_scale=SEQUENTIAL_SCALE, text_auto=text_fmt)
    fig.update_traces(marker_line_width=0)
    fig = _style(fig, title, height=height, xaxis_title=x_title, yaxis_title="")
    fig.update_yaxes(categoryorder="total ascending")
    return fig.to_plotly_json()


def _donut(series: pd.Series, title: str, height: int = 360) -> dict:
    counts = series.value_counts().reset_index()
    counts.columns = ["label", "count"]
    fig = px.pie(counts, names="label", values="count", hole=0.55, color_discrete_sequence=CATEGORICAL_PALETTE)
    fig.update_traces(textinfo="percent+label", textfont_size=12)
    fig = _style(fig, title, height=height, showlegend=False)
    return fig.to_plotly_json()


class MarketService:

    def is_available(self, city: str) -> bool:
        return city_manager.load_market_assets(city) is not None

    def get_filter_options(self, city: str) -> dict[str, Any]:
        df = city_manager.load_market_assets(city)
        if df is None:
            return {}
        return {
            "localities": sorted(df["locality"].dropna().unique().tolist()),
            "builders": sorted(df["company_name"].dropna().unique().tolist()),
            "property_types": sorted(df["flat_type"].dropna().unique().tolist()),
            "price_segments": sorted(df["price_segment"].dropna().unique().tolist()),
        }

    def get_dashboard(self, city: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        filters = filters or {}
        df = city_manager.load_market_assets(city)
        if df is None:
            return {"available": False}

        mask = pd.Series(True, index=df.index)
        if filters.get("locality") not in (None, "All"):
            mask &= df["locality"] == filters["locality"]
        if filters.get("builder") not in (None, "All"):
            mask &= df["company_name"] == filters["builder"]
        if filters.get("property_type") not in (None, "All"):
            mask &= df["flat_type"] == filters["property_type"]
        if filters.get("price_segment") not in (None, "All"):
            mask &= df["price_segment"] == filters["price_segment"]
        fdf = df[mask]

        if fdf.empty:
            return {"available": True, "empty": True}

        kpis = {
            "avg_price": round(float(fdf["price_cr"].mean()), 2),
            "avg_rate": round(float(fdf["price_per_sqft"].mean()), 0),
            "localities": int(fdf["locality"].nunique()),
            "listings": int(len(fdf)),
            "median_bhk": float(fdf["bhk"].median()),
        }

        overview = {
            "price_segment_mix": _donut(fdf["price_segment"], "Price Segment Mix"),
            "property_type_mix": _donut(fdf["flat_type"], "Property Type Mix"),
            "construction_status": _donut(fdf["status"], "Construction Status"),
            "rera_approval": _donut(fdf["rera_approval"], "RERA Approval"),
        }

        listings = fdf["locality"].value_counts().head(12).reset_index()
        listings.columns = ["locality", "value"]
        active_fig = px.bar(listings, x="locality", y="value", color="value",
                             color_continuous_scale=SEQUENTIAL_SCALE, text_auto=True)
        active_fig.update_traces(marker_line_width=0)
        active_fig = _style(active_fig, "Most Active Localities by Listings", height=400,
                             xaxis_title="", yaxis_title="Listings")

        location = {
            "top_expensive_localities": _top_n_bar(fdf, "locality", "price_cr", "mean",
                                                     "Top 10 Most Expensive Localities", "Avg Price (Cr)"),
            "top_rate_localities": _top_n_bar(fdf, "locality", "price_per_sqft", "mean",
                                               "Top 10 Highest Rate Localities", "\u20b9 / sq.ft", text_fmt=".0f"),
            "most_active_localities": active_fig.to_plotly_json(),
        }

        volume_ok = fdf["company_name"].value_counts()
        eligible = volume_ok[volume_ok >= max(5, int(len(fdf) * 0.002))].index
        builder_df = fdf[fdf["company_name"].isin(eligible)]

        soc = fdf[fdf["society"] != "Outside Socity"]["society"].value_counts().head(10).reset_index()
        soc.columns = ["society", "value"]
        soc_fig = px.bar(soc, x="value", y="society", orientation="h", color="value",
                          color_continuous_scale=SEQUENTIAL_SCALE, text_auto=True)
        soc_fig.update_traces(marker_line_width=0)
        soc_fig = _style(soc_fig, "Most Listed Projects", height=400, xaxis_title="Listings", yaxis_title="")
        soc_fig.update_yaxes(categoryorder="total ascending")

        builders = {
            "top_by_listings": _top_n_bar(fdf, "company_name", "price_cr", "count",
                                           "Top Builders by Listings", "Listings", text_fmt=True),
            "top_premium": (_top_n_bar(builder_df, "company_name", "price_cr", "mean",
                                        "Top Premium Builders (min. listing volume)", "Avg Price (Cr)")
                             if not builder_df.empty else None),
            "top_projects": soc_fig.to_plotly_json(),
        }

        clipped = _clip_outliers(_clip_outliers(fdf, "price_cr"), "area")
        price_hist = px.histogram(clipped, x="price_cr", nbins=30, color_discrete_sequence=["#5B4FE9"])
        price_hist = _style(price_hist, "Price Distribution", xaxis_title="Price (Cr)", yaxis_title="Listings")

        area_scatter = px.scatter(clipped, x="area", y="price_cr", color="flat_type", opacity=0.6,
                                   color_discrete_sequence=CATEGORICAL_PALETTE, hover_data=["locality"])
        area_scatter = _style(area_scatter, "Area vs Price", xaxis_title="Area (sq.ft)", yaxis_title="Price (Cr)")

        type_box = px.box(clipped, x="flat_type", y="price_cr", color="flat_type",
                           color_discrete_sequence=CATEGORICAL_PALETTE)
        type_box = _style(type_box, "Price by Property Type", xaxis_title="", yaxis_title="Price (Cr)", showlegend=False)

        rera_price = fdf.groupby("rera_approval", as_index=False)["price_per_sqft"].mean()
        rera_fig = px.bar(rera_price, x="rera_approval", y="price_per_sqft", color="rera_approval",
                           color_discrete_sequence=CATEGORICAL_PALETTE, text_auto=".0f")
        rera_fig = _style(rera_fig, "Avg Rate: RERA vs Non-RERA", xaxis_title="", yaxis_title="\u20b9 / sq.ft", showlegend=False)

        price_area = {
            "price_distribution": price_hist.to_plotly_json(),
            "area_vs_price": area_scatter.to_plotly_json(),
            "price_by_type": type_box.to_plotly_json(),
            "rera_vs_rate": rera_fig.to_plotly_json(),
        }

        price_by_locality = fdf.groupby("locality")["price_cr"].mean()
        builder_counts = fdf["company_name"].value_counts()
        locality_counts = fdf["locality"].value_counts()

        highlights = {
            "most_expensive_locality": price_by_locality.idxmax(),
            "most_expensive_price": round(float(price_by_locality.max()), 2),
            "most_affordable_locality": price_by_locality.idxmin(),
            "most_affordable_price": round(float(price_by_locality.min()), 2),
            "top_builder": builder_counts.idxmax(),
            "top_builder_listings": int(builder_counts.max()),
            "most_active_locality": locality_counts.idxmax(),
            "most_active_count": int(locality_counts.max()),
            "popular_type": fdf["flat_type"].mode()[0],
            "common_bhk": float(fdf["bhk"].mode()[0]),
            "rera_share_pct": round(float((fdf["rera_approval"] == "Approved By Rera").mean() * 100), 0),
            "ready_share_pct": round(float((fdf["status"] == "Ready to Move").mean() * 100), 0),
        }

        return to_jsonable({
            "available": True,
            "empty": False,
            "kpis": kpis,
            "overview": overview,
            "location": location,
            "builders": builders,
            "price_area": price_area,
            "highlights": highlights,
        })


market_service = MarketService()
