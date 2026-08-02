"""
AnalyticsService
------------------
Direct port of utils/analytics.py's logic. The column-alias resolver is the
key piece that makes analytics "just work" for a new city whose CSV uses
different column names (e.g. Mumbai's "locality"/"area" vs Gurgaon's
"sector"/"built_up_area") without any code changes.

Charts are built with Plotly (same as the original) and shipped to the
browser as Plotly JSON, rendered client-side with Plotly.js for full
interactivity (zoom, hover, legend toggling) — matching the original's
`st.plotly_chart`.
"""
from __future__ import annotations

import ast
import base64
import io
import logging
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.services.loader import city_manager
from app.utils.json_utils import to_jsonable

logger = logging.getLogger("real_estate.analytics")

# ==========================================================================
# Column aliases — add more aliases here as you onboard new cities.
# ==========================================================================
COLUMN_ALIASES: dict[str, list[str]] = {
    "price": ["price", "Price", "price_cr", "PriceCr", "price_in_cr"],
    "sector": ["sector", "Sector", "locality", "Locality", "area_name",
               "location", "Location", "neighborhood"],
    "latitude": ["latitude", "Latitude", "lat", "Lat"],
    "longitude": ["longitude", "Longitude", "lon", "lng", "Long"],
    "property_type": ["property_type", "flat_type", "PropertyType", "type",
                       "Type", "property_category"],
    "bedRoom": ["bedRoom", "bedrooms", "Bedrooms", "bhk", "BHK",
                "no_of_bedrooms", "bedroom_num"],
    "built_up_area": ["built_up_area", "area_sqft", "area", "Area",
                       "built_up_area_sqft", "carpet_area", "super_area"],
    "features": ["features", "amenities", "Features", "Amenities"],
    "builder_name": ["builder_name", "company_name", "developer", "builder"],
}


def resolve_columns(df: pd.DataFrame, aliases: dict[str, list[str]] = COLUMN_ALIASES) -> dict[str, str | None]:
    resolved: dict[str, str | None] = {}
    df_columns = list(df.columns)
    lower_lookup = {c.lower(): c for c in df_columns}

    for logical_name, candidates in aliases.items():
        found = None
        for candidate in candidates:
            if candidate in df_columns:
                found = candidate
                break
            if candidate.lower() in lower_lookup:
                found = lower_lookup[candidate.lower()]
                break
        resolved[logical_name] = found
    return resolved


def _plotly_json(fig: go.Figure) -> Any:
    return to_jsonable(fig.to_plotly_json())


