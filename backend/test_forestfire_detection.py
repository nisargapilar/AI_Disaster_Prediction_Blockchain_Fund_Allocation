import asyncio

from modules.forest_fire.detection import (
    _fetch_firms_rows,
    detect_now
)


# ============================================================
# TEST NASA FIRMS FIRE DETECTION
# ============================================================

async def main():

    print("\n" + "=" * 60)
    print("SEARCHING FOR ACTIVE NASA FIRMS FOREST FIRE")
    print("=" * 60)

    # India bounding box
    #
    # west, south, east, north
    #
    india_area = "68,8,97,37"

    print("\nSearching FIRMS for India...")
    print("Area:", india_area)

    try:

        rows = await _fetch_firms_rows(
            india_area,
            "1"
        )

    except Exception as e:

        print("\nFIRMS ERROR:")
        print(e)

        return


    print(
        "\nActive hotspots found:",
        len(rows)
    )


    # ========================================================
    # NO FIRE FOUND
    # ========================================================

    if not rows:

        print(
            "\nNo active FIRMS hotspots found in India."
        )

        return


    # ========================================================
    # SHOW FIRST HOTSPOT
    # ========================================================

    row = rows[0]

    print("\n" + "=" * 60)
    print("ACTIVE FIRMS HOTSPOT FOUND")
    print("=" * 60)

    print(
        "\nLatitude:",
        row.get("latitude")
    )

    print(
        "Longitude:",
        row.get("longitude")
    )

    print(
        "Brightness:",
        row.get("brightness")
        or row.get("bright_ti4")
    )

    print(
        "FRP:",
        row.get("frp")
    )

    print(
        "Confidence:",
        row.get("confidence")
    )

    print(
        "Satellite:",
        row.get("satellite")
    )

    print(
        "Instrument:",
        row.get("instrument")
    )

    print(
        "Acquisition date:",
        row.get("acq_date")
    )

    print(
        "Acquisition time:",
        row.get("acq_time")
    )


    # ========================================================
    # USE HOTSPOT LOCATION
    # ========================================================

    lat = float(
        row["latitude"]
    )

    lon = float(
        row["longitude"]
    )


    print("\n" + "=" * 60)
    print("CALLING detect_now()")
    print("=" * 60)

    print(
        f"\nLatitude : {lat}"
    )

    print(
        f"Longitude: {lon}"
    )


    try:

        results = await detect_now(
            lat=lat,
            lon=lon,
            radius_deg=0.5
        )

    except Exception as e:

        print("\nDETECTION ERROR:")
        print(e)

        return


    # ========================================================
    # RESULTS
    # ========================================================

    print("\n" + "=" * 60)
    print("FIRMS FIRE DETECTION RESULT")
    print("=" * 60)

    print(
        "\nReturned records:",
        len(results)
    )


    for index, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\n--- Record {index} ---"
        )

        print(
            "Event ID:",
            result.get("event_id")
        )

        print(
            "Disaster type:",
            result.get("disaster_type")
        )

        print(
            "Source:",
            result.get("source")
        )

        print(
            "Severity:",
            result.get("severity_tier")
        )

        print(
            "Risk score:",
            result.get("risk_score")
        )

        print(
            "Fund status:",
            result.get("fund_status")
        )

        print(
            "Location:",
            result.get("location")
        )

        print(
            "Input data:",
            result.get("input_data")
        )


    print("\n" + "=" * 60)
    print("REAL FIRE DETECTION TEST FINISHED")
    print("=" * 60)


if __name__ == "__main__":

    asyncio.run(main())