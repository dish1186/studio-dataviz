"""UTCI Step 4: UTC -> local time, daily maximum UTCI per local calendar day, K -> °C -> °F.
A day is valid only if every local hour of that day has a value (23/25 on DST days) (Option 1, Dish).
Days start 1991-01-01 local (the UTC hours before local midnight on 1990-12-31 are not used).
D12 (Dish): all 24 UTC hours of 2021-04-29 are treated as missing (corrupt day in the CDS time series:
hourly pattern anti-correlated with neighbouring days in all 12 cities). Step 3 files are not changed.
Read-only on inputs. Output: data/processed/utci/step04_daily_max/utci_<city>_daily_max.csv (+ summary)."""
import pathlib, numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
IN = ROOT/"data/processed/utci/step03_city_hourly"
OUT = ROOT/"data/processed/utci/step04_daily_max"; OUT.mkdir(parents=True, exist_ok=True)
TZ = {"losangeles":"America/Los_Angeles", "sandiego":"America/Los_Angeles", "bakersfield":"America/Los_Angeles",
      "sanfrancisco":"America/Los_Angeles", "fresno":"America/Los_Angeles", "eugene":"America/Los_Angeles",
      "phoenix":"America/Phoenix",          # MST all year, UTC-7 (as METAR)
      "brownsville":"America/Chicago", "detroit":"America/Detroit", "annarbor":"America/Detroit",
      "boston":"America/New_York", "fairbanks":"America/Anchorage"}
CITIES = ["losangeles","phoenix","sandiego","detroit","bakersfield","sanfrancisco",
          "fresno","boston","eugene","fairbanks","brownsville","annarbor"]   # D10 order
FIRST = pd.Timestamp("1991-01-01")
BAD_UTC_DAYS = ["2021-04-29"]   # D12

summary = []
for city in CITIES:
    h = pd.read_csv(IN/f"utci_{city}_hourly.csv.gz")
    bad_hours = h.time_utc.str[:10].isin(BAD_UTC_DAYS)
    h.loc[bad_hours, "utci_k"] = np.nan                          # D12: set aside, counted below
    t = pd.to_datetime(h.time_utc).dt.tz_localize("UTC").dt.tz_convert(TZ[city])
    h["date"] = t.dt.date; h["hour_local"] = t.dt.hour
    # all local days from 1991-01-01 to the local date of the last UTC hour
    days = pd.date_range(FIRST, pd.Timestamp(h.date.max()), freq="D")
    start = days.tz_localize(TZ[city]); end = (days + pd.Timedelta(days=1)).tz_localize(TZ[city])
    expected = pd.Series(((end - start) / pd.Timedelta(hours=1)).astype(int), index=days.date)
    h = h[h.date >= FIRST.date()]
    g = h.groupby("date")
    d = pd.DataFrame({"n_hours": g.utci_k.count()}).reindex(days.date)
    d["n_hours"] = d.n_hours.fillna(0).astype(int)
    d["n_hours_expected"] = expected
    idx = h.dropna(subset=["utci_k"]).groupby("date").utci_k.idxmax()
    d["utci_max_k"] = h.loc[idx, "utci_k"].set_axis(idx.index).reindex(days.date)
    d["hour_of_max_local"] = h.loc[idx, "hour_local"].set_axis(idx.index).reindex(days.date)
    d["valid"] = (d.n_hours == d.n_hours_expected).astype(int)
    d.loc[d.valid == 0, ["utci_max_k", "hour_of_max_local"]] = np.nan
    d["utci_max_c"] = (d.utci_max_k - 273.15).round(2)
    d["utci_max_f"] = ((d.utci_max_k - 273.15) * 9/5 + 32).round(2)     # from unrounded °C
    d["hour_of_max_local"] = d.hour_of_max_local.astype("Int64")
    d = d.rename_axis("date").reset_index()
    d[["date","utci_max_c","utci_max_f","hour_of_max_local","n_hours","n_hours_expected","valid"]] \
        .to_csv(OUT/f"utci_{city}_daily_max.csv", index=False)
    bad = d[d.valid == 0]
    summary.append(dict(city=city, tz=TZ[city], n_hours_set_aside_D12=int(bad_hours.sum()), first_day=d.date.iloc[0], last_day=d.date.iloc[-1], n_days=len(d),
                        n_valid=int(d.valid.sum()), invalid_days="; ".join(map(str, bad.date)),
                        days_23h=int((d.n_hours_expected == 23).sum()), days_25h=int((d.n_hours_expected == 25).sum()),
                        hottest_day=d.loc[d.utci_max_c.idxmax(), "date"], hottest_c=d.utci_max_c.max(),
                        typical_hour_of_max=int(d.hour_of_max_local.mode()[0])))
s = pd.DataFrame(summary); s.to_csv(OUT/"step04_summary.csv", index=False); print(s.to_string(index=False))