class AnalyticsService:

    def is_available(self, city: str) -> bool:
        analytics_df, _ = city_manager.load_analytics_assets(city)
        return analytics_df is not None

    # ------------------------------------------------------------------
    def get_dashboard(self, city: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        filters = filters or {}
        analytics_df, wordcloud_df = city_manager.load_analytics_assets(city)
        if analytics_df is None:
            return {"available": False}

        cols = resolve_columns(analytics_df)
        wc_cols = resolve_columns(wordcloud_df) if wordcloud_df is not None else {}

        result: dict[str, Any] = {
            "available": True,
            "columns": cols,
            "sector_label": (cols["sector"].replace("_", " ").title() if cols["sector"] else "Sector"),
        }

        result["kpis"] = self._kpis(analytics_df, cols)
        result["filter_options"] = self._filter_options(analytics_df, cols)
        result["geo_map"] = self._geo_map(analytics_df, cols, filters)
        result["area_vs_price"] = self._area_vs_price(analytics_df, cols, filters)
        result["bhk_distribution"] = self._bhk_distribution(analytics_df, cols, filters)
        result["bedroom_price_box"] = self._bedroom_price_box(analytics_df, cols, filters)
        result["price_histogram"] = self._price_histogram(analytics_df, cols, filters)

        if wordcloud_df is not None and wc_cols.get("sector") and wc_cols.get("features"):
            result["wordcloud_available"] = True
            result["wordcloud_sectors"] = sorted(wordcloud_df[wc_cols["sector"]].dropna().unique().tolist())
        else:
            result["wordcloud_available"] = False

        return to_jsonable(result)

    # ------------------------------------------------------------------
    def _kpis(self, df: pd.DataFrame, cols: dict) -> dict[str, Any]:
        price, sector = cols.get("price"), cols.get("sector")
        if not price:
            return {}
        return {
            "avg_price": round(float(df[price].mean()), 2),
            "max_price": round(float(df[price].max()), 2),
            "min_price": round(float(df[price].min()), 3),
            "sector_count": int(df[sector].nunique()) if sector else None,
            "total_properties": int(len(df)),
        }

    def _filter_options(self, df: pd.DataFrame, cols: dict) -> dict[str, Any]:
        opts: dict[str, Any] = {}
        if cols.get("sector"):
            opts["sectors"] = sorted(df[cols["sector"]].dropna().unique().tolist())
        if cols.get("property_type"):
            opts["property_types"] = sorted(df[cols["property_type"]].dropna().unique().tolist())
        if cols.get("bedRoom"):
            try:
                opts["bedrooms"] = sorted(df[cols["bedRoom"]].dropna().unique().tolist())
            except TypeError:
                opts["bedrooms"] = sorted(df[cols["bedRoom"]].dropna().unique().tolist(), key=str)
        if cols.get("price"):
            opts["price_min"] = float(df[cols["price"]].min())
            opts["price_max"] = float(df[cols["price"]].max())
        return opts

    def _apply_common_filters(self, df: pd.DataFrame, cols: dict, filters: dict) -> pd.DataFrame:
        out = df.copy()
        sector = cols.get("sector")
        price = cols.get("price")
        if sector and filters.get("sector") not in (None, "All"):
            out = out[out[sector] == filters["sector"]]
        if price and filters.get("price_min") is not None:
            out = out[out[price] >= float(filters["price_min"])]
        if price and filters.get("price_max") is not None:
            out = out[out[price] <= float(filters["price_max"])]
        return out

    # ------------------------------------------------------------------
    def _geo_map(self, df: pd.DataFrame, cols: dict, filters: dict) -> dict[str, Any] | None:
        price, sector, lat, lon = cols.get("price"), cols.get("sector"), cols.get("latitude"), cols.get("longitude")
        if not all([price, sector, lat, lon]):
            return None

        filtered = self._apply_common_filters(df, cols, filters)
        if filtered.empty:
            return {"empty": True}

        map_df = filtered.groupby(sector, as_index=False).agg({price: "mean", lat: "first", lon: "first"})

        fig = go.Figure(go.Scattermapbox(
            lat=map_df[lat], lon=map_df[lon], mode="markers",
            text=map_df[sector], customdata=map_df[[price]],
            marker=dict(size=18, color=map_df[price], colorscale="Turbo",
                        showscale=True, opacity=0.85, colorbar=dict(title="Avg Price (Cr)")),
            hovertemplate="<b>%{text}</b><br><br>Average Price : \u20b9 %{customdata[0]:.2f} Cr<extra></extra>",
        ))
        fig.update_layout(
            mapbox=dict(style="carto-positron",
                        center=dict(lat=float(map_df[lat].mean()), lon=float(map_df[lon].mean())), zoom=9.5),
            height=520, margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return _plotly_json(fig)

    def _area_vs_price(self, df: pd.DataFrame, cols: dict, filters: dict) -> dict[str, Any] | None:
        price, area = cols.get("price"), cols.get("built_up_area")
        if not price or not area:
            return None

        ptype, bedroom, sector = cols.get("property_type"), cols.get("bedRoom"), cols.get("sector")
        filtered = df.copy()
        if ptype and filters.get("property_type") not in (None, "All"):
            filtered = filtered[filtered[ptype] == filters["property_type"]]
        if bedroom and filters.get("bedrooms") not in (None, "All"):
            filtered = filtered[filtered[bedroom] == filters["bedrooms"]]

        kwargs: dict[str, Any] = dict(x=area, y=price, height=560)
        if sector:
            kwargs["hover_name"] = sector
        if ptype:
            kwargs["color"] = ptype
        if bedroom:
            kwargs["size"] = bedroom

        fig = px.scatter(filtered, **kwargs)
        fig.update_layout(
            template="plotly_dark", xaxis_title="Built-up Area (sq ft)", yaxis_title="Price (Crore \u20b9)",
            title="Area vs Property Price", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(20,24,38,0.6)",
        )
        return _plotly_json(fig)

    def _bhk_distribution(self, df: pd.DataFrame, cols: dict, filters: dict) -> dict[str, Any] | None:
        bedroom, price, sector = cols.get("bedRoom"), cols.get("price"), cols.get("sector")
        if not bedroom or not price:
            return None

        pie_df = df.copy()
        if sector and filters.get("sector") not in (None, "All"):
            pie_df = pie_df[pie_df[sector] == filters["sector"]]
        if pie_df.empty:
            return {"empty": True}

        counts = pie_df[bedroom].value_counts().sort_index().reset_index()
        counts.columns = ["Bedroom", "Count"]

        fig = px.pie(counts, names="Bedroom", values="Count", hole=0.55, color="Bedroom",
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_traces(textposition="inside", textinfo="percent+label",
                           hovertemplate="<b>%{label} BHK</b><br>Properties : %{value}<br>Percentage : %{percent}<extra></extra>")
        fig.update_layout(height=480, paper_bgcolor="rgba(0,0,0,0)", showlegend=True)

        stats = pie_df.groupby(bedroom).agg(Properties=(bedroom, "count"), Avg_Price=(price, "mean")).reset_index()
        stats["Avg_Price"] = stats["Avg_Price"].round(2)

        return {
            "chart": _plotly_json(fig),
            "summary": stats.to_dict(orient="records"),
        }

    def _bedroom_price_box(self, df: pd.DataFrame, cols: dict, filters: dict) -> dict[str, Any] | None:
        bedroom, price, sector = cols.get("bedRoom"), cols.get("price"), cols.get("sector")
        if not bedroom or not price:
            return None

        box_df = df.copy()
        if sector and filters.get("sector") not in (None, "All"):
            box_df = box_df[box_df[sector] == filters["sector"]]
        if box_df.empty:
            return {"empty": True}

        fig = px.box(box_df, x=bedroom, y=price, color=bedroom, points="outliers",
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(title="Bedroom vs Property Price", xaxis_title="Bedrooms",
                           yaxis_title="Price (Crore \u20b9)", height=560, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(20,24,38,0.6)")

        summary = box_df.groupby(bedroom).agg(
            Minimum=(price, "min"), Median=(price, "median"), Average=(price, "mean"), Maximum=(price, "max")
        ).round(2).reset_index()

        return {"chart": _plotly_json(fig), "summary": summary.to_dict(orient="records")}

    def _price_histogram(self, df: pd.DataFrame, cols: dict, filters: dict) -> dict[str, Any] | None:
        price, sector = cols.get("price"), cols.get("sector")
        if not price:
            return None

        hist_df = df.copy()
        if sector and filters.get("sector") not in (None, "All"):
            hist_df = hist_df[hist_df[sector] == filters["sector"]]
        if hist_df.empty:
            return {"empty": True}

        fig = px.histogram(hist_df, x=price, nbins=40, marginal="box", opacity=0.85,
                            color_discrete_sequence=["#8B7CF6"])
        fig.update_layout(title="Property Price Distribution", xaxis_title="Price (Crore \u20b9)",
                           yaxis_title="Number of Properties", height=520, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(20,24,38,0.6)")

        summary = hist_df[price].describe().round(2).to_frame().T.to_dict(orient="records")
        return {"chart": _plotly_json(fig), "summary": summary}

    # ------------------------------------------------------------------
    def get_wordcloud_image(self, city: str, sector: str = "All") -> str | None:
        """Returns a base64-encoded PNG (data URI) of the amenities word cloud,
        same source data/logic as the original matplotlib+wordcloud render."""
        _, wordcloud_df = city_manager.load_analytics_assets(city)
        if wordcloud_df is None:
            return None

        wc_cols = resolve_columns(wordcloud_df)
        sector_col, features_col = wc_cols.get("sector"), wc_cols.get("features")
        if not sector_col or not features_col:
            return None

        filtered = wordcloud_df.copy()
        if sector != "All":
            filtered = filtered[filtered[sector_col] == sector]

        all_features: list[str] = []
        for item in filtered[features_col]:
            try:
                all_features.extend(ast.literal_eval(item))
            except Exception:  # noqa: BLE001
                continue

        text = " ".join(all_features)
        if not text.strip():
            return None

        from wordcloud import WordCloud
        wc = WordCloud(width=1200, height=600, background_color=None, mode="RGBA",
                        colormap="viridis").generate(text)

        buf = io.BytesIO()
        wc.to_image().save(buf, format="PNG")
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"


analytics_service = AnalyticsService()
